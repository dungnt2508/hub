#!/bin/bash
# ============================================
# Script tạo database và user cho Catalog Service
# ============================================
# Script này sẽ tự động chạy khi PostgreSQL khởi động lần đầu
# (thông qua /docker-entrypoint-initdb.d)
# ============================================

set -e

# Tạo user cho catalog service (nếu chưa tồn tại)
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'catalog_user') THEN
            CREATE USER catalog_user WITH PASSWORD 'catalog_pw';
        END IF;
    END
    \$\$;
EOSQL

# Tạo database cho catalog service (nếu chưa tồn tại)
# Kiểm tra xem database đã tồn tại chưa
DB_EXISTS=$(psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -tAc "SELECT 1 FROM pg_database WHERE datname='catalog_db'")

if [ -z "$DB_EXISTS" ]; then
    echo "Đang tạo database catalog_db..."
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        CREATE DATABASE catalog_db
            OWNER catalog_user
            ENCODING 'UTF8'
            LC_COLLATE 'en_US.utf8'
            LC_CTYPE 'en_US.utf8'
            TEMPLATE template0;
EOSQL
    echo "Database catalog_db đã được tạo."
else
    echo "Database catalog_db đã tồn tại, bỏ qua."
fi

# Grant privileges (chạy trên database vừa tạo)
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "catalog_db" <<-EOSQL
    GRANT ALL PRIVILEGES ON DATABASE catalog_db TO catalog_user;
EOSQL

echo "Catalog database và user đã được tạo thành công!"

