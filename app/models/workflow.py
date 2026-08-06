from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class ReviewQueue(Base):
    __tablename__ = 'review_queue'
    
    queue_id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=False)
    reference_type = Column(String)
    reference_id = Column(Integer)
    confidence = Column(Float)
    note = Column(Text)
    resolved_by = Column(Integer, ForeignKey('users.user_id'))
    resolved_at = Column(DateTime(timezone=True))
    resolved_note = Column(Text)
    
    resolver = relationship("User", foreign_keys=[resolved_by])

class Activity(Base):
    __tablename__ = 'activities'
    
    activity_id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    action = Column(String, nullable=False)
    entity_type = Column(String)
    entity_id = Column(Integer)
    metadata_json = Column(Text)  # using text for JSON payload
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")

class Notification(Base):
    __tablename__ = 'notifications'
    
    notification_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text)
    link = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")

class WorkflowHistory(Base):
    __tablename__ = 'workflow_history'
    
    history_id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=False)
    from_stage = Column(String)
    to_stage = Column(String)
    changed_by = Column(Integer, ForeignKey('users.user_id'))
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    remarks = Column(Text)
    
    changer = relationship("User", foreign_keys=[changed_by])
