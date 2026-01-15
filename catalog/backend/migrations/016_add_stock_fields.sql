-- Add stock availability fields for catalog products

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'product_stock_status') THEN
        CREATE TYPE product_stock_status AS ENUM ('in_stock', 'out_of_stock', 'unknown');
    END IF;
END$$;

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS stock_status product_stock_status DEFAULT 'unknown',
    ADD COLUMN IF NOT EXISTS stock_quantity INTEGER;

CREATE INDEX IF NOT EXISTS idx_products_stock_status ON products(stock_status);
CREATE INDEX IF NOT EXISTS idx_products_stock_quantity ON products(stock_quantity);
