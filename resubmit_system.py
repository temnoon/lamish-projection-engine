#!/usr/bin/env python3
"""
Universal content resubmit system for LPE.
Enables any content to be reprocessed through any compatible engine.
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from content_models import (
    ContentItem, ProcessingChain, ProcessingStep, ProcessingParameters,
    ResubmitRequest, ContentOutput, get_available_engines, validate_content_for_engine
)


class ContentRegistry:
    """Registry for tracking all content in the LPE ecosystem."""
    
    def __init__(self, base_path: Path = None):
        self.base_path = base_path or Path.home() / ".lpe" / "content"
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Content storage paths
        self.content_index = self.base_path / "content_index.json"
        self.chains_index = self.base_path / "chains_index.json"
        self.outputs_dir = self.base_path / "outputs"
        self.outputs_dir.mkdir(exist_ok=True)
        
        # Load existing indices
        self.content_items: Dict[str, ContentItem] = self._load_content_index()
        self.processing_chains: Dict[str, ProcessingChain] = self._load_chains_index()
    
    def _load_content_index(self) -> Dict[str, ContentItem]:
        """Load content index from disk."""
        if self.content_index.exists():
            try:
                with open(self.content_index, 'r') as f:
                    data = json.load(f)
                return {k: ContentItem.parse_obj(v) for k, v in data.items()}
            except Exception as e:
                print(f"Warning: Could not load content index: {e}")
        return {}
    
    def _load_chains_index(self) -> Dict[str, ProcessingChain]:
        """Load chains index from disk."""
        if self.chains_index.exists():
            try:
                with open(self.chains_index, 'r') as f:
                    data = json.load(f)
                return {k: ProcessingChain.parse_obj(v) for k, v in data.items()}
            except Exception as e:
                print(f"Warning: Could not load chains index: {e}")
        return {}
    
    def save_indices(self):
        """Save both indices to disk."""
        # Save content index
        content_data = {k: v.dict() for k, v in self.content_items.items()}
        with open(self.content_index, 'w') as f:
            json.dump(content_data, f, indent=2, default=str)
        
        # Save chains index
        chains_data = {k: v.dict() for k, v in self.processing_chains.items()}
        with open(self.chains_index, 'w') as f:
            json.dump(chains_data, f, indent=2, default=str)
    
    def register_content(self, content: ContentItem) -> str:
        """Register new content item."""
        self.content_items[content.id] = content
        self.save_indices()
        return content.id
    
    def register_chain(self, chain: ProcessingChain) -> str:
        """Register new processing chain."""
        self.processing_chains[chain.chain_id] = chain
        self.save_indices()
        return chain.chain_id
    
    def get_content(self, content_id: str) -> Optional[ContentItem]:
        """Get content by ID."""
        return self.content_items.get(content_id)
    
    def get_chain(self, chain_id: str) -> Optional[ProcessingChain]:
        """Get chain by ID."""
        return self.processing_chains.get(chain_id)
    
    def search_content(self, query: str, content_type: str = None) -> List[ContentItem]:
        """Simple text search across content."""
        results = []
        for content in self.content_items.values():
            if content_type and content.content_type != content_type:
                continue
            
            # Search in title and content
            if (query.lower() in content.title.lower() or 
                query.lower() in content.content.lower()):
                results.append(content)
        
        return results


class ResubmitProcessor:
    """Handles resubmission of content to various engines."""
    
    def __init__(self, registry: ContentRegistry):
        self.registry = registry
        
        # Engine processors - these would integrate with existing LPE systems
        self.engine_handlers = {
            "projection": self._handle_projection,
            "translation": self._handle_translation,
            "maieutic": self._handle_maieutic,
            "vision": self._handle_vision,
            "refinement": self._handle_refinement,
            "echo_evolve": self._handle_echo_evolve
        }
    
    def process_resubmit(self, request: ResubmitRequest) -> ContentOutput:
        """Process a resubmit request."""
        
        # Get the source content
        content = self.registry.get_content(request.content_id)
        if not content:
            raise ValueError(f"Content not found: {request.content_id}")
        
        # Validate compatibility
        if not validate_content_for_engine(content, request.target_engine):
            raise ValueError(f"Content type {content.content_type} not compatible with {request.target_engine}")
        
        # Create processing step
        step = ProcessingStep(
            engine=request.target_engine,
            input_content=content,
            parameters=request.parameters,
            status="pending"
        )
        
        # Create or extend processing chain
        if request.create_new_chain:
            chain = ProcessingChain(
                title=f"{request.target_engine.title()} of {content.title}",
                source_content=content,
                steps=[step]
            )
            self.registry.register_chain(chain)
        else:
            # Add to existing chain
            chain = self.registry.get_chain(request.parent_chain_id)
            if not chain:
                raise ValueError(f"Parent chain not found: {request.parent_chain_id}")
            chain.steps.append(step)
        
        # Execute the step
        try:
            step.status = "running"
            step.started_at = datetime.now()
            
            # Call the appropriate engine handler
            handler = self.engine_handlers.get(request.target_engine)
            if not handler:
                raise ValueError(f"No handler for engine: {request.target_engine}")
            
            result = handler(content, request.parameters)
            
            # Create output content
            output_content = ContentItem(
                content_type=content.content_type,
                title=f"{request.target_engine.title()}: {content.title}",
                content=result["content"],
                metadata={
                    "source_content_id": content.id,
                    "processing_engine": request.target_engine,
                    "parameters": request.parameters.dict(),
                    **result.get("metadata", {})
                }
            )
            
            step.output_content = output_content
            step.status = "completed"
            step.completed_at = datetime.now()
            
            # Register the output content
            self.registry.register_content(output_content)
            
            # Update chain status if this was the final step
            if chain.steps and all(s.status == "completed" for s in chain.steps):
                chain.status = "completed"
                chain.final_output = output_content
                chain.completed_at = datetime.now()
            
            # Save to file system
            output_dir = self._create_output_directory(chain.chain_id, step.step_id)
            content_output = self._save_to_filesystem(chain, step, output_dir)
            
            return content_output
            
        except Exception as e:
            step.status = "failed"
            step.error_message = str(e)
            step.completed_at = datetime.now()
            raise
        
        finally:
            # Save updated chain
            self.registry.save_indices()
    
    def _create_output_directory(self, chain_id: str, step_id: str) -> Path:
        """Create directory structure for output."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = self.registry.outputs_dir / f"{timestamp}_{chain_id[:8]}" / step_id[:8]
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
    
    def _save_to_filesystem(self, chain: ProcessingChain, step: ProcessingStep, output_dir: Path) -> ContentOutput:
        """Save processing results to filesystem."""
        
        # Save metadata
        metadata_file = output_dir / "metadata.json"
        metadata = {
            "chain": chain.dict(),
            "step": step.dict(),
            "created_at": datetime.now().isoformat()
        }
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        # Save output content
        files_created = [metadata_file]
        
        if step.output_content:
            content_file = output_dir / "output.md"
            with open(content_file, 'w') as f:
                f.write(step.output_content.content)
            files_created.append(content_file)
            
            # Save any media files if applicable
            if step.output_content.source_path and step.output_content.source_path.exists():
                media_file = output_dir / step.output_content.source_path.name
                shutil.copy2(step.output_content.source_path, media_file)
                files_created.append(media_file)
        
        return ContentOutput(
            content_item=step.output_content,
            processing_chain=chain,
            output_directory=output_dir,
            files_created=files_created,
            metadata_file=metadata_file
        )
    
    # Engine handler methods - these would integrate with existing LPE functionality
    
    def _handle_projection(self, content: ContentItem, params: ProcessingParameters) -> Dict[str, Any]:
        """Handle projection engine processing."""
        # This would integrate with existing projection system
        # For now, simulate processing
        result_content = f"ALLEGORICAL PROJECTION:\n\nPersona: {params.persona}\nNamespace: {params.namespace}\nStyle: {params.style}\n\nOriginal: {content.content}\n\nProjection: [This would be the actual allegorical transformation]"
        
        return {
            "content": result_content,
            "metadata": {
                "processing_type": "projection",
                "persona": params.persona,
                "namespace": params.namespace,
                "style": params.style
            }
        }
    
    def _handle_translation(self, content: ContentItem, params: ProcessingParameters) -> Dict[str, Any]:
        """Handle translation engine processing."""
        result_content = f"TRANSLATION ANALYSIS:\n\nOriginal: {content.content}\n\n[This would be the actual translation analysis]"
        
        return {
            "content": result_content,
            "metadata": {
                "processing_type": "translation"
            }
        }
    
    def _handle_maieutic(self, content: ContentItem, params: ProcessingParameters) -> Dict[str, Any]:
        """Handle maieutic dialogue processing."""
        result_content = f"MAIEUTIC DIALOGUE:\n\nSource: {content.content}\n\n[This would be the actual Socratic questioning]"
        
        return {
            "content": result_content,
            "metadata": {
                "processing_type": "maieutic"
            }
        }
    
    def _handle_vision(self, content: ContentItem, params: ProcessingParameters) -> Dict[str, Any]:
        """Handle vision analysis processing."""
        result_content = f"VISION ANALYSIS:\n\nSource: {content.title}\n\n[This would be the actual image analysis]"
        
        return {
            "content": result_content,
            "metadata": {
                "processing_type": "vision"
            }
        }
    
    def _handle_refinement(self, content: ContentItem, params: ProcessingParameters) -> Dict[str, Any]:
        """Handle content refinement processing."""
        result_content = f"REFINED CONTENT:\n\nOriginal: {content.content}\n\nRefinement with custom prompt: {params.custom_prompt}\n\n[This would be the actual refined content]"
        
        return {
            "content": result_content,
            "metadata": {
                "processing_type": "refinement",
                "custom_prompt": params.custom_prompt
            }
        }
    
    def _handle_echo_evolve(self, content: ContentItem, params: ProcessingParameters) -> Dict[str, Any]:
        """Handle echo and evolve processing."""
        result_content = f"ECHO & EVOLVE:\n\nSource: {content.content}\n\n[This would be the actual echo description and evolution]"
        
        return {
            "content": result_content,
            "metadata": {
                "processing_type": "echo_evolve"
            }
        }


# Global registry instance
_global_registry = None
_global_processor = None

def get_registry() -> ContentRegistry:
    """Get global content registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ContentRegistry()
    return _global_registry

def get_processor() -> ResubmitProcessor:
    """Get global resubmit processor."""
    global _global_processor
    if _global_processor is None:
        _global_processor = ResubmitProcessor(get_registry())
    return _global_processor


# Convenience functions for web interface

def create_resubmit_button_data(content: ContentItem) -> Dict[str, Any]:
    """Create data for resubmit button in web interface."""
    available_engines = get_available_engines(content)
    
    return {
        "content_id": content.id,
        "content_title": content.title,
        "content_type": content.content_type,
        "available_engines": available_engines,
        "resubmit_url": f"/api/resubmit/{content.id}"
    }


def demo_resubmit_flow():
    """Demonstrate the resubmit system."""
    registry = get_registry()
    processor = get_processor()
    
    # Create sample content
    from content_models import create_text_content
    
    sample_text = create_text_content(
        "Innovation drives technological progress through collaborative research.",
        "Sample Innovation Text",
        source="demo"
    )
    
    # Register it
    content_id = registry.register_content(sample_text)
    print(f"Registered content: {content_id}")
    
    # Create resubmit request
    request = ResubmitRequest(
        content_id=content_id,
        target_engine="projection",
        parameters=ProcessingParameters(
            persona="philosopher",
            namespace="academic-realm",
            style="scholarly"
        )
    )
    
    # Process resubmit
    try:
        output = processor.process_resubmit(request)
        print(f"Processing completed!")
        print(f"Output directory: {output.output_directory}")
        print(f"Files created: {len(output.files_created)}")
        
        # Show the result
        print(f"\nResult content:\n{output.content_item.content[:200]}...")
        
        return output
        
    except Exception as e:
        print(f"Processing failed: {e}")
        return None


if __name__ == "__main__":
    demo_resubmit_flow()