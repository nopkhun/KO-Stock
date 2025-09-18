"""
Database connection utilities with retry logic and health monitoring
Enhanced with production-ready connection pooling and timeout settings
"""

import time
import sys
import os
import logging
from typing import Optional, Dict, Any
from sqlalchemy import text, create_engine
from sqlalchemy.exc import OperationalError, DatabaseError
from sqlalchemy.pool import QueuePool


class DatabaseConnectionManager:
    """
    Manages database connections with retry logic, health monitoring,
    and production-ready connection pooling
    """
    
    def __init__(self, db, max_retries: int = 10, retry_delay: float = 1.0):
        """
        Initialize database connection manager
        
        Args:
            db: SQLAlchemy database instance
            max_retries: Maximum number of connection attempts
            retry_delay: Initial delay between retries (exponential backoff)
        """
        self.db = db
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.connection_timeout = int(os.getenv('DB_CONNECTION_TIMEOUT', '30'))
        self.pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', '20'))
        self.logger = logging.getLogger('stock-management-backend.database')
    
    @staticmethod
    def get_engine_config() -> Dict[str, Any]:
        """
        Get production-ready database engine configuration with optimized performance settings
        
        Returns:
            Dictionary with engine configuration parameters
        """
        # Determine optimal pool settings based on environment
        is_production = os.getenv('FLASK_ENV', 'production') == 'production'
        
        # Production-optimized pool settings
        if is_production:
            pool_size = int(os.getenv('DB_POOL_SIZE', '15'))  # Increased for production
            max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '25'))  # Higher overflow
            pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', '30'))  # Longer timeout
            pool_recycle = int(os.getenv('DB_POOL_RECYCLE', '1800'))  # 30 minutes
            statement_timeout = int(os.getenv('DB_STATEMENT_TIMEOUT', '60000'))  # 60 seconds
        else:
            # Development settings
            pool_size = int(os.getenv('DB_POOL_SIZE', '5'))
            max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '10'))
            pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', '20'))
            pool_recycle = int(os.getenv('DB_POOL_RECYCLE', '3600'))  # 1 hour
            statement_timeout = int(os.getenv('DB_STATEMENT_TIMEOUT', '30000'))  # 30 seconds
        
        return {
            'poolclass': QueuePool,
            'pool_size': pool_size,
            'max_overflow': max_overflow,
            'pool_timeout': pool_timeout,
            'pool_recycle': pool_recycle,
            'pool_pre_ping': True,  # Validate connections before use
            'pool_reset_on_return': 'commit',  # Reset connections on return
            'connect_args': {
                'connect_timeout': int(os.getenv('DB_CONNECTION_TIMEOUT', '30')),
                'application_name': 'stock_management_backend',
                'options': f'-c statement_timeout={statement_timeout} -c idle_in_transaction_session_timeout=300000',  # 5 min idle timeout
                'server_side_cursors': True,  # Enable server-side cursors for large result sets
                'sslmode': os.getenv('DB_SSL_MODE', 'prefer'),  # SSL preference
                'target_session_attrs': 'read-write'  # Ensure read-write connection
            },
            'echo': os.getenv('FLASK_ENV') == 'development',
            'echo_pool': os.getenv('DB_ECHO_POOL', 'false').lower() == 'true',
            'execution_options': {
                'isolation_level': 'READ_COMMITTED',  # Optimal isolation level
                'autocommit': False,
                'compiled_cache': {}  # Enable query compilation caching
            }
        }
    
    def wait_for_database(self) -> bool:
        """
        Wait for database to become available with exponential backoff
        Enhanced with better error handling and connection validation
        
        Returns:
            True if database is available, False otherwise
        """
        self.logger.info(
            "Waiting for database connection...",
            extra={
                'connection_timeout': self.connection_timeout,
                'pool_timeout': self.pool_timeout,
                'max_retries': self.max_retries
            }
        )
        
        for attempt in range(1, self.max_retries + 1):
            try:
                # Test database connection with timeout
                start_time = time.time()
                
                with self.db.engine.connect() as conn:
                    # Test basic connectivity
                    result = conn.execute(text('SELECT 1 as test'))
                    test_value = result.scalar()
                    
                    # Test database permissions
                    conn.execute(text('SELECT current_database(), current_user'))
                    
                    # Verify we can create/access tables (basic schema check)
                    conn.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public'
                        )
                    """))
                
                connection_time = time.time() - start_time
                
                # Log connection pool status
                pool = self.db.engine.pool
                
                self.logger.info(
                    "Database connection established",
                    extra={
                        'attempt': attempt,
                        'connection_time_seconds': round(connection_time, 2),
                        'pool_size': pool.size(),
                        'pool_checked_out': pool.checkedout(),
                        'pool_overflow': pool.overflow(),
                        'pool_checked_in': pool.checkedin()
                    }
                )
                
                return True
                
            except (OperationalError, DatabaseError) as e:
                error_msg = str(e).lower()
                
                # Categorize common database errors
                if 'timeout' in error_msg or 'timed out' in error_msg:
                    error_type = "Connection timeout"
                elif 'connection refused' in error_msg:
                    error_type = "Connection refused (database not ready)"
                elif 'authentication failed' in error_msg or 'password' in error_msg:
                    error_type = "Authentication failed"
                elif 'database' in error_msg and 'does not exist' in error_msg:
                    error_type = "Database does not exist"
                elif 'permission denied' in error_msg:
                    error_type = "Permission denied"
                else:
                    error_type = "Database error"
                
                if attempt == self.max_retries:
                    self.logger.critical(
                        f"Database connection failed after {self.max_retries} attempts",
                        extra={
                            'error_type': error_type,
                            'error_message': str(e),
                            'max_retries': self.max_retries,
                            'troubleshooting': [
                                "Check database server is running",
                                "Verify connection parameters (host, port, credentials)",
                                "Check network connectivity",
                                "Review database logs for more details"
                            ]
                        }
                    )
                    return False
                
                # Calculate exponential backoff with jitter
                base_delay = self.retry_delay * (2 ** (attempt - 1))
                jitter = base_delay * 0.1 * (time.time() % 1)  # Add up to 10% jitter
                delay = min(base_delay + jitter, 60)  # Cap at 60 seconds
                
                self.logger.warning(
                    f"Database connection attempt {attempt} failed, retrying in {delay:.1f}s",
                    extra={
                        'attempt': attempt,
                        'error_type': error_type,
                        'error_message': str(e),
                        'retry_delay': delay,
                        'max_retries': self.max_retries
                    }
                )
                time.sleep(delay)
            
            except Exception as e:
                self.logger.error(
                    "Unexpected database error",
                    exc_info=True,
                    extra={
                        'attempt': attempt,
                        'error_type': type(e).__name__,
                        'error_message': str(e)
                    }
                )
                if attempt == self.max_retries:
                    return False
                
                delay = min(self.retry_delay * attempt, 30)  # Linear backoff for unexpected errors
                self.logger.info(f"Retrying in {delay:.1f}s...")
                time.sleep(delay)
        
        return False
    
    def initialize_database(self) -> bool:
        """
        Initialize database schema and seed initial data
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Initializing database schema...")
            
            # Create all tables
            self.db.create_all()
            self.logger.info("Database tables created successfully")
            
            # Seed initial data
            self._seed_initial_data()
            self.logger.info("Initial data seeded successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Database initialization failed",
                exc_info=True,
                extra={
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            )
            return False
    
    def _seed_initial_data(self):
        """Seed initial data if tables are empty"""
        from src.models.location import Location
        from src.models.user import User
        
        # Check if data already exists
        if Location.query.count() > 0:
            self.logger.info("Initial data already exists, skipping seeding")
            return
        
        # Create default locations
        locations = [
            Location(
                name='Central Warehouse',
                location_type='warehouse',
                address='123 Main St, City',
                is_active=True
            ),
            Location(
                name='Store A',
                location_type='store',
                address='456 Store St, City',
                is_active=True
            ),
            Location(
                name='Store B',
                location_type='store',
                address='789 Shop Ave, City',
                is_active=True
            )
        ]
        
        for location in locations:
            self.db.session.add(location)
        
        self.db.session.commit()
        
        # Get the first store for staff user
        store_a = Location.query.filter_by(name='Store A').first()
        
        # Create default users
        users = [
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'full_name': 'System Administrator',
                'role': 'admin',
                'password': 'admin123',
                'location_id': None
            },
            {
                'username': 'manager',
                'email': 'manager@example.com',
                'full_name': 'Store Manager',
                'role': 'manager',
                'password': 'manager123',
                'location_id': None
            },
            {
                'username': 'staff',
                'email': 'staff@example.com',
                'full_name': 'Store Staff',
                'role': 'staff',
                'password': 'staff123',
                'location_id': store_a.id if store_a else None
            }
        ]
        
        for user_data in users:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                full_name=user_data['full_name'],
                role=user_data['role'],
                is_active=True,
                location_id=user_data['location_id']
            )
            user.set_password(user_data['password'])
            self.db.session.add(user)
        
        self.db.session.commit()
        
        self.logger.info(
            "Initial data seeded successfully",
            extra={
                'locations_created': len(locations),
                'users_created': len(users),
                'location_names': [loc.name for loc in locations],
                'user_roles': [user['role'] for user in users]
            }
        )
    
    def check_health(self) -> dict:
        """
        Check database health and return status information
        
        Returns:
            Dictionary with health status information
        """
        try:
            start_time = time.time()
            
            # Test basic connectivity
            with self.db.engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Get connection pool info
            pool = self.db.engine.pool
            pool_status = {
                'size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'invalid': pool.invalid()
            }
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'pool': pool_status
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time_ms': None,
                'pool': None
            }


def configure_database_engine(database_url: str) -> str:
    """
    Configure database URL with production-ready connection parameters
    
    Args:
        database_url: Base database URL
        
    Returns:
        Enhanced database URL with connection parameters
    """
    # Get engine configuration
    engine_config = DatabaseConnectionManager.get_engine_config()
    
    # Add connection parameters to URL if not already present
    if '?' not in database_url:
        # Add basic connection parameters
        params = []
        
        # Connection timeout
        connect_timeout = engine_config['connect_args']['connect_timeout']
        params.append(f'connect_timeout={connect_timeout}')
        
        # Application name for monitoring
        app_name = engine_config['connect_args']['application_name']
        params.append(f'application_name={app_name}')
        
        if params:
            database_url += '?' + '&'.join(params)
    
    return database_url


def setup_database_with_retry(app, db) -> bool:
    """
    Setup database connection with retry logic and enhanced configuration
    
    Args:
        app: Flask application instance
        db: SQLAlchemy database instance
        
    Returns:
        True if setup successful, False otherwise
    """
    logger = logging.getLogger('stock-management-backend.database')
    
    with app.app_context():
        # Configure database engine with production settings
        engine_config = DatabaseConnectionManager.get_engine_config()
        
        # Update SQLAlchemy configuration
        database_url = app.config['SQLALCHEMY_DATABASE_URI']
        enhanced_url = configure_database_engine(database_url)
        
        # Create engine with enhanced configuration
        engine = create_engine(enhanced_url, **{
            k: v for k, v in engine_config.items() 
            if k not in ['connect_args']  # connect_args handled in URL
        })
        
        # Update database configuration
        app.config['SQLALCHEMY_DATABASE_URI'] = enhanced_url
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            k: v for k, v in engine_config.items() 
            if k != 'connect_args'
        }
        
        # Reinitialize database with new configuration
        db.init_app(app)
        
        logger.info(
            "Database engine configured with production settings",
            extra={
                'pool_size': engine_config['pool_size'],
                'max_overflow': engine_config['max_overflow'],
                'pool_timeout': engine_config['pool_timeout'],
                'connection_timeout': engine_config['connect_args']['connect_timeout'],
                'pool_recycle': engine_config['pool_recycle'],
                'pool_pre_ping': engine_config['pool_pre_ping']
            }
        )
        
        db_manager = DatabaseConnectionManager(db)
        
        # Wait for database to become available
        if not db_manager.wait_for_database():
            logger.critical("Database connection failed - cannot continue")
            return False
        
        # Initialize database schema and data
        if not db_manager.initialize_database():
            logger.critical("Database initialization failed - cannot continue")
            return False
        
        logger.info("Database setup completed successfully")
        return True


def validate_startup_environment() -> bool:
    """
    Validate required environment variables at startup
    
    Returns:
        True if all required variables are present and valid
    """
    logger = logging.getLogger('stock-management-backend.startup')
    
    required_vars = [
        'SECRET_KEY',
        'POSTGRES_PASSWORD'
    ]
    
    missing_vars = []
    invalid_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        elif var == 'SECRET_KEY' and len(value) < 32:
            invalid_vars.append(f"{var} (must be at least 32 characters)")
        elif var == 'POSTGRES_PASSWORD' and len(value) < 8:
            invalid_vars.append(f"{var} (must be at least 8 characters)")
    
    if missing_vars or invalid_vars:
        logger.critical(
            "Startup environment validation failed",
            extra={
                'missing_variables': missing_vars,
                'invalid_variables': invalid_vars,
                'required_variables': {
                    'SECRET_KEY': 'Flask secret key (min 32 chars)',
                    'POSTGRES_PASSWORD': 'Database password (min 8 chars)'
                },
                'optional_variables': {
                    'POSTGRES_USER': 'Database username (default: postgres)',
                    'POSTGRES_DB': 'Database name (default: stock_management)',
                    'POSTGRES_HOST': 'Database host (default: database)',
                    'POSTGRES_PORT': 'Database port (default: 5432)',
                    'DATABASE_URL': 'Full connection URL (overrides individual settings)'
                }
            }
        )
        return False
    
    logger.info("Startup environment validation successful")
    return True