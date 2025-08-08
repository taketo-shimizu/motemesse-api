from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    auth0_id = Column(String, unique=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    age = Column(Integer, nullable=True)
    job = Column(String, nullable=True)
    hobby = Column(String, nullable=True)
    residence = Column(String, nullable=True)
    work_place = Column(String, nullable=True)
    blood_type = Column(String, nullable=True)
    education = Column(String, nullable=True)
    work_type = Column(String, nullable=True)
    holiday = Column(String, nullable=True)
    marriage_history = Column(String, nullable=True)
    has_children = Column(String, nullable=True)
    smoking = Column(String, nullable=True)
    drinking = Column(String, nullable=True)
    living_with = Column(String, nullable=True)
    marriage_intention = Column(String, nullable=True)
    self_introduction = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    targets = relationship("Target", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")


class Target(Base):
    __tablename__ = "targets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    age = Column(Integer, nullable=True)
    job = Column(String, nullable=True)
    hobby = Column(String, nullable=True)
    residence = Column(String, nullable=True)
    work_place = Column(String, nullable=True)
    blood_type = Column(String, nullable=True)
    education = Column(String, nullable=True)
    work_type = Column(String, nullable=True)
    holiday = Column(String, nullable=True)
    marriage_history = Column(String, nullable=True)
    has_children = Column(String, nullable=True)
    smoking = Column(String, nullable=True)
    drinking = Column(String, nullable=True)
    living_with = Column(String, nullable=True)
    marriage_intention = Column(String, nullable=True)
    self_introduction = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="targets")
    conversations = relationship("Conversation", back_populates="target")


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    target_id = Column(Integer, ForeignKey("targets.id"))
    female_message = Column(Text, nullable=False)
    male_reply = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="conversations")
    target = relationship("Target", back_populates="conversations")