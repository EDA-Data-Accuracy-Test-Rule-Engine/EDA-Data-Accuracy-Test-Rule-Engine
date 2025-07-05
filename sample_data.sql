-- Sample data creation script for EDA Rule Engine testing
-- This script creates tables and sample data to test various validation rules

-- 1. Users table for email and age validation
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    age INTEGER,
    phone TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Orders table for statistical comparison
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    total_amount DECIMAL(10,2),
    order_date DATE,
    status TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 3. Order items table for cross-table validation
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    product_name TEXT,
    quantity INTEGER,
    price DECIMAL(10,2),
    line_total DECIMAL(10,2),
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- 4. Products table for inventory validation
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    stock_quantity INTEGER,
    price DECIMAL(10,2),
    category TEXT
);

-- 5. Inventory log table for cross-table comparison
CREATE TABLE IF NOT EXISTS inventory_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    current_stock INTEGER,
    log_date DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Insert sample users data (mix of valid and invalid data for testing)
INSERT INTO users (name, email, age, phone) VALUES
-- Valid data
('John Doe', 'john.doe@example.com', 25, '+1-555-0123'),
('Jane Smith', 'jane.smith@company.org', 30, '+1-555-0124'),
('Bob Johnson', 'bob.johnson@test.net', 35, '+1-555-0125'),
('Alice Brown', 'alice.brown@domain.com', 28, '+1-555-0126'),
('Charlie Wilson', 'charlie.wilson@email.co.uk', 32, '+1-555-0127'),

-- Invalid emails for testing email validation rule
('Invalid Email 1', 'invalid-email', 25, '+1-555-0128'),
('Invalid Email 2', 'missing@domain', 30, '+1-555-0129'), 
('Invalid Email 3', 'no-extension@domain', 35, '+1-555-0130'),
('Invalid Email 4', '@missing-local.com', 28, '+1-555-0131'),
('Invalid Email 5', 'spaces in@email.com', 32, '+1-555-0132'),

-- Invalid ages for testing age range validation
('Too Young', 'young@example.com', 15, '+1-555-0133'),
('Too Old', 'old@example.com', 150, '+1-555-0134'),
('Negative Age', 'negative@example.com', -5, '+1-555-0135'),

-- NULL values for testing
('NULL Email', NULL, 25, '+1-555-0136'),
('NULL Age', 'null.age@example.com', NULL, '+1-555-0137'),

-- More valid data to increase sample size
('David Lee', 'david.lee@example.com', 27, '+1-555-0138'),
('Emma Davis', 'emma.davis@company.org', 29, '+1-555-0139'),
('Frank Miller', 'frank.miller@test.net', 31, '+1-555-0140'),
('Grace Taylor', 'grace.taylor@domain.com', 26, '+1-555-0141'),
('Henry Anderson', 'henry.anderson@email.com', 33, '+1-555-0142');

-- Insert sample orders data
INSERT INTO orders (user_id, total_amount, order_date, status) VALUES
(1, 150.00, '2025-07-01', 'completed'),
(2, 250.50, '2025-07-02', 'completed'),
(3, 89.99, '2025-07-03', 'pending'),
(4, 320.75, '2025-07-04', 'completed'),
(5, 99.00, '2025-07-05', 'shipped'),
(1, 175.25, '2025-07-05', 'pending'),
(2, 445.80, '2025-07-04', 'completed'),
(3, 67.50, '2025-07-03', 'cancelled'),
(4, 210.00, '2025-07-02', 'completed'),
(5, 156.75, '2025-07-01', 'shipped');

-- Insert order items data (some with intentional inconsistencies for testing)
INSERT INTO order_items (order_id, product_name, quantity, price, line_total) VALUES
-- Order 1 items (total should be 150.00)
(1, 'Product A', 2, 50.00, 100.00),
(1, 'Product B', 1, 50.00, 50.00),

-- Order 2 items (total should be 250.50)
(2, 'Product C', 3, 75.00, 225.00),
(2, 'Product D', 1, 25.50, 25.50),

-- Order 3 items (total should be 89.99 but will have inconsistency)
(3, 'Product A', 1, 50.00, 50.00),
(3, 'Product E', 1, 35.00, 35.00), -- Missing 4.99 to match order total

-- Order 4 items (total should be 320.75)
(4, 'Product F', 4, 80.00, 320.00),
(4, 'Product G', 1, 0.75, 0.75),

-- Order 5 items (intentional mismatch for testing)
(5, 'Product H', 2, 45.00, 90.00), -- Order total is 99.00 but items sum to 90.00

-- More order items
(6, 'Product A', 3, 50.00, 150.00),
(6, 'Product I', 1, 25.25, 25.25),

(7, 'Product J', 5, 89.16, 445.80),

(8, 'Product K', 2, 33.75, 67.50),

(9, 'Product L', 1, 210.00, 210.00),

(10, 'Product M', 4, 39.19, 156.76); -- Slight rounding difference

-- Insert products data
INSERT INTO products (product_name, stock_quantity, price, category) VALUES
('Product A', 100, 50.00, 'Electronics'),
('Product B', 50, 50.00, 'Electronics'),
('Product C', 75, 75.00, 'Clothing'),
('Product D', 200, 25.50, 'Books'),
('Product E', 30, 35.00, 'Home'),
('Product F', 25, 80.00, 'Electronics'),
('Product G', 500, 0.75, 'Accessories'),
('Product H', 60, 45.00, 'Sports'),
('Product I', 150, 25.25, 'Books'),
('Product J', 40, 89.16, 'Electronics'),
('Product K', 80, 33.75, 'Clothing'),
('Product L', 15, 210.00, 'Electronics'),
('Product M', 120, 39.19, 'Home');

-- Insert inventory log data (some with intentional discrepancies)
INSERT INTO inventory_log (product_id, current_stock, log_date) VALUES
-- Matching stock quantities
(1, 100, '2025-07-05'),
(2, 50, '2025-07-05'),
(3, 75, '2025-07-05'),
(4, 200, '2025-07-05'),

-- Mismatched stock quantities for testing
(5, 35, '2025-07-05'), -- Product E shows 30 in products but 35 in log
(6, 20, '2025-07-05'), -- Product F shows 25 in products but 20 in log
(7, 500, '2025-07-05'),
(8, 65, '2025-07-05'), -- Product H shows 60 in products but 65 in log

-- Missing entries for some products to test data completeness
(11, 80, '2025-07-05'),
(12, 15, '2025-07-05'),
(13, 125, '2025-07-05'); -- Product M shows 120 in products but 125 in log