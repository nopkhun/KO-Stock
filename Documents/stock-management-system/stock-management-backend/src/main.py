import os
import sys
import signal
import atexit
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS

# Import security and performance middleware
from src.middleware.security import SecurityMiddleware
from src.middleware.performance import PerformanceMiddleware

# Import environment validation and database utilities
from src.config import (
    validate_environment, 
    get_database_config, 
    EnvironmentValidationError,
    setup_database_with_retry,
    setup_logging,
    setup_error_handlers,
    log_startup_info,
    log_shutdown_info,
    db_error_handler
)
from src.config.database import validate_startup_environment

# Import all models
from src.models.user import db
from src.models.location import Location
from src.models.supplier import Supplier
from src.models.brand import Brand
from src.models.product import Product
from src.models.inventory import Inventory
from src.models.stock_transaction import StockTransaction
from src.models.daily_count import DailyCount

# Import all routes
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.location import location_bp
from src.routes.supplier import supplier_bp
from src.routes.brand import brand_bp
from src.routes.product import product_bp
from src.routes.inventory import inventory_bp
from src.routes.stock_transaction import stock_transaction_bp
from src.routes.daily_count import daily_count_bp
from src.routes.reports import reports_bp
from src.routes.dashboard import dashboard_bp
from src.routes.health import health_bp

# Setup comprehensive logging first
logger = setup_logging("stock-management-backend")

# Setup graceful shutdown handlers
def shutdown_handler(signum, frame):
    """Handle graceful shutdown"""
    log_shutdown_info(logger, f"Signal {signum} received")
    sys.exit(0)

def cleanup_on_exit():
    """Cleanup function called on normal exit"""
    log_shutdown_info(logger, "normal")

# Register shutdown handlers
signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)
atexit.register(cleanup_on_exit)

# Validate environment variables before starting the application
logger.info("Starting Stock Management Backend...")
logger.info("="*50)

# Quick startup validation for critical variables
if not validate_startup_environment():
    logger.critical("Startup environment validation failed")
    sys.exit(1)

try:
    logger.info("Validating complete environment configuration...")
    validated_config = validate_environment()
    logger.info("Environment validation successful!")
except EnvironmentValidationError as e:
    logger.critical(f"Environment validation failed: {e}")
    sys.exit(1)
except Exception as e:
    logger.critical(f"Unexpected error during environment validation: {e}", exc_info=True)
    sys.exit(1)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Initialize security and performance middleware
security_middleware = SecurityMiddleware(app)
performance_middleware = PerformanceMiddleware(app)

# Application configuration using validated environment variables
app.config['SECRET_KEY'] = validated_config['SECRET_KEY']
app.config['SESSION_COOKIE_SECURE'] = validated_config.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
app.config['SESSION_COOKIE_SAMESITE'] = validated_config.get('SESSION_COOKIE_SAMESITE', 'Lax')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session timeout

# Configure CORS with validated origins
cors_origins = validated_config.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173')
if cors_origins == '*':
    allowed_origins = ['*']
    CORS(app, resources={r'/api/*': {'origins': '*'}}, supports_credentials=False)
    logger.warning("CORS configured for all origins (*) - not recommended for production")
else:
    allowed_origins = [origin.strip() for origin in cors_origins.split(',') if origin.strip()]
    CORS(app, resources={r'/api/*': {'origins': allowed_origins}}, supports_credentials=True)

logger.info(f"CORS configured for origins: {allowed_origins}")

# Register all blueprints
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(location_bp, url_prefix='/api')
app.register_blueprint(supplier_bp, url_prefix='/api')
app.register_blueprint(brand_bp, url_prefix='/api')
app.register_blueprint(product_bp, url_prefix='/api')
app.register_blueprint(inventory_bp, url_prefix='/api')
app.register_blueprint(stock_transaction_bp, url_prefix='/api')
app.register_blueprint(daily_count_bp, url_prefix='/api')
app.register_blueprint(reports_bp, url_prefix='/api')
app.register_blueprint(dashboard_bp, url_prefix='/api')
app.register_blueprint(health_bp, url_prefix='/api')

# Database configuration using validated environment variables
try:
    database_url = get_database_config(validated_config)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    # Log database configuration without exposing credentials
    db_info = database_url.split('@')[0] if '@' in database_url else database_url.split('://')[0]
    logger.info(f"Database configured: {db_info}@[HIDDEN]")
except Exception as e:
    db_error_handler.log_database_error(
        logger, e, "database configuration", 
        {'config_keys': list(validated_config.keys())}
    )
    
    # Fallback to SQLite for development only
    if validated_config.get('FLASK_ENV') == 'development':
        default_sqlite_path = os.path.join(os.path.dirname(__file__), 'database', 'app.db')
        os.makedirs(os.path.dirname(default_sqlite_path), exist_ok=True)
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{default_sqlite_path}"
        logger.warning(f"Using SQLite fallback for development: {default_sqlite_path}")
    else:
        logger.critical("Database configuration required for production environment")
        sys.exit(1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Setup comprehensive error handlers
setup_error_handlers(app)

# Setup database with retry logic and initialization
logger.info("Setting up database connection...")
if not setup_database_with_retry(app, db):
    logger.critical("Database setup failed")
    sys.exit(1)

# Log comprehensive startup information
log_startup_info(logger, {
    'FLASK_ENV': validated_config.get('FLASK_ENV'),
    'DEBUG': app.debug,
    'SQLALCHEMY_DATABASE_URI': bool(app.config.get('SQLALCHEMY_DATABASE_URI')),
    'SECRET_KEY': bool(app.config.get('SECRET_KEY')),
    'CORS_ORIGINS': cors_origins
})

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
