#!/usr/bin/env python3
"""
Simple content models for LPE without Pydantic dependency.
Enables universal resubmit system and processing pipeline visualization.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union


class ContentItem:
    """Base model for any content item in the LPE ecosystem."""
    
    def __init__(self, content_type: str, title: str, content: str, 
                 source_path: Optional[Path] = None, metadata: Optional[Dict] = None,
                 content_id: Optional[str] = None):
        self.id = content_id or str(uuid.uuid4())
        self.content_type = content_type  # "text", "image", "audio", "conversation", "projection", "translation"
        self.title = title
        self.content = content  # Text content or file path for media
        self.source_path = Path(source_path) if source_path else None
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.file_size = None
        self.mime_type = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content_type": self.content_type,
            "title": self.title,
            "content": self.content,
            "source_path": str(self.source_path) if self.source_path else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "file_size": self.file_size,
            "mime_type": self.mime_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentItem':
        item = cls(
            content_type=data["content_type"],
            title=data["title"],
            content=data["content"],
            source_path=data.get("source_path"),
            metadata=data.get("metadata", {}),
            content_id=data.get("id")
        )
        if "created_at" in data:
            item.created_at = datetime.fromisoformat(data["created_at"])
        return item


class ProcessingParameters:
    """Parameters for any LPE processing step."""
    
    def __init__(self, persona: str = "neutral", namespace: str = "lamish-galaxy",
                 style: str = "standard", temperature: float = 0.7,
                 max_tokens: int = 4096, custom_prompt: Optional[str] = None,
                 additional_context: Optional[str] = None,
                 provider: Optional[str] = None, model: Optional[str] = None):
        self.persona = persona
        self.namespace = namespace
        self.style = style
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.custom_prompt = custom_prompt
        self.additional_context = additional_context
        self.provider = provider
        self.model = model
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "persona": self.persona,
            "namespace": self.namespace,
            "style": self.style,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "custom_prompt": self.custom_prompt,
            "additional_context": self.additional_context,
            "provider": self.provider,
            "model": self.model
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingParameters':
        return cls(**data)


class ProcessingStep:
    """A single step in a processing chain."""
    
    def __init__(self, engine: str, input_content: ContentItem, 
                 parameters: ProcessingParameters, step_id: Optional[str] = None):
        self.step_id = step_id or str(uuid.uuid4())
        self.engine = engine  # "projection", "translation", "maieutic", "vision", "refinement", "echo_evolve"
        self.input_content = input_content
        self.parameters = parameters
        self.output_content: Optional[ContentItem] = None
        self.intermediate_outputs: List[ContentItem] = []
        self.status = "pending"  # "pending", "running", "completed", "failed", "cancelled"
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.execution_time: Optional[float] = None
    
    @property
    def duration(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return self.execution_time
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "engine": self.engine,
            "input_content": self.input_content.to_dict(),
            "parameters": self.parameters.to_dict(),
            "output_content": self.output_content.to_dict() if self.output_content else None,
            "intermediate_outputs": [item.to_dict() for item in self.intermediate_outputs],
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "execution_time": self.execution_time
        }


class ProcessingChain:
    """A sequence of processing steps with branching capability."""
    
    def __init__(self, title: str, source_content: ContentItem, 
                 description: Optional[str] = None, chain_id: Optional[str] = None):
        self.chain_id = chain_id or str(uuid.uuid4())
        self.title = title
        self.description = description
        self.source_content = source_content
        self.steps: List[ProcessingStep] = []
        self.final_output: Optional[ContentItem] = None
        self.status = "pending"  # "pending", "running", "completed", "failed", "cancelled"
        self.created_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.branching_points: List[str] = []  # Step IDs where branching occurred
        self.parent_chain_id: Optional[str] = None
        self.tags: List[str] = []
    
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
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "title": self.title,
            "description": self.description,
            "source_content": self.source_content.to_dict(),
            "steps": [step.to_dict() for step in self.steps],
            "final_output": self.final_output.to_dict() if self.final_output else None,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "branching_points": self.branching_points,
            "parent_chain_id": self.parent_chain_id,
            "tags": self.tags
        }


class ResubmitRequest:
    """Request model for resubmitting content to any engine."""
    
    def __init__(self, content_id: str, target_engine: str, 
                 parameters: ProcessingParameters, create_new_chain: bool = True,
                 parent_chain_id: Optional[str] = None, 
                 branch_from_step: Optional[str] = None):
        self.content_id = content_id
        self.target_engine = target_engine  # "projection", "translation", "maieutic", "vision", "refinement", "echo_evolve"
        self.parameters = parameters
        self.create_new_chain = create_new_chain
        self.parent_chain_id = parent_chain_id
        self.branch_from_step = branch_from_step


class ContentOutput:
    """Structured output from any LPE processing."""
    
    def __init__(self, content_item: ContentItem, processing_chain: ProcessingChain,
                 output_directory: Path, files_created: Optional[List[Path]] = None,
                 metadata_file: Optional[Path] = None):
        self.content_item = content_item
        self.processing_chain = processing_chain
        self.output_directory = output_directory
        self.files_created = files_created or []
        self.metadata_file = metadata_file


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