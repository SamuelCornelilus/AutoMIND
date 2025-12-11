# app/models_history.py
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text

from .db import Base


class QueryHistory(Base):
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    query = Column(Text, nullable=False)
    results = Column(Text, nullable=False)  # JSON disimpan sebagai string
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
