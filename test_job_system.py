#!/usr/bin/env python3
"""Test the job management system."""
import sys
import asyncio
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from lamish_projection_engine.core.jobs import get_job_manager, JobType, JobStatus
from lamish_projection_engine.core.job_workers import projection_worker, translation_worker, maieutic_worker

console = Console()

async def test_job_system():
    """Test the job management system."""
    console.print("[bold cyan]Testing Job Management System[/bold cyan]\n")
    
    job_manager = get_job_manager()
    
    # Test 1: Create a projection job
    console.print("1. Testing projection job creation...")
    try:
        job_id = await projection_worker.create_projection_job(
            "Sam Altman dropped out of Stanford to start a company.",
            persona="philosopher",
            namespace="lamish-galaxy", 
            style="academic"
        )
        console.print(f"   [green]✓ Created projection job: {job_id}[/green]")
        
        # Wait a bit and check job status
        await asyncio.sleep(2)
        job = job_manager.get_job(job_id)
        if job:
            console.print(f"   Status: {job.status.value}")
            if job.progress:
                console.print(f"   Progress: {job.progress.current_step} ({job.progress.percentage:.1f}%)")
        
        # Wait for completion
        console.print("   Waiting for completion...")
        for i in range(30):  # Wait up to 30 seconds
            await asyncio.sleep(1)
            job = job_manager.get_job(job_id)
            if job and job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                break
        
        if job.status == JobStatus.COMPLETED:
            console.print(f"   [green]✓ Job completed successfully[/green]")
            if job.result_data:
                final_projection = job.result_data.get('final_projection', '')
                console.print(f"   Result preview: {final_projection[:100]}...")
        else:
            console.print(f"   [red]✗ Job failed: {job.error_message}[/red]")
            
    except Exception as e:
        console.print(f"   [red]✗ Error: {e}[/red]")
    
    console.print()
    
    # Test 2: Create a translation job
    console.print("2. Testing translation job creation...")
    try:
        job_id = await translation_worker.create_translation_job(
            "Innovation drives progress in technology.",
            "spanish"
        )
        console.print(f"   [green]✓ Created translation job: {job_id}[/green]")
        
        # Wait for completion
        console.print("   Waiting for completion...")
        for i in range(20):  # Wait up to 20 seconds
            await asyncio.sleep(1)
            job = job_manager.get_job(job_id)
            if job and job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                break
        
        if job.status == JobStatus.COMPLETED:
            console.print(f"   [green]✓ Job completed successfully[/green]")
            if job.result_data:
                drift = job.result_data.get('semantic_drift', 0)
                console.print(f"   Semantic drift: {drift:.1%}")
        else:
            console.print(f"   [red]✗ Job failed: {job.error_message}[/red]")
            
    except Exception as e:
        console.print(f"   [red]✗ Error: {e}[/red]")
    
    console.print()
    
    # Test 3: List all jobs
    console.print("3. Listing recent jobs...")
    try:
        jobs = job_manager.list_jobs(limit=10)
        console.print(f"   Found {len(jobs)} jobs:")
        for job in jobs[:5]:  # Show first 5
            console.print(f"   - {job.id[:8]}... | {job.type.value} | {job.status.value} | {job.title}")
            
    except Exception as e:
        console.print(f"   [red]✗ Error: {e}[/red]")
    
    console.print("\n[bold green]✓ Job system testing complete![/bold green]")

def main():
    """Run the test."""
    asyncio.run(test_job_system())

if __name__ == "__main__":
    main()