from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# class API_Resolution:
#     status: int
#     error_code: int
#     message : str
# # app = FastAPI()

class APIException(Exception):
    def __init__(self, code: str,  status: int = 400,message: str="", details: dict = None):
        self.code = code
        self.message = message or ""
        self.status = status
        self.details = details or {}

    def to_dict(self):
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "status": self.status,
                "details": self.details
            }
        }