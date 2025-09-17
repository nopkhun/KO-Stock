-- Stock Management System Database Schema
-- PostgreSQL Database Initialization Script

-- Create database (run this separately if needed)
-- CREATE DATABASE stock_management;

-- Use the database
-- \c stock_management;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
CREATE TYPE user_role AS ENUM ('admin', 'manager', 'warehouse_staff', 'store_staff');
CREATE TYPE transaction_type AS ENUM ('stock_in', 'transfer', 'adjustment', 'daily_count');

-- 1. Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role user_role NOT NULL DEFAULT 'store_staff',
    location_id UUID,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Locations table (Central Warehouse + Stores)
CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('warehouse', 'store')),
    address TEXT,
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Suppliers table
CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Brands table
CREATE TABLE brands (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Categories table
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Products table
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    brand_id UUID REFERENCES brands(id),
    supplier_id UUID REFERENCES suppliers(id),
    category_id UUID REFERENCES categories(id),
    unit VARCHAR(20) NOT NULL DEFAULT 'pcs',
    reorder_point INTEGER DEFAULT 0,
    image_url VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Stock table (Current stock levels by location)
CREATE TABLE stock (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id),
    location_id UUID NOT NULL REFERENCES locations(id),
    quantity INTEGER NOT NULL DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, location_id)
);

-- 8. Stock transactions table (All stock movements)
CREATE TABLE stock_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_type transaction_type NOT NULL,
    product_id UUID NOT NULL REFERENCES products(id),
    from_location_id UUID REFERENCES locations(id),
    to_location_id UUID REFERENCES locations(id),
    quantity INTEGER NOT NULL,
    reference_number VARCHAR(50),
    notes TEXT,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. Daily stock counts table (For daily usage calculation)
CREATE TABLE daily_stock_counts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id),
    location_id UUID NOT NULL REFERENCES locations(id),
    count_date DATE NOT NULL,
    opening_stock INTEGER NOT NULL DEFAULT 0,
    transfers_in INTEGER NOT NULL DEFAULT 0,
    counted_stock INTEGER NOT NULL,
    calculated_usage INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    counted_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, location_id, count_date)
);

-- 10. Purchase suggestions table
CREATE TABLE purchase_suggestions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id),
    supplier_id UUID NOT NULL REFERENCES suppliers(id),
    current_stock INTEGER NOT NULL,
    reorder_point INTEGER NOT NULL,
    suggested_quantity INTEGER NOT NULL,
    average_daily_usage DECIMAL(10,2) DEFAULT 0,
    days_of_stock INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'ordered', 'cancelled')),
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add foreign key constraints
ALTER TABLE users ADD CONSTRAINT fk_users_location FOREIGN KEY (location_id) REFERENCES locations(id);

-- Create indexes for better performance
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_brand ON products(brand_id);
CREATE INDEX idx_products_supplier ON products(supplier_id);
CREATE INDEX idx_stock_product_location ON stock(product_id, location_id);
CREATE INDEX idx_stock_transactions_product ON stock_transactions(product_id);
CREATE INDEX idx_stock_transactions_created_at ON stock_transactions(created_at);
CREATE INDEX idx_daily_counts_date ON daily_stock_counts(count_date);
CREATE INDEX idx_daily_counts_location ON daily_stock_counts(location_id);
CREATE INDEX idx_purchase_suggestions_status ON purchase_suggestions(status);

-- Create triggers for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_locations_updated_at BEFORE UPDATE ON locations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_suppliers_updated_at BEFORE UPDATE ON suppliers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_brands_updated_at BEFORE UPDATE ON brands FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_purchase_suggestions_updated_at BEFORE UPDATE ON purchase_suggestions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert initial data
INSERT INTO locations (name, code, type, address) VALUES
('Central Warehouse', 'CW001', 'warehouse', '123 Main Street, Bangkok'),
('Store A', 'SA001', 'store', '456 Branch Road, Bangkok'),
('Store B', 'SB001', 'store', '789 Mall Avenue, Bangkok'),
('Store C', 'SC001', 'store', '321 Shopping Center, Bangkok'),
('Store D', 'SD001', 'store', '654 Market Street, Bangkok'),
('Store E', 'SE001', 'store', '987 Plaza Drive, Bangkok');

INSERT INTO categories (name, code, description) VALUES
('Electronics', 'ELEC', 'Electronic devices and accessories'),
('Clothing', 'CLOTH', 'Apparel and fashion items'),
('Food & Beverage', 'F&B', 'Food and drink products'),
('Home & Garden', 'H&G', 'Home improvement and garden supplies'),
('Health & Beauty', 'H&B', 'Health and beauty products');

INSERT INTO brands (name, code, description) VALUES
('Samsung', 'SAMSUNG', 'Samsung Electronics'),
('Apple', 'APPLE', 'Apple Inc.'),
('Nike', 'NIKE', 'Nike Sportswear'),
('Adidas', 'ADIDAS', 'Adidas Sports'),
('Coca-Cola', 'COKE', 'The Coca-Cola Company');

INSERT INTO suppliers (name, code, contact_person, phone, email) VALUES
('Tech Distributor Co.', 'TECH001', 'John Smith', '02-123-4567', 'john@techdist.com'),
('Fashion Wholesale Ltd.', 'FASH001', 'Jane Doe', '02-234-5678', 'jane@fashwhole.com'),
('Food Supply Chain', 'FOOD001', 'Mike Johnson', '02-345-6789', 'mike@foodsupply.com'),
('Home Products Inc.', 'HOME001', 'Sarah Wilson', '02-456-7890', 'sarah@homeproducts.com'),
('Beauty Distributors', 'BEAUTY001', 'Lisa Brown', '02-567-8901', 'lisa@beautydist.com');

-- Insert admin user (password: admin123 - should be hashed in real implementation)
INSERT INTO users (username, email, password_hash, full_name, role) VALUES
('admin', 'admin@stockmanagement.com', '$2b$10$example_hash_here', 'System Administrator', 'admin');

