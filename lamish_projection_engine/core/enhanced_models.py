"""Enhanced database models for advanced LPE features."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, Float,
    ForeignKey, Boolean, JSON, Index, Enum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
import uuid
import hashlib
import enum

# Import existing base
from lamish_projection_engine.core.models import Base

# Enums
class TranslationDirection(enum.Enum):
    """Direction of translation."""
    FORWARD = "forward"
    BACKWARD = "backward"


class AttributeFieldType(enum.Enum):
    """Types of attribute fields."""
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    SELECT = "select"
    TEXTAREA = "textarea"
    JSON = "json"


# Enhanced Models for Dynamic Configuration
class DynamicAttributeDefinition(Base):
    """Definition of a dynamic attribute type."""
    __tablename__ = "dynamic_attribute_definitions"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)  # persona, namespace, language_style
    description = Column(Text)
    version = Column(String(20), default="1.0")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    instances = relationship("DynamicAttributeInstance", back_populates="definition")
    fields = relationship("DynamicAttributeField", back_populates="definition")


class DynamicAttributeField(Base):
    """Field definition for dynamic attributes."""
    __tablename__ = "dynamic_attribute_fields"
    
    id = Column(Integer, primary_key=True)
    definition_id = Column(Integer, ForeignKey("dynamic_attribute_definitions.id"), nullable=False)
    name = Column(String(100), nullable=False)
    field_type = Column(Enum(AttributeFieldType), default=AttributeFieldType.TEXT)
    description = Column(Text)
    options = Column(JSONB)  # For select fields
    default_value = Column(Text)
    prompt_template = Column(Text)  # For AI-generated fields
    is_core = Column(Boolean, default=True)
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    definition = relationship("DynamicAttributeDefinition", back_populates="fields")
    values = relationship("DynamicAttributeValue", back_populates="field")
    
    # Unique constraint
    __table_args__ = (Index('idx_definition_field', 'definition_id', 'name', unique=True),)


class DynamicAttributeInstance(Base):
    """Instance of a dynamic attribute configuration."""
    __tablename__ = "dynamic_attribute_instances"
    
    id = Column(Integer, primary_key=True)
    definition_id = Column(Integer, ForeignKey("dynamic_attribute_definitions.id"), nullable=False)
    name = Column(String(100), nullable=False)  # e.g., "my_custom_persona"
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    definition = relationship("DynamicAttributeDefinition", back_populates="instances")
    values = relationship("DynamicAttributeValue", back_populates="instance")
    
    # Unique constraint
    __table_args__ = (Index('idx_definition_instance', 'definition_id', 'name', unique=True),)


class DynamicAttributeValue(Base):
    """Value of a field in an attribute instance."""
    __tablename__ = "dynamic_attribute_values"
    
    id = Column(Integer, primary_key=True)
    instance_id = Column(Integer, ForeignKey("dynamic_attribute_instances.id"), nullable=False)
    field_id = Column(Integer, ForeignKey("dynamic_attribute_fields.id"), nullable=False)
    value = Column(Text)
    generated_by = Column(String(50), default="user")  # user, ai, system
    last_modified = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    instance = relationship("DynamicAttributeInstance", back_populates="values")
    field = relationship("DynamicAttributeField", back_populates="values")
    
    # Unique constraint
    __table_args__ = (Index('idx_instance_field', 'instance_id', 'field_id', unique=True),)


# Language Round-trip Models
class LanguageTranslation(Base):
    """Record of language translations."""
    __tablename__ = "language_translations"
    
    id = Column(Integer, primary_key=True)
    source_text = Column(Text, nullable=False)
    target_text = Column(Text, nullable=False)
    source_language = Column(String(50), nullable=False)
    target_language = Column(String(50), nullable=False)
    direction = Column(Enum(TranslationDirection), nullable=False)
    confidence = Column(Float, default=1.0)
    metadata = Column(JSONB)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    round_trip_id = Column(Integer, ForeignKey("round_trip_results.id"), nullable=True)
    round_trip = relationship("RoundTripResult", back_populates="translations")


class RoundTripResult(Base):
    """Result of round-trip translation analysis."""
    __tablename__ = "round_trip_results"
    
    id = Column(Integer, primary_key=True)
    original_text = Column(Text, nullable=False)
    final_text = Column(Text, nullable=False)
    intermediate_language = Column(String(50), nullable=False)
    semantic_drift = Column(Float, default=0.0)
    linguistic_analysis = Column(JSONB)
    preserved_elements = Column(JSONB)  # Array of strings
    lost_elements = Column(JSONB)  # Array of strings
    gained_elements = Column(JSONB)  # Array of strings
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    translations = relationship("LanguageTranslation", back_populates="round_trip")
    projection_id = Column(Integer, ForeignKey("projections.id"), nullable=True)


# Maieutic Dialogue Models
class MaieuticSession(Base):
    """Maieutic dialogue session."""
    __tablename__ = "maieutic_sessions"
    
    id = Column(Integer, primary_key=True)
    initial_narrative = Column(Text, nullable=False)
    goal = Column(String(100), default="understand")
    final_understanding = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    turns = relationship("MaieuticTurn", back_populates="session", order_by="MaieuticTurn.turn_number")
    extracted_elements = Column(JSONB)


class MaieuticTurn(Base):
    """Individual turn in maieutic dialogue."""
    __tablename__ = "maieutic_turns"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("maieutic_sessions.id"), nullable=False)
    turn_number = Column(Integer, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    insights = Column(JSONB)  # Array of strings
    depth_level = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("MaieuticSession", back_populates="turns")
    
    # Unique constraint
    __table_args__ = (Index('idx_session_turn', 'session_id', 'turn_number', unique=True),)


# Text Version Control
class TextVersion(Base):
    """Version control for text transformations."""
    __tablename__ = "text_versions"
    
    id = Column(Integer, primary_key=True)
    original_text = Column(Text, nullable=False)
    transformed_text = Column(Text, nullable=False)
    transformation_type = Column(String(50), nullable=False)  # projection, translation, etc.
    version_number = Column(Integer, default=1)
    parent_version_id = Column(Integer, ForeignKey("text_versions.id"), nullable=True)
    transformation_metadata = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    parent = relationship("TextVersion", remote_side=[id], backref="children")
    embedding = relationship("TextVersionEmbedding", back_populates="text_version", uselist=False)


class TextVersionEmbedding(Base):
    """Embeddings for text versions."""
    __tablename__ = "text_version_embeddings"
    
    id = Column(Integer, primary_key=True)
    text_version_id = Column(Integer, ForeignKey("text_versions.id"), nullable=False)
    embedding = Column(Vector(768))
    model_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    text_version = relationship("TextVersion", back_populates="embedding")


# Enhanced projection tracking
class ProjectionSession(Base):
    """Session tracking for projection creation."""
    __tablename__ = "projection_sessions"
    
    id = Column(Integer, primary_key=True)
    session_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    user_id = Column(String(100))  # Optional user identification
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    session_metadata = Column(JSONB)
    
    # Relationships
    projections = relationship("EnhancedProjection", back_populates="session")


class EnhancedProjection(Base):
    """Enhanced projection with full traceability."""
    __tablename__ = "enhanced_projections"
    
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    session_id = Column(Integer, ForeignKey("projection_sessions.id"), nullable=True)
    
    # Dynamic attribute instances used
    persona_instance_id = Column(Integer, ForeignKey("dynamic_attribute_instances.id"), nullable=True)
    namespace_instance_id = Column(Integer, ForeignKey("dynamic_attribute_instances.id"), nullable=True)
    style_instance_id = Column(Integer, ForeignKey("dynamic_attribute_instances.id"), nullable=True)
    
    # Content
    source_text = Column(Text, nullable=False)
    final_projection = Column(Text, nullable=False)
    reflection = Column(Text)
    
    # Metadata
    system_prompt_used = Column(Text)  # The arbitrated prompt
    transformation_steps = Column(JSONB)  # Detailed step records
    performance_metrics = Column(JSONB)  # Timing, token usage, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ProjectionSession", back_populates="projections")
    persona_instance = relationship("DynamicAttributeInstance", foreign_keys=[persona_instance_id])
    namespace_instance = relationship("DynamicAttributeInstance", foreign_keys=[namespace_instance_id])
    style_instance = relationship("DynamicAttributeInstance", foreign_keys=[style_instance_id])
    
    # Link to maieutic session if created from dialogue
    maieutic_session_id = Column(Integer, ForeignKey("maieutic_sessions.id"), nullable=True)
    maieutic_session = relationship("MaieuticSession")
    
    # Round-trip analysis
    round_trip_results = relationship("RoundTripResult")
    
    # Embeddings
    embedding = relationship("EnhancedProjectionEmbedding", back_populates="projection", uselist=False)


class EnhancedProjectionEmbedding(Base):
    """Embeddings for enhanced projections."""
    __tablename__ = "enhanced_projection_embeddings"
    
    id = Column(Integer, primary_key=True)
    projection_id = Column(Integer, ForeignKey("enhanced_projections.id"), nullable=False)
    embedding = Column(Vector(768))
    model_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    projection = relationship("EnhancedProjection", back_populates="embedding")


# Arbitrator and Prompt Management
class PromptContribution(Base):
    """Individual contributions to system prompts."""
    __tablename__ = "prompt_contributions"
    
    id = Column(Integer, primary_key=True)
    source = Column(String(100), nullable=False)  # persona, namespace, style, etc.
    content = Column(Text, nullable=False)
    weight = Column(Float, default=1.0)
    context_dependent = Column(Boolean, default=False)
    conditions = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Link to specific instances
    attribute_instance_id = Column(Integer, ForeignKey("dynamic_attribute_instances.id"), nullable=True)
    attribute_instance = relationship("DynamicAttributeInstance")


class ArbitratorDecision(Base):
    """Record of arbitrator decisions about prompt composition."""
    __tablename__ = "arbitrator_decisions"
    
    id = Column(Integer, primary_key=True)
    context = Column(JSONB)  # The context that influenced the decision
    contributions_considered = Column(JSONB)  # List of contribution IDs
    final_prompt = Column(Text, nullable=False)
    reasoning = Column(Text)  # AI's reasoning for the decision
    effectiveness_score = Column(Float)  # Post-hoc evaluation
    created_at = Column(DateTime, default=datetime.utcnow)


# Utility functions for enhanced models
def initialize_enhanced_schema(session: Session):
    """Initialize the enhanced database schema."""
    # Create base attribute definitions
    definitions = [
        DynamicAttributeDefinition(
            name="persona",
            description="Narrative perspective and voice configuration"
        ),
        DynamicAttributeDefinition(
            name="namespace", 
            description="Fictional universe for allegorical projection"
        ),
        DynamicAttributeDefinition(
            name="language_style",
            description="Language style and rhetorical approach"
        )
    ]
    
    for definition in definitions:
        existing = session.query(DynamicAttributeDefinition).filter_by(name=definition.name).first()
        if not existing:
            session.add(definition)
    
    session.commit()


def create_enhanced_tables(engine):
    """Create all enhanced tables."""
    Base.metadata.create_all(bind=engine)


def migrate_to_enhanced_schema(session: Session):
    """Migrate existing data to enhanced schema."""
    # This would migrate data from the original models to the enhanced ones
    # Implementation depends on the existing data structure
    pass