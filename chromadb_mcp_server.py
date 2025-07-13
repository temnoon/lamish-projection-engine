#!/usr/bin/env python3
"""
ChromaDB Memory MCP Server for LPE Enhanced System
Provides semantic search and memory capabilities for content processing chains.
"""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("ChromaDB not available - install with: pip install chromadb")

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.types as types
from mcp.server.stdio import stdio_server

# Import our content models
from simple_content_models import ContentItem, ProcessingChain
from simple_resubmit_system import get_registry


class ChromaDBMemoryServer:
    """MCP server providing ChromaDB-backed semantic memory for LPE."""
    
    def __init__(self):
        self.server = Server("chromadb-memory")
        self.content_registry = get_registry()
        
        # ChromaDB setup
        self.chroma_path = Path.home() / ".lpe" / "chroma_db"
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        
        if CHROMADB_AVAILABLE:
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.chroma_path),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Collections for different content types
            self.collections = {
                "content_items": self._get_or_create_collection("lpe_content_items"),
                "processing_chains": self._get_or_create_collection("lpe_processing_chains"),
                "nab_conversations": self._get_or_create_collection("nab_conversations"),
                "processing_outputs": self._get_or_create_collection("lpe_processing_outputs")
            }
        else:
            self.chroma_client = None
            self.collections = {}
        
        self._setup_handlers()
    
    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection."""
        try:
            return self.chroma_client.get_collection(name)
        except:
            return self.chroma_client.create_collection(name)
    
    def _setup_handlers(self):
        """Setup MCP server handlers."""
        
        @self.server.list_resources()
        async def handle_list_resources() -> list[Resource]:
            """List available memory resources."""
            resources = [
                Resource(
                    uri="chromadb://content_items",
                    name="Content Items Memory",
                    description="Semantic search across all content items",
                    mimeType="application/json"
                ),
                Resource(
                    uri="chromadb://processing_chains", 
                    name="Processing Chains Memory",
                    description="Search and analyze processing workflows",
                    mimeType="application/json"
                ),
                Resource(
                    uri="chromadb://semantic_search",
                    name="Universal Semantic Search",
                    description="Search across all content types semantically",
                    mimeType="application/json"
                )
            ]
            
            if not CHROMADB_AVAILABLE:
                resources.append(Resource(
                    uri="chromadb://status",
                    name="ChromaDB Status",
                    description="ChromaDB installation status and setup instructions",
                    mimeType="text/plain"
                ))
            
            return resources
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read memory resource."""
            if uri == "chromadb://status":
                return self._get_status_info()
            elif uri == "chromadb://content_items":
                return await self._get_content_items_summary()
            elif uri == "chromadb://processing_chains":
                return await self._get_processing_chains_summary()
            elif uri == "chromadb://semantic_search":
                return await self._get_search_capabilities()
            else:
                raise ValueError(f"Unknown resource: {uri}")
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available memory tools."""
            tools = []
            
            if CHROMADB_AVAILABLE:
                tools.extend([
                    Tool(
                        name="add_content_to_memory",
                        description="Add content item to semantic memory",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "content_id": {"type": "string", "description": "Content item ID"},
                                "content_type": {"type": "string", "description": "Type of content"},
                                "force_reindex": {"type": "boolean", "default": False}
                            },
                            "required": ["content_id"]
                        }
                    ),
                    Tool(
                        name="semantic_search",
                        description="Search content semantically using embeddings",
                        inputSchema={
                            "type": "object", 
                            "properties": {
                                "query": {"type": "string", "description": "Search query"},
                                "collection": {"type": "string", "description": "Collection to search", "default": "content_items"},
                                "n_results": {"type": "integer", "description": "Number of results", "default": 5},
                                "include_metadata": {"type": "boolean", "default": True}
                            },
                            "required": ["query"]
                        }
                    ),
                    Tool(
                        name="add_processing_chain_to_memory",
                        description="Add processing chain to memory for analysis",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "chain_id": {"type": "string", "description": "Processing chain ID"},
                                "include_steps": {"type": "boolean", "default": True}
                            },
                            "required": ["chain_id"]
                        }
                    ),
                    Tool(
                        name="find_similar_content",
                        description="Find content similar to a given item",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "content_id": {"type": "string", "description": "Reference content ID"},
                                "similarity_threshold": {"type": "number", "default": 0.7},
                                "max_results": {"type": "integer", "default": 10}
                            },
                            "required": ["content_id"]
                        }
                    ),
                    Tool(
                        name="analyze_processing_patterns",
                        description="Analyze patterns in processing chains and outputs",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "engine_type": {"type": "string", "description": "Filter by engine type"},
                                "time_range_days": {"type": "integer", "default": 30}
                            }
                        }
                    ),
                    Tool(
                        name="bulk_index_content",
                        description="Index all content from registry into ChromaDB",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "force_reindex": {"type": "boolean", "default": False},
                                "content_types": {"type": "array", "items": {"type": "string"}, "default": ["text", "conversation", "projection"]}
                            }
                        }
                    )
                ])
            else:
                tools.append(Tool(
                    name="setup_chromadb",
                    description="Get instructions for setting up ChromaDB",
                    inputSchema={"type": "object", "properties": {}}
                ))
            
            return tools
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Handle tool calls."""
            if not CHROMADB_AVAILABLE and name != "setup_chromadb":
                return [types.TextContent(
                    type="text",
                    text="ChromaDB not available. Use setup_chromadb tool for installation instructions."
                )]
            
            if name == "setup_chromadb":
                return [types.TextContent(type="text", text=self._get_setup_instructions())]
            elif name == "add_content_to_memory":
                return await self._add_content_to_memory(arguments)
            elif name == "semantic_search":
                return await self._semantic_search(arguments)
            elif name == "add_processing_chain_to_memory":
                return await self._add_processing_chain_to_memory(arguments)
            elif name == "find_similar_content":
                return await self._find_similar_content(arguments)
            elif name == "analyze_processing_patterns":
                return await self._analyze_processing_patterns(arguments)
            elif name == "bulk_index_content":
                return await self._bulk_index_content(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    def _get_status_info(self) -> str:
        """Get ChromaDB status information."""
        if CHROMADB_AVAILABLE:
            stats = {
                "status": "available",
                "client_path": str(self.chroma_path),
                "collections": {name: coll.count() for name, coll in self.collections.items()},
                "total_items": sum(coll.count() for coll in self.collections.values())
            }
            return json.dumps(stats, indent=2)
        else:
            return "ChromaDB not available - requires installation"
    
    async def _get_content_items_summary(self) -> str:
        """Get summary of content items in memory."""
        if not CHROMADB_AVAILABLE:
            return "ChromaDB not available"
        
        collection = self.collections["content_items"]
        count = collection.count()
        
        summary = {
            "total_content_items": count,
            "collection_name": "lpe_content_items",
            "capabilities": [
                "Semantic search across content",
                "Similarity matching",
                "Content type filtering",
                "Metadata-based queries"
            ]
        }
        
        if count > 0:
            # Get a sample of recent items
            results = collection.get(limit=5, include=["metadatas", "documents"])
            summary["sample_items"] = [
                {
                    "id": id_,
                    "metadata": meta,
                    "content_preview": doc[:100] + "..." if len(doc) > 100 else doc
                }
                for id_, meta, doc in zip(results["ids"], results["metadatas"], results["documents"])
            ]
        
        return json.dumps(summary, indent=2)
    
    async def _get_processing_chains_summary(self) -> str:
        """Get summary of processing chains in memory."""
        if not CHROMADB_AVAILABLE:
            return "ChromaDB not available"
        
        collection = self.collections["processing_chains"]
        count = collection.count()
        
        summary = {
            "total_processing_chains": count,
            "collection_name": "lpe_processing_chains",
            "analysis_capabilities": [
                "Engine usage patterns",
                "Processing success rates",
                "Chain complexity analysis",
                "Parameter effectiveness"
            ]
        }
        
        return json.dumps(summary, indent=2)
    
    async def _get_search_capabilities(self) -> str:
        """Get information about search capabilities."""
        capabilities = {
            "semantic_search": {
                "description": "Vector-based similarity search using embeddings",
                "collections": list(self.collections.keys()) if CHROMADB_AVAILABLE else [],
                "features": [
                    "Natural language queries",
                    "Similarity thresholds",
                    "Metadata filtering",
                    "Cross-collection search"
                ]
            },
            "content_discovery": {
                "description": "Find related content and processing chains",
                "use_cases": [
                    "Find similar conversations",
                    "Discover processing patterns",
                    "Recommend next processing steps",
                    "Identify content gaps"
                ]
            }
        }
        
        return json.dumps(capabilities, indent=2)
    
    def _get_setup_instructions(self) -> str:
        """Get ChromaDB setup instructions."""
        return """
# ChromaDB Setup Instructions for LPE Enhanced System

## Installation
```bash
pip install chromadb

# Or with conda
conda install -c conda-forge chromadb
```

## Features Enabled After Installation
- Semantic search across all content types
- Processing chain pattern analysis  
- Content similarity matching
- Cross-system content discovery (NAB + LPE)
- Automated content indexing

## Directory Structure
ChromaDB will create persistent storage at:
- `~/.lpe/chroma_db/` - Main database
- Collections:
  - `lpe_content_items` - All content items
  - `lpe_processing_chains` - Processing workflows
  - `nab_conversations` - NAB conversation imports
  - `lpe_processing_outputs` - Generated content

## Usage After Installation
1. Restart the MCP server
2. Use `bulk_index_content` to index existing content
3. Use `semantic_search` for intelligent content discovery
4. Use `find_similar_content` for recommendations

## Integration Benefits
- NAB conversations become searchable by meaning
- LPE transformations build on semantic context
- Processing chains optimize based on similar content
- Universal content discovery across systems
        """.strip()
    
    async def _add_content_to_memory(self, args: dict) -> list[types.TextContent]:
        """Add content item to semantic memory."""
        content_id = args["content_id"]
        force_reindex = args.get("force_reindex", False)
        
        content = self.content_registry.get_content(content_id)
        if not content:
            return [types.TextContent(
                type="text",
                text=f"Content not found: {content_id}"
            )]
        
        collection = self.collections["content_items"]
        
        # Check if already indexed
        existing = collection.get(ids=[content_id])
        if existing["ids"] and not force_reindex:
            return [types.TextContent(
                type="text", 
                text=f"Content {content_id} already in memory. Use force_reindex=true to update."
            )]
        
        # Prepare document and metadata
        document = f"{content.title}\n\n{content.content}"
        metadata = {
            "content_type": content.content_type,
            "title": content.title,
            "created_at": content.created_at.isoformat(),
            "source": content.metadata.get("source", "unknown"),
            **content.metadata
        }
        
        # Add to collection
        if existing["ids"]:
            collection.update(
                ids=[content_id],
                documents=[document],
                metadatas=[metadata]
            )
            action = "updated"
        else:
            collection.add(
                ids=[content_id],
                documents=[document],
                metadatas=[metadata]
            )
            action = "added"
        
        return [types.TextContent(
            type="text",
            text=f"Content {content_id} {action} to semantic memory successfully."
        )]
    
    async def _semantic_search(self, args: dict) -> list[types.TextContent]:
        """Perform semantic search."""
        query = args["query"]
        collection_name = args.get("collection", "content_items")
        n_results = args.get("n_results", 5)
        include_metadata = args.get("include_metadata", True)
        
        if collection_name not in self.collections:
            return [types.TextContent(
                type="text",
                text=f"Collection not found: {collection_name}"
            )]
        
        collection = self.collections[collection_name]
        
        # Perform search
        include = ["documents", "distances"]
        if include_metadata:
            include.append("metadatas")
        
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=include
        )
        
        # Format results
        formatted_results = {
            "query": query,
            "collection": collection_name,
            "total_results": len(results["ids"][0]),
            "results": []
        }
        
        for i, item_id in enumerate(results["ids"][0]):
            result_item = {
                "id": item_id,
                "distance": results["distances"][0][i],
                "similarity": 1 - results["distances"][0][i],  # Convert distance to similarity
                "document": results["documents"][0][i][:200] + "..." if len(results["documents"][0][i]) > 200 else results["documents"][0][i]
            }
            
            if include_metadata and "metadatas" in results:
                result_item["metadata"] = results["metadatas"][0][i]
            
            formatted_results["results"].append(result_item)
        
        return [types.TextContent(
            type="text",
            text=json.dumps(formatted_results, indent=2)
        )]
    
    async def _add_processing_chain_to_memory(self, args: dict) -> list[types.TextContent]:
        """Add processing chain to memory."""
        chain_id = args["chain_id"]
        include_steps = args.get("include_steps", True)
        
        chain = self.content_registry.get_chain(chain_id)
        if not chain:
            return [types.TextContent(
                type="text",
                text=f"Processing chain not found: {chain_id}"
            )]
        
        collection = self.collections["processing_chains"]
        
        # Create document from chain
        document_parts = [
            f"Title: {chain.title}",
            f"Description: {chain.description or 'No description'}",
            f"Source: {chain.source_content.title}",
            f"Status: {chain.status}"
        ]
        
        if include_steps:
            document_parts.append("Processing Steps:")
            for step in chain.steps:
                document_parts.append(f"- {step.engine}: {step.status}")
                if step.output_content:
                    document_parts.append(f"  Output: {step.output_content.title}")
        
        document = "\n".join(document_parts)
        
        metadata = {
            "chain_id": chain_id,
            "title": chain.title,
            "status": chain.status,
            "created_at": chain.created_at.isoformat(),
            "step_count": len(chain.steps),
            "engines_used": [step.engine for step in chain.steps],
            "final_engine": chain.steps[-1].engine if chain.steps else None
        }
        
        collection.upsert(
            ids=[chain_id],
            documents=[document],
            metadatas=[metadata]
        )
        
        return [types.TextContent(
            type="text",
            text=f"Processing chain {chain_id} added to memory successfully."
        )]
    
    async def _find_similar_content(self, args: dict) -> list[types.TextContent]:
        """Find content similar to a reference item."""
        content_id = args["content_id"]
        similarity_threshold = args.get("similarity_threshold", 0.7)
        max_results = args.get("max_results", 10)
        
        # Get the reference content
        content = self.content_registry.get_content(content_id)
        if not content:
            return [types.TextContent(
                type="text",
                text=f"Reference content not found: {content_id}"
            )]
        
        collection = self.collections["content_items"]
        
        # Search using the content as query
        query_text = f"{content.title}\n\n{content.content}"
        results = collection.query(
            query_texts=[query_text],
            n_results=max_results + 1,  # +1 to account for self-match
            include=["documents", "distances", "metadatas"]
        )
        
        # Filter results
        similar_items = []
        for i, (item_id, distance, doc, metadata) in enumerate(zip(
            results["ids"][0], results["distances"][0], 
            results["documents"][0], results["metadatas"][0]
        )):
            similarity = 1 - distance
            
            # Skip self and items below threshold
            if item_id == content_id or similarity < similarity_threshold:
                continue
            
            similar_items.append({
                "id": item_id,
                "similarity": similarity,
                "title": metadata.get("title", "Unknown"),
                "content_type": metadata.get("content_type", "unknown"),
                "preview": doc[:150] + "..." if len(doc) > 150 else doc
            })
        
        result = {
            "reference_content": {
                "id": content_id,
                "title": content.title,
                "type": content.content_type
            },
            "similar_items": similar_items,
            "similarity_threshold": similarity_threshold,
            "total_found": len(similar_items)
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    async def _analyze_processing_patterns(self, args: dict) -> list[types.TextContent]:
        """Analyze patterns in processing chains."""
        engine_type = args.get("engine_type")
        time_range_days = args.get("time_range_days", 30)
        
        collection = self.collections["processing_chains"]
        
        # Get all chains
        all_chains = collection.get(include=["metadatas"])
        
        # Analyze patterns
        analysis = {
            "total_chains": len(all_chains["ids"]),
            "engine_usage": {},
            "success_rates": {},
            "average_steps": 0,
            "most_common_patterns": []
        }
        
        if all_chains["metadatas"]:
            engine_counts = {}
            success_counts = {}
            total_counts = {}
            step_counts = []
            
            for metadata in all_chains["metadatas"]:
                engines = metadata.get("engines_used", [])
                status = metadata.get("status", "unknown")
                step_count = metadata.get("step_count", 0)
                
                step_counts.append(step_count)
                
                for engine in engines:
                    if engine_type and engine != engine_type:
                        continue
                    
                    engine_counts[engine] = engine_counts.get(engine, 0) + 1
                    total_counts[engine] = total_counts.get(engine, 0) + 1
                    
                    if status == "completed":
                        success_counts[engine] = success_counts.get(engine, 0) + 1
            
            analysis["engine_usage"] = engine_counts
            analysis["success_rates"] = {
                engine: (success_counts.get(engine, 0) / total_counts[engine]) * 100
                for engine in total_counts
            }
            analysis["average_steps"] = sum(step_counts) / len(step_counts) if step_counts else 0
        
        return [types.TextContent(
            type="text",
            text=json.dumps(analysis, indent=2)
        )]
    
    async def _bulk_index_content(self, args: dict) -> list[types.TextContent]:
        """Bulk index all content from registry."""
        force_reindex = args.get("force_reindex", False)
        content_types = args.get("content_types", ["text", "conversation", "projection"])
        
        indexed_count = 0
        skipped_count = 0
        error_count = 0
        
        collection = self.collections["content_items"]
        
        for content_id, content in self.content_registry.content_items.items():
            if content.content_type not in content_types:
                continue
            
            try:
                # Check if already indexed
                existing = collection.get(ids=[content_id])
                if existing["ids"] and not force_reindex:
                    skipped_count += 1
                    continue
                
                # Index the content
                document = f"{content.title}\n\n{content.content}"
                metadata = {
                    "content_type": content.content_type,
                    "title": content.title,
                    "created_at": content.created_at.isoformat(),
                    "source": content.metadata.get("source", "unknown"),
                    **content.metadata
                }
                
                if existing["ids"]:
                    collection.update(
                        ids=[content_id],
                        documents=[document],
                        metadatas=[metadata]
                    )
                else:
                    collection.add(
                        ids=[content_id],
                        documents=[document],
                        metadatas=[metadata]
                    )
                
                indexed_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"Error indexing {content_id}: {e}")
        
        result = {
            "bulk_indexing_complete": True,
            "indexed": indexed_count,
            "skipped": skipped_count,
            "errors": error_count,
            "total_processed": indexed_count + skipped_count + error_count,
            "content_types_processed": content_types
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]


async def main():
    """Run the ChromaDB Memory MCP server."""
    memory_server = ChromaDBMemoryServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await memory_server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="chromadb-memory",
                server_version="1.0.0",
                capabilities=memory_server.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())