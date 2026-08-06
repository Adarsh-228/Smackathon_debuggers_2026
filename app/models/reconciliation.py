from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Block(Base):
    __tablename__ = 'blocks'
    
    block_id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey('document_versions.version_id'), nullable=False)
    order_index = Column(Integer, nullable=False)
    kind = Column(String)
    raw_text = Column(Text, nullable=False)
    normalized_text = Column(Text)
    content_hash = Column(String, index=True)
    section_path = Column(String)
    source_reference = Column(String)
    
    version = relationship("DocumentVersion", back_populates="blocks")

class Correction(Base):
    __tablename__ = 'corrections'
    
    correction_id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=False)
    title = Column(String)
    description = Column(Text)
    before_text = Column(Text)
    after_text = Column(Text)
    location_hint = Column(String)
    created_by = Column(Integer, ForeignKey('users.user_id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    creator = relationship("User")
    states = relationship("CorrectionState", back_populates="correction")

class CorrectionState(Base):
    __tablename__ = 'correction_states'
    
    state_id = Column(Integer, primary_key=True, index=True)
    correction_id = Column(Integer, ForeignKey('corrections.correction_id'), nullable=False)
    version_id = Column(Integer, ForeignKey('document_versions.version_id'), nullable=False)
    status = Column(String)
    match_score = Column(Float)
    matched_block_id = Column(Integer, ForeignKey('blocks.block_id'))
    evidence = Column(Text)
    evaluated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    correction = relationship("Correction", back_populates="states")

class ChangeEvent(Base):
    __tablename__ = 'change_events'
    
    event_id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=False)
    from_version_id = Column(Integer, ForeignKey('document_versions.version_id'))
    to_version_id = Column(Integer, ForeignKey('document_versions.version_id'))
    change_type = Column(String)
    category = Column(String)
    from_block_id = Column(Integer, ForeignKey('blocks.block_id'))
    to_block_id = Column(Integer, ForeignKey('blocks.block_id'))
    similarity = Column(Float)
    confidence = Column(Float)
    evidence = Column(Text)

class ReconciliationReport(Base):
    __tablename__ = 'reconciliation_reports'
    
    report_id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=False)
    version_id = Column(Integer, ForeignKey('document_versions.version_id'), nullable=False)
    generated_by = Column(Integer, ForeignKey('users.user_id'))
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    summary = Column(Text)
    overall_confidence = Column(Float)
    pdf_file_id = Column(Integer, ForeignKey('report_files.file_id', use_alter=True))
    json_file_id = Column(Integer, ForeignKey('report_files.file_id', use_alter=True))
    
    files = relationship("ReportFile", back_populates="report", foreign_keys="ReportFile.report_id")

class ReportFile(Base):
    __tablename__ = 'report_files'
    
    file_id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey('reconciliation_reports.report_id'), nullable=False)
    file_type = Column(String)
    storage_path = Column(String, nullable=False)
    checksum = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    report = relationship("ReconciliationReport", back_populates="files", foreign_keys=[report_id])

class Arbitration(Base):
    __tablename__ = 'arbitrations'
    
    arbitration_id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=False)
    candidate_a_version = Column(Integer, ForeignKey('document_versions.version_id'))
    candidate_b_version = Column(Integer, ForeignKey('document_versions.version_id'))
    preferred_version = Column(Integer, ForeignKey('document_versions.version_id'))
    reason = Column(Text)
    resolved_a = Column(Boolean)
    resolved_b = Column(Boolean)
    total_tracked = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
