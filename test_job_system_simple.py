#!/usr/bin/env python3
"""Test the job management system."""
import sys
import asyncio
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from lamish_projection_engine.core.jobs import get_job_manager, JobType, JobStatus
from lamish_projection_engine.core.job_workers import projection_worker, translation_worker, maieutic_worker

async def test_job_system():
    """Test the job management system."""
    print("Testing Job Management System\n")
    
    job_manager = get_job_manager()
    
    # Test 1: Create a projection job
    print("1. Testing projection job creation...")
    try:
        job_id = await projection_worker.create_projection_job(
            "Sam Altman dropped out of Stanford to start a company.",
            persona="philosopher",
            namespace="lamish-galaxy", 
            style="academic"
        )
        print(f"   ✓ Created projection job: {job_id}")
        
        # Wait a bit and check job status
        await asyncio.sleep(2)
        job = job_manager.get_job(job_id)
        if job:
            print(f"   Status: {job.status.value}")
            if job.progress:
                print(f"   Progress: {job.progress.current_step} ({job.progress.percentage:.1f}%)")
        
        # Wait for completion
        print("   Waiting for completion...")
        for i in range(30):  # Wait up to 30 seconds
            await asyncio.sleep(1)
            job = job_manager.get_job(job_id)
            if job and job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                break
        
        if job.status == JobStatus.COMPLETED:
            print(f"   ✓ Job completed successfully")
            if job.result_data:
                final_projection = job.result_data.get('final_projection', '')
                print(f"   Result preview: {final_projection[:100]}...")
        else:
            print(f"   ✗ Job failed: {job.error_message}")
            
    except Exception as e:
        import traceback
        print(f"   ✗ Error: {e}")
        traceback.print_exc()
    
    print()
    
    # Test 2: List all jobs
    print("2. Listing recent jobs...")
    try:
        jobs = job_manager.list_jobs(limit=10)
        print(f"   Found {len(jobs)} jobs:")
        for job in jobs[:5]:  # Show first 5
            print(f"   - {job.id[:8]}... | {job.type.value} | {job.status.value} | {job.title}")
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n✓ Job system testing complete!")

def main():
    """Run the test."""
    asyncio.run(test_job_system())

if __name__ == "__main__":
    main()