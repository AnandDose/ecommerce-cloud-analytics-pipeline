import pandas as pd
import numpy as np
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import statsmodels.api as sm

# ==========================================
# 1. CONNECT TO SNOWFLAKE & FETCH DATA
# ==========================================
print("Connecting to Snowflake...")
conn = snowflake.connector.connect(
    user='YOUR_SNOWFLAKE_USERNAME',
    password='YOUR_SNOWFLAKE_PASSWORD',
    account='YOUR_SNOWFLAKE_ACCOUNT_ID', 
    warehouse='ecommerce_wh',
    database='ecommerce_db',
    schema='raw'
)

print("Fetching transaction datasets for statistical modeling...")
query = """
    SELECT t.transaction_id, t.user_id, t.product_id, t.quantity, t.price_paid, t.transaction_date, p.category
    FROM transactions t
    JOIN products p ON t.product_id = p.product_id
"""
df = pd.read_sql(query, conn)
df.columns = df.columns.str.lower()
print(f"Successfully pulled {len(df)} transactions into Python DataFrame.\n")


# ==========================================
# 2. STATS MODEL 1: PRICE ELASTICITY OF DEMAND
# ==========================================
print("--- Running Log-Log Linear Regression for Price Elasticity ---")
elasticity_results = []

for category in df['category'].unique():
    cat_df = df[df['category'] == category].copy()
    
    # Group to see total quantities sold at specific execution price points
    grouped = cat_df.groupby('price_paid')['quantity'].sum().reset_index()
    grouped = grouped[grouped['quantity'] > 0] # Avoid log(0)
    
    # Log-Transforming features for constant elasticity model: Log(Q) = B0 + B1 * Log(P)
    X = np.log(grouped['price_paid'])
    X = sm.add_constant(X) # Adds Intercept
    y = np.log(grouped['quantity'])
    
    model = sm.OLS(y, X).fit()
    price_coefficient = model.params.iloc[1] # This is our elasticity value
    p_value = model.pvalues.iloc[1]
    
    # Business logic evaluation
    if price_coefficient < -1:
        market_status = 'Elastic (Highly Price Sensitive)'
    elif -1 <= price_coefficient <= 0:
        market_status = 'Inelastic (Price Insensitive)'
    else:
        market_status = 'Positive Relationship (Anomaly)'
        
    elasticity_results.append({
        'CATEGORY': category,
        'ELASTICITY_COEFFICIENT': float(round(price_coefficient, 3)),
        'P_VALUE': float(round(p_value, 4)),
        'MARKET_STATUS': market_status
    })

df_elasticity = pd.DataFrame(elasticity_results)
print(df_elasticity.to_string(index=False))
print("\n" + "="*60 + "\n")


# ==========================================
# 3. STATS MODEL 2: CUSTOMER CHURN RISK (RFM)
# ==========================================
print("--- Computing Statistical Quantiles for Churn Segmentation ---")
df['transaction_date'] = pd.to_datetime(df['transaction_date'])
max_date = df['transaction_date'].max() + pd.Timedelta(days=1)

# Aggregating metrics per individual consumer
rfm = df.groupby('user_id').agg({
    'transaction_date': lambda x: (max_date - x.max()).days, # Recency
    'transaction_id': 'count',                                   # Frequency
    'price_paid': 'sum'                                           # Monetary
}).reset_index()

rfm.columns = ['USER_ID', 'RECENCY', 'FREQUENCY', 'MONETARY']

# Statistical percentile splits using Quantiles (1 to 4 scaling metrics)
rfm['R_SCORE'] = pd.qcut(rfm['RECENCY'], 4, labels=[1, 2, 3, 4]).astype(int)
rfm['F_SCORE'] = pd.qcut(rfm['FREQUENCY'].rank(method='first'), 4, labels=[4, 3, 2, 1]).astype(int)
rfm['M_SCORE'] = pd.qcut(rfm['MONETARY'], 4, labels=[4, 3, 2, 1]).astype(int)

# Summing scores to determine ultimate Churn Matrix
rfm['RISK_SCORE_TOTAL'] = rfm['R_SCORE'] + rfm['F_SCORE'] + rfm['M_SCORE']

def segment_churn(score):
    if score >= 9: return 'Critical Churn Risk'
    elif score >= 6: return 'Medium Risk (Drifting)'
    else: return 'Low Risk (Loyal)'

rfm['CHURN_SEGMENT'] = rfm['RISK_SCORE_TOTAL'].apply(segment_churn)
print(rfm['CHURN_SEGMENT'].value_counts())


# ==========================================
# 4. WRITE INSIGHTS BACK TO SNOWFLAKE
# ==========================================
print("\nWriting processed analytical layers back to Snowflake target schema...")

# Write back tables into the database under 'ANALYTICS' schema
success_elasticity, nchunks_e, nrows_e, _ = write_pandas(
    conn, df_elasticity, table_name='PRICE_ELASTICITY', schema='ANALYTICS', auto_create_table=True
)

success_churn, nchunks_c, nrows_c, _ = write_pandas(
    conn, rfm, table_name='USER_CHURN_SEGMENTS', schema='ANALYTICS', auto_create_table=True
)

conn.close()
print(f"Success! Uploaded {nrows_e} price elasticity rows and {nrows_c} customer segmentation rows.")