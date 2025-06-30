import datetime
import logging
from sqlmodel import Session, delete
from .config import RETENTION_DAYS
from .db import engine, Reading

logger = logging.getLogger(__name__)

def clean_old():
    """Delete readings older than the retention period."""
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=RETENTION_DAYS)
    
    with Session(engine) as session:
        # Count records to be deleted
        stmt = delete(Reading).where(Reading.timestamp < cutoff)
        result = session.exec(stmt)
        deleted_count = result.rowcount
        
        # Commit the transaction
        session.commit()
        
        logger.info(f"Cleaned {deleted_count} readings older than {RETENTION_DAYS} days")
        
    return deleted_count 