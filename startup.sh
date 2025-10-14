#!/bin/bash

# Azure Web App startup script
# Installs ODBC driver if needed, then starts Gunicorn

set -e

echo "Starting Azure Web App startup script..."

# Check if we're on Linux (Azure App Service)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux environment, checking ODBC driver..."
    
    # Check if ODBC driver 18 is already installed
    if ! command -v sqlcmd &> /dev/null || ! dpkg -l | grep -q msodbcsql18; then
        echo "Installing ODBC driver..."
        
        # Update package list
        apt-get update -y
        
        # Install unixodbc
        apt-get install -y unixodbc unixodbc-dev
        
        # Try to install ODBC Driver 18 for SQL Server
        if ! curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -; then
            echo "Failed to add Microsoft key, trying alternative method..."
        fi
        
        # Add Microsoft repository
        curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
        
        # Update package list again
        apt-get update -y
        
        # Try ODBC Driver 18 first
        if apt-get install -y msodbcsql18; then
            echo "Successfully installed ODBC Driver 18"
            export ODBC_DRIVER="ODBC Driver 18 for SQL Server"
        else
            echo "ODBC Driver 18 not available, trying Driver 17..."
            if apt-get install -y msodbcsql17; then
                echo "Successfully installed ODBC Driver 17"
                export ODBC_DRIVER="ODBC Driver 17 for SQL Server"
            else
                echo "Warning: Could not install ODBC drivers. App may not work properly."
            fi
        fi
        
        # Set ODBC environment variables
        export ODBCINSTINI=/etc/odbcinst.ini
        export ODBCSYSINI=/etc
    else
        echo "ODBC driver already installed"
    fi
else
    echo "Non-Linux environment detected, skipping ODBC installation"
fi

# Set default port if not provided
export PORT=${PORT:-8000}

echo "Starting Gunicorn on port $PORT..."

# Start the application
exec gunicorn --chdir src "app:create_app()" \
    --bind 0.0.0.0:$PORT \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
