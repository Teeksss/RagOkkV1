#!/usr/bin/env python3
"""
Post-deployment monitoring script.
"""
import os
import sys
import time
import logging
import requests
import json
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger("deployment-monitor")

# Configuration
API_URL = os.environ.get("API_URL", "https://api.rag-system.example.com")
HEALTH_ENDPOINT = "/health"
METRICS_ENDPOINT = "/metrics"
ALERT_THRESHOLD = 0.95  # 95% resource utilization

# Slack webhook for alerting
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK")


def check_api_health():
    """Check if the API is healthy."""
    try:
        response = requests.get(f"{API_URL}{HEALTH_ENDPOINT}", timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            logger.info(f"API health check: {health_data.get('status', 'Unknown')}")
            return True, health_data
        else:
            logger.error(f"API health check failed with status code: {response.status_code}")
            return False, {"status": "error", "error": f"Status code: {response.status_code}"}
    
    except requests.RequestException as e:
        logger.error(f"API health check failed with error: {str(e)}")
        return False, {"status": "error", "error": str(e)}


def get_system_metrics():
    """Get system metrics from the API."""
    try:
        response = requests.get(f"{API_URL}{METRICS_ENDPOINT}", timeout=10)
        
        if response.status_code == 200:
            metrics_data = response.json()
            logger.info(f"Retrieved system metrics: {len(metrics_data)} metrics")
            return True, metrics_data
        else:
            logger.error(f"Failed to get metrics with status code: {response.status_code}")
            return False, {"status": "error", "error": f"Status code: {response.status_code}"}
    
    except requests.RequestException as e:
        logger.error(f"Failed to get metrics with error: {str(e)}")
        return False, {"status": "error", "error": str(e)}


def check_resource_utilization(metrics):
    """Check resource utilization and alert if above threshold."""
    alerts = []
    
    # Check CPU utilization
    if "cpu_utilization" in metrics and metrics["cpu_utilization"] > ALERT_THRESHOLD:
        alerts.append(f"High CPU utilization: {metrics['cpu_utilization']:.2%}")
    
    # Check memory utilization
    if "memory_utilization" in metrics and metrics["memory_utilization"] > ALERT_THRESHOLD:
        alerts.append(f"High memory utilization: {metrics['memory_utilization']:.2%}")
    
    # Check disk utilization
    if "disk_utilization" in metrics and metrics["disk_utilization"] > ALERT_THRESHOLD:
        alerts.append(f"High disk utilization: {metrics['disk_utilization']:.2%}")
    
    return alerts


def check_error_rates(metrics):
    """Check error rates and alert if too high."""
    alerts = []
    
    # Check error rate
    if "error_rate" in metrics and metrics["error_rate"] > 0.05:  # 5% error rate
        alerts.append(f"High error rate: {metrics['error_rate']:.2%}")
    
    # Check 5xx errors
    if "status_5xx_count" in metrics and metrics["status_5xx_count"] > 10:
        alerts.append(f"High number of 5xx errors: {metrics['status_5xx_count']}")
    
    return alerts


def send_alert(message):
    """Send alert to Slack."""
    if not SLACK_WEBHOOK:
        logger.warning("No Slack webhook configured, skipping alert")
        return
    
    try:
        payload = {
            "text": f"🚨 *RAG System Alert*: {message}",
            "username": "Deployment Monitor",
            "icon_emoji": ":robot_face:"
        }
        
        response = requests.post(SLACK_WEBHOOK, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Alert sent to Slack: {message}")
        else:
            logger.error(f"Failed to send alert to Slack: {response.status_code}")
    
    except requests.RequestException as e:
        logger.error(f"Failed to send alert to Slack: {str(e)}")


def run_checks():
    """Run all monitoring checks."""
    # Check API health
    health_status, health_data = check_api_health()
    
    if not health_status:
        send_alert(f"API is unhealthy: {health_data.get('error', 'Unknown error')}")
        return False
    
    # Get system metrics
    metrics_status, metrics_data = get_system_metrics()
    
    if not metrics_status:
        send_alert(f"Failed to get system metrics: {metrics_data.get('error', 'Unknown error')}")
        return False
    
    # Check resource utilization
    utilization_alerts = check_resource_utilization(metrics_data)
    
    # Check error rates
    error_alerts = check_error_rates(metrics_data)
    
    # Send alerts
    all_alerts = utilization_alerts + error_alerts
    
    if all_alerts:
        send_alert("\n".join(all_alerts))
        return False
    
    logger.info("All checks passed")
    return True


def main():
    """Main function."""
    logger.info(f"Starting post-deployment monitoring for {API_URL}")
    
    # Run checks
    success = run_checks()
    
    # Exit with appropriate code
    if success:
        logger.info("Monitoring checks completed successfully")
        sys.exit(0)
    else:
        logger.error("Monitoring checks failed")
        sys.exit(1)


if __name__ == "__main__":
    main()