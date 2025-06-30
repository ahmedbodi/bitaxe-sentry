from fastapi import FastAPI, Request, Depends, Query
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pathlib
import logging
from sqlmodel import Session, select, func
import datetime
from typing import Optional
from .db import get_session, Miner, Reading
from .config import ENDPOINTS
from .notifier import send_startup_notification

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Bitaxe Sentry")

# Set up templates directory
templates_path = pathlib.Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

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
def dashboard(request: Request, session: Session = Depends(get_session)):
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
        {
            "request": request, 
            "readings": latest_readings,
            "current_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_updated": last_updated
        }
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
        {
            "request": request,
            "miners": miners,
            "selected_miner": selected_miner,
            "readings_by_miner": readings_by_miner
        }
    ) 