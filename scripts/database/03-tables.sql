-- Workshop table creation

CREATE TABLE sales_data (
    sale_id     bigint,
    product_id  bigint,
    customer_id bigint,
    sale_amount numeric(12,2),
    sale_date   date
);


INSERT INTO sales_data (sale_id, product_id, customer_id, sale_amount, sale_date)
SELECT 
    generate_series(1, 5000000) as sale_id,
    floor(random() * 1000 + 1)::bigint as product_id,
    floor(random() * 10000 + 1)::bigint as customer_id,
    round((random() * 1000)::numeric, 2) as sale_amount,
    (timestamp '2020-01-01' + 
        (random() * (timestamp '2025-11-30' - timestamp '2020-01-01'))::interval)::date as sale_date
;

-- Create indexes
CREATE INDEX sales_data_sale_date_idx ON sales_data (sale_date);
CREATE INDEX sales_data_sale_id_idx ON sales_data (sale_id);

-- Create orders table
CREATE TABLE orders (
   order_id SERIAL PRIMARY KEY,
   customer_id INT,
   order_date DATE,
   status VARCHAR(20),
   total_amount DECIMAL(10,2),
   region VARCHAR(50)
);

-- Insert 1 million sample orders
INSERT INTO orders (customer_id, order_date, status, total_amount, region)
SELECT
   (random() * 10000)::INT as customer_id,
   CURRENT_DATE - (random() * 365)::INT as order_date,
   CASE (random() * 4)::INT
       WHEN 0 THEN 'pending'
       WHEN 1 THEN 'processing'
       WHEN 2 THEN 'shipped'
       ELSE 'delivered'
   END as status,
   (random() * 1000)::DECIMAL(10,2) as total_amount,
   CASE (random() * 5)::INT
       WHEN 0 THEN 'North'
       WHEN 1 THEN 'South'
       WHEN 2 THEN 'East'
       WHEN 3 THEN 'West'
       ELSE 'Central'
   END as region
FROM generate_series(1, 1000000);
-- Check data count
SELECT COUNT(*) FROM orders;
-- Update statistics
ANALYZE orders;
-- Create individual indexes
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);