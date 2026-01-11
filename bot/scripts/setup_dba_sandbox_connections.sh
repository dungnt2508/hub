#!/bin/bash

# DBA Sandbox Connection Setup Script
# This script sets up database connections for DBA Sandbox

set -e

echo "================================"
echo "DBA Sandbox Connection Setup"
echo "================================"
echo ""

# Check if environment variable already set
if [ -n "$DBA_CONNECTIONS_JSON" ]; then
    echo "✓ DBA_CONNECTIONS_JSON already set"
    echo "Current value:"
    echo "$DBA_CONNECTIONS_JSON" | python -m json.tool 2>/dev/null || echo "$DBA_CONNECTIONS_JSON"
    echo ""
    read -p "Do you want to override? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing configuration"
        exit 0
    fi
fi

echo "Select database types to configure:"
echo "1) SQL Server (Local)"
echo "2) PostgreSQL (Local)"
echo "3) MySQL (Local)"
echo "4) All of above"
echo "5) Custom configuration"
echo ""
read -p "Choice (1-5): " choice

case $choice in
    1)
        # SQL Server only
        CONNECTIONS='[
  {
    "id": "dev-1",
    "name": "DEV_DB",
    "db_type": "sql_server",
    "host": "localhost",
    "port": 1433,
    "database": "master",
    "username": "sa",
    "password": "YourPassword123",
    "is_production": false,
    "description": "Local development database"
  }
]'
        ;;
    2)
        # PostgreSQL only
        CONNECTIONS='[
  {
    "id": "dev-pg",
    "name": "DEV_POSTGRES",
    "db_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database": "postgres",
    "username": "postgres",
    "password": "postgres",
    "is_production": false,
    "description": "Local PostgreSQL"
  }
]'
        ;;
    3)
        # MySQL only
        CONNECTIONS='[
  {
    "id": "dev-mysql",
    "name": "DEV_MYSQL",
    "db_type": "mysql",
    "host": "localhost",
    "port": 3306,
    "database": "mysql",
    "username": "root",
    "password": "root",
    "is_production": false,
    "description": "Local MySQL"
  }
]'
        ;;
    4)
        # All three
        CONNECTIONS='[
  {
    "id": "dev-1",
    "name": "DEV_DB",
    "db_type": "sql_server",
    "host": "localhost",
    "port": 1433,
    "database": "master",
    "username": "sa",
    "password": "YourPassword123",
    "is_production": false,
    "description": "Local development database"
  },
  {
    "id": "dev-pg",
    "name": "DEV_POSTGRES",
    "db_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database": "postgres",
    "username": "postgres",
    "password": "postgres",
    "is_production": false,
    "description": "Local PostgreSQL"
  },
  {
    "id": "dev-mysql",
    "name": "DEV_MYSQL",
    "db_type": "mysql",
    "host": "localhost",
    "port": 3306,
    "database": "mysql",
    "username": "root",
    "password": "root",
    "is_production": false,
    "description": "Local MySQL"
  }
]'
        ;;
    5)
        # Custom - read from file
        read -p "Enter path to JSON file with connections: " json_file
        if [ ! -f "$json_file" ]; then
            echo "✗ File not found: $json_file"
            exit 1
        fi
        CONNECTIONS=$(cat "$json_file")
        ;;
    *)
        echo "✗ Invalid choice"
        exit 1
        ;;
esac

# Validate JSON
echo ""
echo "Validating JSON configuration..."
if echo "$CONNECTIONS" | python -m json.tool >/dev/null 2>&1; then
    echo "✓ JSON is valid"
else
    echo "✗ JSON validation failed"
    exit 1
fi

# Show configuration
echo ""
echo "Configuration to be set:"
echo "$CONNECTIONS" | python -m json.tool
echo ""

# Detect shell configuration file
SHELL_CONFIG=""
if [ -f "$HOME/.bashrc" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
elif [ -f "$HOME/.bash_profile" ]; then
    SHELL_CONFIG="$HOME/.bash_profile"
elif [ -f "$HOME/.zshrc" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
else
    SHELL_CONFIG="$HOME/.bashrc"
fi

read -p "Would you like to save to $SHELL_CONFIG? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Remove existing line if present
    if grep -q "export DBA_CONNECTIONS_JSON" "$SHELL_CONFIG"; then
        # Use sed to replace or comment out
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' '/export DBA_CONNECTIONS_JSON/d' "$SHELL_CONFIG"
        else
            sed -i '/export DBA_CONNECTIONS_JSON/d' "$SHELL_CONFIG"
        fi
    fi
    
    # Add new line
    echo "" >> "$SHELL_CONFIG"
    echo "# DBA Sandbox Connections (Added by setup script)" >> "$SHELL_CONFIG"
    echo "export DBA_CONNECTIONS_JSON='$CONNECTIONS'" >> "$SHELL_CONFIG"
    
    echo "✓ Configuration saved to $SHELL_CONFIG"
    echo ""
    echo "To apply immediately, run:"
    echo "  source $SHELL_CONFIG"
else
    echo "Skipping save to file"
    echo ""
    echo "To use, export the variable:"
    echo "  export DBA_CONNECTIONS_JSON='$CONNECTIONS'"
fi

# Set it for this session
export DBA_CONNECTIONS_JSON="$CONNECTIONS"

echo ""
echo "================================"
echo "✓ Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Verify database connections are running"
echo "2. Update passwords if needed"
echo "3. Start/restart backend: python -m uvicorn backend.interface.api:app"
echo "4. Open DBA Sandbox: http://localhost:3000/admin/domain-sandboxes/dba"
echo ""
