# Azure Web App Deployment Guide

This guide walks you through deploying the Flask RBAC application to Azure Web Apps using Azure SQL Database.

## Prerequisites

- Azure subscription
- GitHub repository with this code
- Azure CLI installed (optional, for command-line operations)

## Step 1: Create Azure SQL Database

### 1.1 Create SQL Server
1. Go to [Azure Portal](https://portal.azure.com)
2. Click "Create a resource" → "Databases" → "Azure SQL"
3. Fill in the details:
   - **Subscription**: Your subscription
   - **Resource group**: Create new or use existing
   - **Database name**: `flask-rbac-db` (or your preferred name)
   - **Server**: Create new server
   - **Server name**: `flask-rbac-server` (must be globally unique)
   - **Location**: Choose your preferred region
   - **Authentication method**: SQL authentication
   - **Server admin login**: `flaskadmin` (or your preferred username)
   - **Password**: Create a strong password
   - **Want to use Azure AD authentication**: No
4. Click "Review + create" → "Create"

### 1.2 Configure Firewall
1. Go to your SQL server in the Azure Portal
2. Under "Security" → "Networking"
3. Add your current IP address to the firewall rules
4. Enable "Allow Azure services and resources to access this server"
5. Save the configuration

### 1.3 Get Connection Details
Note down these values for later:
- **Server name**: `flask-rbac-server.database.windows.net`
- **Database name**: `flask-rbac-db`
- **Username**: `flaskadmin`
- **Password**: (the one you created)

## Step 2: Create Azure Web App

### 2.1 Create Web App
1. Go to [Azure Portal](https://portal.azure.com)
2. Click "Create a resource" → "Web App"
3. Fill in the details:
   - **Subscription**: Your subscription
   - **Resource group**: Same as SQL server
   - **Name**: `flask-rbac-app` (must be globally unique)
   - **Publish**: Code
   - **Runtime stack**: Python 3.11
   - **Operating System**: Linux
   - **Region**: Same as SQL server
   - **Pricing plan**: Free F1 (for testing) or Basic B1 (for production)
4. Click "Review + create" → "Create"

### 2.2 Create Deployment Slot (Optional but Recommended)
1. Create a staging branch in the repo
2. Go to your Web App in the Azure Portal
2. Under "Deployment" → "Deployment slots"
3. Click "Add slot"
4. Name: `staging`
5. Click "Add"

## Step 3: Configure Deployment Center

### 3.1 Connect to GitHub
1. Go to your Web App in the Azure Portal
2. Under "Deployment" → "Deployment Center"
3. Choose "GitHub" as source
4. Authorize Azure to access your GitHub account
5. Select your repository and branch
6. Choose the deployment slot (staging or production)
7. Click "Save"

### 3.2 Configure Build Settings
The deployment will automatically detect Python and install dependencies from `requirements.txt`.

## Step 4: Configure Application Settings

### 4.1 Add Environment Variables
1. Go to your Web App in the Azure Portal
2. Under "Settings" → "Configuration" → "Application settings"
3. Add the following settings:

```
SECRET_KEY = your-secret-key-here
AZURE_SQL_SERVER = flask-rbac-server.database.windows.net
AZURE_SQL_DB = flask-rbac-db
AZURE_SQL_USER = flaskadmin
AZURE_SQL_PASSWORD = your-sql-password
FLASK_ENV = production
SCM_DO_BUILD_DURING_DEPLOYMENT = 1
```

### 4.2 Optional Settings
```
ODBC_DRIVER = ODBC Driver 18 for SQL Server
```

### 4.3 Startup Command (if not using Procfile)
If you're not using the Procfile, set the startup command:
```
STARTUP_COMMAND = bash startup.sh
```

## Step 5: Deploy and Initialize Database

### 5.1 Deploy the Application
1. The deployment will start automatically after connecting to GitHub
2. Monitor the deployment in "Deployment Center" → "Logs"
3. Wait for deployment to complete

### 5.2 Initialize Database
1. Go to your Web App in the Azure Portal
2. Under "Development Tools" → "SSH"
3. Click "Go" to open SSH session
4. Run the following commands:

```bash
# Navigate to the app directory
cd /home/site/wwwroot

# Activate virtual environment
source /home/site/wwwroot/venv/bin/activate

# Set Flask app
export FLASK_APP=src/app

# Run database migrations
flask db upgrade

# Create admin user
flask create-admin --email admin@example.com --password 'AdminPass123!'
```

### 5.3 Test the Application
1. Go to your Web App URL (e.g., `https://flask-rbac-app.azurewebsites.net`)
2. You should see the landing page
3. Try registering a new user
4. Login with the admin account you created

## Step 6: Swap to Production (if using staging slot)

1. Go to your Web App in the Azure Portal
2. Under "Deployment" → "Deployment slots"
3. Click "Swap" next to your staging slot
4. Choose "staging" → "production"
5. Click "Swap"

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check firewall rules in Azure SQL
   - Verify connection string in application settings
   - Ensure ODBC driver is installed (handled by startup.sh)

2. **Deployment Failures**
   - Check deployment logs in "Deployment Center"
   - Verify all dependencies in requirements.txt
   - Ensure Python version matches runtime.txt

3. **Application Errors**
   - Check application logs in "Monitoring" → "Log stream"
   - Verify all environment variables are set
   - Check database migrations were run

### Logs and Monitoring

- **Application Logs**: Go to "Monitoring" → "Log stream"
- **Deployment Logs**: Go to "Deployment Center" → "Logs"
- **SSH Access**: Go to "Development Tools" → "SSH"

## Security Considerations

1. **Change Default Secret Key**: Generate a new SECRET_KEY for production
2. **Use Strong Passwords**: For both SQL server and admin account
3. **Enable HTTPS**: Azure Web Apps have HTTPS by default
4. **Regular Updates**: Keep dependencies updated
5. **Monitor Access**: Use Azure Security Center for monitoring

## Scaling and Performance

1. **App Service Plan**: Upgrade to higher tiers for better performance
2. **Database Scaling**: Consider Azure SQL Database scaling options
3. **CDN**: Use Azure CDN for static assets
4. **Monitoring**: Set up Application Insights for detailed monitoring

## Cost Optimization

1. **Use Free Tier**: For development and testing
2. **Auto-shutdown**: Configure auto-shutdown for development environments
3. **Resource Cleanup**: Delete unused resources to avoid charges
4. **Monitoring**: Use Azure Cost Management to track spending
