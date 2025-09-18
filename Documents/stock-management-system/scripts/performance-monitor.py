#!/usr/bin/env python3
"""
Performance monitoring script for Stock Management System
Monitors application performance metrics and generates reports
"""

import requests
import time
import json
import sys
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import statistics


class PerformanceMonitor:
    """
    Monitor application performance metrics
    """
    
    def __init__(self, base_url: str = "http://localhost", timeout: int = 30):
        """
        Initialize performance monitor
        
        Args:
            base_url: Base URL of the application
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.timeout = timeout
        
        # Performance thresholds
        self.thresholds = {
            'response_time_warning': 1000,  # ms
            'response_time_critical': 3000,  # ms
            'memory_warning': 80,  # %
            'memory_critical': 90,  # %
            'cpu_warning': 70,  # %
            'cpu_critical': 85,  # %
            'disk_warning': 80,  # %
            'disk_critical': 90  # %
        }
    
    def check_health_endpoint(self) -> Dict:
        """
        Check application health endpoint
        
        Returns:
            Health check results
        """
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/health")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                health_data = response.json()
                health_data['measured_response_time'] = response_time
                return {
                    'status': 'success',
                    'data': health_data,
                    'response_time': response_time
                }
            else:
                return {
                    'status': 'error',
                    'error': f"HTTP {response.status_code}",
                    'response_time': response_time
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'error': str(e),
                'response_time': None
            }
    
    def check_readiness_endpoint(self) -> Dict:
        """
        Check application readiness endpoint
        
        Returns:
            Readiness check results
        """
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/health/ready")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return {
                    'status': 'ready',
                    'data': response.json(),
                    'response_time': response_time
                }
            else:
                return {
                    'status': 'not_ready',
                    'error': f"HTTP {response.status_code}",
                    'response_time': response_time
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'error': str(e),
                'response_time': None
            }
    
    def check_liveness_endpoint(self) -> Dict:
        """
        Check application liveness endpoint
        
        Returns:
            Liveness check results
        """
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/health/live")
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return {
                    'status': 'alive',
                    'data': response.json(),
                    'response_time': response_time
                }
            else:
                return {
                    'status': 'not_alive',
                    'error': f"HTTP {response.status_code}",
                    'response_time': response_time
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'error': str(e),
                'response_time': None
            }
    
    def test_api_endpoints(self) -> Dict:
        """
        Test various API endpoints for performance
        
        Returns:
            API performance test results
        """
        endpoints = [
            '/api/health',
            '/api/health/ready',
            '/api/health/live',
            '/api/dashboard/summary',
            '/api/inventory',
            '/api/products',
            '/api/locations'
        ]
        
        results = {}
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}{endpoint}")
                response_time = (time.time() - start_time) * 1000
                
                results[endpoint] = {
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'content_length': len(response.content) if response.content else 0,
                    'status': 'success' if 200 <= response.status_code < 300 else 'error'
                }
                
            except requests.exceptions.RequestException as e:
                results[endpoint] = {
                    'status': 'error',
                    'error': str(e),
                    'response_time': None
                }
        
        return results
    
    def analyze_performance(self, health_data: Dict) -> Dict:
        """
        Analyze performance metrics and identify issues
        
        Args:
            health_data: Health check data
            
        Returns:
            Performance analysis results
        """
        analysis = {
            'overall_status': 'healthy',
            'warnings': [],
            'critical_issues': [],
            'recommendations': []
        }
        
        if 'data' not in health_data or 'system' not in health_data['data']:
            analysis['overall_status'] = 'unknown'
            analysis['critical_issues'].append("Unable to retrieve system metrics")
            return analysis
        
        system = health_data['data']['system']
        
        # Check response time
        response_time = health_data.get('response_time', 0)
        if response_time > self.thresholds['response_time_critical']:
            analysis['critical_issues'].append(f"Critical response time: {response_time:.1f}ms")
            analysis['overall_status'] = 'critical'
        elif response_time > self.thresholds['response_time_warning']:
            analysis['warnings'].append(f"Slow response time: {response_time:.1f}ms")
            if analysis['overall_status'] == 'healthy':
                analysis['overall_status'] = 'warning'
        
        # Check memory usage
        if 'memory' in system:
            memory_percent = system['memory'].get('percent', 0)
            if memory_percent > self.thresholds['memory_critical']:
                analysis['critical_issues'].append(f"Critical memory usage: {memory_percent:.1f}%")
                analysis['overall_status'] = 'critical'
            elif memory_percent > self.thresholds['memory_warning']:
                analysis['warnings'].append(f"High memory usage: {memory_percent:.1f}%")
                if analysis['overall_status'] == 'healthy':
                    analysis['overall_status'] = 'warning'
        
        # Check CPU usage
        if 'cpu' in system:
            cpu_percent = system['cpu'].get('percent', 0)
            if cpu_percent > self.thresholds['cpu_critical']:
                analysis['critical_issues'].append(f"Critical CPU usage: {cpu_percent:.1f}%")
                analysis['overall_status'] = 'critical'
            elif cpu_percent > self.thresholds['cpu_warning']:
                analysis['warnings'].append(f"High CPU usage: {cpu_percent:.1f}%")
                if analysis['overall_status'] == 'healthy':
                    analysis['overall_status'] = 'warning'
        
        # Check disk usage
        if 'disk' in system:
            disk_percent = system['disk'].get('percent', 0)
            if disk_percent > self.thresholds['disk_critical']:
                analysis['critical_issues'].append(f"Critical disk usage: {disk_percent:.1f}%")
                analysis['overall_status'] = 'critical'
            elif disk_percent > self.thresholds['disk_warning']:
                analysis['warnings'].append(f"High disk usage: {disk_percent:.1f}%")
                if analysis['overall_status'] == 'healthy':
                    analysis['overall_status'] = 'warning'
        
        # Check database status
        if 'database' in health_data['data']:
            db_status = health_data['data']['database'].get('status')
            if db_status != 'connected':
                analysis['critical_issues'].append("Database not connected")
                analysis['overall_status'] = 'critical'
            else:
                db_response_time = health_data['data']['database'].get('response_time_ms', 0)
                if db_response_time > 1000:
                    analysis['warnings'].append(f"Slow database response: {db_response_time:.1f}ms")
                    if analysis['overall_status'] == 'healthy':
                        analysis['overall_status'] = 'warning'
        
        # Generate recommendations
        if analysis['warnings'] or analysis['critical_issues']:
            if any('memory' in issue.lower() for issue in analysis['critical_issues'] + analysis['warnings']):
                analysis['recommendations'].append("Consider increasing memory allocation or optimizing memory usage")
            
            if any('cpu' in issue.lower() for issue in analysis['critical_issues'] + analysis['warnings']):
                analysis['recommendations'].append("Consider increasing CPU allocation or optimizing CPU-intensive operations")
            
            if any('disk' in issue.lower() for issue in analysis['critical_issues'] + analysis['warnings']):
                analysis['recommendations'].append("Clean up disk space or increase storage allocation")
            
            if any('response time' in issue.lower() for issue in analysis['critical_issues'] + analysis['warnings']):
                analysis['recommendations'].append("Optimize application performance or increase resource allocation")
            
            if any('database' in issue.lower() for issue in analysis['critical_issues'] + analysis['warnings']):
                analysis['recommendations'].append("Check database configuration and connection pool settings")
        
        return analysis
    
    def run_performance_test(self, duration: int = 60, interval: int = 5) -> Dict:
        """
        Run continuous performance monitoring for specified duration
        
        Args:
            duration: Test duration in seconds
            interval: Check interval in seconds
            
        Returns:
            Performance test results
        """
        print(f"Running performance test for {duration} seconds with {interval}s intervals...")
        
        start_time = time.time()
        end_time = start_time + duration
        
        results = {
            'start_time': datetime.fromtimestamp(start_time).isoformat(),
            'duration': duration,
            'interval': interval,
            'checks': [],
            'summary': {}
        }
        
        response_times = []
        
        while time.time() < end_time:
            check_time = datetime.now().isoformat()
            
            # Health check
            health_result = self.check_health_endpoint()
            
            # API endpoint tests
            api_results = self.test_api_endpoints()
            
            check_result = {
                'timestamp': check_time,
                'health': health_result,
                'api_endpoints': api_results
            }
            
            results['checks'].append(check_result)
            
            if health_result.get('response_time'):
                response_times.append(health_result['response_time'])
            
            print(f"Check at {check_time}: Health={health_result.get('status', 'unknown')}, "
                  f"Response={health_result.get('response_time', 'N/A'):.1f}ms")
            
            time.sleep(interval)
        
        # Calculate summary statistics
        if response_times:
            results['summary'] = {
                'total_checks': len(results['checks']),
                'successful_checks': len([c for c in results['checks'] if c['health']['status'] == 'success']),
                'average_response_time': statistics.mean(response_times),
                'median_response_time': statistics.median(response_times),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'response_time_std': statistics.stdev(response_times) if len(response_times) > 1 else 0
            }
        
        return results
    
    def generate_report(self, results: Dict) -> str:
        """
        Generate human-readable performance report
        
        Args:
            results: Performance test results
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 60)
        report.append("STOCK MANAGEMENT SYSTEM - PERFORMANCE REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Base URL: {self.base_url}")
        report.append("")
        
        if 'summary' in results and results['summary']:
            summary = results['summary']
            report.append("SUMMARY STATISTICS:")
            report.append("-" * 20)
            report.append(f"Total Checks: {summary['total_checks']}")
            report.append(f"Successful Checks: {summary['successful_checks']}")
            report.append(f"Success Rate: {(summary['successful_checks']/summary['total_checks']*100):.1f}%")
            report.append(f"Average Response Time: {summary['average_response_time']:.1f}ms")
            report.append(f"Median Response Time: {summary['median_response_time']:.1f}ms")
            report.append(f"Min Response Time: {summary['min_response_time']:.1f}ms")
            report.append(f"Max Response Time: {summary['max_response_time']:.1f}ms")
            report.append(f"Response Time Std Dev: {summary['response_time_std']:.1f}ms")
            report.append("")
        
        # Get latest health check for analysis
        if results.get('checks'):
            latest_check = results['checks'][-1]
            analysis = self.analyze_performance(latest_check['health'])
            
            report.append("PERFORMANCE ANALYSIS:")
            report.append("-" * 20)
            report.append(f"Overall Status: {analysis['overall_status'].upper()}")
            
            if analysis['critical_issues']:
                report.append("\nCRITICAL ISSUES:")
                for issue in analysis['critical_issues']:
                    report.append(f"  ❌ {issue}")
            
            if analysis['warnings']:
                report.append("\nWARNINGS:")
                for warning in analysis['warnings']:
                    report.append(f"  ⚠️  {warning}")
            
            if analysis['recommendations']:
                report.append("\nRECOMMENDATIONS:")
                for rec in analysis['recommendations']:
                    report.append(f"  💡 {rec}")
            
            if not analysis['critical_issues'] and not analysis['warnings']:
                report.append("  ✅ All performance metrics within acceptable ranges")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description="Stock Management System Performance Monitor")
    parser.add_argument("--url", default="http://localhost", help="Base URL of the application")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("--interval", type=int, default=5, help="Check interval in seconds")
    parser.add_argument("--output", help="Output file for results (JSON format)")
    parser.add_argument("--report", help="Output file for human-readable report")
    parser.add_argument("--single", action="store_true", help="Run single check instead of continuous monitoring")
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor(args.url, args.timeout)
    
    try:
        if args.single:
            # Single health check
            print("Running single performance check...")
            health_result = monitor.check_health_endpoint()
            readiness_result = monitor.check_readiness_endpoint()
            liveness_result = monitor.check_liveness_endpoint()
            api_results = monitor.test_api_endpoints()
            
            results = {
                'timestamp': datetime.now().isoformat(),
                'health': health_result,
                'readiness': readiness_result,
                'liveness': liveness_result,
                'api_endpoints': api_results
            }
            
            # Analyze performance
            analysis = monitor.analyze_performance(health_result)
            results['analysis'] = analysis
            
            print(f"\nHealth Status: {health_result.get('status', 'unknown')}")
            print(f"Response Time: {health_result.get('response_time', 'N/A'):.1f}ms")
            print(f"Overall Performance: {analysis['overall_status'].upper()}")
            
            if analysis['critical_issues']:
                print("\nCritical Issues:")
                for issue in analysis['critical_issues']:
                    print(f"  - {issue}")
            
            if analysis['warnings']:
                print("\nWarnings:")
                for warning in analysis['warnings']:
                    print(f"  - {warning}")
        
        else:
            # Continuous monitoring
            results = monitor.run_performance_test(args.duration, args.interval)
        
        # Save results to file if specified
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to: {args.output}")
        
        # Generate and save report if specified
        if args.report:
            report = monitor.generate_report(results)
            with open(args.report, 'w') as f:
                f.write(report)
            print(f"Report saved to: {args.report}")
        else:
            # Print report to console
            report = monitor.generate_report(results)
            print("\n" + report)
    
    except KeyboardInterrupt:
        print("\nMonitoring interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error during monitoring: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()