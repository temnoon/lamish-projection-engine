#!/usr/bin/env python3
"""
System Verification Script for LPE Enhanced System
Run this to verify all components are working correctly.
"""

import sys
import json
import requests
import subprocess
from pathlib import Path
from datetime import datetime

def print_status(message, status="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    symbols = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
    print(f"[{timestamp}] {symbols.get(status, 'ℹ️')} {message}")

def check_git_status():
    """Verify git branch and status."""
    print_status("Checking git status...")
    try:
        # Check current branch
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True, check=True)
        branch = result.stdout.strip()
        
        if branch == "pydev":
            print_status(f"On correct branch: {branch}", "SUCCESS")
        else:
            print_status(f"Warning: On branch '{branch}', expected 'pydev'", "WARNING")
        
        # Check status
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        if result.stdout.strip():
            print_status("Uncommitted changes detected", "WARNING")
            print(f"    {result.stdout.strip()}")
        else:
            print_status("Git working directory clean", "SUCCESS")
            
    except subprocess.CalledProcessError as e:
        print_status(f"Git command failed: {e}", "ERROR")

def check_file_structure():
    """Verify all required files exist."""
    print_status("Checking file structure...")
    
    required_files = [
        "simple_content_models.py",
        "simple_resubmit_system.py", 
        "minimal_test_interface.py",
        "chromadb_mcp_server.py",
        "ENHANCED_SYSTEM_SUMMARY.md",
        "CHROMADB_INTEGRATION_NOTES.md",
        "NEW_SESSION_BRIEFING.md"
    ]
    
    missing_files = []
    for file in required_files:
        if Path(file).exists():
            print_status(f"Found: {file}", "SUCCESS")
        else:
            missing_files.append(file)
            print_status(f"Missing: {file}", "ERROR")
    
    if missing_files:
        print_status(f"Missing {len(missing_files)} required files", "ERROR")
        return False
    else:
        print_status("All required files present", "SUCCESS")
        return True

def check_content_models():
    """Test content models functionality."""
    print_status("Testing content models...")
    try:
        from simple_content_models import (
            ContentItem, ProcessingParameters, create_text_content, 
            get_available_engines
        )
        
        # Test content creation
        content = create_text_content("Test content", "Test Title")
        print_status(f"Content created with ID: {content.id[:8]}...", "SUCCESS")
        
        # Test engine compatibility
        engines = get_available_engines(content)
        print_status(f"Available engines for text: {engines}", "SUCCESS")
        
        return True
        
    except Exception as e:
        print_status(f"Content models test failed: {e}", "ERROR")
        return False

def check_resubmit_system():
    """Test resubmit system functionality."""
    print_status("Testing resubmit system...")
    try:
        from simple_resubmit_system import get_registry, get_processor
        from simple_content_models import create_text_content, ProcessingParameters, ResubmitRequest
        
        # Test registry
        registry = get_registry()
        print_status(f"Content registry loaded, {len(registry.content_items)} items", "SUCCESS")
        
        # Test processor
        processor = get_processor()
        print_status("Resubmit processor initialized", "SUCCESS")
        
        # Test with sample content
        sample_content = create_text_content("Sample for testing", "Test Sample")
        content_id = registry.register_content(sample_content)
        print_status(f"Sample content registered: {content_id[:8]}...", "SUCCESS")
        
        # Test resubmit workflow
        request = ResubmitRequest(
            content_id=content_id,
            target_engine="projection",
            parameters=ProcessingParameters(persona="test", namespace="test-realm")
        )
        
        output = processor.process_resubmit(request)
        print_status(f"Resubmit test successful, output in: {output.output_directory}", "SUCCESS")
        
        return True
        
    except Exception as e:
        print_status(f"Resubmit system test failed: {e}", "ERROR")
        return False

def check_chromadb_availability():
    """Check if ChromaDB is available."""
    print_status("Checking ChromaDB availability...")
    try:
        import chromadb
        print_status("ChromaDB module available", "SUCCESS")
        
        # Test basic functionality
        client = chromadb.Client()
        collection = client.create_collection("test_collection")
        collection.add(
            documents=["test document"],
            metadatas=[{"test": "metadata"}],
            ids=["test_id"]
        )
        print_status("ChromaDB basic functionality working", "SUCCESS")
        return True
        
    except ImportError:
        print_status("ChromaDB not installed - install with: pip install chromadb", "WARNING")
        return False
    except Exception as e:
        print_status(f"ChromaDB test failed: {e}", "ERROR")
        return False

def check_web_interface(port=8090):
    """Check if web interface can start."""
    print_status(f"Checking web interface (port {port})...")
    
    # Check if port is available
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        result = s.connect_ex(('localhost', port))
        if result == 0:
            print_status(f"Port {port} is already in use", "WARNING")
            
            # Try to get response
            try:
                response = requests.get(f"http://localhost:{port}/", timeout=5)
                if response.status_code == 200:
                    print_status(f"Interface already running at http://localhost:{port}", "SUCCESS")
                    return True
            except:
                print_status(f"Port {port} occupied by non-HTTP service", "WARNING")
                return False
        else:
            print_status(f"Port {port} available", "SUCCESS")
            return True

def check_output_directories():
    """Check output directory structure."""
    print_status("Checking output directories...")
    
    base_path = Path.home() / ".lpe" / "content"
    outputs_path = base_path / "outputs"
    
    if base_path.exists():
        print_status(f"Base directory exists: {base_path}", "SUCCESS")
    else:
        print_status(f"Base directory will be created: {base_path}", "INFO")
    
    if outputs_path.exists():
        output_dirs = list(outputs_path.glob("*"))
        print_status(f"Found {len(output_dirs)} existing output directories", "INFO")
        
        # Show most recent
        if output_dirs:
            recent = max(output_dirs, key=lambda p: p.stat().st_mtime)
            print_status(f"Most recent output: {recent.name}", "INFO")
    
    return True

def run_full_verification():
    """Run complete system verification."""
    print("🔮 LPE Enhanced System Verification")
    print("=" * 50)
    
    checks = [
        ("Git Status", check_git_status),
        ("File Structure", check_file_structure),
        ("Content Models", check_content_models),
        ("Resubmit System", check_resubmit_system),
        ("ChromaDB Availability", check_chromadb_availability),
        ("Web Interface", check_web_interface),
        ("Output Directories", check_output_directories)
    ]
    
    results = {}
    for name, check_func in checks:
        print(f"\n🔍 {name}")
        print("-" * 30)
        try:
            results[name] = check_func()
        except Exception as e:
            print_status(f"Unexpected error in {name}: {e}", "ERROR")
            results[name] = False
    
    # Summary
    print("\n📊 Verification Summary")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result is True)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL" if result is False else "⚠️ WARN"
        print(f"{status} {name}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print_status("🎉 All systems operational!", "SUCCESS")
        print("\nNext steps:")
        print("1. Start the interface: python minimal_test_interface.py")
        print("2. Open browser: http://localhost:8090")
        print("3. Create test content and try resubmit workflow")
        if not results.get("ChromaDB Availability"):
            print("4. Optional: Install ChromaDB for semantic search: pip install chromadb")
    else:
        print_status("⚠️ Some issues detected - check output above", "WARNING")
    
    return passed == total

if __name__ == "__main__":
    success = run_full_verification()
    sys.exit(0 if success else 1)