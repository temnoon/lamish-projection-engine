#!/usr/bin/env python3
"""
Core Pydantic models for LPE content management and processing chains.
Enables universal resubmit system and processing pipeline visualization.
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Literal, Union
from datetime import datetime
from pathlib import Path
import uuid
import json


class ContentItem(BaseModel):
    """Base model for any content item in the LPE ecosystem."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content_type: Literal["text", "image", "audio", "conversation", "projection", "translation"] 
    title: str
    content: str  # Text content or file path for media
    source_path: Optional[Path] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    
    class Config:
        json_encoders = {
            Path: str,
            datetime: lambda dt: dt.isoformat()
        }
    
    @validator('source_path', pre=True)
    def validate_path(cls, v):
        if v is not None and isinstance(v, str):
            return Path(v)
        return v


class ProcessingParameters(BaseModel):
    """Parameters for any LPE processing step."""
    
    persona: Optional[str] = "neutral"
    namespace: Optional[str] = "lamish-galaxy" 
    style: Optional[str] = "standard"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096
    custom_prompt: Optional[str] = None
    additional_context: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None


class ProcessingStep(BaseModel):
    """A single step in a processing chain."""
    
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    engine: Literal["projection", "translation", "maieutic", "vision", "refinement", "echo_evolve"]
    input_content: ContentItem
    parameters: ProcessingParameters
    output_content: Optional[ContentItem] = None
    intermediate_outputs: List[ContentItem] = Field(default_factory=list)
    status: Literal["pending", "running", "completed", "failed", "cancelled"] = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None  # seconds
    
    @property
    def duration(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return self.execution_time


class ProcessingChain(BaseModel):
    """A sequence of processing steps with branching capability."""
    
    chain_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    source_content: ContentItem
    steps: List[ProcessingStep] = Field(default_factory=list)
    final_output: Optional[ContentItem] = None
    status: Literal["pending", "running", "completed", "failed", "cancelled"] = "pending"
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    branching_points: List[str] = Field(default_factory=list)  # Step IDs where branching occurred
    parent_chain_id: Optional[str] = None  # For branched chains
    tags: List[str] = Field(default_factory=list)
    
    @property
    def current_step(self) -> Optional[ProcessingStep]:
        """Get the currently executing or next pending step."""
        for step in self.steps:
            if step.status in ["running", "pending"]:
                return step
        return None
    
    @property
    def progress_percentage(self) -> float:
        """Calculate completion percentage."""
        if not self.steps:
            return 0.0
        completed = len([s for s in self.steps if s.status == "completed"])
        return (completed / len(self.steps)) * 100


class ResubmitRequest(BaseModel):
    """Request model for resubmitting content to any engine."""
    
    content_id: str
    target_engine: Literal["projection", "translation", "maieutic", "vision", "refinement", "echo_evolve"]
    parameters: ProcessingParameters
    create_new_chain: bool = True
    parent_chain_id: Optional[str] = None
    branch_from_step: Optional[str] = None


class ContentOutput(BaseModel):
    """Structured output from any LPE processing."""
    
    content_item: ContentItem
    processing_chain: ProcessingChain
    output_directory: Path
    files_created: List[Path] = Field(default_factory=list)
    metadata_file: Path
    
    class Config:
        json_encoders = {
            Path: str
        }


class UnifiedSearchResult(BaseModel):
    """Search result across all content types."""
    
    content: ContentItem
    relevance_score: float
    source_type: Literal["nab_conversation", "lpe_output", "intermediate_step", "media_file"]
    snippet: Optional[str] = None
    matching_chains: List[str] = Field(default_factory=list)  # Chain IDs using this content


# Factory functions for creating common content types

def create_text_content(text: str, title: str, content_type: str = "text", **metadata) -> ContentItem:
    """Create a text content item."""
    return ContentItem(
        content_type=content_type,
        title=title,
        content=text,
        metadata=metadata
    )


def create_image_content(image_path: Path, title: str, **metadata) -> ContentItem:
    """Create an image content item."""
    return ContentItem(
        content_type="image",
        title=title,
        content=str(image_path),
        source_path=image_path,
        file_size=image_path.stat().st_size if image_path.exists() else None,
        mime_type="image/png",  # Could be detected
        metadata=metadata
    )


def create_conversation_content(conversation_data: Dict, title: str, **metadata) -> ContentItem:
    """Create a conversation content item from NAB data."""
    return ContentItem(
        content_type="conversation",
        title=title,
        content=json.dumps(conversation_data, indent=2),
        metadata={**metadata, "message_count": len(conversation_data.get("messages", []))}
    )


def create_processing_chain(source: ContentItem, title: str, steps: List[str]) -> ProcessingChain:
    """Create a processing chain with predefined steps."""
    chain = ProcessingChain(
        title=title,
        source_content=source
    )
    
    # Create step objects (they'll be populated during execution)
    for i, engine in enumerate(steps):
        step = ProcessingStep(
            engine=engine,
            input_content=source if i == 0 else ContentItem(
                content_type="text", 
                title=f"Intermediate from {steps[i-1]}",
                content=""
            ),
            parameters=ProcessingParameters()
        )
        chain.steps.append(step)
    
    return chain


# Validation and utility functions

def validate_content_for_engine(content: ContentItem, engine: str) -> bool:
    """Check if content is compatible with an engine."""
    compatibility = {
        "projection": ["text", "conversation"],
        "translation": ["text", "conversation"], 
        "maieutic": ["text", "conversation"],
        "vision": ["image", "text"],
        "refinement": ["text", "projection", "translation"],
        "echo_evolve": ["image", "text"]
    }
    return content.content_type in compatibility.get(engine, [])


def get_available_engines(content: ContentItem) -> List[str]:
    """Get list of engines that can process this content type."""
    available = []
    engines = ["projection", "translation", "maieutic", "vision", "refinement", "echo_evolve"]
    
    for engine in engines:
        if validate_content_for_engine(content, engine):
            available.append(engine)
    
    return available


# Example usage and testing functions

def example_usage():
    """Demonstrate the content model usage."""
    
    # Create some content
    text_content = create_text_content(
        "Innovation drives technological progress", 
        "Sample Text",
        source="user_input"
    )
    
    # Create a processing chain
    chain = create_processing_chain(
        text_content,
        "Translation and Projection Chain",
        ["translation", "projection", "refinement"]
    )
    
    print(f"Created chain: {chain.title}")
    print(f"Steps: {[step.engine for step in chain.steps]}")
    print(f"Available engines for text: {get_available_engines(text_content)}")
    
    return chain


if __name__ == "__main__":
    example_usage()