from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.error_codes import ErrorCode
from core.error_messages import get_error_message



    


class APIException(Exception):
    """Base exception for all API errors"""
    
    def __init__(
        self,
        status_code: int,
        error_code: ErrorCode,
        message: str = None,
        details: dict = None,
        headers: dict = None
    ):
        self.status_code = status_code
        self.error_code = error_code
        # Use provided message or get from error code mapping
        self.message = message or get_error_message(error_code)
        self.details = details or {}
        self.headers = headers or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary for JSON response"""
        return {
            "success": False,
            "status_code": self.status_code,
            "code": self.error_code.value if hasattr(self.error_code, 'value') else str(self.error_code),
            "message": self.message,
            "details": self.details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    

    