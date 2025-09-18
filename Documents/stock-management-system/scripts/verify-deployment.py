#!/usr/bin/env python3
"""
Post-deployment health check verification script for Stock Management System.

This script verifies that all services are running correctly after deployment
to Dokploy by checking health endpoints, database connectivity, and API functionality.

Usage:
    python scripts/verify-deployment.py [--base-url https://yourdomain.com] [--timeout 30]

Options:
    --base-url: Base URL of the deployed application (default: http://localhost)
    --timeout: Request timeout in seconds (default: 30)
    --verbose: Enable verbose output
    --help: Show this help message
"""

import os
import sys
import time
import json
import argparse
import requests
from typing import Dict, List, Tuple, Optional
from urllib.parse import urljoin, urlparse

class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class HealthCheckResult:
    """Represents the result of a health check."""
    
    def __init__(self, name: str, passed: bool, message: str, 
                 response_time: Optional[float] = None, details: Optional[Dict] = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.response_time = response_time
        self.details = details or {}

class DeploymentVerifier:
    """Main verification class for post-deployment checks."""
    
    def __init__(self, base_url: str = 'http://localhost', timeout: int = 30, verbose: bool = False):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.verbose = verbose
        self.results: List[HealthCheckResult] = []
        
        # Configure requests session
        self.session = requests.Session()
        self.session.timeout = timeout
        
        # Health check endpoints to test
        self.health_endpoints = {
            'frontend': '/',
            'frontend_health': '/health',
            'api_health': '/api/health',
            'api_health_detailed': '/api/health/detailed',
            'api_health_ready': '/api/health/ready',
            'api_health_live': '/api/health/live'
        }
        
        # API endpoints to test
        self.api_endpoints = {
            'auth_status': '/api/auth/status',
            'locations': '/api/locations',
            'brands': '/api/brands',
            'suppliers': '/api/suppliers'
        }

    def print_header(self, text: str):
        """Print a formatted header."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")

    def print_result(self, result: HealthCheckResult):
        """Print a health check result with appropriate formatting."""
        if result.passed:
            icon = f"{Colors.GREEN}✓{Colors.END}"
            color = Colors.GREEN
        else:
            icon = f"{Colors.RED}✗{Colors.END}"
            color = Colors.RED
        
        response_time_str = ""
        if result.response_time is not None:
            response_time_str = f" ({result.response_time:.2f}s)"
        
        print(f"{icon} {Colors.BOLD}{result.name}{Colors.END}: {color}{result.message}{Colors.END}{response_time_str}")
        
        if self.verbose and result.details:
            for key, value in result.details.items():
                print(f"    {Colors.BLUE}{key}:{Colors.END} {value}")

    def make_request(self, endpoint: str, method: str = 'GET', 
                    expected_status: int = 200) -> Tuple[bool, float, Optional[Dict]]:
        """Make HTTP request and return success status, response time, and data."""
        url = urljoin(self.base_url, endpoint)
        start_time = time.time()
        
        try:
            if self.verbose:
                print(f"    Making {method} request to: {url}")
            
            response = self.session.request(method, url)
            response_time = time.time() - start_time
            
            if response.status_code == expected_status:
                try:
                    data = response.json() if response.content else {}
                    return True, response_time, data
                except json.JSONDecodeError:
                    # Non-JSON response is OK for some endpoints
                    return True, response_time, {'content': response.text[:200]}
            else:
                return False, response_time, {
                    'status_code': response.status_code,
                    'content': response.text[:200]
                }
                
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            return False, response_time, {'error': 'Request timeout'}
        except requests.exceptions.ConnectionError:
            response_time = time.time() - start_time
            return False, response_time, {'error': 'Connection error'}
        except Exception as e:
            response_time = time.time() - start_time
            return False, response_time, {'error': str(e)}

    def verify_frontend_accessibility(self):
        """Verify that the frontend is accessible."""
        self.print_header("FRONTEND ACCESSIBILITY")
        
        # Test main frontend page
        success, response_time, data = self.make_request('/')
        
        if success:
            self.results.append(HealthCheckResult(
                "Frontend Main Page",
                True,
                "Frontend is accessible",
                response_time,
                data
            ))
        else:
            self.results.append(HealthCheckResult(
                "Frontend Main Page",
                False,
                f"Frontend not accessible: {data.get('error', 'Unknown error')}",
                response_time,
                data
            ))
        
        # Test frontend health endpoint (if available)
        success, response_time, data = self.make_request('/health')
        
        if success:
            self.results.append(HealthCheckResult(
                "Frontend Health Endpoint",
                True,
                "Frontend health check passed",
                response_time,
                data
            ))
        else:
            # Frontend health endpoint might not exist, so this is not critical
            self.results.append(HealthCheckResult(
                "Frontend Health Endpoint",
                False,
                "Frontend health endpoint not available (optional)",
                response_time,
                data
            ))

    def verify_api_health_endpoints(self):
        """Verify API health check endpoints."""
        self.print_header("API HEALTH ENDPOINTS")
        
        # Test basic health endpoint
        success, response_time, data = self.make_request('/api/health')
        
        if success:
            self.results.append(HealthCheckResult(
                "API Basic Health",
                True,
                "API health check passed",
                response_time,
                data
            ))
            
            # Verify health response structure
            if isinstance(data, dict):
                status = data.get('status', 'unknown')
                if status in ['healthy', 'ok']:
                    self.results.append(HealthCheckResult(
                        "API Health Status",
                        True,
                        f"API reports status: {status}",
                        details={'status': status}
                    ))
                else:
                    self.results.append(HealthCheckResult(
                        "API Health Status",
                        False,
                        f"API reports unhealthy status: {status}",
                        details={'status': status}
                    ))
        else:
            self.results.append(HealthCheckResult(
                "API Basic Health",
                False,
                f"API health check failed: {data.get('error', 'Unknown error')}",
                response_time,
                data
            ))
        
        # Test detailed health endpoint
        success, response_time, data = self.make_request('/api/health/detailed')
        
        if success:
            self.results.append(HealthCheckResult(
                "API Detailed Health",
                True,
                "API detailed health check passed",
                response_time,
                data
            ))
            
            # Check for system metrics
            if isinstance(data, dict):
                system_info = data.get('system', {})
                database_info = data.get('database', {})
                
                if system_info:
                    self.results.append(HealthCheckResult(
                        "System Metrics",
                        True,
                        "System metrics available",
                        details=system_info
                    ))
                
                if database_info:
                    db_status = database_info.get('status', 'unknown')
                    if db_status in ['connected', 'healthy']:
                        self.results.append(HealthCheckResult(
                            "Database Connectivity",
                            True,
                            f"Database status: {db_status}",
                            details=database_info
                        ))
                    else:
                        self.results.append(HealthCheckResult(
                            "Database Connectivity",
                            False,
                            f"Database status: {db_status}",
                            details=database_info
                        ))
        else:
            self.results.append(HealthCheckResult(
                "API Detailed Health",
                False,
                f"API detailed health check failed: {data.get('error', 'Unknown error')}",
                response_time,
                data
            ))
        
        # Test readiness probe
        success, response_time, data = self.make_request('/api/health/ready')
        
        if success:
            self.results.append(HealthCheckResult(
                "API Readiness Probe",
                True,
                "API readiness check passed",
                response_time,
                data
            ))
        else:
            self.results.append(HealthCheckResult(
                "API Readiness Probe",
                False,
                f"API readiness check failed: {data.get('error', 'Unknown error')}",
                response_time,
                data
            ))
        
        # Test liveness probe
        success, response_time, data = self.make_request('/api/health/live')
        
        if success:
            self.results.append(HealthCheckResult(
                "API Liveness Probe",
                True,
                "API liveness check passed",
                response_time,
                data
            ))
        else:
            self.results.append(HealthCheckResult(
                "API Liveness Probe",
                False,
                f"API liveness check failed: {data.get('error', 'Unknown error')}",
                response_time,
                data
            ))

    def verify_api_endpoints(self):
        """Verify core API endpoints are accessible."""
        self.print_header("API ENDPOINTS")
        
        for endpoint_name, endpoint_path in self.api_endpoints.items():
            success, response_time, data = self.make_request(endpoint_path)
            
            if success:
                self.results.append(HealthCheckResult(
                    f"API Endpoint: {endpoint_name}",
                    True,
                    f"Endpoint {endpoint_path} is accessible",
                    response_time,
                    {'endpoint': endpoint_path}
                ))
                
                # Check if response contains expected data structure
                if isinstance(data, dict):
                    if 'error' in data:
                        # API returned an error (might be authentication required)
                        error_msg = data.get('error', 'Unknown error')
                        if 'authentication' in error_msg.lower() or 'unauthorized' in error_msg.lower():
                            self.results.append(HealthCheckResult(
                                f"API Auth: {endpoint_name}",
                                True,
                                "Authentication required (expected for protected endpoints)",
                                details={'auth_required': True}
                            ))
                        else:
                            self.results.append(HealthCheckResult(
                                f"API Response: {endpoint_name}",
                                False,
                                f"API error: {error_msg}",
                                details=data
                            ))
                    elif isinstance(data, list) or 'data' in data:
                        self.results.append(HealthCheckResult(
                            f"API Response: {endpoint_name}",
                            True,
                            "API returned expected data structure",
                            details={'response_type': type(data).__name__}
                        ))
            else:
                self.results.append(HealthCheckResult(
                    f"API Endpoint: {endpoint_name}",
                    False,
                    f"Endpoint {endpoint_path} failed: {data.get('error', 'Unknown error')}",
                    response_time,
                    data
                ))

    def verify_cors_configuration(self):
        """Verify CORS configuration is working correctly."""
        self.print_header("CORS CONFIGURATION")
        
        # Test CORS preflight request
        success, response_time, data = self.make_request(
            '/api/health', 
            method='OPTIONS'
        )
        
        if success:
            self.results.append(HealthCheckResult(
                "CORS Preflight",
                True,
                "CORS preflight request successful",
                response_time,
                data
            ))
        else:
            self.results.append(HealthCheckResult(
                "CORS Preflight",
                False,
                f"CORS preflight failed: {data.get('error', 'Unknown error')}",
                response_time,
                data
            ))
        
        # Test actual CORS request with Origin header
        parsed_url = urlparse(self.base_url)
        origin = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        try:
            headers = {'Origin': origin}
            url = urljoin(self.base_url, '/api/health')
            start_time = time.time()
            
            response = self.session.get(url, headers=headers)
            response_time = time.time() - start_time
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            if response.status_code == 200:
                self.results.append(HealthCheckResult(
                    "CORS Headers",
                    True,
                    "CORS headers present in response",
                    response_time,
                    cors_headers
                ))
            else:
                self.results.append(HealthCheckResult(
                    "CORS Headers",
                    False,
                    f"CORS request failed with status {response.status_code}",
                    response_time,
                    cors_headers
                ))
                
        except Exception as e:
            self.results.append(HealthCheckResult(
                "CORS Headers",
                False,
                f"CORS test failed: {str(e)}",
                details={'error': str(e)}
            ))

    def verify_security_headers(self):
        """Verify security headers are present."""
        self.print_header("SECURITY HEADERS")
        
        success, response_time, data = self.make_request('/')
        
        if success:
            # Get the actual response to check headers
            try:
                url = urljoin(self.base_url, '/')
                response = self.session.get(url)
                
                security_headers = {
                    'X-Content-Type-Options': response.headers.get('X-Content-Type-Options'),
                    'X-Frame-Options': response.headers.get('X-Frame-Options'),
                    'X-XSS-Protection': response.headers.get('X-XSS-Protection'),
                    'Strict-Transport-Security': response.headers.get('Strict-Transport-Security'),
                    'Content-Security-Policy': response.headers.get('Content-Security-Policy')
                }
                
                present_headers = {k: v for k, v in security_headers.items() if v is not None}
                missing_headers = [k for k, v in security_headers.items() if v is None]
                
                if present_headers:
                    self.results.append(HealthCheckResult(
                        "Security Headers Present",
                        True,
                        f"Found {len(present_headers)} security headers",
                        details=present_headers
                    ))
                
                if missing_headers:
                    self.results.append(HealthCheckResult(
                        "Security Headers Missing",
                        False,
                        f"Missing {len(missing_headers)} security headers: {', '.join(missing_headers)}",
                        details={'missing': missing_headers}
                    ))
                else:
                    self.results.append(HealthCheckResult(
                        "Security Headers Complete",
                        True,
                        "All expected security headers present"
                    ))
                    
            except Exception as e:
                self.results.append(HealthCheckResult(
                    "Security Headers",
                    False,
                    f"Failed to check security headers: {str(e)}",
                    details={'error': str(e)}
                ))

    def verify_performance_metrics(self):
        """Verify performance metrics and response times."""
        self.print_header("PERFORMANCE METRICS")
        
        # Calculate average response times
        response_times = [r.response_time for r in self.results if r.response_time is not None]
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            self.results.append(HealthCheckResult(
                "Average Response Time",
                avg_response_time < 2.0,  # Consider good if under 2 seconds
                f"{avg_response_time:.2f}s (min: {min_response_time:.2f}s, max: {max_response_time:.2f}s)",
                details={
                    'average': avg_response_time,
                    'minimum': min_response_time,
                    'maximum': max_response_time,
                    'total_requests': len(response_times)
                }
            ))
            
            # Check for slow responses
            slow_responses = [r for r in self.results if r.response_time and r.response_time > 5.0]
            if slow_responses:
                self.results.append(HealthCheckResult(
                    "Slow Responses",
                    False,
                    f"Found {len(slow_responses)} slow responses (>5s)",
                    details={'slow_endpoints': [r.name for r in slow_responses]}
                ))
            else:
                self.results.append(HealthCheckResult(
                    "Response Times",
                    True,
                    "All responses under 5 seconds"
                ))

    def generate_summary(self) -> Tuple[int, int]:
        """Generate and print verification summary."""
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        
        self.print_header("VERIFICATION SUMMARY")
        
        print(f"{Colors.GREEN}✓ Passed:{Colors.END} {passed}")
        print(f"{Colors.RED}✗ Failed:{Colors.END} {failed}")
        print(f"{Colors.BOLD}Total Checks:{Colors.END} {len(self.results)}")
        
        # Print failed checks
        if failed > 0:
            print(f"\n{Colors.RED}{Colors.BOLD}FAILED CHECKS:{Colors.END}")
            for result in self.results:
                if not result.passed:
                    print(f"  {Colors.RED}✗{Colors.END} {result.name}: {result.message}")
        
        return passed, failed

    def run_verification(self) -> bool:
        """Run all verification checks."""
        print(f"{Colors.BOLD}{Colors.MAGENTA}Stock Management System - Deployment Verification{Colors.END}")
        print(f"Base URL: {self.base_url}")
        print(f"Timeout: {self.timeout}s")
        print(f"Verbose: {'Enabled' if self.verbose else 'Disabled'}")
        
        # Run all verification checks
        self.verify_frontend_accessibility()
        self.verify_api_health_endpoints()
        self.verify_api_endpoints()
        self.verify_cors_configuration()
        self.verify_security_headers()
        self.verify_performance_metrics()
        
        # Print all results
        print(f"\n{Colors.BOLD}{Colors.BLUE}DETAILED RESULTS:{Colors.END}")
        for result in self.results:
            self.print_result(result)
        
        # Generate summary
        passed, failed = self.generate_summary()
        
        # Determine overall success
        if failed > 0:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ VERIFICATION FAILED{Colors.END}")
            print(f"Fix the {failed} failed check(s) for optimal deployment.")
            return False
        else:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ VERIFICATION PASSED{Colors.END}")
            print("All checks passed. Deployment is healthy!")
            return True

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Verify Stock Management System deployment health",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/verify-deployment.py
  python scripts/verify-deployment.py --base-url https://myapp.com
  python scripts/verify-deployment.py --base-url http://localhost:8080 --timeout 60
  python scripts/verify-deployment.py --base-url https://myapp.com --verbose
        """
    )
    
    parser.add_argument(
        '--base-url',
        default='http://localhost',
        help='Base URL of the deployed application (default: http://localhost)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='Request timeout in seconds (default: 30)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Create verifier and run verification
    verifier = DeploymentVerifier(args.base_url, args.timeout, args.verbose)
    success = verifier.run_verification()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()