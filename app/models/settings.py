from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, Float, JSON
from sqlalchemy.sql import func

from ..core.database import Base


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False, index=True)  # store, security, email, notifications
    key = Column(String, nullable=False, index=True)
    value = Column(Text, nullable=True)  # JSON string for complex values
    data_type = Column(String, nullable=False, default="string")  # string, integer, float, boolean, json
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_typed_value(self):
        """Convert the stored value to the appropriate Python type"""
        if self.value is None:
            return None
        
        if self.data_type == "boolean":
            return self.value.lower() == 'true'
        elif self.data_type == "integer":
            return int(self.value)
        elif self.data_type == "float":
            return float(self.value)
        elif self.data_type == "json":
            import json
            return json.loads(self.value)
        else:  # string
            return self.value

    def set_typed_value(self, value):
        """Set the value with appropriate type conversion"""
        if value is None:
            self.value = None
            return
        
        if isinstance(value, bool):
            self.data_type = "boolean"
            self.value = str(value).lower()
        elif isinstance(value, int):
            self.data_type = "integer"
            self.value = str(value)
        elif isinstance(value, float):
            self.data_type = "float"
            self.value = str(value)
        elif isinstance(value, (dict, list)):
            self.data_type = "json"
            import json
            self.value = json.dumps(value)
        else:
            self.data_type = "string"
            self.value = str(value) 