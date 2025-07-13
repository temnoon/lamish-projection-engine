"""FastAPI web application for LPE."""
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from lamish_projection_engine.config.dynamic_attributes import (
    ConfigurationManager, PersonaAttribute, NamespaceAttribute, LanguageStyleAttribute
)
from lamish_projection_engine.core.projection import TranslationChain, ProjectionEngine
from lamish_projection_engine.core.maieutic import MaieuticDialogue, DialogueTurn
from lamish_projection_engine.core.translation_roundtrip import LanguageRoundTripAnalyzer
from lamish_projection_engine.core.jobs import get_job_manager, JobStatus
from lamish_projection_engine.core.job_workers import projection_worker, translation_worker, maieutic_worker
from lamish_projection_engine.web.websockets import websocket_endpoint, setup_job_callbacks
from lamish_projection_engine.utils.config import get_config

logger = logging.getLogger(__name__)

# Global state
config_manager: Optional[ConfigurationManager] = None
projection_engine: Optional[ProjectionEngine] = None
round_trip_analyzer: Optional[LanguageRoundTripAnalyzer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup for the FastAPI app."""
    global config_manager, projection_engine, round_trip_analyzer
    
    # Initialize components
    config_manager = ConfigurationManager()
    projection_engine = ProjectionEngine()
    round_trip_analyzer = LanguageRoundTripAnalyzer()
    
    # Setup job callbacks for WebSocket notifications
    setup_job_callbacks()
    
    logger.info("LPE Web Application initialized")
    yield
    
    # Cleanup
    if config_manager:
        config_manager.save_all_configurations()
    logger.info("LPE Web Application shutdown")


app = FastAPI(
    title="Lamish Projection Engine",
    description="AI-powered allegorical narrative transformation system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API requests
class ProjectionRequest(BaseModel):
    narrative: str
    persona: Optional[str] = None
    namespace: Optional[str] = None
    style: Optional[str] = None
    show_steps: bool = True


class MaieuticRequest(BaseModel):
    narrative: str
    goal: str = "understand"
    max_turns: int = 5


class AttributeUpdateRequest(BaseModel):
    field_name: str
    value: Any
    updated_by: str = "user"


class FieldGenerationRequest(BaseModel):
    field_name: str
    prompt_template: str
    context: Optional[Dict[str, Any]] = None


class RoundTripRequest(BaseModel):
    text: str
    intermediate_language: str
    source_language: str = "english"


# Dependency to get configuration manager
def get_config_manager() -> ConfigurationManager:
    if config_manager is None:
        raise HTTPException(status_code=500, detail="Configuration manager not initialized")
    return config_manager


def get_projection_engine() -> ProjectionEngine:
    if projection_engine is None:
        raise HTTPException(status_code=500, detail="Projection engine not initialized")
    return projection_engine


def get_round_trip_analyzer() -> LanguageRoundTripAnalyzer:
    if round_trip_analyzer is None:
        raise HTTPException(status_code=500, detail="Round-trip analyzer not initialized")
    return round_trip_analyzer


# Configuration Management Routes
@app.get("/api/config")
async def get_configuration(cm: ConfigurationManager = Depends(get_config_manager)):
    """Get all configuration attributes."""
    return cm.to_dict()


@app.get("/api/config/{attribute_name}")
async def get_attribute_config(attribute_name: str, 
                              cm: ConfigurationManager = Depends(get_config_manager)):
    """Get configuration for a specific attribute."""
    attribute = cm.get_attribute(attribute_name)
    if not attribute:
        raise HTTPException(status_code=404, detail=f"Attribute '{attribute_name}' not found")
    return attribute.to_dict()


@app.put("/api/config/{attribute_name}/{field_name}")
async def update_attribute_field(attribute_name: str, field_name: str, 
                                request: AttributeUpdateRequest,
                                cm: ConfigurationManager = Depends(get_config_manager)):
    """Update a field in an attribute."""
    attribute = cm.get_attribute(attribute_name)
    if not attribute:
        raise HTTPException(status_code=404, detail=f"Attribute '{attribute_name}' not found")
    
    attribute.update_field(field_name, request.value, request.updated_by)
    attribute.save_config()
    
    return {"success": True, "message": f"Updated {field_name} in {attribute_name}"}


@app.post("/api/config/{attribute_name}/generate-field")
async def generate_field_with_ai(attribute_name: str,
                                request: FieldGenerationRequest,
                                background_tasks: BackgroundTasks,
                                cm: ConfigurationManager = Depends(get_config_manager)):
    """Generate a field value using AI."""
    attribute = cm.get_attribute(attribute_name)
    if not attribute:
        raise HTTPException(status_code=404, detail=f"Attribute '{attribute_name}' not found")
    
    # Run generation in background
    background_tasks.add_task(
        attribute.generate_field_with_ai,
        request.field_name,
        request.prompt_template,
        request.context
    )
    
    return {"success": True, "message": f"Generating field '{request.field_name}' with AI"}


@app.get("/api/config/system-prompt")
async def get_system_prompt(context: Optional[str] = None,
                           cm: ConfigurationManager = Depends(get_config_manager)):
    """Get the generated system prompt."""
    context_dict = {}
    if context:
        try:
            context_dict = json.loads(context)
        except json.JSONDecodeError:
            context_dict = {"narrative_topic": context}
    
    prompt = cm.generate_system_prompt(context_dict)
    return {"system_prompt": prompt, "context": context_dict}


# Projection Routes
@app.post("/api/projection/create")
async def create_projection(request: ProjectionRequest,
                           pe: ProjectionEngine = Depends(get_projection_engine),
                           cm: ConfigurationManager = Depends(get_config_manager)):
    """Create a new allegorical projection."""
    try:
        # Use configuration manager to get current settings
        persona_attr = cm.get_attribute("persona")
        namespace_attr = cm.get_attribute("namespace")
        style_attr = cm.get_attribute("language_style")
        
        persona = request.persona or persona_attr.fields.get("base_type", {}).value if persona_attr else "neutral"
        namespace = request.namespace or namespace_attr.fields.get("base_setting", {}).value if namespace_attr else "lamish-galaxy"
        style = request.style or style_attr.fields.get("base_style", {}).value if style_attr else "standard"
        
        projection = pe.create_projection(
            request.narrative,
            persona,
            namespace,
            style,
            request.show_steps
        )
        
        return projection.to_dict()
        
    except Exception as e:
        logger.error(f"Projection creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projection/{projection_id}")
async def get_projection(projection_id: int,
                        pe: ProjectionEngine = Depends(get_projection_engine)):
    """Get a specific projection."""
    projection = pe.get_projection(projection_id)
    if not projection:
        raise HTTPException(status_code=404, detail="Projection not found")
    return projection.to_dict()


@app.get("/api/projections/search")
async def search_projections(query: str, limit: int = 10,
                            pe: ProjectionEngine = Depends(get_projection_engine)):
    """Search projections by content."""
    projections = pe.search_projections(query, limit)
    return [p.to_dict() for p in projections]


# Maieutic Dialogue Routes
@app.post("/api/maieutic/start")
async def start_maieutic_session(request: MaieuticRequest):
    """Start a new maieutic dialogue session as a background job."""
    try:
        job_id = await maieutic_worker.create_maieutic_job(
            request.narrative,
            request.goal,
            request.max_turns
        )
        
        return {
            "job_id": job_id,
            "message": "Maieutic dialogue job started",
            "status": "pending"
        }
        
    except Exception as e:
        logger.error(f"Failed to start maieutic job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/maieutic/{session_id}/question")
async def generate_maieutic_question(session_id: int, depth_level: int = 0):
    """Generate a maieutic question for a session."""
    # In a real implementation, retrieve session from database
    dialogue = MaieuticDialogue()
    question = dialogue.generate_question(depth_level)
    
    return {"question": question, "depth_level": depth_level}


# Round-trip Translation Routes
@app.post("/api/translation/round-trip")
async def perform_round_trip(request: RoundTripRequest):
    """Perform round-trip translation analysis as a background job."""
    try:
        job_id = await translation_worker.create_translation_job(
            request.text,
            request.intermediate_language,
            request.source_language
        )
        
        return {
            "job_id": job_id,
            "message": "Translation analysis job started",
            "status": "pending"
        }
        
    except Exception as e:
        logger.error(f"Failed to start translation job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/translation/stability-analysis")
async def analyze_stability(text: str, languages: Optional[str] = None,
                           analyzer: LanguageRoundTripAnalyzer = Depends(get_round_trip_analyzer)):
    """Analyze semantic stability across multiple languages."""
    try:
        test_languages = None
        if languages:
            test_languages = languages.split(",")
        
        stable_core = analyzer.find_stable_meaning_core(text, test_languages)
        return stable_core
        
    except Exception as e:
        logger.error(f"Stability analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/translation/supported-languages")
async def get_supported_languages(analyzer: LanguageRoundTripAnalyzer = Depends(get_round_trip_analyzer)):
    """Get list of supported languages for translation."""
    return {"languages": analyzer.supported_languages}


# Health and Status Routes
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "LPE Web API is running"}


@app.get("/api/status")
async def get_status():
    """Get system status."""
    config = get_config()
    return {
        "version": "1.0.0",
        "llm_model": config.llm_model,
        "embedding_model": config.embedding_model,
        "use_mock_llm": config.use_mock_llm,
        "components": {
            "configuration_manager": config_manager is not None,
            "projection_engine": projection_engine is not None,
            "round_trip_analyzer": round_trip_analyzer is not None
        }
    }


# Static files and main page
@app.get("/", response_class=HTMLResponse)
async def main_page():
    """Serve the main web interface."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lamish Projection Engine</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    </head>
    <body>
        <div class="container-fluid">
            <div class="row">
                <!-- Header -->
                <div class="col-12 bg-primary text-white p-3">
                    <h1>Lamish Projection Engine</h1>
                    <p class="mb-0">AI-powered allegorical narrative transformation system</p>
                </div>
            </div>
            
            <div class="row">
                <!-- Sidebar -->
                <div class="col-md-3 bg-light p-3">
                    <nav class="nav flex-column">
                        <a class="nav-link active" href="#projection">Projection</a>
                        <a class="nav-link" href="#maieutic">Maieutic Dialogue</a>
                        <a class="nav-link" href="#translation">Round-trip Translation</a>
                        <a class="nav-link" href="#configuration">Configuration</a>
                    </nav>
                </div>
                
                <!-- Main Content -->
                <div class="col-md-9 p-3">
                    <!-- Projection Tab -->
                    <div id="projection" class="tab-content active">
                        <h2>Create Projection</h2>
                        <form id="projection-form">
                            <div class="mb-3">
                                <label for="narrative" class="form-label">Narrative Text</label>
                                <textarea class="form-control" id="narrative" rows="4" 
                                         placeholder="Enter the narrative to transform..."></textarea>
                            </div>
                            <div class="row">
                                <div class="col-md-4">
                                    <label for="persona" class="form-label">Persona</label>
                                    <select class="form-control" id="persona">
                                        <option value="">Use current configuration</option>
                                        <option value="neutral">Neutral</option>
                                        <option value="advocate">Advocate</option>
                                        <option value="critic">Critic</option>
                                        <option value="philosopher">Philosopher</option>
                                        <option value="storyteller">Storyteller</option>
                                    </select>
                                </div>
                                <div class="col-md-4">
                                    <label for="namespace" class="form-label">Namespace</label>
                                    <select class="form-control" id="namespace">
                                        <option value="">Use current configuration</option>
                                        <option value="lamish-galaxy">Lamish Galaxy</option>
                                        <option value="medieval-realm">Medieval Realm</option>
                                        <option value="corporate-dystopia">Corporate Dystopia</option>
                                        <option value="natural-world">Natural World</option>
                                    </select>
                                </div>
                                <div class="col-md-4">
                                    <label for="style" class="form-label">Style</label>
                                    <select class="form-control" id="style">
                                        <option value="">Use current configuration</option>
                                        <option value="standard">Standard</option>
                                        <option value="academic">Academic</option>
                                        <option value="poetic">Poetic</option>
                                        <option value="technical">Technical</option>
                                    </select>
                                </div>
                            </div>
                            <div class="mt-3">
                                <button type="submit" class="btn btn-primary">Create Projection</button>
                            </div>
                        </form>
                        
                        <div id="projection-result" class="mt-4" style="display: none;">
                            <h3>Projection Result</h3>
                            <div id="projection-content" class="border p-3 bg-light"></div>
                        </div>
                    </div>
                    
                    <!-- Configuration Tab -->
                    <div id="configuration" class="tab-content" style="display: none;">
                        <h2>Dynamic Configuration</h2>
                        <div id="config-content">
                            <p>Loading configuration...</p>
                        </div>
                    </div>
                    
                    <!-- Maieutic Tab -->
                    <div id="maieutic" class="tab-content" style="display: none;">
                        <h2>Maieutic (Socratic) Dialogue</h2>
                        <form id="maieutic-form">
                            <div class="mb-3">
                                <label for="maieutic-narrative" class="form-label">Narrative to Explore</label>
                                <textarea class="form-control" id="maieutic-narrative" rows="4" 
                                         placeholder="Enter the narrative you want to explore through Socratic questioning..."></textarea>
                            </div>
                            <div class="row">
                                <div class="col-md-6">
                                    <label for="dialogue-goal" class="form-label">Exploration Goal</label>
                                    <select class="form-control" id="dialogue-goal">
                                        <option value="understand">Understand</option>
                                        <option value="clarify">Clarify</option>
                                        <option value="discover">Discover</option>
                                        <option value="question">Question</option>
                                    </select>
                                </div>
                                <div class="col-md-6">
                                    <label for="max-turns" class="form-label">Maximum Turns</label>
                                    <select class="form-control" id="max-turns">
                                        <option value="3">3</option>
                                        <option value="5" selected>5</option>
                                        <option value="7">7</option>
                                        <option value="10">10</option>
                                    </select>
                                </div>
                            </div>
                            <div class="mt-3">
                                <button type="submit" class="btn btn-primary">Start Dialogue</button>
                            </div>
                        </form>
                        
                        <div id="maieutic-session" class="mt-4" style="display: none;">
                            <h3>Dialogue Session</h3>
                            <div id="dialogue-turns" class="mb-3"></div>
                            <div id="current-question" class="card mb-3" style="display: none;">
                                <div class="card-header">
                                    <h5>Question <span id="question-number"></span></h5>
                                </div>
                                <div class="card-body">
                                    <p id="question-text" class="card-text"></p>
                                    <div class="mb-3">
                                        <label for="answer-input" class="form-label">Your Response</label>
                                        <textarea class="form-control" id="answer-input" rows="3" 
                                                 placeholder="Reflect and respond to the question..."></textarea>
                                    </div>
                                    <button id="submit-answer" class="btn btn-success">Submit Answer</button>
                                    <button id="end-dialogue" class="btn btn-secondary ms-2">End Dialogue</button>
                                </div>
                            </div>
                            <div id="dialogue-complete" class="alert alert-success" style="display: none;">
                                <h4>Dialogue Complete!</h4>
                                <p>The Socratic exploration has revealed new insights about your narrative.</p>
                                <button id="create-projection" class="btn btn-primary">Create Allegorical Projection</button>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Translation Tab -->
                    <div id="translation" class="tab-content" style="display: none;">
                        <h2>Round-trip Translation Analysis</h2>
                        <form id="translation-form">
                            <div class="mb-3">
                                <label for="translation-text" class="form-label">Text to Analyze</label>
                                <textarea class="form-control" id="translation-text" rows="4" 
                                         placeholder="Enter text for round-trip analysis..."></textarea>
                            </div>
                            <div class="row">
                                <div class="col-md-6">
                                    <label for="intermediate-language" class="form-label">Intermediate Language</label>
                                    <select class="form-control" id="intermediate-language">
                                        <option value="spanish">Spanish</option>
                                        <option value="french">French</option>
                                        <option value="german">German</option>
                                        <option value="chinese">Chinese</option>
                                        <option value="arabic">Arabic</option>
                                    </select>
                                </div>
                            </div>
                            <div class="mt-3">
                                <button type="submit" class="btn btn-primary">Analyze Translation</button>
                            </div>
                        </form>
                        
                        <div id="translation-result" class="mt-4" style="display: none;">
                            <h3>Translation Analysis</h3>
                            <div id="translation-content" class="border p-3 bg-light"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // WebSocket connection for real-time updates
            let ws = null;
            let activeJobs = new Set();
            
            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws`;
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() {
                    console.log('WebSocket connected');
                };
                
                ws.onmessage = function(event) {
                    const message = JSON.parse(event.data);
                    handleWebSocketMessage(message);
                };
                
                ws.onclose = function() {
                    console.log('WebSocket disconnected');
                    setTimeout(connectWebSocket, 3000); // Reconnect after 3 seconds
                };
                
                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                };
            }
            
            function handleWebSocketMessage(message) {
                const { type, job_id, data, status, result_data, error_message } = message;
                
                if (type === 'progress') {
                    updateJobProgress(job_id, data);
                } else if (type === 'status') {
                    updateJobStatus(job_id, status, result_data, error_message);
                }
            }
            
            function watchJob(jobId) {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ type: 'watch', job_id: jobId }));
                    activeJobs.add(jobId);
                }
            }
            
            function updateJobProgress(jobId, progressData) {
                const progressElement = $(`#progress-${jobId}`);
                if (progressElement.length > 0) {
                    const { current_step, percentage, details } = progressData;
                    progressElement.find('.progress-bar').css('width', `${percentage}%`);
                    progressElement.find('.progress-text').text(`${current_step} (${percentage.toFixed(1)}%)`);
                    progressElement.find('.progress-details').text(details);
                }
            }
            
            function updateJobStatus(jobId, status, resultData, errorMessage) {
                const progressElement = $(`#progress-${jobId}`);
                
                if (status === 'completed' && resultData) {
                    progressElement.hide();
                    displayJobResult(jobId, resultData);
                    activeJobs.delete(jobId);
                } else if (status === 'failed') {
                    progressElement.find('.progress-text').text('Failed');
                    progressElement.find('.progress-details').text(errorMessage);
                    progressElement.addClass('bg-danger');
                    activeJobs.delete(jobId);
                }
            }
            
            function displayJobResult(jobId, resultData) {
                const resultElement = $(`#result-${jobId}`);
                
                if (jobId.includes('projection')) {
                    displayProjectionResult(resultElement, resultData);
                } else if (jobId.includes('translation')) {
                    displayTranslationResult(resultElement, resultData);
                } else if (jobId.includes('maieutic')) {
                    displayMaieuticResult(resultElement, resultData);
                }
                
                resultElement.show();
            }
            
            function displayProjectionResult(element, data) {
                element.html(`
                    <h4>Final Projection</h4>
                    <div class="border p-3 bg-light mb-3">${data.final_projection}</div>
                    <h4>Reflection</h4>
                    <div class="border p-3 bg-light mb-3">${data.reflection}</div>
                    <small class="text-muted">
                        Persona: ${data.persona} | 
                        Namespace: ${data.namespace} | 
                        Style: ${data.style}
                    </small>
                `);
            }
            
            function displayTranslationResult(element, data) {
                element.html(`
                    <h4>Original Text</h4>
                    <p>${data.original_text}</p>
                    <h4>Final Text (After Round-trip)</h4>
                    <p>${data.final_text}</p>
                    <h4>Analysis</h4>
                    <p><strong>Semantic Drift:</strong> ${(data.semantic_drift * 100).toFixed(1)}%</p>
                    <p><strong>Preserved Elements:</strong> ${data.preserved_elements.join(', ')}</p>
                    <p><strong>Lost Elements:</strong> ${data.lost_elements.join(', ')}</p>
                    <p><strong>Gained Elements:</strong> ${data.gained_elements.join(', ')}</p>
                `);
            }
            
            function displayMaieuticResult(element, data) {
                element.html(`
                    <h4>Dialogue Session Ready</h4>
                    <p>Prepared ${data.questions.length} Socratic questions for exploration.</p>
                    <div class="alert alert-info">
                        <strong>Goal:</strong> ${data.goal}<br>
                        <strong>Narrative:</strong> ${data.narrative.substring(0, 100)}...
                    </div>
                `);
            }
            
            function showProgress(containerId, jobId, title) {
                const progressHtml = `
                    <div id="progress-${jobId}" class="alert alert-info">
                        <h5>${title}</h5>
                        <div class="progress mb-2">
                            <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                        </div>
                        <div class="progress-text">Starting...</div>
                        <div class="progress-details text-muted"></div>
                    </div>
                    <div id="result-${jobId}" style="display: none;"></div>
                `;
                
                $(containerId).html(progressHtml).show();
            }
            
            // Simple tab navigation
            $('.nav-link').click(function(e) {
                e.preventDefault();
                $('.nav-link').removeClass('active');
                $('.tab-content').hide();
                $(this).addClass('active');
                $($(this).attr('href')).show();
            });
            
            // Projection form submission
            $('#projection-form').submit(function(e) {
                e.preventDefault();
                
                const data = {
                    narrative: $('#narrative').val(),
                    persona: $('#persona').val() || null,
                    namespace: $('#namespace').val() || null,
                    style: $('#style').val() || null,
                    show_steps: true
                };
                
                $.ajax({
                    url: '/api/projection/create',
                    method: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify(data),
                    success: function(result) {
                        const jobId = result.job_id;
                        showProgress('#projection-result', jobId, 'Creating Allegorical Projection');
                        watchJob(jobId);
                    },
                    error: function(xhr) {
                        alert('Error starting projection: ' + xhr.responseJSON.detail);
                    }
                });
            });
            
            // Maieutic form submission
            $('#maieutic-form').submit(function(e) {
                e.preventDefault();
                
                const data = {
                    narrative: $('#maieutic-narrative').val(),
                    goal: $('#dialogue-goal').val(),
                    max_turns: parseInt($('#max-turns').val())
                };
                
                $.ajax({
                    url: '/api/maieutic/start',
                    method: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify(data),
                    success: function(result) {
                        const jobId = result.job_id;
                        showProgress('#maieutic-session', jobId, 'Preparing Maieutic Dialogue');
                        watchJob(jobId);
                    },
                    error: function(xhr) {
                        alert('Error starting dialogue: ' + xhr.responseJSON.detail);
                    }
                });
            });
            
            // Translation form submission
            $('#translation-form').submit(function(e) {
                e.preventDefault();
                
                const data = {
                    text: $('#translation-text').val(),
                    intermediate_language: $('#intermediate-language').val(),
                    source_language: 'english'
                };
                
                $.ajax({
                    url: '/api/translation/round-trip',
                    method: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify(data),
                    success: function(result) {
                        const jobId = result.job_id;
                        showProgress('#translation-result', jobId, 'Analyzing Round-trip Translation');
                        watchJob(jobId);
                    },
                    error: function(xhr) {
                        alert('Error starting translation analysis: ' + xhr.responseJSON.detail);
                    }
                });
            });
            
            // Load configuration on startup
            function loadConfiguration() {
                $.get('/api/config', function(config) {
                    let html = '<div class="row">';
                    
                    for (const [name, attr] of Object.entries(config)) {
                        html += `<div class="col-md-4 mb-4">
                            <div class="card">
                                <div class="card-header">
                                    <h5>${name.charAt(0).toUpperCase() + name.slice(1)}</h5>
                                </div>
                                <div class="card-body">`;
                        
                        for (const [fieldName, field] of Object.entries(attr.fields)) {
                            html += `<div class="mb-2">
                                <label><strong>${fieldName}:</strong></label>
                                <p class="mb-1">${field.value}</p>
                                <small class="text-muted">${field.description}</small>
                            </div>`;
                        }
                        
                        html += `</div></div></div>`;
                    }
                    
                    html += '</div>';
                    $('#config-content').html(html);
                });
            }
            
            // Load configuration when page loads
            $(document).ready(function() {
                loadConfiguration();
                connectWebSocket();
            });
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)