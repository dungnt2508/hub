-- Remove stock availability fields for catalog products

ALTER TABLE products
    DROP COLUMN IF EXISTS stock_status,
    DROP COLUMN IF EXISTS stock_quantity;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'product_stock_status') THEN
        DROP TYPE product_stock_status;
    END IF;
END$$;
