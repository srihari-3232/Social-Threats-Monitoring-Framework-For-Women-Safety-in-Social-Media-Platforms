from abc import ABC, abstractmethod
from datetime import datetime
from utils.logger import setup_logger

class BaseService(ABC):
    def __init__(self, service_name):
        self.service_name = service_name
        self.logger = setup_logger(f"{service_name}_service")

    @abstractmethod
    def fetch_data(self, **kwargs):
        """Fetch fresh data from the service"""
        pass

    def format_response(self, data, success=True, message="", error=None):
        """Standard response format"""
        return {
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "success": success,
            "message": message,
            "error": str(error) if error else None,
            "data": data,
            "total_items": len(data) if isinstance(data, list) else 0
        }
