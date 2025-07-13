"""Database models for Lamish Projection Engine."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, Float,
    ForeignKey, Boolean, JSON, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
import uuid
import hashlib

# Create base class for models
Base = declarative_base()


# Models
class Persona(Base):
    """Persona identity for projections."""
    __tablename__ = "personas"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    system_prompt = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    agent_configurations = relationship("AgentConfiguration", back_populates="persona")


class Namespace(Base):
    """Fictional universe for allegorical projection."""
    __tablename__ = "namespaces"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    context_prompt = Column(Text, nullable=False)
    version = Column(Integer, default=1)
    parent_namespace_id = Column(Integer, ForeignKey("namespaces.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    parent = relationship("Namespace", remote_side=[id], backref="derivatives")
    agent_configurations = relationship("AgentConfiguration", back_populates="namespace")


class LanguageStyle(Base):
    """Language style for output formatting."""
    __tablename__ = "language_styles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    style_prompt = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    agent_configurations = relationship("AgentConfiguration", back_populates="language_style")


class AgentConfiguration(Base):
    """Combined configuration for projection agents."""
    __tablename__ = "agent_configurations"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    persona_id = Column(Integer, ForeignKey("personas.id"))
    namespace_id = Column(Integer, ForeignKey("namespaces.id"))
    language_style_id = Column(Integer, ForeignKey("language_styles.id"))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    persona = relationship("Persona", back_populates="agent_configurations")
    namespace = relationship("Namespace", back_populates="agent_configurations")
    language_style = relationship("LanguageStyle", back_populates="agent_configurations")
    projections = relationship("Projection", back_populates="agent_configuration")


class SourceNarrative(Base):
    """Original narrative text for projection."""
    __tablename__ = "source_narratives"
    
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), unique=True)  # SHA-256 hash for deduplication
    meta_data = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    projections = relationship("Projection", back_populates="source_narrative")
    
    def __init__(self, content: str, **kwargs):
        super().__init__(**kwargs)
        self.content = content
        self.content_hash = hashlib.sha256(content.encode()).hexdigest()


class Projection(Base):
    """Complete projection with transformation history."""
    __tablename__ = "projections"
    
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    source_narrative_id = Column(Integer, ForeignKey("source_narratives.id"))
    agent_configuration_id = Column(Integer, ForeignKey("agent_configurations.id"))
    content = Column(Text, nullable=False)  # Final projection
    reflection = Column(Text)  # Meta-commentary on the projection
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    source_narrative = relationship("SourceNarrative", back_populates="projections")
    agent_configuration = relationship("AgentConfiguration", back_populates="projections")
    translation_steps = relationship("TranslationChainStep", back_populates="projection", 
                                   order_by="TranslationChainStep.step_order")
    embedding = relationship("NarrativeEmbedding", back_populates="projection", uselist=False)
    interactions = relationship("ProjectionInteraction", back_populates="projection")


class TranslationChainStep(Base):
    """Individual step in the translation chain."""
    __tablename__ = "translation_chain_steps"
    
    id = Column(Integer, primary_key=True)
    projection_id = Column(Integer, ForeignKey("projections.id"))
    step_name = Column(String(100), nullable=False)
    step_order = Column(Integer, nullable=False)
    input_data = Column(JSONB)
    output_data = Column(JSONB)
    meta_data = Column(JSONB, default={})
    duration_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    projection = relationship("Projection", back_populates="translation_steps")
    
    # Indexes
    __table_args__ = (
        Index('idx_projection_step_order', 'projection_id', 'step_order'),
    )


class NarrativeEmbedding(Base):
    """Vector embeddings for semantic search."""
    __tablename__ = "narrative_embeddings"
    
    id = Column(Integer, primary_key=True)
    projection_id = Column(Integer, ForeignKey("projections.id"), unique=True)
    embedding = Column(Vector(768), nullable=False)  # 768-dim for sentence-transformers
    model_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    projection = relationship("Projection", back_populates="embedding")
    
    # Indexes for vector similarity search
    __table_args__ = (
        Index('idx_embedding_vector', 'embedding', postgresql_using='ivfflat'),
    )


class ProjectionInteraction(Base):
    """Track user interactions with projections."""
    __tablename__ = "projection_interactions"
    
    id = Column(Integer, primary_key=True)
    projection_id = Column(Integer, ForeignKey("projections.id"))
    interaction_type = Column(String(50))  # 'view', 'fork', 'iterate', 'share'
    meta_data = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    projection = relationship("Projection", back_populates="interactions")


class PromptCache(Base):
    """Cache for LLM prompts to reduce API calls."""
    __tablename__ = "prompt_cache"
    
    id = Column(Integer, primary_key=True)
    prompt_hash = Column(String(64), unique=True)
    prompt_text = Column(Text)
    response_text = Column(Text)
    model_name = Column(String(100))
    meta_data = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    # Indexes
    __table_args__ = (
        Index('idx_prompt_hash', 'prompt_hash'),
        Index('idx_expires', 'expires_at'),
    )


def seed_initial_data(db: Session):
    """Seed database with initial personas, namespaces, and styles."""
    # Check if already seeded
    if db.query(Persona).count() > 0:
        return
    
    # Create default personas
    personas = [
        Persona(
            name="neutral",
            description="Balanced observer without bias",
            system_prompt="You are a neutral observer. Present information objectively without emotional coloring."
        ),
        Persona(
            name="advocate",
            description="Emphasizes positive aspects",
            system_prompt="You are an advocate. Highlight strengths and opportunities while acknowledging challenges."
        ),
        Persona(
            name="critic",
            description="Analytical and questioning",
            system_prompt="You are a thoughtful critic. Analyze thoroughly and question assumptions constructively."
        ),
        Persona(
            name="philosopher",
            description="Seeks deeper meaning",
            system_prompt="You are a philosopher. Explore underlying meanings and universal truths."
        ),
        Persona(
            name="storyteller",
            description="Narrative-focused transformer",
            system_prompt="You are a storyteller. Weave engaging narratives that captivate and illuminate."
        )
    ]
    
    # Create default namespaces
    namespaces = [
        Namespace(
            name="lamish-galaxy",
            description="The primordial sci-fi allegory space",
            context_prompt="The Lamish Galaxy: A vast network connected by the Pulse, where ideas flow as energy..."
        ),
        Namespace(
            name="medieval-realm",
            description="Fantasy kingdom of quests and honor",
            context_prompt="The Medieval Realm: Where knights quest for truth and dragons guard ancient wisdom..."
        ),
        Namespace(
            name="corporate-dystopia",
            description="Modern business allegories",
            context_prompt="Corporate Dystopia: Megacorps vie for market dominance while algorithms shape reality..."
        ),
        Namespace(
            name="natural-world",
            description="Ecological metaphors and cycles",
            context_prompt="The Natural World: Where every creature plays a role in the great ecosystem of ideas..."
        ),
        Namespace(
            name="quantum-realm",
            description="Abstract probability spaces",
            context_prompt="The Quantum Realm: Where possibilities collapse into reality through observation..."
        )
    ]
    
    # Create default language styles
    styles = [
        LanguageStyle(
            name="standard",
            description="Clear and accessible",
            style_prompt="Write in clear, accessible language suitable for general audiences."
        ),
        LanguageStyle(
            name="academic",
            description="Formal and scholarly",
            style_prompt="Write in formal academic style with precise terminology and structured arguments."
        ),
        LanguageStyle(
            name="poetic",
            description="Rich in metaphor",
            style_prompt="Write with poetic flair, using metaphor and imagery to convey meaning."
        ),
        LanguageStyle(
            name="technical",
            description="Precise and detailed",
            style_prompt="Write with technical precision, using specific terminology and detailed explanations."
        ),
        LanguageStyle(
            name="casual",
            description="Conversational tone",
            style_prompt="Write in a casual, conversational tone as if speaking to a friend."
        )
    ]
    
    # Add all to database
    db.add_all(personas)
    db.add_all(namespaces)
    db.add_all(styles)
    db.commit()