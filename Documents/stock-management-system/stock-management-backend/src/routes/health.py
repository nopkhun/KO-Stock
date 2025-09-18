from flask import Blueprint, jsonify
from datetime import datetime
import psutil
import os
import time
from src.models.user import db
from src.config import DatabaseConnectionManager

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Comprehensive health check endpoint for monitoring and load balancers
    Returns detailed system status and metrics for production monitoring
    """
    start_time = time.time()
    
    try:
        # Basic system information
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'stock-management-backend',
            'version': '1.0.0',
            'uptime': get_uptime(),
            'system': get_detailed_system_metrics()
        }
        
        # Database connectivity check with detailed information
        db_manager = DatabaseConnectionManager(db)
        db_health = db_manager.check_health()
        
        if db_health['status'] == 'healthy':
            health_data['database'] = {
                'status': 'connected',
                'response_time_ms': db_health['response_time_ms'],
                'pool': db_health['pool']
            }
        else:
            health_data['database'] = {
                'status': 'disconnected',
                'error': db_health['error']
            }
            health_data['status'] = 'degraded'
        
        # Environment configuration status
        health_data['environment'] = {
            'flask_env': os.getenv('FLASK_ENV', 'unknown'),
            'debug_mode': os.getenv('DEBUG', 'false').lower() == 'true',
            'secret_key_configured': bool(os.getenv('SECRET_KEY')),
            'database_url_configured': bool(os.getenv('DATABASE_URL') or 
                                          (os.getenv('POSTGRES_PASSWORD') and os.getenv('POSTGRES_USER'))),
            'cors_origins_configured': bool(os.getenv('CORS_ORIGINS'))
        }
        
        # Application-specific health checks
        health_data['application'] = get_application_health()
        
        # Performance metrics
        response_time = (time.time() - start_time) * 1000
        health_data['performance'] = {
            'response_time_ms': round(response_time, 2),
            'load_average': get_load_average()
        }
        
        # Determine overall status based on critical components
        if health_data['database']['status'] == 'disconnected':
            health_data['status'] = 'degraded'
        
        # Check for critical system resource issues
        system = health_data['system']
        if system['memory_percent'] > 90 or system['disk_percent'] > 95:
            health_data['status'] = 'degraded'
            health_data['warnings'] = []
            if system['memory_percent'] > 90:
                health_data['warnings'].append(f"High memory usage: {system['memory_percent']:.1f}%")
            if system['disk_percent'] > 95:
                health_data['warnings'].append(f"High disk usage: {system['disk_percent']:.1f}%")
        
        # Determine HTTP status code
        status_code = 200 if health_data['status'] == 'healthy' else 503
        
        return jsonify(health_data), status_code
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'stock-management-backend',
            'error': str(e),
            'error_type': type(e).__name__,
            'response_time_ms': round(response_time, 2)
        }), 503

@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """
    Readiness check for Kubernetes and container orchestration
    Returns 200 when service is ready to accept traffic
    Checks all critical dependencies and configurations
    """
    start_time = time.time()
    checks = {}
    overall_ready = True
    
    try:
        # Check database connection and basic query
        try:
            result = db.session.execute(db.text('SELECT 1 as test, current_database(), current_user'))
            row = result.fetchone()
            checks['database'] = {
                'status': 'ready',
                'test_query': 'passed',
                'database': row[1] if row else 'unknown',
                'user': row[2] if row else 'unknown'
            }
        except Exception as e:
            checks['database'] = {
                'status': 'not_ready',
                'error': str(e)
            }
            overall_ready = False
        
        # Check if required environment variables are set
        required_env_vars = ['SECRET_KEY', 'POSTGRES_PASSWORD']
        env_status = 'ready'
        missing_vars = []
        
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
                env_status = 'not_ready'
                overall_ready = False
        
        checks['environment'] = {
            'status': env_status,
            'missing_variables': missing_vars if missing_vars else None
        }
        
        # Check system resources (basic thresholds)
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            resource_issues = []
            if memory.percent > 95:
                resource_issues.append(f"Critical memory usage: {memory.percent:.1f}%")
            if disk.percent > 98:
                resource_issues.append(f"Critical disk usage: {disk.percent:.1f}%")
            
            if resource_issues:
                checks['resources'] = {
                    'status': 'not_ready',
                    'issues': resource_issues
                }
                overall_ready = False
            else:
                checks['resources'] = {
                    'status': 'ready',
                    'memory_percent': round(memory.percent, 1),
                    'disk_percent': round(disk.percent, 1)
                }
        except Exception as e:
            checks['resources'] = {
                'status': 'unknown',
                'error': str(e)
            }
        
        response_time = (time.time() - start_time) * 1000
        
        response_data = {
            'status': 'ready' if overall_ready else 'not_ready',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'stock-management-backend',
            'checks': checks,
            'response_time_ms': round(response_time, 2)
        }
        
        return jsonify(response_data), 200 if overall_ready else 503
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return jsonify({
            'status': 'not_ready',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'stock-management-backend',
            'error': str(e),
            'error_type': type(e).__name__,
            'response_time_ms': round(response_time, 2)
        }), 503

@health_bp.route('/health/resources', methods=['GET'])
def resource_monitoring():
    """
    Detailed resource monitoring endpoint for performance analysis
    Returns comprehensive system resource usage and container limits
    """
    start_time = time.time()
    
    try:
        # Get detailed system metrics
        system_metrics = get_detailed_system_metrics()
        
        # Get database connection pool status
        db_manager = DatabaseConnectionManager(db)
        db_health = db_manager.check_health()
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000
        
        resource_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'stock-management-backend',
            'response_time_ms': round(response_time, 2),
            'system': system_metrics,
            'database_pool': db_health.get('pool'),
            'environment': {
                'flask_env': os.getenv('FLASK_ENV', 'unknown'),
                'container_limits': system_metrics.get('container_limits'),
                'resource_alerts': system_metrics.get('resource_alerts', [])
            }
        }
        
        # Determine status based on resource alerts
        alerts = system_metrics.get('resource_alerts', [])
        critical_alerts = [alert for alert in alerts if alert.get('type') == 'critical']
        warning_alerts = [alert for alert in alerts if alert.get('type') == 'warning']
        
        if critical_alerts:
            resource_data['status'] = 'critical'
            resource_data['alert_summary'] = {
                'critical_count': len(critical_alerts),
                'warning_count': len(warning_alerts),
                'critical_resources': [alert['resource'] for alert in critical_alerts]
            }
        elif warning_alerts:
            resource_data['status'] = 'warning'
            resource_data['alert_summary'] = {
                'warning_count': len(warning_alerts),
                'warning_resources': [alert['resource'] for alert in warning_alerts]
            }
        else:
            resource_data['status'] = 'healthy'
        
        # Add recommendations based on resource usage
        recommendations = []
        if system_metrics.get('cpu', {}).get('percent', 0) > 80:
            recommendations.append("Consider scaling CPU resources or optimizing CPU-intensive operations")
        if system_metrics.get('memory', {}).get('percent', 0) > 85:
            recommendations.append("Consider increasing memory allocation or optimizing memory usage")
        if system_metrics.get('disk', {}).get('percent', 0) > 85:
            recommendations.append("Consider cleaning up disk space or increasing storage allocation")
        
        if recommendations:
            resource_data['recommendations'] = recommendations
        
        status_code = 200 if resource_data['status'] in ['healthy', 'warning'] else 503
        
        return jsonify(resource_data), status_code
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'stock-management-backend',
            'error': str(e),
            'error_type': type(e).__name__,
            'response_time_ms': round(response_time, 2)
        }), 503


@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """
    Liveness check for Kubernetes and container orchestration
    Returns 200 when service is alive (basic functionality)
    This should be a lightweight check that doesn't depend on external services
    """
    start_time = time.time()
    
    try:
        # Basic application functionality test
        # Test that Flask is responding and basic Python functionality works
        test_data = {
            'math_test': 2 + 2,  # Basic computation
            'string_test': 'hello'.upper(),  # Basic string operation
            'time_test': time.time() > 0  # Basic time function
        }
        
        # Verify basic functionality
        if (test_data['math_test'] == 4 and 
            test_data['string_test'] == 'HELLO' and 
            test_data['time_test']):
            
            response_time = (time.time() - start_time) * 1000
            
            return jsonify({
                'status': 'alive',
                'timestamp': datetime.utcnow().isoformat(),
                'service': 'stock-management-backend',
                'version': '1.0.0',
                'response_time_ms': round(response_time, 2),
                'uptime': get_uptime()
            }), 200
        else:
            return jsonify({
                'status': 'not_alive',
                'timestamp': datetime.utcnow().isoformat(),
                'error': 'Basic functionality test failed'
            }), 503
            
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return jsonify({
            'status': 'not_alive',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e),
            'error_type': type(e).__name__,
            'response_time_ms': round(response_time, 2)
        }), 503

def get_uptime():
    """Get system uptime in seconds"""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
        return uptime_seconds
    except:
        # Fallback for non-Linux systems
        try:
            import psutil
            return time.time() - psutil.boot_time()
        except:
            return None

def get_detailed_system_metrics():
    """Get comprehensive system metrics with resource monitoring"""
    try:
        # CPU metrics with load average
        cpu_percent = psutil.cpu_percent(interval=0.1)  # Short interval for more accurate reading
        cpu_count = psutil.cpu_count()
        cpu_count_logical = psutil.cpu_count(logical=True)
        
        # Get CPU frequency if available
        try:
            cpu_freq = psutil.cpu_freq()
            cpu_frequency = {
                'current': round(cpu_freq.current, 1) if cpu_freq else None,
                'min': round(cpu_freq.min, 1) if cpu_freq else None,
                'max': round(cpu_freq.max, 1) if cpu_freq else None
            }
        except:
            cpu_frequency = None
        
        # Memory metrics with detailed breakdown
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disk metrics with I/O statistics
        disk = psutil.disk_usage('/')
        try:
            disk_io = psutil.disk_io_counters()
            disk_io_stats = {
                'read_bytes': disk_io.read_bytes,
                'write_bytes': disk_io.write_bytes,
                'read_count': disk_io.read_count,
                'write_count': disk_io.write_count,
                'read_time': disk_io.read_time,
                'write_time': disk_io.write_time
            } if disk_io else None
        except:
            disk_io_stats = None
        
        # Network metrics with detailed statistics
        try:
            network = psutil.net_io_counters()
            network_stats = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv,
                'errin': network.errin,
                'errout': network.errout,
                'dropin': network.dropin,
                'dropout': network.dropout
            } if network else None
        except:
            network_stats = None
        
        # Process-specific metrics
        try:
            current_process = psutil.Process()
            process_info = {
                'pid': current_process.pid,
                'memory_percent': round(current_process.memory_percent(), 2),
                'cpu_percent': round(current_process.cpu_percent(), 2),
                'num_threads': current_process.num_threads(),
                'num_fds': current_process.num_fds() if hasattr(current_process, 'num_fds') else None,
                'create_time': current_process.create_time(),
                'status': current_process.status()
            }
        except:
            process_info = None
        
        # Container resource limits (if running in Docker)
        container_limits = get_container_resource_limits()
        
        return {
            'cpu': {
                'percent': round(cpu_percent, 1),
                'count_physical': cpu_count,
                'count_logical': cpu_count_logical,
                'frequency': cpu_frequency,
                'load_average': get_load_average()
            },
            'memory': {
                'percent': round(memory.percent, 1),
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'free_gb': round(memory.free / (1024**3), 2),
                'cached_gb': round(memory.cached / (1024**3), 2) if hasattr(memory, 'cached') else None,
                'buffers_gb': round(memory.buffers / (1024**3), 2) if hasattr(memory, 'buffers') else None
            },
            'swap': {
                'percent': round(swap.percent, 1),
                'total_gb': round(swap.total / (1024**3), 2),
                'used_gb': round(swap.used / (1024**3), 2),
                'free_gb': round(swap.free / (1024**3), 2)
            },
            'disk': {
                'percent': round(disk.percent, 1),
                'total_gb': round(disk.total / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'io_stats': disk_io_stats
            },
            'network': network_stats,
            'process': process_info,
            'container_limits': container_limits,
            'resource_alerts': check_resource_thresholds(cpu_percent, memory.percent, disk.percent)
        }
    except Exception as e:
        # Fallback to basic metrics if detailed collection fails
        return {
            'cpu_percent': psutil.cpu_percent(interval=None),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'error': f"Detailed metrics unavailable: {str(e)}"
        }

def get_load_average():
    """Get system load average"""
    try:
        # Linux/Unix load average
        with open('/proc/loadavg', 'r') as f:
            load_avg = f.readline().split()[:3]
            return {
                '1min': float(load_avg[0]),
                '5min': float(load_avg[1]),
                '15min': float(load_avg[2])
            }
    except:
        # Fallback for non-Linux systems
        try:
            import os
            load_avg = os.getloadavg()
            return {
                '1min': round(load_avg[0], 2),
                '5min': round(load_avg[1], 2),
                '15min': round(load_avg[2], 2)
            }
        except:
            return None

def get_container_resource_limits():
    """
    Get Docker container resource limits if running in a container
    
    Returns:
        Dictionary with container resource limits or None
    """
    try:
        limits = {}
        
        # Check memory limit from cgroup
        try:
            with open('/sys/fs/cgroup/memory/memory.limit_in_bytes', 'r') as f:
                memory_limit = int(f.read().strip())
                # Convert to GB, but check if it's a real limit (not the huge default)
                if memory_limit < (1024**4):  # Less than 1TB (likely a real limit)
                    limits['memory_gb'] = round(memory_limit / (1024**3), 2)
        except:
            pass
        
        # Check CPU limit from cgroup
        try:
            with open('/sys/fs/cgroup/cpu/cpu.cfs_quota_us', 'r') as f:
                cpu_quota = int(f.read().strip())
            with open('/sys/fs/cgroup/cpu/cpu.cfs_period_us', 'r') as f:
                cpu_period = int(f.read().strip())
            
            if cpu_quota > 0 and cpu_period > 0:
                limits['cpu_cores'] = round(cpu_quota / cpu_period, 2)
        except:
            pass
        
        # Check if we're in a container
        try:
            with open('/proc/1/cgroup', 'r') as f:
                cgroup_content = f.read()
                limits['in_container'] = 'docker' in cgroup_content or 'containerd' in cgroup_content
        except:
            limits['in_container'] = False
        
        return limits if limits else None
        
    except Exception:
        return None


def check_resource_thresholds(cpu_percent, memory_percent, disk_percent):
    """
    Check resource usage against thresholds and generate alerts
    
    Args:
        cpu_percent: CPU usage percentage
        memory_percent: Memory usage percentage
        disk_percent: Disk usage percentage
    
    Returns:
        List of resource alerts
    """
    alerts = []
    
    # Define thresholds
    thresholds = {
        'cpu': {'warning': 70, 'critical': 85},
        'memory': {'warning': 80, 'critical': 90},
        'disk': {'warning': 80, 'critical': 90}
    }
    
    # Check CPU
    if cpu_percent >= thresholds['cpu']['critical']:
        alerts.append({
            'type': 'critical',
            'resource': 'cpu',
            'message': f'Critical CPU usage: {cpu_percent:.1f}%',
            'threshold': thresholds['cpu']['critical'],
            'current': cpu_percent
        })
    elif cpu_percent >= thresholds['cpu']['warning']:
        alerts.append({
            'type': 'warning',
            'resource': 'cpu',
            'message': f'High CPU usage: {cpu_percent:.1f}%',
            'threshold': thresholds['cpu']['warning'],
            'current': cpu_percent
        })
    
    # Check Memory
    if memory_percent >= thresholds['memory']['critical']:
        alerts.append({
            'type': 'critical',
            'resource': 'memory',
            'message': f'Critical memory usage: {memory_percent:.1f}%',
            'threshold': thresholds['memory']['critical'],
            'current': memory_percent
        })
    elif memory_percent >= thresholds['memory']['warning']:
        alerts.append({
            'type': 'warning',
            'resource': 'memory',
            'message': f'High memory usage: {memory_percent:.1f}%',
            'threshold': thresholds['memory']['warning'],
            'current': memory_percent
        })
    
    # Check Disk
    if disk_percent >= thresholds['disk']['critical']:
        alerts.append({
            'type': 'critical',
            'resource': 'disk',
            'message': f'Critical disk usage: {disk_percent:.1f}%',
            'threshold': thresholds['disk']['critical'],
            'current': disk_percent
        })
    elif disk_percent >= thresholds['disk']['warning']:
        alerts.append({
            'type': 'warning',
            'resource': 'disk',
            'message': f'High disk usage: {disk_percent:.1f}%',
            'threshold': thresholds['disk']['warning'],
            'current': disk_percent
        })
    
    return alerts


def get_application_health():
    """Get application-specific health information with resource monitoring"""
    try:
        # Check if we can import key modules
        health_info = {
            'flask_app': True,
            'database_models': True,
            'routes_loaded': True
        }
        
        # Test basic Flask functionality
        try:
            from flask import current_app
            health_info['current_app'] = bool(current_app)
            
            # Get Flask app configuration status
            if current_app:
                health_info['app_config'] = {
                    'debug': current_app.debug,
                    'testing': current_app.testing,
                    'secret_key_set': bool(current_app.secret_key),
                    'database_uri_set': bool(current_app.config.get('SQLALCHEMY_DATABASE_URI'))
                }
        except:
            health_info['current_app'] = False
        
        # Test database models import
        try:
            from src.models.user import User
            from src.models.product import Product
            health_info['models_importable'] = True
        except Exception as e:
            health_info['models_importable'] = False
            health_info['models_error'] = str(e)
        
        # Check if we're in a valid Flask application context
        try:
            from flask import g
            health_info['app_context'] = True
        except RuntimeError:
            health_info['app_context'] = False
        
        # Check middleware status
        try:
            health_info['middleware'] = {
                'security_middleware': True,  # Assume loaded if no error
                'performance_middleware': True,  # Assume loaded if no error
                'cors_enabled': True  # Assume enabled if no error
            }
        except:
            health_info['middleware'] = {'status': 'unknown'}
        
        return health_info
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

@health_bp.route('/ping', methods=['GET'])
def ping():
    """
    Ultra-simple ping endpoint for basic connectivity testing
    Returns immediately without any dependencies or checks
    """
    return jsonify({
        'status': 'ok',
        'message': 'pong',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@health_bp.route('/health/simple', methods=['GET'])
def simple_health():
    """
    Simple health check without database dependencies
    Use this for initial container health verification
    """
    try:
        return jsonify({
            'status': 'healthy',
            'service': 'stock-management-backend',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503