-- 1. DATABASE & WAREHOUSE SETUP
CREATE OR REPLACE WAREHOUSE ecommerce_wh 
  WITH WAREHOUSE_SIZE = 'XSMALL' 
  AUTO_SUSPEND = 300 
  AUTO_RESUME = TRUE;

CREATE OR REPLACE DATABASE ecommerce_db;
CREATE OR REPLACE SCHEMA ecommerce_db.raw;

USE WAREHOUSE ecommerce_wh;
USE DATABASE ecommerce_db;
USE SCHEMA raw;

-- 2. FILE FORMAT SETUP
CREATE OR REPLACE FILE FORMAT csv_format
  TYPE = 'CSV'
  FIELD_DELIMITER = ','
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  NULL_IF = ('NULL', 'null');

-- 3. RELATIONAL TABLES SETUP
CREATE OR REPLACE TABLE users (
    user_id INT,
    name STRING,
    email STRING,
    country STRING,
    signup_date DATE
);

CREATE OR REPLACE TABLE products (
    product_id INT,
    product_name STRING,
    category STRING,
    base_price FLOAT
);

CREATE OR REPLACE TABLE transactions (
    transaction_id INT,
    user_id INT,
    product_id INT,
    transaction_date TIMESTAMP,
    quantity INT,
    price_paid FLOAT
);

-- 4. DIRECT CLOUD STAGE CONNECTION
CREATE OR REPLACE STAGE s3_stage_direct
  URL = 's3://ecommerce-analytics-project-anand/'
  CREDENTIALS = (
    AWS_KEY_ID = 'YOUR_AWS_ACCESS_KEY_ID' 
    AWS_SECRET_KEY = 'YOUR_AWS_SECRET_ACCESS_KEY'
  )
  FILE_FORMAT = csv_format;

-- 5. DATA PIPELINE INGESTION
COPY INTO users FROM @s3_stage_direct/raw_data/users.csv;
COPY INTO products FROM @s3_stage_direct/raw_data/products.csv;
COPY INTO transactions FROM @s3_stage_direct/raw_data/transactions.csv;

-- 6. DATA VERIFICATION
SELECT * FROM users LIMIT 5;
SELECT * FROM products LIMIT 5;
SELECT * FROM transactions LIMIT 5;



-- Create a dedicated schema for our processed insights
CREATE OR REPLACE SCHEMA ecommerce_db.analytics;

-- Verify both schemas now exist under your database
SHOW SCHEMAS IN DATABASE ecommerce_db;