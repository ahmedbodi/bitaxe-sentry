from sqlmodel import SQLModel, Field, create_engine, Session, select
import datetime
import pathlib
import os

# Check for environment variable to override database path
DB_ENV_PATH = os.environ.get("DB_PATH")

# Define database path relative to this file
if DB_ENV_PATH:
    # Use environment variable if provided
    DB_PATH = pathlib.Path(DB_ENV_PATH)
elif os.path.exists('/app/data'):
    # Default Docker path
    DB_PATH = pathlib.Path('/app/data') / "bitaxe_sentry.db"
else:
    # Check if there's a data directory at the project root
    project_root = pathlib.Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    if data_dir.exists():
        DB_PATH = data_dir / "bitaxe_sentry.db"
    else:
        # Fallback to the package directory
        DB_PATH = pathlib.Path(__file__).parent.parent / "bitaxe_sentry.db"


class Miner(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    endpoint: str
    added_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)


class Reading(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    miner_id: int = Field(foreign_key="miner.id")
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    hash_rate: float
    temperature: float
    best_diff: str
    voltage: float = Field(default=0.0)  # Voltage in millivolts
    # Additional fields can be added here as needed


# Create SQLite engine
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


def init_db():
    """Initialize the database by creating all tables."""
    # Ensure the parent directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get a database session."""
    with Session(engine) as session:
        yield session 