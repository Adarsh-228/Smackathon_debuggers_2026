from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Document(Base):
    __tablename__ = 'documents'
    
    document_id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    current_version_id = Column(Integer, ForeignKey('document_versions.version_id', use_alter=True))
    created_by = Column(Integer, ForeignKey('users.user_id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_edited_by = Column(Integer, ForeignKey('users.user_id'))
    last_edited_at = Column(DateTime(timezone=True))
    checked_out_by = Column(Integer, ForeignKey('users.user_id'))
    checked_out_at = Column(DateTime(timezone=True))
    lock_expires_at = Column(DateTime(timezone=True))
    
    project = relationship("Project", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document", foreign_keys="DocumentVersion.document_id")

class DocumentVersion(Base):
    __tablename__ = 'document_versions'
    
    version_id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.document_id'), nullable=False)
    parent_version_id = Column(Integer, ForeignKey('document_versions.version_id'))
    version_label = Column(String)
    major = Column(Integer, default=0)
    minor = Column(Integer, default=0)
    patch = Column(Integer, default=0)
    uploaded_by = Column(Integer, ForeignKey('users.user_id'))
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
    summary = Column(Text)
    storage_path = Column(String, nullable=False)
    checksum = Column(String)
    file_size = Column(BigInteger)
    
    document = relationship("Document", back_populates="versions", foreign_keys=[document_id])
    uploader = relationship("User")
    diffs_from = relationship("VersionDiff", foreign_keys="VersionDiff.from_version_id")
    diffs_to = relationship("VersionDiff", foreign_keys="VersionDiff.to_version_id")
    blocks = relationship("Block", back_populates="version")

class VersionDiff(Base):
    __tablename__ = 'version_diffs'
    
    diff_id = Column(Integer, primary_key=True, index=True)
    from_version_id = Column(Integer, ForeignKey('document_versions.version_id'), nullable=False)
    to_version_id = Column(Integer, ForeignKey('document_versions.version_id'), nullable=False)
    diff_path = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
