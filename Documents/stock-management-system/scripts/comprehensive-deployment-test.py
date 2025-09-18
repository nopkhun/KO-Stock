#!/usr/bin/env python3
"""
Comprehensive Deployment Testing Script
Tests complete stack deployment, health checks, and database persistence
"""

import os
import sys
import time
import json
import requests
import subprocess
from datetime import datetime
import logging

# Try to import psycopg2, but make it optional
try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    print("Warning: psycopg2 not available. Database tests will be skipped.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment-test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DeploymentTester:
    def __init__(self):
        self.frontend_url = "http://localhost:80"
        self.backend_url = "http://localhost:5000"
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'overall_status': 'PENDING'
        }
        
    def run_all_tests(self):
        """Run all deployment tests"""
        logger.info("Starting comprehensive deployment testing...")
        
        tests = [
            ('docker_compose_deployment', self.test_docker_compose_deployment),
            ('service_health_checks', self.test_service_health_checks),
            ('database_connectivity', self.test_database_connectivity),
            ('api_endpoints', self.test_api_endpoints),
            ('frontend_accessibility', self.test_frontend_accessibility),
            ('database_persistence', self.test_database_persistence),
            ('service_restart_resilience', self.test_service_restart_resilience)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"Running test: {test_name}")
            try:
                result = test_func()
                self.test_results['tests'][test_name] = result
                if result['status'] == 'PASS':
                    passed_tests += 1
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.error(f"❌ {test_name}: FAILED - {result.get('error', 'Unknown error')}")
            except Exception as e:
                logger.error(f"❌ {test_name}: ERROR - {str(e)}")
                self.test_results['tests'][test_name] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
        
        # Calculate overall status
        if passed_tests == total_tests:
            self.test_results['overall_status'] = 'PASS'
        elif passed_tests > 0:
            self.test_results['overall_status'] = 'PARTIAL'
        else:
            self.test_results['overall_status'] = 'FAIL'
            
        self.generate_report()
        return self.test_results['overall_status']
    
    def test_docker_compose_deployment(self):
        """Test complete stack deployment with docker-compose"""
        try:
            # Check if docker-compose is available
            result = subprocess.run(['docker-compose', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return {'status': 'FAIL', 'error': 'docker-compose not available'}
            
            # Stop any existing containers
            subprocess.run(['docker-compose', 'down'], 
                          capture_output=True, timeout=30)
            
            # Start the stack
            logger.info("Starting docker-compose stack...")
            result = subprocess.run(['docker-compose', 'up', '-d'], 
                                  capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                return {
                    'status': 'FAIL', 
                    'error': f'Docker compose failed: {result.stderr}'
                }
            
            # Wait for services to start
            time.sleep(30)
            
            # Check if all containers are running
            result = subprocess.run(['docker-compose', 'ps'], 
                                  capture_output=True, text=True, timeout=10)
            
            if 'Up' not in result.stdout:
                return {
                    'status': 'FAIL', 
                    'error': 'Not all containers are running'
                }
            
            return {
                'status': 'PASS',
                'message': 'Docker compose deployment successful',
                'containers': result.stdout
            }
            
        except subprocess.TimeoutExpired:
            return {'status': 'FAIL', 'error': 'Docker compose deployment timeout'}
        except Exception as e:
            return {'status': 'FAIL', 'error': str(e)}
    
    def test_service_health_checks(self):
        """Validate all health checks and monitoring endpoints"""
        health_endpoints = [
            f"{self.backend_url}/health",
            f"{self.backend_url}/health/ready",
            f"{self.backend_url}/health/live"
        ]
        
        results = {}
        all_healthy = True
        
        for endpoint in health_endpoints:
            try:
                response = requests.get(endpoint, timeout=10)
                if response.status_code == 200:
                    health_data = response.json()
                    results[endpoint] = {
                        'status': 'HEALTHY',
                        'response_time': response.elapsed.total_seconds(),
                        'data': health_data
                    }
                else:
                    results[endpoint] = {
                        'status': 'UNHEALTHY',
                        'status_code': response.status_code
                    }
                    all_healthy = False
            except Exception as e:
                results[endpoint] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
                all_healthy = False
        
        return {
            'status': 'PASS' if all_healthy else 'FAIL',
            'endpoints': results,
            'message': 'All health checks passed' if all_healthy else 'Some health checks failed'
        }
    
    def test_database_connectivity(self):
        """Test database connectivity and basic operations"""
        if not PSYCOPG2_AVAILABLE:
            return {
                'status': 'SKIP',
                'message': 'psycopg2 not available, skipping database tests'
            }
        
        try:
            # Get database connection details from environment or defaults
            db_config = {
                'host': 'localhost',
                'port': 5432,
                'database': os.getenv('POSTGRES_DB', 'stock_management'),
                'user': os.getenv('POSTGRES_USER', 'postgres'),
                'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
            }
            
            # Test connection
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            # Test table existence
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            return {
                'status': 'PASS',
                'database_version': version,
                'tables_found': len(tables),
                'tables': tables
            }
            
        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e)
            }
    
    def test_api_endpoints(self):
        """Test key API endpoints"""
        endpoints_to_test = [
            ('GET', '/api/products', 'List products'),
            ('GET', '/api/locations', 'List locations'),
            ('GET', '/api/brands', 'List brands'),
            ('GET', '/api/suppliers', 'List suppliers')
        ]
        
        results = {}
        all_passed = True
        
        for method, endpoint, description in endpoints_to_test:
            try:
                url = f"{self.backend_url}{endpoint}"
                response = requests.get(url, timeout=10)
                
                if response.status_code in [200, 404]:  # 404 is acceptable for empty data
                    results[endpoint] = {
                        'status': 'PASS',
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds()
                    }
                else:
                    results[endpoint] = {
                        'status': 'FAIL',
                        'status_code': response.status_code
                    }
                    all_passed = False
                    
            except Exception as e:
                results[endpoint] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
                all_passed = False
        
        return {
            'status': 'PASS' if all_passed else 'FAIL',
            'endpoints': results
        }
    
    def test_frontend_accessibility(self):
        """Test frontend accessibility and basic functionality"""
        try:
            # Test main page
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code != 200:
                return {
                    'status': 'FAIL',
                    'error': f'Frontend not accessible: {response.status_code}'
                }
            
            # Check if it's serving HTML content
            if 'text/html' not in response.headers.get('content-type', ''):
                return {
                    'status': 'FAIL',
                    'error': 'Frontend not serving HTML content'
                }
            
            # Test static assets (basic check)
            static_tests = []
            for asset_path in ['/favicon.ico']:
                try:
                    asset_response = requests.get(f"{self.frontend_url}{asset_path}", timeout=5)
                    static_tests.append({
                        'path': asset_path,
                        'status_code': asset_response.status_code
                    })
                except:
                    static_tests.append({
                        'path': asset_path,
                        'status_code': 'ERROR'
                    })
            
            return {
                'status': 'PASS',
                'main_page_status': response.status_code,
                'content_type': response.headers.get('content-type'),
                'static_assets': static_tests
            }
            
        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e)
            }
    
    def test_database_persistence(self):
        """Verify database persistence and data integrity"""
        if not PSYCOPG2_AVAILABLE:
            return {
                'status': 'SKIP',
                'message': 'psycopg2 not available, skipping database tests'
            }
        
        try:
            # Connect to database
            db_config = {
                'host': 'localhost',
                'port': 5432,
                'database': os.getenv('POSTGRES_DB', 'stock_management'),
                'user': os.getenv('POSTGRES_USER', 'postgres'),
                'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
            }
            
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            
            # Create a test record
            test_data = {
                'name': f'Test Location {int(time.time())}',
                'description': 'Test location for deployment testing'
            }
            
            # Insert test data
            cursor.execute("""
                INSERT INTO locations (name, description) 
                VALUES (%(name)s, %(description)s) 
                RETURNING id
            """, test_data)
            test_id = cursor.fetchone()[0]
            conn.commit()
            
            # Verify data was inserted
            cursor.execute("SELECT name, description FROM locations WHERE id = %s", (test_id,))
            result = cursor.fetchone()
            
            if not result or result[0] != test_data['name']:
                return {
                    'status': 'FAIL',
                    'error': 'Data insertion/retrieval failed'
                }
            
            # Clean up test data
            cursor.execute("DELETE FROM locations WHERE id = %s", (test_id,))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return {
                'status': 'PASS',
                'message': 'Database persistence test successful',
                'test_record_id': test_id
            }
            
        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e)
            }
    
    def test_service_restart_resilience(self):
        """Test service restart resilience"""
        try:
            # Test backend restart
            logger.info("Testing backend service restart...")
            
            # Stop backend container
            result = subprocess.run(['docker-compose', 'stop', 'backend'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                return {
                    'status': 'FAIL',
                    'error': f'Failed to stop backend: {result.stderr}'
                }
            
            # Wait a moment
            time.sleep(5)
            
            # Start backend container
            result = subprocess.run(['docker-compose', 'start', 'backend'], 
                                  capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                return {
                    'status': 'FAIL',
                    'error': f'Failed to start backend: {result.stderr}'
                }
            
            # Wait for service to be ready
            time.sleep(15)
            
            # Test if backend is responsive
            max_retries = 6
            for i in range(max_retries):
                try:
                    response = requests.get(f"{self.backend_url}/health", timeout=10)
                    if response.status_code == 200:
                        break
                    time.sleep(5)
                except:
                    if i == max_retries - 1:
                        return {
                            'status': 'FAIL',
                            'error': 'Backend not responsive after restart'
                        }
                    time.sleep(5)
            
            return {
                'status': 'PASS',
                'message': 'Service restart resilience test passed'
            }
            
        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e)
            }
    
    def generate_report(self):
        """Generate comprehensive test report"""
        report_file = 'deployment-test-report.json'
        
        # Save detailed JSON report
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        # Generate summary report
        summary_file = 'deployment-test-summary.txt'
        with open(summary_file, 'w') as f:
            f.write("DEPLOYMENT TEST SUMMARY\n")
            f.write("=" * 50 + "\n")
            f.write(f"Timestamp: {self.test_results['timestamp']}\n")
            f.write(f"Overall Status: {self.test_results['overall_status']}\n\n")
            
            passed = sum(1 for test in self.test_results['tests'].values() 
                        if test.get('status') == 'PASS')
            total = len(self.test_results['tests'])
            f.write(f"Tests Passed: {passed}/{total}\n\n")
            
            f.write("INDIVIDUAL TEST RESULTS:\n")
            f.write("-" * 30 + "\n")
            
            for test_name, result in self.test_results['tests'].items():
                status = result.get('status', 'UNKNOWN')
                f.write(f"{test_name}: {status}\n")
                if status != 'PASS' and 'error' in result:
                    f.write(f"  Error: {result['error']}\n")
                f.write("\n")
        
        logger.info(f"Test report saved to {report_file}")
        logger.info(f"Test summary saved to {summary_file}")

def main():
    """Main function to run deployment tests"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Usage: python comprehensive-deployment-test.py")
        print("This script performs comprehensive deployment testing including:")
        print("- Docker compose deployment")
        print("- Service health checks")
        print("- Database connectivity and persistence")
        print("- API endpoint testing")
        print("- Frontend accessibility")
        print("- Service restart resilience")
        return
    
    tester = DeploymentTester()
    
    try:
        overall_status = tester.run_all_tests()
        
        print("\n" + "=" * 60)
        print("DEPLOYMENT TEST COMPLETED")
        print("=" * 60)
        print(f"Overall Status: {overall_status}")
        
        if overall_status == 'PASS':
            print("✅ All tests passed! Deployment is ready.")
            sys.exit(0)
        elif overall_status == 'PARTIAL':
            print("⚠️  Some tests failed. Check the report for details.")
            sys.exit(1)
        else:
            print("❌ Deployment tests failed. Check the report for details.")
            sys.exit(2)
            
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        sys.exit(3)
    except Exception as e:
        print(f"Test execution failed: {str(e)}")
        sys.exit(4)

if __name__ == "__main__":
    main()