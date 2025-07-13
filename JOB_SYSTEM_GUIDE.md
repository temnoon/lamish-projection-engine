# LPE Asynchronous Job System

## Overview

The Lamish Projection Engine now includes a comprehensive asynchronous job management system that allows long-running operations to execute in the background while providing real-time progress updates to users. This solves the issue of browser timeouts and provides a much better user experience.

## Key Features

### 1. **Persistent Job Storage**
- Jobs are stored in SQLite database (`~/.lpe/jobs.db`)
- Survives application restarts and browser disconnections
- Complete audit trail of all operations

### 2. **Real-time Progress Updates**
- WebSocket connections for live progress feeds
- Detailed step-by-step progress tracking
- Specific operation details at each stage

### 3. **Background Processing**
- All LLM operations run asynchronously
- Non-blocking web interface
- Multiple jobs can run concurrently

### 4. **Comprehensive Job Types**
- **Projection Jobs**: Allegorical narrative transformations
- **Translation Jobs**: Round-trip semantic analysis
- **Maieutic Jobs**: Socratic dialogue generation
- **Configuration Jobs**: Dynamic attribute generation

## Architecture

### Core Components

1. **Job Manager** (`core/jobs.py`)
   - Centralized job orchestration
   - Database persistence
   - Progress tracking
   - Job lifecycle management

2. **Job Workers** (`core/job_workers.py`)
   - Specialized workers for each operation type
   - Async execution with progress reporting
   - Error handling and recovery

3. **WebSocket Handler** (`web/websockets.py`)
   - Real-time job status updates
   - Client subscription management
   - Automatic reconnection support

4. **Updated Web Interface** (`web/app.py`)
   - Job-based API endpoints
   - Progress indicators
   - Live result display

## Usage Examples

### Starting a Projection Job

```javascript
// Frontend JavaScript
const response = await fetch('/api/projection/create', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        narrative: "Your narrative text here",
        persona: "philosopher",
        namespace: "lamish-galaxy",
        style: "academic"
    })
});

const {job_id} = await response.json();

// Watch for progress via WebSocket
ws.send(JSON.stringify({type: 'watch', job_id: job_id}));
```

### Progress Updates

The system provides detailed progress for each operation:

**Projection Progress Steps:**
1. Initializing configuration (16.7%)
2. Creating projection (33.3%)
3. Processing steps (50.0% - 83.3%)
4. Finalizing projection (100%)

**Translation Progress Steps:**
1. Initializing analysis (20%)
2. Forward translation (40%)
3. Backward translation (60%)
4. Analyzing semantic drift (80%)
5. Analysis complete (100%)

### Job Status Monitoring

```javascript
// WebSocket message handling
ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    
    if (message.type === 'progress') {
        // Update progress bar
        updateProgress(message.job_id, message.data);
    } else if (message.type === 'status') {
        // Handle completion/failure
        if (message.status === 'completed') {
            displayResult(message.job_id, message.result_data);
        }
    }
};
```

## Database Schema

The job system uses a comprehensive SQLite schema:

```sql
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,           -- UUID job identifier
    type TEXT NOT NULL,            -- projection|translation|maieutic
    status TEXT NOT NULL,          -- pending|running|completed|failed
    title TEXT NOT NULL,           -- Human-readable job title
    description TEXT,              -- Detailed description
    input_data TEXT,              -- JSON input parameters
    result_data TEXT,             -- JSON result data
    error_message TEXT,           -- Error details if failed
    progress TEXT,                -- JSON progress information
    created_at TEXT NOT NULL,     -- ISO timestamp
    started_at TEXT,              -- ISO timestamp
    completed_at TEXT             -- ISO timestamp
);
```

## Job Lifecycle

1. **Creation**: Job created with PENDING status
2. **Queuing**: Job added to background processing queue
3. **Execution**: Status changed to RUNNING, progress updates sent
4. **Completion**: Status changed to COMPLETED/FAILED, results stored

## API Endpoints

### Job Management
- `GET /api/jobs/{job_id}` - Get job status and results
- `GET /api/jobs` - List recent jobs
- `POST /api/jobs/{job_id}/cancel` - Cancel running job

### Operation Endpoints (all return job_id)
- `POST /api/projection/create` - Start projection job
- `POST /api/translation/round-trip` - Start translation job
- `POST /api/maieutic/start` - Start dialogue job

### WebSocket
- `WS /ws` - Real-time job updates

## Progress Tracking Details

Each job provides specific progress information:

### Projection Jobs
- Configuration loading
- LLM model initialization
- Deconstruction phase
- Mapping phase
- Reconstruction phase
- Stylization phase
- Reflection generation

### Translation Jobs
- Language model preparation
- Forward translation to intermediate language
- Backward translation to source language
- Semantic drift analysis
- Element preservation analysis

### Maieutic Jobs
- Session initialization
- Question generation (per depth level)
- Dialogue structure preparation
- Interactive session setup

## Error Handling

- Comprehensive error capture and storage
- Graceful fallback to mock LLM if needed
- Detailed error messages for debugging
- Automatic job cleanup on failure

## Performance Benefits

1. **Non-blocking Interface**: Users can continue using the application while jobs run
2. **Persistent Operations**: Jobs survive browser crashes and disconnections
3. **Progress Visibility**: Users know exactly what's happening and estimated completion
4. **Resource Management**: Background processing prevents browser memory issues
5. **Concurrent Operations**: Multiple jobs can run simultaneously

## Migration from Synchronous System

The new system is backward compatible. Old synchronous endpoints still work, but new job-based endpoints provide the enhanced experience. The web interface has been updated to use the job system by default.

## Future Enhancements

- Job priority queuing
- Scheduled job execution
- Job result caching
- Advanced error recovery
- Job dependency chains
- Performance metrics and analytics

This job system transforms the LPE from a simple request-response application into a sophisticated, production-ready platform capable of handling complex, long-running AI operations with full user visibility and control.