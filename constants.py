# constants.py
import os
from pathlib import Path


# ==================== Secret Key for JWT ====================
SECRET_KEY = os.getenv("API_SECRET_KEY", "supersecret_default_key_123!")

# Algorithm used for JWT
ALGORITHM = os.getenv("API_ALGORITHM", "HS256")

# Token expiry time in minutes
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 10))


DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "")


# ==================== Database Configuration ====================

def get_database_url() -> str:
    """
    Get database URL from environment or create a SQLite file.
    Checks for existing database file and creates one if not found.
    """
    # Check if DATABASE_URL is set in environment
    db_url = os.getenv("AUTH_DATABASE_URL","sqlite:///../auth_db/auth_db_data.db")
    
    if db_url:
        # If it's a SQLite URL, check if the file exists or create directory
        if db_url.startswith("sqlite:///"):
            db_path_str = db_url.replace("sqlite:///", "")
            db_path = Path(db_path_str)
            
            # Create parent directory if it doesn't exist
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            if db_path.exists():
                print(f"✓ Found existing database file: {db_path}")
            else:
                print(f"✗ Database file not found. Will create new at: {db_path}")
        
        return db_url
    
    # Default: Use SQLite file in the data directory
    # Get the directory where this file is located
    base_dir = Path(__file__).resolve().parent
    
    # Create data directory if it doesn't exist
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Database file path
    db_file = data_dir / "auth_db_test.db"
    
    # Check if database file exists
    if db_file.exists():
        print(f"✓ Found existing database file: {db_file}")
    else:
        print(f"✗ Database file not found. Will create new database at: {db_file}")
    
    # Return SQLite URL
    return f"sqlite:///{db_file}"

# Database URL for the auth server
AUTH_DATABASE_URL = get_database_url()

# ==================== CORS Configuration ====================
# Specify the allowed origins to access the auth provider
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", '*').split(',')

# ==================== Optional: Database Info ====================
def get_database_info() -> dict:
    """Get information about the current database configuration"""
    info = {
        "url": AUTH_DATABASE_URL,
        "type": "sqlite" if "sqlite" in AUTH_DATABASE_URL else "postgresql",
    }
    
    # If SQLite, get file info
    if "sqlite" in AUTH_DATABASE_URL and AUTH_DATABASE_URL.startswith("sqlite:///"):
        db_path_str = AUTH_DATABASE_URL.replace("sqlite:///", "")
        db_path = Path(db_path_str)
        
        info["path"] = str(db_path)
        info["exists"] = db_path.exists()
        
        if db_path.exists():
            file_size = db_path.stat().st_size
            info["size_bytes"] = file_size
            info["size_mb"] = round(file_size / (1024 * 1024), 2)
        else:
            info["size_bytes"] = 0
            info["size_mb"] = 0
    
    return info

# ==================== Print Database Info on Import ====================
if __name__ != "__main__":
    # Only print if not running as main script
    db_info = get_database_info()
    print(f"📊 Database: {db_info.get('type', 'unknown')}")
    if "path" in db_info:
        print(f"📁 Path: {db_info['path']}")
        print(f"📦 Exists: {db_info.get('exists', False)}")
        if db_info.get('exists'):
            print(f"💾 Size: {db_info.get('size_mb', 0)} MB")