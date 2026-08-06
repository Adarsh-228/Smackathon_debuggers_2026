from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Date
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from app.core.database import Base

class Organization(Base):
    __tablename__ = 'organizations'
    
    organization_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    logo = Column(String)
    website = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # relationships
    members = relationship("OrganizationMember", back_populates="organization")
    projects = relationship("Project", back_populates="organization")

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    avatar_url = Column(String)
    bio = Column(Text)
    status = Column(String, default="active")
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # relationships
    org_memberships = relationship("OrganizationMember", back_populates="user")
    project_memberships = relationship("ProjectMember", back_populates="user")

class OrganizationMember(Base):
    __tablename__ = 'organization_members'
    
    membership_id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.organization_id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="org_memberships")

class Project(Base):
    __tablename__ = 'projects'
    
    project_id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.organization_id'), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="active")
    lead_user_id = Column(Integer, ForeignKey('users.user_id'))
    created_by = Column(Integer, ForeignKey('users.user_id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deadline = Column(Date)
    current_stage = Column(String)
    
    organization = relationship("Organization", back_populates="projects")
    members = relationship("ProjectMember", back_populates="project")
    documents = relationship("Document", back_populates="project")
    tasks = relationship("Task", back_populates="project")

class Role(Base):
    __tablename__ = 'roles'
    
    role_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    
    permissions = relationship("RolePermission", back_populates="role")
    members = relationship("ProjectMember", back_populates="role")

class RolePermission(Base):
    __tablename__ = 'role_permissions'
    
    permission_id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey('roles.role_id'), nullable=False)
    permission = Column(String, nullable=False)
    
    role = relationship("Role", back_populates="permissions")

class ProjectMember(Base):
    __tablename__ = 'project_members'
    
    member_id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.role_id'), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")
    role = relationship("Role", back_populates="members")

class Comment(Base):
    __tablename__ = 'comments'
    
    comment_id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.document_id'))
    version_id = Column(Integer, ForeignKey('document_versions.version_id'))
    block_id = Column(Integer, ForeignKey('blocks.block_id'))
    author_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    parent_comment_id = Column(Integer, ForeignKey('comments.comment_id'))
    text = Column(Text, nullable=False)
    status = Column(String, default="open")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_by = Column(Integer, ForeignKey('users.user_id'))
    resolved_at = Column(DateTime(timezone=True))
    
    author = relationship("User", foreign_keys=[author_id])
    resolver = relationship("User", foreign_keys=[resolved_by])
    replies = relationship("Comment", backref=backref("parent", remote_side=[comment_id]))

class Task(Base):
    __tablename__ = 'tasks'
    
    task_id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.project_id'), nullable=False)
    document_id = Column(Integer, ForeignKey('documents.document_id'))
    assigned_by = Column(Integer, ForeignKey('users.user_id'))
    assigned_to = Column(Integer, ForeignKey('users.user_id'))
    title = Column(String, nullable=False)
    description = Column(Text)
    priority = Column(String)
    status = Column(String, default="pending")
    due_date = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    project = relationship("Project", back_populates="tasks")
    assigner = relationship("User", foreign_keys=[assigned_by])
    assignee = relationship("User", foreign_keys=[assigned_to])
