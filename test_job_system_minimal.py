#!/usr/bin/env python3
"""Test the job management system with minimal dependencies."""
import sys
import asyncio
import os
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

# Mock the config import to avoid pydantic dependency
sys.modules['lamish_projection_engine.utils.config'] = __import__('simple_config')

# Force mock LLM to avoid Ollama dependency issues  
os.environ['LPE_USE_MOCK_LLM'] = 'true'

from lamish_projection_engine.core.jobs import get_job_manager, JobType, JobStatus

async def test_basic_job_creation():
    """Test basic job creation and storage."""
    print("Testing Basic Job Management\n")
    
    job_manager = get_job_manager()
    
    # Test 1: Create a simple job
    print("1. Creating a test job...")
    try:
        job_id = job_manager.create_job(
            JobType.PROJECTION,
            "Test Projection Job",
            "Testing job creation and storage",
            {"narrative": "Test narrative", "persona": "test"}
        )
        print(f"   ✓ Created job: {job_id}")
        
        # Test 2: Retrieve the job
        job = job_manager.get_job(job_id)
        if job:
            print(f"   ✓ Retrieved job: {job.title}")
            print(f"   Status: {job.status.value}")
            print(f"   Type: {job.type.value}")
        else:
            print("   ✗ Failed to retrieve job")
        
        # Test 3: Update progress
        print("2. Testing progress updates...")
        job_manager.update_progress(job_id, "Processing", 1, 3, "Starting work")
        job = job_manager.get_job(job_id)
        if job and job.progress:
            print(f"   ✓ Progress updated: {job.progress.current_step} ({job.progress.percentage:.1f}%)")
        
        job_manager.update_progress(job_id, "Halfway done", 2, 3, "Making progress")
        job = job_manager.get_job(job_id)
        if job and job.progress:
            print(f"   ✓ Progress updated: {job.progress.current_step} ({job.progress.percentage:.1f}%)")
        
        # Test 4: Complete job
        print("3. Testing job completion...")
        job_manager.complete_job(job_id, {"result": "Test completed successfully"})
        job = job_manager.get_job(job_id)
        if job:
            print(f"   ✓ Job completed: {job.status.value}")
            print(f"   Result: {job.result_data}")
        
        # Test 5: List jobs
        print("4. Testing job listing...")
        jobs = job_manager.list_jobs(limit=5)
        print(f"   Found {len(jobs)} jobs in database")
        for j in jobs:
            print(f"   - {j.id[:8]}... | {j.type.value} | {j.status.value}")
            
    except Exception as e:
        import traceback
        print(f"   ✗ Error: {e}")
        traceback.print_exc()
    
    print("\n✓ Basic job system test complete!")

def main():
    """Run the test."""
    asyncio.run(test_basic_job_creation())

if __name__ == "__main__":
    main()