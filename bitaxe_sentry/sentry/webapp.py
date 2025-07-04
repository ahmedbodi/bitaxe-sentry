from fastapi import FastAPI, Request, Depends, Query, HTTPException, Response, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
import pathlib
import logging
from sqlmodel import Session, select, func, delete
import datetime
import os
import signal
import subprocess
from typing import Optional, Dict, Any, List
import json
from pydantic import BaseModel
from .db import get_session, Miner, Reading
from .config import ENDPOINTS, reload_config
from .notifier import send_startup_notification, send_test_notification
from .version import __version__
from .settings_manager import load_settings, save_settings
from .poller import poll_once

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Bitaxe Sentry")

# Set up templates directory
templates_path = pathlib.Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

# Helper function to add version to template context
def get_template_context(request: Request, context: Dict[str, Any]) -> Dict[str, Any]:
    context["request"] = request
    context["version"] = __version__
    return context

# Set up static files directory
static_path = pathlib.Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)  # Create directory if it doesn't exist
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Favicon routes
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    favicon_path = static_path / "favicon-32x32.png"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    return FileResponse(static_path / "logo.png")

@app.get("/apple-touch-icon.png", include_in_schema=False)
@app.get("/apple-touch-icon-precomposed.png", include_in_schema=False)
@app.get("/apple-touch-icon-120x120.png", include_in_schema=False)
@app.get("/apple-touch-icon-120x120-precomposed.png", include_in_schema=False)
async def apple_touch_icon():
    icon_path = static_path / "favicon-192x192.png"
    if icon_path.exists():
        return FileResponse(icon_path)
    return FileResponse(static_path / "logo.png")

# Stats for dashboard
@app.get("/")
def dashboard(request: Request, success: Optional[str] = None, error: Optional[str] = None, session: Session = Depends(get_session)):
    # Get the latest reading for each miner
    latest_readings = []
    miners = session.exec(select(Miner)).all()
    
    # Track the most recent reading timestamp
    most_recent_timestamp = None
    
    for miner in miners:
        latest = session.exec(
            select(Reading)
            .where(Reading.miner_id == miner.id)
            .order_by(Reading.timestamp.desc())
            .limit(1)
        ).first()
        
        if latest:
            # Ensure voltage has a default value if it's None
            if latest.voltage is None:
                latest.voltage = 0.0
                
            latest_readings.append({
                "miner": miner,
                "reading": latest,
                "timestamp_ago": (datetime.datetime.utcnow() - latest.timestamp).total_seconds() // 60
            })
            
            # Update most recent timestamp if this reading is newer
            if most_recent_timestamp is None or latest.timestamp > most_recent_timestamp:
                most_recent_timestamp = latest.timestamp
    
    # Use the most recent reading timestamp if available, otherwise use current time
    last_updated = most_recent_timestamp.strftime("%Y-%m-%d %H:%M:%S") if most_recent_timestamp else "Never"
    
    return templates.TemplateResponse(
        "dashboard.html", 
        get_template_context(request, {
            "readings": latest_readings,
            "current_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_updated": last_updated,
            "success_message": success,
            "error_message": error
        })
    )

@app.get("/history")
def history(
    request: Request, 
    miner_id: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    # Get list of miners for dropdown
    miners = session.exec(select(Miner)).all()
    
    # Parse miner_id to integer if it's not None or empty
    selected_miner = None
    if miner_id and miner_id.strip():
        try:
            selected_miner = int(miner_id)
        except ValueError:
            logger.warning(f"Invalid miner_id parameter: {miner_id}")
            selected_miner = None
    
    # Get historical data
    query = select(Reading)
    if selected_miner:
        query = query.where(Reading.miner_id == selected_miner)
    
    # Limit to last 24 hours of data to keep chart readable
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
    query = query.where(Reading.timestamp > cutoff)
    
    # Order by timestamp
    query = query.order_by(Reading.timestamp)
    readings = session.exec(query).all()
    
    # Group readings by miner
    readings_by_miner = {}
    for reading in readings:
        miner = next((m for m in miners if m.id == reading.miner_id), None)
        if miner:
            if miner.name not in readings_by_miner:
                readings_by_miner[miner.name] = []
            
            # Ensure voltage has a default value if it's None
            voltage = reading.voltage
            if voltage is None:
                voltage = 0.0
                
            readings_by_miner[miner.name].append({
                "timestamp": reading.timestamp.strftime("%H:%M:%S"),
                "hash_rate": reading.hash_rate,
                "temperature": reading.temperature,
                "best_diff": reading.best_diff,
                "voltage": voltage
            })
    
    return templates.TemplateResponse(
        "history.html", 
        get_template_context(request, {
            "miners": miners,
            "selected_miner": selected_miner,
            "readings_by_miner": readings_by_miner
        })
    )

@app.delete("/api/miners/{miner_id}")
def delete_miner(
    miner_id: int,
    session: Session = Depends(get_session)
):
    """
    Delete a miner and all its associated readings
    """
    # First verify miner exists
    miner = session.get(Miner, miner_id)
    if not miner:
        raise HTTPException(status_code=404, detail="Miner not found")
    
    # Delete all readings for this miner
    session.exec(delete(Reading).where(Reading.miner_id == miner_id))
    
    # Delete the miner itself
    session.delete(miner)
    session.commit()
    
    logger.info(f"Deleted miner ID {miner_id} ({miner.name}) and all associated readings")
    
    return {"success": True}

@app.get("/settings")
def settings_page(request: Request, success: Optional[str] = None, error: Optional[str] = None):
    """Settings page to configure the application"""
    current_settings = load_settings()
    
    # Convert endpoints list to string for the form
    if isinstance(current_settings["BITAXE_ENDPOINTS"], list):
        current_settings["BITAXE_ENDPOINTS"] = ",".join(current_settings["BITAXE_ENDPOINTS"])
    
    # Context for the template
    context = {
        "settings": current_settings,
        "success_message": success,
        "error_message": error
    }
    
    return templates.TemplateResponse("settings.html", get_template_context(request, context))

def notify_sentry_service():
    """Send SIGHUP signal to the sentry service to reload configuration"""
    try:
        data_dir = pathlib.Path(os.getenv("DB_DATA_DIR", "/app/data"))
        pid_file = data_dir / "sentry.pid"
        
        if pid_file.exists():
            pid = int(pid_file.read_text().strip())
            logger.info(f"Sending SIGHUP to sentry service (PID: {pid})")
            os.kill(pid, signal.SIGHUP)
            return True
        else:
            logger.warning("Sentry PID file not found, cannot send SIGHUP")
            return False
    except Exception as e:
        logger.exception(f"Error sending SIGHUP to sentry service: {e}")
        return False


@app.post("/settings")
async def save_settings_handler(request: Request):
    """Handle settings form submission"""
    form_data = await request.form()
    settings_dict = dict(form_data)
    
    # Log the settings being saved
    logger.info(f"Saving settings: {settings_dict}")
    
    # Check if endpoints have changed
    current_settings = load_settings()
    endpoints_changed = False
    
    if isinstance(current_settings["BITAXE_ENDPOINTS"], list):
        current_endpoints = ",".join(current_settings["BITAXE_ENDPOINTS"])
    else:
        current_endpoints = current_settings["BITAXE_ENDPOINTS"]
    
    if current_endpoints != settings_dict.get("BITAXE_ENDPOINTS", ""):
        endpoints_changed = True
        logger.info("Endpoints have changed, will trigger immediate poll")
    
    # Check if voltage threshold changed
    volt_min_changed = False
    try:
        current_volt_min = float(current_settings["VOLT_MIN"])
        new_volt_min = float(settings_dict.get("VOLT_MIN", current_volt_min))
        if current_volt_min != new_volt_min:
            volt_min_changed = True
            logger.info(f"Voltage threshold changed from {current_volt_min}V to {new_volt_min}V")
    except (ValueError, TypeError):
        pass
    
    # Save settings
    success = save_settings(settings_dict)
    
    if success:
        try:
            # Reload config in the current process
            reload_config()
            
            # Notify the sentry service to reload its configuration
            notify_sentry_service()
            
            # Only poll immediately if endpoints have changed
            poll_result = 0
            if endpoints_changed:
                poll_result = poll_once()
                logger.info(f"Immediate poll completed, polled {poll_result} devices")
            
            # Provide appropriate feedback
            if endpoints_changed:
                if poll_result == 0:
                    return RedirectResponse(url="/?error=No+miners+configured.+Please+check+your+settings.", status_code=303)
                else:
                    return RedirectResponse(url="/?success=Settings+saved+and+miners+polled+successfully.", status_code=303)
            else:
                return RedirectResponse(url="/?success=Settings+saved+successfully.", status_code=303)
        except Exception as e:
            logger.exception("Error reloading configuration")
            return RedirectResponse(url="/settings?error=Settings+saved+but+polling+failed", status_code=303)
    else:
        return RedirectResponse(url="/settings?error=Failed+to+save+settings", status_code=303)

class WebhookTestRequest(BaseModel):
    webhook_url: str

@app.post("/api/test-webhook")
def test_webhook(request: WebhookTestRequest):
    """Test the Discord webhook"""
    try:
        success = send_test_notification(request.webhook_url)
        if success:
            return {"success": True}
        else:
            return {"success": False, "error": "Failed to send notification"}
    except Exception as e:
        logger.exception("Error testing webhook")
        return {"success": False, "error": str(e)}

@app.post("/api/poll-now")
def poll_now():
    """Trigger an immediate poll of all devices"""
    try:
        # Run the polling function
        success_count = poll_once()
        return {"success": True, "polled_count": success_count}
    except Exception as e:
        logger.exception("Error triggering poll")
        return {"success": False, "error": str(e)} 