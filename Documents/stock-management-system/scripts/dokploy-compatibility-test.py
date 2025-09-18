#!/usr/bin/env python3
"""
Dokploy Compatibility Validation Script
Tests environment variable injection, service discovery, and persistent volumes
"""

import os
import sys
import json
import time
import subprocess
import requests
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dokploy-compatibility-test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DokployCompatibilityTester:
    def __init__(self):
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'overall_status': 'PENDING'
        }
        
    def run_all_tests(self):
        """Run all Dokploy compatibility tests"""
        logger.info("Starting Dokploy compatibility testing...")
        
        tests = [
            ('environment_variable_injection', self.test_environment_variable_injection),
            ('service_discovery_networking', self.test_service_discovery_networking),
            ('persistent_volume_mounting', self.test_persistent_volume_mounting),
            ('dokploy_specific_configs', self.test_dokploy_specific_configs),
            ('container_orchestration', self.test_container_orchestration),
            ('health_check_integration', self.test_health_check_integration)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"Running test: {test_name}")
            try:
                result = test_func()
                self.test_results['tests'][test_name] = result
                if result['status'] in ['PASS', 'SKIP']:
                    passed_tests += 1
                    status_icon = "✅" if result['status'] == 'PASS' else "⏭️"
                    logger.info(f"{status_icon} {test_name}: {result['status']}")
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
    
    def test_environment_variable_injection(self):
        """Test environment variable injection through Dokploy interface"""
        try:
            # Check if required environment variables are properly set
            required_vars = [
                'POSTGRES_DB',
                'POSTGRES_USER', 
                'POSTGRES_PASSWORD',
                'SECRET_KEY'
            ]
            
            missing_vars = []
            present_vars = []
            
            for var in required_vars:
                if os.getenv(var):
                    present_vars.append(var)
                else:
                    missing_vars.append(var)
            
            # Check if docker-compose can access environment variables
            result = subprocess.run([
                'docker-compose', 'config'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return {
                    'status': 'FAIL',
                    'error': f'Docker compose config failed: {result.stderr}'
                }
            
            # Parse the composed configuration to check variable substitution
            config_output = result.stdout
            
            # Check for unresolved variables (indicated by ${VAR} patterns)
            import re
            unresolved_vars = re.findall(r'\$\{([^}]+)\}', config_output)
            
            return {
                'status': 'PASS' if not missing_vars and not unresolved_vars else 'PARTIAL',
                'present_variables': present_vars,
                'missing_variables': missing_vars,
                'unresolved_variables': unresolved_vars,
                'message': 'Environment variable injection working' if not missing_vars else 'Some variables missing'
            }
            
        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e)
            }
    
    def test_service_discovery_networking(self):
        """Verify service discovery and internal networking"""
        try:
            # Check if services can resolve each other by name
            services_to_test = ['backend', 'frontend', 'postgres']
            
            # Get running containers
            result = subprocess.run([
                'docker-compose', 'ps', '--services', '--filter', 'status=running'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return {
                    'status': 'FAIL',
                    'error': 'Could not get running services'
                }
            
            running_services = result.stdout.strip().split('\n')
            
            # Test network connectivity between services
            network_tests = {}
            
            for service in running_services:
                if service in services_to_test:
                    # Test if we can resolve the service name from within the network
                    test_result = subprocess.run([
                        'docker-compose', 'exec', '-T', service, 'nslookup', 'backend'
                    ], capture_output=True, text=True, timeout=10)
                    
                    network_tests[service] = {
                        'can_resolve_backend': test_result.returncode == 0,
                        'output': test_result.stdout if test_result.returncode == 0 else test_result.stderr
                    }
            
            # Check Docker network configuration
            network_result = subprocess.run([
                'docker', 'network', 'ls', '--filter', 'name=stock-management'
            ], capture_output=True, text=True, timeout=10)
            
            networks_found = len(network_result.stdout.strip().split('\n')) - 1  # Subtract header
            
            return {
                'status': 'PASS' if networks_found > 0 else 'PARTIAL',
                'running_services': running_services,
                'network_tests': network_tests,
                'networks_found': networks_found,
                'message': 'Service discovery working' if networks_found > 0 else 'Limited network functionality'
            }
            
        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e)
            }
    
    def test_persistent_volume_mounting(self):
        """Validate persistent volume mounting and data persistence"""
        try:
            # Check if volumes are properly defined in docker-compose
            result = subprocess.run([
                'docker-compose', 'config'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return {
                    'status': 'FAIL',
                    'error': 'Could not get docker-compose configuration'
                }
            
            config_output = result.stdout
            
            # Check for volume definitions
            volume_checks = {
                'postgres_data_volume': 'postgres_data' in config_output,
                'volume_mounts': '/var/lib/postgresql/data' in config_output,
                'named_volumes': 'volumes:' in config_output
            }
            
            # Check actual Docker volumes
            volumes_result = subprocess.run([
                'docker', 'volume', 'ls', '--filter', 'name=stock-management'
            ], capture_output=True, text=True, timeout=10)
            
            volumes_found = []
            if volumes_result.returncode == 0:
                lines = volumes_result.stdout.strip().split('\n')[1:]  # Skip header
                volumes_found = [line.split()[-1] for line in lines if line.strip()]
            
            # Test volume persistence by checking if database files exist
            persistence_test = False
            if 'backend' in subprocess.run(['docker-compose', 'ps', '--services'], 
                                         capture_output=True, text=True).stdout:
                # Try to check if database directory exists in postgres container
                db_check = subprocess.run([
                    'docker-compose', 'exec', '-T', 'postgres', 'ls', '/var/lib/postgresql/data'
                ], capture_output=True, text=True, timeout=10)
                persistence_test = db_check.returncode == 0
            
            all_checks_passed = all(volume_checks.values()) and len(volumes_found) > 0
            
            return {
                'status': 'PASS' if all_checks_passed else 'PARTIAL',
                'volume_checks': volume_checks,
                'volumes_found': volumes_found,
                'persistence_test': persistence_test,
                'message': 'Volume mounting working correctly' if all_checks_passed else 'Some volume issues detected'
            }
            
        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e)
            }
    
    def test_dokploy_specific_configs(self):
        """Test Dokploy-specific configuration compatibility"""
        try:
            # Check for Dokploy-friendly configurations
            dokploy_configs = {}
            
            # Check docker-compose.yml for Dokploy compatibility
            with open('docker-compose.yml', 'r') as f:
                compose_content = f.read()
                
            # Check for health checks
            dokploy_configs['health_checks'] = 'healthcheck:' in compose_content
            
            # Check for restart policies
            dokploy_configs['restart_policies'] = 'restart:' in compose_content
            
            # Check for resource limits
            dokploy_configs['resource_limits'] = any(limit in compose_content for limit in ['mem_limit', 'cpus', 'deploy:'])
            
            # Check for proper port exposure
            dokploy_configs['port_exposure'] = 'ports:' in compose_content
            
            # Check for environment variable placeholders
            dokploy_configs['env_variables'] = '${' in compose_content
            
            # Check if .env.production exists (Dokploy template)
            dokploy_configs['production_env'] = os.path.exists('.env.production')
            
            # Check for Dokploy deployment guide
            dokploy_configs['deployment_guide'] = os.path.exists('DOKPLOY_DEPLOYMENT_GUIDE.md')
            
            passed_configs = sum(dokploy_configs.values())
            total_configs = len(dokploy_configs)
            
            return {
                'status': 'PASS' if passed_configs >= total_configs * 0.8 else 'PARTIAL',
                'configurations': dokploy_configs,
                'passed_configs': f"{passed_configs}/{total_configs}",
                'message': f'Dokploy compatibility: {passed_configs}/{total_configs} checks passed'
            }
            
        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e)
            }
    
    def test_container_orchestration(self):
        """Test container orchestration and dependency management"""
        try:
            # Check service dependencies in docker-compose
            result = subprocess.run([
                'docker-compose', 'config'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return {
                    'status': 'FAIL',
                    'error': 'Could not get docker-compose configuration'
                }
            
            config_output = result.stdout
            
            # Check for proper service dependencies
            orchestration_checks = {
                'depends_on': 'depends_on:' in config_output,
                'service_definitions': config_output.count('services:') >= 1,
                'network_definitions': 'networks:' in config_output or 'default' in config_output
            }
            
            # Test service startup order
            startup_test = True
            try:
                # Stop all services
                subprocess.run(['docker-compose', 'down'], capture_output=True, timeout=30)
                
                # Start services and check if they come up in correct order
                start_result = subprocess.run([
                    'docker-compose', 'up', '-d'
                ], capture_output=True, text=True, timeout=120)
                
                startup_test = start_result.returncode == 0
                
            except subprocess.TimeoutExpired:
                startup_test = False
            
            all_checks_passed = all(orchestration_checks.values()) and startup_test
            
            return {
                'status': 'PASS' if all_checks_passed else 'PARTIAL',
                'orchestration_checks': orchestration_checks,
                'startup_test': startup_test,
                'message': 'Container orchestration working' if all_checks_passed else 'Some orchestration issues'
            }
            
        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e)
            }
    
    def test_health_check_integration(self):
        """Test health check integration for Dokploy monitoring"""
        try:
            # Wait for services to be ready
            time.sleep(10)
            
            health_endpoints = [
                'http://localhost:5000/health',
                'http://localhost:5000/health/ready',
                'http://localhost:5000/health/live'
            ]
            
            health_results = {}
            
            for endpoint in health_endpoints:
                try:
                    response = requests.get(endpoint, timeout=5)
                    health_results[endpoint] = {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'accessible': True
                    }
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            health_results[endpoint]['has_json_response'] = True
                            health_results[endpoint]['response_data'] = data
                        except:
                            health_results[endpoint]['has_json_response'] = False
                    
                except requests.RequestException:
                    health_results[endpoint] = {
                        'accessible': False,
                        'error': 'Connection failed'
                    }
            
            # Check if Docker health checks are configured
            docker_health_check = False
            try:
                inspect_result = subprocess.run([
                    'docker-compose', 'ps', '--format', 'json'
                ], capture_output=True, text=True, timeout=10)
                
                if inspect_result.returncode == 0:
                    # Check if any service has health check configured
                    docker_health_check = 'Health' in inspect_result.stdout
            except:
                pass
            
            accessible_endpoints = sum(1 for result in health_results.values() 
                                     if result.get('accessible', False))
            
            return {
                'status': 'PASS' if accessible_endpoints >= 2 else 'PARTIAL',
                'health_endpoints': health_results,
                'docker_health_checks': docker_health_check,
                'accessible_endpoints': f"{accessible_endpoints}/{len(health_endpoints)}",
                'message': 'Health check integration working' if accessible_endpoints >= 2 else 'Limited health check functionality'
            }
            
        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e)
            }
    
    def generate_report(self):
        """Generate comprehensive Dokploy compatibility report"""
        report_file = 'dokploy-compatibility-report.json'
        
        # Save detailed JSON report
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        # Generate summary report
        summary_file = 'dokploy-compatibility-summary.txt'
        with open(summary_file, 'w') as f:
            f.write("DOKPLOY COMPATIBILITY TEST SUMMARY\n")
            f.write("=" * 50 + "\n")
            f.write(f"Timestamp: {self.test_results['timestamp']}\n")
            f.write(f"Overall Status: {self.test_results['overall_status']}\n\n")
            
            passed = sum(1 for test in self.test_results['tests'].values() 
                        if test.get('status') in ['PASS', 'SKIP'])
            total = len(self.test_results['tests'])
            f.write(f"Tests Passed/Skipped: {passed}/{total}\n\n")
            
            f.write("INDIVIDUAL TEST RESULTS:\n")
            f.write("-" * 30 + "\n")
            
            for test_name, result in self.test_results['tests'].items():
                status = result.get('status', 'UNKNOWN')
                f.write(f"{test_name}: {status}\n")
                if 'message' in result:
                    f.write(f"  Message: {result['message']}\n")
                if status not in ['PASS', 'SKIP'] and 'error' in result:
                    f.write(f"  Error: {result['error']}\n")
                f.write("\n")
            
            # Add recommendations
            f.write("DOKPLOY DEPLOYMENT RECOMMENDATIONS:\n")
            f.write("-" * 40 + "\n")
            f.write("1. Ensure all environment variables are configured in Dokploy\n")
            f.write("2. Verify persistent volumes are properly mounted\n")
            f.write("3. Check that health checks are responding correctly\n")
            f.write("4. Validate service networking and discovery\n")
            f.write("5. Monitor resource usage and adjust limits as needed\n")
        
        logger.info(f"Dokploy compatibility report saved to {report_file}")
        logger.info(f"Dokploy compatibility summary saved to {summary_file}")

def main():
    """Main function to run Dokploy compatibility tests"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Usage: python dokploy-compatibility-test.py")
        print("This script performs Dokploy compatibility testing including:")
        print("- Environment variable injection through Dokploy interface")
        print("- Service discovery and internal networking")
        print("- Persistent volume mounting and data persistence")
        print("- Dokploy-specific configuration validation")
        print("- Container orchestration testing")
        print("- Health check integration")
        return
    
    tester = DokployCompatibilityTester()
    
    try:
        overall_status = tester.run_all_tests()
        
        print("\n" + "=" * 60)
        print("DOKPLOY COMPATIBILITY TEST COMPLETED")
        print("=" * 60)
        print(f"Overall Status: {overall_status}")
        
        if overall_status == 'PASS':
            print("✅ All compatibility tests passed! Ready for Dokploy deployment.")
            sys.exit(0)
        elif overall_status == 'PARTIAL':
            print("⚠️  Some tests failed. Check the report for details.")
            sys.exit(1)
        else:
            print("❌ Dokploy compatibility tests failed. Check the report for details.")
            sys.exit(2)
            
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        sys.exit(3)
    except Exception as e:
        print(f"Test execution failed: {str(e)}")
        sys.exit(4)

if __name__ == "__main__":
    main()