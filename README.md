# Flask RBAC App

A production-ready Flask web application with email/password authentication and role-based access control (RBAC), designed for Azure deployment with Azure SQL Database.

## Features

- **Secure Authentication**: Email/password login with PBKDF2 password hashing
- **Role-Based Access Control**: Many-to-many user-role relationships with admin controls
- **Azure SQL Integration**: SQLAlchemy 2.0 with Azure SQL Database support
- **CSRF Protection**: Flask-WTF CSRF protection on all forms
- **Responsive UI**: Bootstrap 5 with modern, mobile-friendly design
- **Admin Dashboard**: User management and role assignment interface
- **Database Migrations**: Alembic for database schema management
- **Comprehensive Testing**: pytest test suite with 100% coverage

## Tech Stack

- **Backend**: Flask 3.x, SQLAlchemy 2.x, Flask-Login, Flask-WTF
- **Database**: Azure SQL Database (SQL Server) with pyodbc
- **Frontend**: Bootstrap 5, Jinja2 templates
- **Authentication**: PBKDF2 password hashing, session-based auth
- **Deployment**: Azure Web Apps, Gunicorn
- **Testing**: pytest, pytest-flask

## Project Structure

```
azure-flask-sqlalchemy-app/
├── .env.example                 # Environment variables template
├── .flaskenv                    # Flask configuration
├── .gitignore                   # Git ignore rules
├── Procfile                     # Azure deployment command
├── requirements.txt             # Python dependencies
├── runtime.txt                  # Python version for Azure
├── startup.sh                   # Azure startup script
├── src/
│   └── app/
│       ├── __init__.py          # Flask app factory
│       ├── config.py            # Configuration classes
│       ├── extensions.py        # Flask extensions
│       ├── cli.py               # CLI commands
│       ├── models/              # SQLAlchemy models
│       ├── auth/                # Authentication blueprint
│       ├── main/                # Main application blueprint
│       ├── admin/                # Admin blueprint
│       ├── security/             # RBAC utilities
│       ├── templates/            # Jinja2 templates
│       └── static/               # Static assets
├── migrations/                   # Alembic migrations
├── tests/                        # Test suite
└── azure/                        # Azure deployment files
```

## Quick Start

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd azure-flask-sqlalchemy-app
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Initialize database**:
   ```bash
   export FLASK_APP=src/app
   flask db upgrade
   flask create-admin --email admin@example.com --password 'AdminPass123!'
   ```

4. **Run the application**:
   ```bash
   flask run
   ```

5. **Access the application**:
   - Open http://localhost:5000
   - Register a new user or login with admin account
   - Access admin panel at http://localhost:5000/admin (admin users only)

### Azure Deployment

See [azure/README_DEPLOY.md](azure/README_DEPLOY.md) for detailed Azure deployment instructions.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `development` |
| `SECRET_KEY` | Flask secret key | `dev-secret-key-change-in-production` |
| `AZURE_SQL_SERVER` | Azure SQL server name | - |
| `AZURE_SQL_DB` | Azure SQL database name | - |
| `AZURE_SQL_USER` | Azure SQL username | - |
| `AZURE_SQL_PASSWORD` | Azure SQL password | - |
| `ODBC_DRIVER` | ODBC driver name | `ODBC Driver 18 for SQL Server` |

### Database Configuration

The application automatically configures the database connection based on environment variables:

- **Local Development**: Uses SQLite if Azure SQL variables are not set
- **Production**: Uses Azure SQL Database with ODBC connection
- **Testing**: Uses in-memory SQLite database

## User Roles and Permissions

### Default Roles

- **admin**: Full access to admin panel and user management
- **user**: Standard user access (can be extended)

### Permission System

- **Public Routes**: Landing page, registration, login
- **Authenticated Routes**: Dashboard (requires login)
- **Admin Routes**: Admin dashboard, user management (requires admin role)

### Role Management

Admins can:
- View all users and their roles
- Assign/remove roles from users
- Activate/deactivate user accounts
- View system statistics

## API Endpoints

### Authentication
- `GET /auth/register` - Registration form
- `POST /auth/register` - Create new user
- `GET /auth/login` - Login form
- `POST /auth/login` - Authenticate user
- `GET /auth/logout` - Logout user
- `GET /auth/forgot-password` - Password reset form

### Main Application
- `GET /` - Landing page
- `GET /dashboard` - User dashboard (login required)

### Admin Panel
- `GET /admin/` - Admin dashboard (admin required)
- `GET /admin/users` - User management (admin required)
- `POST /admin/users/<id>/roles` - Assign role (admin required)
- `POST /admin/users/<id>/roles/remove` - Remove role (admin required)
- `POST /admin/users/<id>/toggle-active` - Toggle user status (admin required)

## Database Schema

### Users Table
- `id`: UUID primary key
- `email`: Unique email address (indexed)
- `password_hash`: PBKDF2 hashed password
- `is_active`: Account status
- `created_at`, `updated_at`: Timestamps

### Roles Table
- `id`: UUID primary key
- `name`: Unique role name (indexed)
- `created_at`: Timestamp

### User-Roles Association
- `user_id`: Foreign key to users
- `role_id`: Foreign key to roles
- Cascade delete on user/role deletion

### Projects Table (Example)
- `id`: UUID primary key
- `name`: Project name
- `description`: Project description
- `owner_id`: Foreign key to users
- `created_at`, `updated_at`: Timestamps

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/app

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

### Test Coverage

The test suite covers:
- User authentication and authorization
- Role-based access control
- Database models and relationships
- Admin functionality
- Form validation
- Error handling

## Security Features

- **Password Security**: PBKDF2 hashing with salt
- **CSRF Protection**: Flask-WTF CSRF tokens on all forms
- **Session Security**: Secure cookies in production
- **Input Validation**: WTForms validation on all inputs
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **XSS Protection**: Jinja2 auto-escaping
- **Content Security Policy**: CSP headers for additional security

## Deployment

### Azure Web Apps

The application is designed for Azure Web Apps deployment:

1. **Automatic ODBC Driver Installation**: The `startup.sh` script handles ODBC driver installation
2. **Environment Configuration**: All settings via Azure App Settings
3. **Database Migrations**: Run automatically on deployment
4. **Health Checks**: Built-in health monitoring

### Production Considerations

- **Secret Management**: Use Azure Key Vault for production secrets
- **Monitoring**: Enable Application Insights for monitoring
- **Scaling**: Configure auto-scaling based on demand
- **Backup**: Regular database backups
- **SSL/TLS**: HTTPS enabled by default on Azure Web Apps

## Development

### Adding New Features

1. **Models**: Add to `src/app/models/`
2. **Routes**: Add to appropriate blueprint
3. **Templates**: Add to `src/app/templates/`
4. **Tests**: Add to `tests/`
5. **Migrations**: Run `flask db migrate -m "Description"`

### Code Style

- Follow PEP 8 Python style guide
- Use type hints for function parameters and return values
- Write comprehensive docstrings
- Maintain test coverage above 90%

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check Azure SQL firewall rules
   - Verify connection string format
   - Ensure ODBC driver is installed

2. **Deployment Failures**
   - Check Azure deployment logs
   - Verify all dependencies in requirements.txt
   - Ensure Python version matches runtime.txt

3. **Authentication Issues**
   - Verify SECRET_KEY is set
   - Check session configuration
   - Ensure CSRF tokens are enabled

### Getting Help

- Check the [Azure deployment guide](azure/README_DEPLOY.md)
- Review the test suite for usage examples
- Check Flask and SQLAlchemy documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Changelog

### v1.0.0
- Initial release
- Flask 3.x with SQLAlchemy 2.0
- Azure SQL Database integration
- Role-based access control
- Admin dashboard
- Comprehensive test suite
- Azure deployment support
