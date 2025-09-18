#!/usr/bin/env python3
"""
Resource monitoring and alerting script for Stock Management System
Monitors system resources and sends alerts when thresholds are exceeded
"""

import requests
import time
import json
import sys
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart


class ResourceMonitor:
    """
    Monitor system resources and generate alerts
    """
    
    def __init__(self, base_url: str = "http://localhost", config_file: str = None):
        """
        Initialize resource monitor
        
        Args:
            base_url: Base URL of the application
            config_file: Path to configuration file
        """
        self.base_url = base_url.rstrip('/')
        self.config = self.load_config(config_file)
        self.logger = self.setup_logging()
        
        # Default thresholds (can be overridden by config)
        self.thresholds = self.config.get('thresholds', {
            'cpu': {'warning': 70, 'critical': 85},
            'memory': {'warning': 80, 'critical': 90},
            'disk': {'warning': 80, 'critical': 90},
            'response_time': {'warning': 1000, 'critical': 3000}  # milliseconds
        })
        
        # Alert settings
        self.alert_settings = self.config.get('alerts', {
            'enabled': True,
            'email_enabled': False,
            'webhook_enabled': False,
            'cooldown_minutes': 15  # Minimum time between alerts for same issue
        })
        
        # Track last alert times to prevent spam
        self.last_alerts = {}
    
    def load_config(self, config_file: str) -> Dict:
        """
        Load configuration from file
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        if config_file:
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load config file {config_file}: {e}")
        
        return {}
    
    def setup_logging(self) -> logging.Logger:
        """
        Setup logging configuration
        
        Returns:
            Configured logger
        """
        logger = logging.getLogger('resource_monitor')
        logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # File handler if specified in config
        log_file = self.config.get('logging', {}).get('file')
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def get_resource_metrics(self) -> Dict:
        """
        Get current resource metrics from the application
        
        Returns:
            Resource metrics dictionary
        """
        try:
            response = requests.get(f"{self.base_url}/api/health/resources", timeout=30)
            
            if response.status_code == 200:
                return {
                    'status': 'success',
                    'data': response.json()
                }
            else:
                return {
                    'status': 'error',
                    'error': f"HTTP {response.status_code}",
                    'data': None
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'error': str(e),
                'data': None
            }
    
    def check_thresholds(self, metrics: Dict) -> List[Dict]:
        """
        Check resource metrics against thresholds
        
        Args:
            metrics: Resource metrics data
            
        Returns:
            List of threshold violations
        """
        violations = []
        
        if not metrics or 'system' not in metrics:
            return violations
        
        system = metrics['system']
        
        # Check CPU usage
        if 'cpu' in system and 'percent' in system['cpu']:
            cpu_percent = system['cpu']['percent']
            if cpu_percent >= self.thresholds['cpu']['critical']:
                violations.append({
                    'type': 'critical',
                    'resource': 'cpu',
                    'current': cpu_percent,
                    'threshold': self.thresholds['cpu']['critical'],
                    'message': f"Critical CPU usage: {cpu_percent:.1f}%"
                })
            elif cpu_percent >= self.thresholds['cpu']['warning']:
                violations.append({
                    'type': 'warning',
                    'resource': 'cpu',
                    'current': cpu_percent,
                    'threshold': self.thresholds['cpu']['warning'],
                    'message': f"High CPU usage: {cpu_percent:.1f}%"
                })
        
        # Check Memory usage
        if 'memory' in system and 'percent' in system['memory']:
            memory_percent = system['memory']['percent']
            if memory_percent >= self.thresholds['memory']['critical']:
                violations.append({
                    'type': 'critical',
                    'resource': 'memory',
                    'current': memory_percent,
                    'threshold': self.thresholds['memory']['critical'],
                    'message': f"Critical memory usage: {memory_percent:.1f}%"
                })
            elif memory_percent >= self.thresholds['memory']['warning']:
                violations.append({
                    'type': 'warning',
                    'resource': 'memory',
                    'current': memory_percent,
                    'threshold': self.thresholds['memory']['warning'],
                    'message': f"High memory usage: {memory_percent:.1f}%"
                })
        
        # Check Disk usage
        if 'disk' in system and 'percent' in system['disk']:
            disk_percent = system['disk']['percent']
            if disk_percent >= self.thresholds['disk']['critical']:
                violations.append({
                    'type': 'critical',
                    'resource': 'disk',
                    'current': disk_percent,
                    'threshold': self.thresholds['disk']['critical'],
                    'message': f"Critical disk usage: {disk_percent:.1f}%"
                })
            elif disk_percent >= self.thresholds['disk']['warning']:
                violations.append({
                    'type': 'warning',
                    'resource': 'disk',
                    'current': disk_percent,
                    'threshold': self.thresholds['disk']['warning'],
                    'message': f"High disk usage: {disk_percent:.1f}%"
                })
        
        # Check Response time
        response_time = metrics.get('response_time_ms', 0)
        if response_time >= self.thresholds['response_time']['critical']:
            violations.append({
                'type': 'critical',
                'resource': 'response_time',
                'current': response_time,
                'threshold': self.thresholds['response_time']['critical'],
                'message': f"Critical response time: {response_time:.1f}ms"
            })
        elif response_time >= self.thresholds['response_time']['warning']:
            violations.append({
                'type': 'warning',
                'resource': 'response_time',
                'current': response_time,
                'threshold': self.thresholds['response_time']['warning'],
                'message': f"Slow response time: {response_time:.1f}ms"
            })
        
        return violations
    
    def should_send_alert(self, violation: Dict) -> bool:
        """
        Check if alert should be sent based on cooldown period
        
        Args:
            violation: Threshold violation data
            
        Returns:
            True if alert should be sent
        """
        if not self.alert_settings.get('enabled', True):
            return False
        
        alert_key = f"{violation['resource']}_{violation['type']}"
        now = datetime.now()
        
        if alert_key in self.last_alerts:
            last_alert_time = self.last_alerts[alert_key]
            cooldown_period = timedelta(minutes=self.alert_settings.get('cooldown_minutes', 15))
            
            if now - last_alert_time < cooldown_period:
                return False
        
        self.last_alerts[alert_key] = now
        return True
    
    def send_email_alert(self, violations: List[Dict], metrics: Dict):
        """
        Send email alert for threshold violations
        
        Args:
            violations: List of threshold violations
            metrics: Current resource metrics
        """
        email_config = self.config.get('email', {})
        
        if not email_config.get('enabled', False):
            return
        
        try:
            # Create message
            msg = MimeMultipart()
            msg['From'] = email_config['from']
            msg['To'] = ', '.join(email_config['to'])
            msg['Subject'] = f"Stock Management System - Resource Alert ({len(violations)} issues)"
            
            # Create email body
            body = self.create_alert_email_body(violations, metrics)
            msg.attach(MimeText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            if email_config.get('use_tls', True):
                server.starttls()
            if email_config.get('username') and email_config.get('password'):
                server.login(email_config['username'], email_config['password'])
            
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email alert sent for {len(violations)} violations")
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
    
    def send_webhook_alert(self, violations: List[Dict], metrics: Dict):
        """
        Send webhook alert for threshold violations
        
        Args:
            violations: List of threshold violations
            metrics: Current resource metrics
        """
        webhook_config = self.config.get('webhook', {})
        
        if not webhook_config.get('enabled', False):
            return
        
        try:
            payload = {
                'timestamp': datetime.now().isoformat(),
                'service': 'stock-management-system',
                'alert_type': 'resource_threshold',
                'violations': violations,
                'metrics_summary': {
                    'cpu_percent': metrics.get('system', {}).get('cpu', {}).get('percent'),
                    'memory_percent': metrics.get('system', {}).get('memory', {}).get('percent'),
                    'disk_percent': metrics.get('system', {}).get('disk', {}).get('percent'),
                    'response_time_ms': metrics.get('response_time_ms')
                }
            }
            
            response = requests.post(
                webhook_config['url'],
                json=payload,
                headers=webhook_config.get('headers', {}),
                timeout=30
            )
            
            if response.status_code == 200:
                self.logger.info(f"Webhook alert sent for {len(violations)} violations")
            else:
                self.logger.error(f"Webhook alert failed: HTTP {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}")
    
    def create_alert_email_body(self, violations: List[Dict], metrics: Dict) -> str:
        """
        Create HTML email body for alert
        
        Args:
            violations: List of threshold violations
            metrics: Current resource metrics
            
        Returns:
            HTML email body
        """
        critical_count = len([v for v in violations if v['type'] == 'critical'])
        warning_count = len([v for v in violations if v['type'] == 'warning'])
        
        html = f"""
        <html>
        <body>
        <h2>Stock Management System - Resource Alert</h2>
        <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Service:</strong> {self.base_url}</p>
        
        <h3>Alert Summary</h3>
        <ul>
        <li>Critical Issues: {critical_count}</li>
        <li>Warnings: {warning_count}</li>
        </ul>
        
        <h3>Threshold Violations</h3>
        <table border="1" cellpadding="5" cellspacing="0">
        <tr>
        <th>Type</th>
        <th>Resource</th>
        <th>Current</th>
        <th>Threshold</th>
        <th>Message</th>
        </tr>
        """
        
        for violation in violations:
            color = '#ff4444' if violation['type'] == 'critical' else '#ffaa00'
            html += f"""
            <tr style="background-color: {color}; color: white;">
            <td>{violation['type'].upper()}</td>
            <td>{violation['resource']}</td>
            <td>{violation['current']}</td>
            <td>{violation['threshold']}</td>
            <td>{violation['message']}</td>
            </tr>
            """
        
        html += """
        </table>
        
        <h3>Current System Status</h3>
        """
        
        if 'system' in metrics:
            system = metrics['system']
            html += f"""
            <ul>
            <li>CPU Usage: {system.get('cpu', {}).get('percent', 'N/A')}%</li>
            <li>Memory Usage: {system.get('memory', {}).get('percent', 'N/A')}%</li>
            <li>Disk Usage: {system.get('disk', {}).get('percent', 'N/A')}%</li>
            <li>Response Time: {metrics.get('response_time_ms', 'N/A')}ms</li>
            </ul>
            """
        
        html += """
        <p>Please investigate and take appropriate action to resolve these issues.</p>
        </body>
        </html>
        """
        
        return html
    
    def monitor_resources(self, duration: int = None, interval: int = 60):
        """
        Monitor resources continuously
        
        Args:
            duration: Monitoring duration in seconds (None for infinite)
            interval: Check interval in seconds
        """
        self.logger.info(f"Starting resource monitoring (interval: {interval}s)")
        
        start_time = time.time()
        
        try:
            while True:
                # Check if duration limit reached
                if duration and (time.time() - start_time) >= duration:
                    break
                
                # Get current metrics
                result = self.get_resource_metrics()
                
                if result['status'] == 'success':
                    metrics = result['data']
                    violations = self.check_thresholds(metrics)
                    
                    if violations:
                        # Log violations
                        critical_violations = [v for v in violations if v['type'] == 'critical']
                        warning_violations = [v for v in violations if v['type'] == 'warning']
                        
                        if critical_violations:
                            self.logger.critical(f"Critical resource issues detected: {len(critical_violations)} violations")
                            for violation in critical_violations:
                                self.logger.critical(violation['message'])
                        
                        if warning_violations:
                            self.logger.warning(f"Resource warnings detected: {len(warning_violations)} violations")
                            for violation in warning_violations:
                                self.logger.warning(violation['message'])
                        
                        # Send alerts for new violations
                        new_violations = [v for v in violations if self.should_send_alert(v)]
                        
                        if new_violations:
                            if self.alert_settings.get('email_enabled', False):
                                self.send_email_alert(new_violations, metrics)
                            
                            if self.alert_settings.get('webhook_enabled', False):
                                self.send_webhook_alert(new_violations, metrics)
                    
                    else:
                        self.logger.info("All resource metrics within acceptable ranges")
                
                else:
                    self.logger.error(f"Failed to get resource metrics: {result['error']}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.logger.info("Resource monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Error during resource monitoring: {e}")


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description="Stock Management System Resource Monitor")
    parser.add_argument("--url", default="http://localhost", help="Base URL of the application")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--duration", type=int, help="Monitoring duration in seconds")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds")
    parser.add_argument("--single", action="store_true", help="Run single check instead of continuous monitoring")
    
    args = parser.parse_args()
    
    monitor = ResourceMonitor(args.url, args.config)
    
    try:
        if args.single:
            # Single resource check
            result = monitor.get_resource_metrics()
            
            if result['status'] == 'success':
                metrics = result['data']
                violations = monitor.check_thresholds(metrics)
                
                print(f"Resource Status: {metrics.get('status', 'unknown')}")
                print(f"Response Time: {metrics.get('response_time_ms', 'N/A')}ms")
                
                if violations:
                    print(f"\nThreshold Violations ({len(violations)}):")
                    for violation in violations:
                        print(f"  {violation['type'].upper()}: {violation['message']}")
                else:
                    print("\nAll resources within acceptable ranges")
            else:
                print(f"Error: {result['error']}")
                sys.exit(1)
        
        else:
            # Continuous monitoring
            monitor.monitor_resources(args.duration, args.interval)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()