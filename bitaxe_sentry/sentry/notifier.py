import requests
import logging
from .config import DISCORD_WEBHOOK
import socket
import datetime

logger = logging.getLogger(__name__)

def send_startup_notification(service="main"):
    """
    Send a notification when the system starts up to verify webhook configuration.
    
    Args:
        service: The service that's starting ('main' or 'web')
    """
    if not DISCORD_WEBHOOK:
        logger.warning("Discord webhook URL not configured, skipping startup notification")
        return False
        
    hostname = socket.gethostname()
    try:
        ip_address = socket.gethostbyname(hostname)
    except:
        ip_address = "unknown"
    
    service_name = "Web UI" if service == "web" else "Monitor"
    
    content = (
      f"🚀 **Bitaxe Sentry {service_name}** started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
      f"✅ Discord notifications are working correctly!"
    )
    
    try:
        response = requests.post(
            DISCORD_WEBHOOK, 
            json={"content": content},
            timeout=10
        )
        response.raise_for_status()
        logger.info(f"Startup notification for {service_name} sent successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to send startup notification: {e}")
        return False


def send_alert(miner, reading, alert_type="temperature"):
    """
    Send temperature or voltage alert via Discord webhook.
    
    Args:
        miner: The miner instance
        reading: Reading instance with temperature/voltage data
        alert_type: Type of alert ("temperature" or "voltage")
    """
    if not DISCORD_WEBHOOK:
        logger.warning("Discord webhook URL not configured, skipping alert")
        return
    
    if alert_type == "temperature":
        emoji = "🔥"
        message = f"⚠️ **{miner.name}** temperature out of range: {reading.temperature:.1f}°C"
    elif alert_type == "voltage":
        emoji = "⚡"
        message = f"⚠️ **{miner.name}** voltage out of range: {reading.voltage:.2f}V"
    else:
        logger.error(f"Unknown alert type: {alert_type}")
        return
        
    content = (
      f"{message}\n"
      f"Temperature: {reading.temperature:.1f}°C | Voltage: {reading.voltage:.2f}V | Hash Rate: {reading.hash_rate:.2f} MH/s"
    )
    
    try:
        response = requests.post(
            DISCORD_WEBHOOK, 
            json={"content": content},
            timeout=10
        )
        response.raise_for_status()
        logger.info(f"{alert_type.capitalize()} alert sent for {miner.name}")
    except Exception as e:
        logger.error(f"Failed to send {alert_type} alert: {e}")


def send_voltage_alert(miner, reading):
    """
    Send voltage alert via Discord webhook.
    
    Args:
        miner: The miner instance
        reading: Reading instance with voltage data
    """
    send_alert(miner, reading, alert_type="voltage")


def send_temperature_alert(miner, reading):
    """
    Send temperature alert via Discord webhook.
    
    Args:
        miner: The miner instance
        reading: Reading instance with temperature data
    """
    send_alert(miner, reading, alert_type="temperature")


def send_diff_alert(miner, reading):
    """
    Send new best difficulty notification via Discord webhook.
    
    Args:
        miner: The miner instance
        reading: Reading instance with best_diff data
    """
    if not DISCORD_WEBHOOK:
        logger.warning("Discord webhook URL not configured, skipping alert")
        return
        
    content = (
      f"🎉 **{miner.name}** new best diff! {reading.best_diff}\n"
      f"Temperature: {reading.temperature:.1f}°C | Voltage: {reading.voltage:.2f}V | Hash Rate: {reading.hash_rate:.2f} MH/s"
    )
    
    try:
        response = requests.post(
            DISCORD_WEBHOOK, 
            json={"content": content},
            timeout=10
        )
        response.raise_for_status()
        logger.info(f"New best diff alert sent for {miner.name}: {reading.best_diff}")
    except Exception as e:
        logger.error(f"Failed to send best diff alert: {e}") 