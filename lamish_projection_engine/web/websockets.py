"""WebSocket handlers for real-time progress updates."""
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from lamish_projection_engine.core.jobs import get_job_manager, JobProgress

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for job progress updates."""
    
    def __init__(self):
        # job_id -> set of websockets
        self.job_connections: Dict[str, Set[WebSocket]] = {}
        # websocket -> set of job_ids being watched
        self.connection_jobs: Dict[WebSocket, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.connection_jobs[websocket] = set()
        logger.info("WebSocket connected")
    
    def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection."""
        if websocket in self.connection_jobs:
            # Remove from all job subscriptions
            job_ids = self.connection_jobs[websocket].copy()
            for job_id in job_ids:
                self.unwatch_job(websocket, job_id)
            
            # Remove the connection
            del self.connection_jobs[websocket]
        
        logger.info("WebSocket disconnected")
    
    def watch_job(self, websocket: WebSocket, job_id: str):
        """Subscribe a WebSocket to job progress updates."""
        # Add to job connections
        if job_id not in self.job_connections:
            self.job_connections[job_id] = set()
        self.job_connections[job_id].add(websocket)
        
        # Add to connection jobs
        if websocket in self.connection_jobs:
            self.connection_jobs[websocket].add(job_id)
        
        logger.info(f"WebSocket watching job {job_id}")
    
    def unwatch_job(self, websocket: WebSocket, job_id: str):
        """Unsubscribe a WebSocket from job progress updates."""
        # Remove from job connections
        if job_id in self.job_connections:
            self.job_connections[job_id].discard(websocket)
            if not self.job_connections[job_id]:
                del self.job_connections[job_id]
        
        # Remove from connection jobs
        if websocket in self.connection_jobs:
            self.connection_jobs[websocket].discard(job_id)
        
        logger.info(f"WebSocket stopped watching job {job_id}")
    
    async def send_job_progress(self, job_id: str, progress: JobProgress):
        """Send progress update to all connections watching this job."""
        if job_id not in self.job_connections:
            return
        
        message = {
            "type": "progress",
            "job_id": job_id,
            "data": progress.to_dict()
        }
        
        # Send to all connections watching this job
        disconnected = set()
        for websocket in self.job_connections[job_id].copy():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending progress to WebSocket: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected sockets
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def send_job_status(self, job_id: str, status: str, result_data=None, error_message=None):
        """Send job status update to all connections watching this job."""
        if job_id not in self.job_connections:
            return
        
        message = {
            "type": "status",
            "job_id": job_id,
            "status": status,
            "result_data": result_data,
            "error_message": error_message
        }
        
        # Send to all connections watching this job
        disconnected = set()
        for websocket in self.job_connections[job_id].copy():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending status to WebSocket: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected sockets
        for websocket in disconnected:
            self.disconnect(websocket)
        
        # Clean up job connections when job completes
        if status in ["completed", "failed", "cancelled"]:
            if job_id in self.job_connections:
                for websocket in self.job_connections[job_id].copy():
                    self.unwatch_job(websocket, job_id)


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for job progress updates."""
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "watch":
                job_id = message["job_id"]
                manager.watch_job(websocket, job_id)
                
                # Send current job status if available
                job_manager = get_job_manager()
                job = job_manager.get_job(job_id)
                if job:
                    status_message = {
                        "type": "status",
                        "job_id": job_id,
                        "status": job.status.value,
                        "result_data": job.result_data,
                        "error_message": job.error_message
                    }
                    await websocket.send_text(json.dumps(status_message))
                    
                    if job.progress:
                        progress_message = {
                            "type": "progress",
                            "job_id": job_id,
                            "data": job.progress.to_dict()
                        }
                        await websocket.send_text(json.dumps(progress_message))
            
            elif message["type"] == "unwatch":
                job_id = message["job_id"]
                manager.unwatch_job(websocket, job_id)
            
            elif message["type"] == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


def setup_job_callbacks():
    """Set up job manager callbacks for WebSocket notifications."""
    job_manager = get_job_manager()
    
    # Override the progress update method to send WebSocket notifications
    original_update_progress = job_manager.update_progress
    original_complete_job = job_manager.complete_job
    original_fail_job = job_manager.fail_job
    
    def notify_progress(job_id: str, current_step: str, completed_steps: int, 
                       total_steps: int, details: str = ""):
        original_update_progress(job_id, current_step, completed_steps, total_steps, details)
        job = job_manager.get_job(job_id)
        if job and job.progress:
            import asyncio
            # Run the async function in the event loop if available
            try:
                loop = asyncio.get_event_loop()
                asyncio.create_task(manager.send_job_progress(job_id, job.progress))
            except RuntimeError:
                # No event loop running, skip WebSocket notification
                pass
    
    def notify_completion(job_id: str, result_data: Dict):
        original_complete_job(job_id, result_data)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            asyncio.create_task(manager.send_job_status(job_id, "completed", result_data))
        except RuntimeError:
            pass
    
    def notify_failure(job_id: str, error_message: str):
        original_fail_job(job_id, error_message)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            asyncio.create_task(manager.send_job_status(job_id, "failed", error_message=error_message))
        except RuntimeError:
            pass
    
    # Override the methods
    job_manager.update_progress = notify_progress
    job_manager.complete_job = notify_completion
    job_manager.fail_job = notify_failure