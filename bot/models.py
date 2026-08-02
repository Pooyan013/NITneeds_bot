from sqlalchemy import JSON, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from bot.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    full_name = Column(String)
    usage_count = Column(Integer, default=0)

    request_limit = relationship("RequestLimit", back_populates="user", uselist=False)


class RequestLimit(Base):
    __tablename__ = "request_limits"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), unique=True, nullable=False)
    timestamps = Column(JSON, default=list)

    user = relationship("User", back_populates="request_limit")
