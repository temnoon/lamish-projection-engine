#!/usr/bin/env python3
"""LPE Interface with immediate processing and real results - Port 8000."""
import sys
import os
import json
import http.server
import socketserver
from pathlib import Path
from urllib.parse import urlparse
import time

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

# Mock the config import
sys.modules['lamish_projection_engine.utils.config'] = __import__('simple_config')

# Use real LLM, not mock
os.environ['LPE_USE_MOCK_LLM'] = 'false'

# Import enhanced job manager
from enhanced_job_manager import EnhancedJobManager, JobType

# Import unified LLM manager and language config
from llm_providers import llm_manager
from language_config import LANGUAGE_HIERARCHY, generate_language_select_html, get_language_name

# Enhanced LLM class with multi-provider support  
class SimpleLLM:
    def __init__(self):
        # Use unified LLM manager
        self.manager = llm_manager
        
        # Load configuration 
        self.load_llm_config()
        
        # Set current provider and model
        self.current_provider = self.llm_config.get('provider', self.manager.default_provider)
        self.current_model = self.llm_config.get('model')
        self.temperature = self.llm_config.get('temperature', 0.7)
        self.max_tokens = self.llm_config.get('max_tokens', 4096)
        
        # Check availability
        available_providers = self.manager.get_available_providers()
        self.available = available_providers.get(self.current_provider, False)
        
        print(f"LLM Providers available: {[k for k, v in available_providers.items() if v]}")
        print(f"Current provider: {self.current_provider}")
        print(f"LLM Available: {self.available}")
        
        # Backward compatibility properties
        self.model = self.current_model
        self.base_url = "http://localhost:11434"  # For Ollama compatibility
    
    def load_llm_config(self):
        """Load LLM configuration from multi-provider admin interface."""
        # Try new multi-provider config first
        multi_config_file = Path.home() / ".lpe" / "multi_llm_config.json"
        legacy_config_file = Path.home() / ".lpe" / "llm_config.json"
        
        default_config = {
            "provider": "ollama",
            "model": "llama3.2:latest",
            "temperature": 0.7,
            "max_tokens": 4096,
            "timeout": 120
        }
        
        # Load multi-provider config if available
        if multi_config_file.exists():
            try:
                with open(multi_config_file, 'r') as f:
                    multi_config = json.load(f)
                    provider = multi_config.get("default_provider", "ollama")
                    provider_settings = multi_config.get("provider_settings", {}).get(provider, {})
                    
                    self.llm_config = {
                        "provider": provider,
                        "model": provider_settings.get("default_model"),
                        "temperature": provider_settings.get("temperature", 0.7),
                        "max_tokens": provider_settings.get("max_tokens", 4096),
                        "timeout": provider_settings.get("timeout", 120)
                    }
                    return
            except:
                pass
        
        # Fallback to legacy config
        if legacy_config_file.exists():
            try:
                with open(legacy_config_file, 'r') as f:
                    legacy_config = json.load(f)
                    self.llm_config = {
                        "provider": "ollama",
                        "model": legacy_config.get("llm_model", "llama3.2:latest"),
                        "temperature": legacy_config.get("temperature", 0.7),
                        "max_tokens": legacy_config.get("max_tokens", 4096),
                        "timeout": legacy_config.get("timeout", 120)
                    }
                    return
            except:
                pass
        
        self.llm_config = default_config
    
    def _generate_request(self, model: str, prompt: str):
        """Generate text using the unified LLM manager."""
        try:
            return self.manager.generate_text(
                prompt, 
                provider=self.current_provider,
                model=model or self.current_model,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
        except Exception as e:
            # Fallback to any available provider
            available = self.manager.get_available_providers()
            for provider_name, is_available in available.items():
                if is_available and provider_name != self.current_provider:
                    try:
                        return self.manager.generate_text(
                            prompt,
                            provider=provider_name,
                            temperature=self.temperature,
                            max_tokens=self.max_tokens
                        )
                    except:
                        continue
            raise e
    
    def generate_projection(self, narrative: str, persona: str = "philosopher", 
                          namespace: str = "lamish-galaxy", style: str = "academic"):
        """Generate an allegorical projection immediately."""
        if not self.available:
            return {
                "final_projection": f"[DEMO] In the {namespace}, a {persona} would say: This narrative about '{narrative[:50]}...' reveals the deeper patterns of transformation and growth that transcend specific contexts.",
                "reflection": f"[DEMO] This projection demonstrates how {namespace} provides a lens for understanding universal themes through the {persona} perspective.",
                "persona": persona,
                "namespace": namespace,
                "style": style
            }
        
        try:
            # Use direct Ollama connection
            system_prompt = f"""You are a {persona} creating an allegorical projection into the {namespace} universe.
Transform the given narrative while preserving its core meaning. Use {style} style."""
            
            projection_prompt = f"""Transform this narrative into the {namespace}: {narrative}

Create an allegorical version that preserves the essential meaning while translating it into the {namespace} context."""
            
            # Generate projection
            full_prompt = f"{system_prompt}\n\n{projection_prompt}"
            projection = self._generate_request(self.model, full_prompt)
            
            # Generate reflection
            reflection_prompt = f"""As a {persona} reflecting on allegorical transformations:

Reflect on this {namespace} transformation: {projection}

Explain how this {namespace} version illuminates the original narrative about: {narrative}"""
            
            reflection = self._generate_request(self.model, reflection_prompt)
            
            return {
                "final_projection": projection,
                "reflection": reflection,
                "persona": persona,
                "namespace": namespace,
                "style": style
            }
        except Exception as e:
            return {
                "final_projection": f"Error generating projection: {str(e)}",
                "reflection": "Processing failed - please check LLM connection",
                "persona": persona,
                "namespace": namespace,
                "style": style
            }
    
    def generate_translation_analysis(self, text: str, intermediate_language: str):
        """Generate round-trip translation analysis immediately.""" 
        if not self.available:
            return {
                "original_text": text,
                "final_text": f"[DEMO] Round-trip result of '{text}' via {intermediate_language}",
                "semantic_drift": 0.15,
                "preserved_elements": ["core meaning", "key concepts"],
                "lost_elements": ["nuanced phrasing"],
                "gained_elements": ["cultural context"],
                "analysis": f"[DEMO] Translation through {intermediate_language} preserves main meaning with minor drift."
            }
        
        try:
            # Forward translation using direct generate API
            forward_prompt = f"You are a professional translator. Translate this text to {intermediate_language}: {text}"
            forward_result = self._generate_request(self.model, forward_prompt)
            
            # Backward translation using direct generate API
            backward_prompt = f"You are a professional translator. Translate this {intermediate_language} text back to English: {forward_result}"
            backward_result = self._generate_request(self.model, backward_prompt)
            
            # Analysis using direct generate API
            analysis_prompt = f"""You are a linguistic analyst. Compare these texts for semantic drift:
Original: {text}
After round-trip: {backward_result}

Analyze what was preserved, lost, or gained in the translation."""
            analysis = self._generate_request(self.model, analysis_prompt)
            
            return {
                "original_text": text,
                "final_text": backward_result,
                "intermediate_text": forward_result,
                "semantic_drift": 0.2,  # Could calculate this more precisely
                "preserved_elements": ["main concepts"],
                "lost_elements": ["subtle nuances"], 
                "gained_elements": ["linguistic variations"],
                "analysis": analysis
            }
        except Exception as e:
            return {
                "original_text": text,
                "final_text": f"Translation error: {str(e)}",
                "analysis": "Translation failed - please check LLM connection"
            }
    
    def generate_maieutic_dialogue(self, narrative: str, goal: str = "understand", max_turns: int = 5):
        """Generate Socratic questions immediately."""
        if not self.available:
            questions = [
                f"What do you think is the central assumption in '{narrative[:30]}...'?",
                f"How might someone with a different perspective view this?", 
                f"What evidence supports the main claim here?",
                f"What would be the implications if this assumption were false?",
                f"How does this connect to broader patterns you've observed?"
            ]
            return {
                "questions": questions[:max_turns],
                "goal": goal,
                "narrative": narrative
            }
        
        try:
            system_prompt = f"""You are a Socratic questioner. Your goal is to help {goal} the given narrative through thoughtful questions.
Generate {max_turns} increasingly deep questions that probe assumptions, implications, and connections."""
            
            prompt = f"""Generate {max_turns} Socratic questions about this narrative: {narrative}

Each question should probe deeper than the last, helping to {goal} the underlying assumptions and implications."""
            
            # Use direct generate API call
            full_prompt = f"{system_prompt}\n\n{prompt}"
            response = self._generate_request(self.model, full_prompt)
            
            # Parse questions from response (simple splitting)
            questions = [q.strip() for q in response.split('\n') if q.strip() and ('?' in q)]
            
            return {
                "questions": questions[:max_turns],
                "goal": goal,
                "narrative": narrative,
                "full_response": response
            }
        except Exception as e:
            return {
                "questions": [f"Error generating questions: {str(e)}"],
                "goal": goal,
                "narrative": narrative
            }
    
    def generate_namespace_suggestions(self, prompt: str):
        """Generate namespace suggestions based on user prompt."""
        if not self.available:
            return [
                {"name": "cyber-matrix", "description": "Digital realm of interconnected systems and data flows"},
                {"name": "ancient-grove", "description": "Mystical forest where old wisdom meets new growth"},
                {"name": "stellar-forge", "description": "Cosmic workshop where stars and destinies are crafted"}
            ]
        
        try:
            system_prompt = """You are a creative worldbuilder. Generate 3-5 unique fictional namespace suggestions based on the user's prompt.
Return as a JSON array with objects containing 'name' and 'description' fields."""
            
            generation_prompt = f"""Generate namespace suggestions based on: '{prompt}'

Return only the JSON array, no other text."""
            
            full_prompt = f"{system_prompt}\n\n{generation_prompt}"
            response = self._generate_request(self.model, full_prompt)
            
            # Try to parse JSON response
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                suggestions_json = json_match.group(0)
                suggestions = json.loads(suggestions_json)
                return suggestions
            else:
                # Fallback
                return [{"name": "custom-realm", "description": "A unique universe tailored to your narrative needs"}]
                
        except Exception as e:
            print(f"Error generating namespace suggestions: {e}")
            return [{"name": "custom-realm", "description": "A unique universe tailored to your narrative needs"}]
    
    def generate_persona_suggestions(self, prompt: str):
        """Generate persona suggestions based on user prompt."""
        if not self.available:
            return [
                {"name": "sage-observer", "description": "Wise commentator who sees patterns across time and space"},
                {"name": "skeptical-analyst", "description": "Critical thinker who questions assumptions and seeks evidence"},
                {"name": "empathetic-guide", "description": "Understanding mentor who helps others discover their own truths"}
            ]
        
        try:
            system_prompt = """You are a character development expert. Generate 3-5 unique persona suggestions based on the user's prompt.
Return as a JSON array with objects containing 'name' and 'description' fields."""
            
            generation_prompt = f"""Generate persona suggestions based on: '{prompt}'

Return only the JSON array, no other text."""
            
            full_prompt = f"{system_prompt}\n\n{generation_prompt}"
            response = self._generate_request(self.model, full_prompt)
            
            # Try to parse JSON response
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                suggestions_json = json_match.group(0)
                suggestions = json.loads(suggestions_json)
                return suggestions
            else:
                # Fallback
                return [{"name": "thoughtful-explorer", "description": "Curious investigator who seeks deeper meaning in all narratives"}]
                
        except Exception as e:
            print(f"Error generating persona suggestions: {e}")
            return [{"name": "thoughtful-explorer", "description": "Curious investigator who seeks deeper meaning in all narratives"}]
    
    def synthesize_maieutic_dialogue(self, original_narrative: str, goal: str, qa_pairs: list):
        """Synthesize a revised narrative incorporating insights from Q&A dialogue."""
        if not self.available:
            return f"[DEMO] Revised narrative incorporating insights from {len(qa_pairs)} questions and answers about '{original_narrative[:50]}...'"
        
        try:
            # Format the Q&A pairs for the prompt
            qa_text = ""
            for i, qa in enumerate(qa_pairs, 1):
                qa_text += f"Q{i}: {qa['question']}\nA{i}: {qa['answer']}\n\n"
            
            synthesis_prompt = f"""You are a narrative synthesis expert. Your task is to revise an original narrative by incorporating insights from a Socratic dialogue.

ORIGINAL NARRATIVE:
{original_narrative}

DIALOGUE GOAL: {goal}

QUESTIONS AND ANSWERS:
{qa_text}

TASK: Create a revised version of the original narrative that incorporates the insights, clarifications, and deeper understanding revealed through the Q&A dialogue. The revised narrative should:
1. Maintain the core story and characters
2. Integrate the deeper insights from the answers
3. Address any clarifications or new perspectives that emerged
4. Be more nuanced and thoughtful than the original
5. Feel natural and cohesive, not forced

Return only the revised narrative, without explanations or meta-commentary."""
            
            revised_narrative = self._generate_request(self.current_model, synthesis_prompt)
            return revised_narrative.strip()
            
        except Exception as e:
            return f"Error synthesizing dialogue: {str(e)}"

# Initialize components
try:
    from enhanced_job_manager import enhanced_job_manager as job_manager
    print("✅ Using enhanced job manager with PostgreSQL support")
except ImportError:
    job_manager = EnhancedJobManager()
    print("⚠ Using simple SQLite job manager")

llm = SimpleLLM()

print("LPE Immediate Interface Starting...")
print(f"LLM Available: {llm.available}")
print("Available at: http://localhost:8000")

class ImmediateHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if urlparse(self.path).path == '/':
            self.serve_main_interface()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except:
            data = {}
        
        path = urlparse(self.path).path
        
        if path == '/api/projection/create':
            self.handle_projection_immediate(data)
        elif path == '/api/translation/round-trip':
            self.handle_translation_immediate(data)
        elif path == '/api/vision/analyze':
            self.handle_vision_immediate(data)
        elif path == '/api/maieutic/start':
            self.handle_maieutic_immediate(data)
        elif path == '/api/maieutic/synthesize':
            self.handle_maieutic_synthesis(data)
        elif path == '/api/generate/namespace':
            self.handle_namespace_generation(data)
        elif path == '/api/generate/persona':
            self.handle_persona_generation(data)
        else:
            self.send_response(404)
            self.end_headers()
    
    def handle_projection_immediate(self, data):
        """Process projection immediately and return results."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Process immediately
        result = llm.generate_projection(
            data.get('narrative', ''),
            data.get('persona', 'philosopher'),
            data.get('namespace', 'lamish-galaxy'),
            data.get('style', 'academic')
        )
        
        # Save to job history with enhanced features
        try:
            from enhanced_job_manager import JobType as EnhancedJobType
            job_id = job_manager.create_and_complete_job_sync(
                EnhancedJobType.PROJECTION,
                "Allegorical Projection",
                data,
                result
            )
        except (ImportError, AttributeError):
            job_id = job_manager.create_and_complete_job(
                JobType.PROJECTION,
                "Allegorical Projection",
                data,
                result
            )
        
        # Return immediate results
        response = {
            "success": True,
            "job_id": job_id,
            "result": result
        }
        
        self.wfile.write(json.dumps(response).encode())
    
    def handle_translation_immediate(self, data):
        """Process translation immediately and return results."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Process immediately
        result = llm.generate_translation_analysis(
            data.get('text', ''),
            data.get('intermediate_language', 'spanish')
        )
        
        # Save to job history with enhanced features
        try:
            from enhanced_job_manager import JobType as EnhancedJobType
            job_id = job_manager.create_and_complete_job_sync(
                EnhancedJobType.TRANSLATION,
                "Translation Analysis",
                data,
                result
            )
        except (ImportError, AttributeError):
            job_id = job_manager.create_and_complete_job(
                JobType.TRANSLATION,
                "Translation Analysis",
                data,
                result
            )
        
        # Return immediate results
        response = {
            "success": True,
            "job_id": job_id,
            "result": result
        }
        
        self.wfile.write(json.dumps(response).encode())
    
    def handle_vision_immediate(self, data):
        """Process vision analysis immediately and return results."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Extract data
        prompt = data.get('prompt', 'What do you see in this image?')
        model = data.get('model', 'gemini-pro-vision')
        image_data = data.get('image_data', '')
        
        # Process immediately using Google provider with vision
        try:
            google_provider = llm_manager.get_provider('google')
            if not google_provider or not google_provider.available:
                raise Exception("Google provider not available or API key not configured")
            
            if model not in google_provider.get_vision_models():
                raise Exception(f"Model {model} does not support vision")
            
            # Generate analysis
            analysis = google_provider.generate_text(
                prompt, 
                model=model, 
                image_data=image_data
            )
            
            result = {
                "analysis": analysis,
                "model": model,
                "prompt": prompt
            }
            
        except Exception as e:
            result = {
                "analysis": f"Vision analysis error: {str(e)}",
                "model": model,
                "prompt": prompt
            }
        
        # Save to job history
        try:
            from enhanced_job_manager import JobType as EnhancedJobType
            job_id = job_manager.create_and_complete_job_sync(
                EnhancedJobType.PROJECTION,  # Using projection type for now
                "Vision Analysis",
                data,
                result
            )
        except (ImportError, AttributeError):
            job_id = job_manager.create_and_complete_job(
                JobType.PROJECTION,
                "Vision Analysis", 
                data,
                result
            )
        
        # Return immediate results
        response = {
            "success": True,
            "job_id": job_id,
            "result": result
        }
        
        self.wfile.write(json.dumps(response).encode())
    
    def handle_maieutic_immediate(self, data):
        """Process maieutic dialogue immediately and return results."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Process immediately
        result = llm.generate_maieutic_dialogue(
            data.get('narrative', ''),
            data.get('goal', 'understand'),
            data.get('max_turns', 5)
        )
        
        # Save to job history with enhanced features
        try:
            from enhanced_job_manager import JobType as EnhancedJobType
            job_id = job_manager.create_and_complete_job_sync(
                EnhancedJobType.MAIEUTIC,
                "Maieutic Dialogue",
                data,
                result
            )
        except (ImportError, AttributeError):
            job_id = job_manager.create_and_complete_job(
                JobType.MAIEUTIC,
                "Maieutic Dialogue",
                data,
                result
            )
        
        # Return immediate results
        response = {
            "success": True,
            "job_id": job_id,
            "result": result
        }
        
        self.wfile.write(json.dumps(response).encode())
    
    def handle_maieutic_synthesis(self, data):
        """Synthesize a revised narrative from Q&A pairs."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Extract data
        original_narrative = data.get('original_narrative', '')
        goal = data.get('goal', 'understand')
        qa_pairs = data.get('qa_pairs', [])
        
        if not original_narrative or not qa_pairs:
            response = {"success": False, "error": "Missing narrative or Q&A pairs"}
            self.wfile.write(json.dumps(response).encode())
            return
        
        # Generate synthesis using LLM
        result = llm.synthesize_maieutic_dialogue(original_narrative, goal, qa_pairs)
        
        # Save to job history
        synthesis_data = {
            "original_narrative": original_narrative,
            "goal": goal,
            "qa_pairs": qa_pairs,
            "synthesis": result
        }
        
        try:
            from enhanced_job_manager import JobType as EnhancedJobType
            job_id = job_manager.create_and_complete_job_sync(
                EnhancedJobType.MAIEUTIC,
                "Maieutic Synthesis",
                data,
                {"revised_narrative": result, "synthesis": result}
            )
        except (ImportError, AttributeError):
            job_id = job_manager.create_and_complete_job(
                JobType.MAIEUTIC,
                "Maieutic Synthesis",
                data,
                {"revised_narrative": result, "synthesis": result}
            )
        
        response = {
            "success": True,
            "job_id": job_id,
            "result": {"revised_narrative": result, "synthesis": result}
        }
        
        self.wfile.write(json.dumps(response).encode())
    
    def handle_namespace_generation(self, data):
        """Generate namespace suggestions from prompt."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        prompt = data.get('prompt', '')
        if not prompt:
            response = {"success": False, "error": "No prompt provided"}
            self.wfile.write(json.dumps(response).encode())
            return
        
        # Generate namespace suggestions
        suggestions = llm.generate_namespace_suggestions(prompt)
        
        response = {
            "success": True,
            "suggestions": suggestions
        }
        
        self.wfile.write(json.dumps(response).encode())
    
    def handle_persona_generation(self, data):
        """Generate persona suggestions from prompt."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        prompt = data.get('prompt', '')
        if not prompt:
            response = {"success": False, "error": "No prompt provided"}
            self.wfile.write(json.dumps(response).encode())
            return
        
        # Generate persona suggestions
        suggestions = llm.generate_persona_suggestions(prompt)
        
        response = {
            "success": True,
            "suggestions": suggestions
        }
        
        self.wfile.write(json.dumps(response).encode())
    
    def serve_main_interface(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        # Generate language options for translation
        language_options = ""
        for category, languages in LANGUAGE_HIERARCHY.items():
            language_options += f'<optgroup label="{category}">\n'
            for name, code in languages.items():
                selected = 'selected' if code == 'es' else ''
                language_options += f'    <option value="{code}" {selected}>{name}</option>\n'
            language_options += '</optgroup>\n'
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Lamish Projection Engine</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.4/dist/katex.min.css">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/markdown-it@13.0.1/dist/markdown-it.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.4/dist/katex.min.js"></script>
    <style>
        .nav-link.active { background-color: #0d6efd !important; color: white !important; }
        .processing { background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .result { background-color: #d1edff; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .admin-link { position: fixed; top: 10px; right: 10px; z-index: 1000; }
        .spinner { display: none; }
        .markdown-content { line-height: 1.6; }
        .markdown-content h1, .markdown-content h2, .markdown-content h3 { margin-top: 1.5em; margin-bottom: 0.5em; }
        .markdown-content p { margin-bottom: 1em; }
        .markdown-content ul, .markdown-content ol { margin-bottom: 1em; padding-left: 2em; }
        .markdown-content li { margin-bottom: 0.25em; }
        .markdown-content code { background-color: #f8f9fa; padding: 0.2em 0.4em; border-radius: 3px; }
        .markdown-content pre { background-color: #f8f9fa; padding: 1em; border-radius: 5px; overflow-x: auto; }
        .markdown-content blockquote { border-left: 4px solid #007cba; padding-left: 1em; margin-left: 0; font-style: italic; }
        
        /* Interactive Dialogue Styles */
        .question-card { border: 1px solid #e9ecef; }
        .question-card .card-header { background-color: #f8f9fa; }
        .question-card .card-header button { text-decoration: none; color: #495057; }
        .question-card .card-header button:hover { color: #007cba; }
        .question-text { background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #007cba; }
        .synthesis-result { background-color: #d4edda; border: 1px solid #c3e6cb; padding: 20px; border-radius: 5px; }
        #synthesize-btn:disabled { opacity: 0.6; cursor: not-allowed; }
        
        /* Content Actions */
        .content-with-actions { position: relative; }
        .content-actions { 
            position: absolute; 
            top: -35px; 
            right: 0px; 
            opacity: 0; 
            transition: opacity 0.2s;
            background: rgba(0, 123, 186, 0.9);
            border-radius: 4px;
            padding: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            z-index: 10;
        }
        .content-with-actions:hover .content-actions { opacity: 1; }
        .action-btn { 
            background: none; 
            border: none; 
            color: white; 
            cursor: pointer; 
            padding: 4px; 
            margin: 0 2px;
            font-size: 14px;
        }
        .action-btn:hover { color: #ffd700; }
        .copy-feedback { 
            position: fixed; 
            top: 50%; 
            left: 50%; 
            transform: translate(-50%, -50%);
            background: #28a745; 
            color: white; 
            padding: 8px 16px; 
            border-radius: 4px; 
            z-index: 2000;
            display: none;
        }
    </style>
</head>
<body>
    <a href="http://localhost:8001" target="_blank" class="btn btn-sm btn-secondary admin-link">Admin</a>
    
    <!-- Copy feedback -->
    <div id="copy-feedback" class="copy-feedback">Copied to clipboard!</div>
    
    <div class="container-fluid">
        <div class="row">
            <div class="col-12 bg-primary text-white p-3">
                <h1>Lamish Projection Engine</h1>
                <p class="mb-0">AI-powered allegorical narrative transformation system - Immediate Processing</p>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-3 bg-light p-3">
                <nav class="nav flex-column">
                    <a class="nav-link active" href="#projection">Projection</a>
                    <a class="nav-link" href="#maieutic">Maieutic Dialogue</a>
                    <a class="nav-link" href="#translation">Round-trip Translation</a>
                    <a class="nav-link" href="#vision">Vision Analysis</a>
                    <a class="nav-link" href="#management">Manage Assets</a>
                </nav>
            </div>
            
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
                                <div class="input-group">
                                    <select class="form-control" id="persona">
                                        <option value="philosopher">Philosopher</option>
                                        <option value="storyteller">Storyteller</option>
                                        <option value="critic">Critic</option>
                                        <option value="advocate">Advocate</option>
                                    </select>
                                    <button type="button" class="btn btn-outline-secondary" onclick="openGenerateModal('persona')" title="Generate persona suggestions">
                                        💡
                                    </button>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <label for="namespace" class="form-label">Namespace</label>
                                <div class="input-group">
                                    <select class="form-control" id="namespace">
                                        <option value="lamish-galaxy">Lamish Galaxy</option>
                                        <option value="medieval-realm">Medieval Realm</option>
                                        <option value="corporate-dystopia">Corporate Dystopia</option>
                                        <option value="natural-world">Natural World</option>
                                    </select>
                                    <button type="button" class="btn btn-outline-secondary" onclick="openGenerateModal('namespace')" title="Generate namespace suggestions">
                                        💡
                                    </button>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <label for="style" class="form-label">Style</label>
                                <select class="form-control" id="style">
                                    <option value="academic">Academic</option>
                                    <option value="poetic">Poetic</option>
                                    <option value="technical">Technical</option>
                                    <option value="standard">Standard</option>
                                </select>
                            </div>
                        </div>
                        <div class="mt-3">
                            <button type="submit" class="btn btn-primary">
                                <span class="spinner spinner-border spinner-border-sm me-2" role="status"></span>
                                Create Projection
                            </button>
                        </div>
                    </form>
                    
                    <div id="projection-result" class="mt-4" style="display: none;"></div>
                </div>
                
                <!-- Maieutic Tab -->
                <div id="maieutic" class="tab-content" style="display: none;">
                    <h2>Maieutic (Socratic) Dialogue</h2>
                    <form id="maieutic-form">
                        <div class="mb-3">
                            <label for="maieutic-narrative" class="form-label">Narrative to Explore</label>
                            <textarea class="form-control" id="maieutic-narrative" rows="4" 
                                     placeholder="Enter the narrative you want to explore..."></textarea>
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
                                <label for="max-turns" class="form-label">Number of Questions</label>
                                <select class="form-control" id="max-turns">
                                    <option value="3">3</option>
                                    <option value="5" selected>5</option>
                                    <option value="7">7</option>
                                </select>
                            </div>
                        </div>
                        <div class="mt-3">
                            <button type="submit" class="btn btn-primary">
                                <span class="spinner spinner-border spinner-border-sm me-2" role="status"></span>
                                Generate Questions
                            </button>
                        </div>
                    </form>
                    
                    
                    <!-- Interactive Q&A Section -->
                    <div id="maieutic-dialogue" class="mt-4" style="display: none;">
                        <h4>Interactive Socratic Dialogue</h4>
                        <p class="text-muted">Answer the questions below in any order. Your responses will inform a revised narrative.</p>
                        
                        <div id="question-answers" class="mt-3">
                            <!-- Questions and answer fields will be populated here -->
                        </div>
                        
                        <div class="mt-4">
                            <button id="synthesize-btn" class="btn btn-success" onclick="synthesizeDialogue()" disabled>
                                <span class="spinner-border spinner-border-sm me-2" id="synthesize-spinner" style="display: none;"></span>
                                Synthesize Revised Narrative
                            </button>
                            <button class="btn btn-secondary ms-2" onclick="resetDialogue()">Reset Dialogue</button>
                        </div>
                        
                        <div id="synthesis-result" class="mt-4" style="display: none;">
                            <h5>Revised Narrative</h5>
                            <div class="synthesis-result markdown-content" id="revised-narrative"></div>
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
                                    {language_options}
                                </select>
                            </div>
                        </div>
                        <div class="mt-3">
                            <button type="submit" class="btn btn-primary">
                                <span class="spinner spinner-border spinner-border-sm me-2" role="status"></span>
                                Analyze Translation
                            </button>
                        </div>
                    </form>
                    
                    <div id="translation-result" class="mt-4" style="display: none;"></div>
                </div>
                
                <!-- Vision Analysis Tab -->
                <div id="vision" class="tab-content" style="display: none;">
                    <h2>Vision Analysis with Gemini Pro</h2>
                    <form id="vision-form">
                        <div class="mb-3">
                            <label for="vision-prompt" class="form-label">Analysis Prompt</label>
                            <textarea class="form-control" id="vision-prompt" rows="3" 
                                     placeholder="Describe what you want to analyze in the image...">What do you see in this image? Please provide a detailed description.</textarea>
                        </div>
                        <div class="mb-3">
                            <label for="vision-image" class="form-label">Upload Image</label>
                            <input type="file" class="form-control" id="vision-image" accept="image/*">
                        </div>
                        <div class="mb-3">
                            <label for="vision-model" class="form-label">Vision Model</label>
                            <select class="form-control" id="vision-model">
                                <option value="gemini-pro-vision">Gemini Pro Vision</option>
                                <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                                <option value="gemini-2.0-flash-exp">Gemini 2.0 Flash (Experimental)</option>
                            </select>
                        </div>
                        <div class="mt-3">
                            <button type="submit" class="btn btn-primary">
                                <span class="spinner spinner-border spinner-border-sm me-2" role="status"></span>
                                Analyze Image
                            </button>
                        </div>
                    </form>
                    
                    <div id="vision-result" class="mt-4" style="display: none;"></div>
                </div>
                
                <!-- Management Tab -->
                <div id="management" class="tab-content" style="display: none;">
                    <h2>Manage Assets</h2>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    <h5>🎭 Personas</h5>
                                </div>
                                <div class="card-body">
                                    <div class="mb-3">
                                        <label for="new-persona-name" class="form-label">Name:</label>
                                        <input type="text" class="form-control" id="new-persona-name" placeholder="e.g., wise-sage">
                                    </div>
                                    <div class="mb-3">
                                        <label for="new-persona-desc" class="form-label">Description:</label>
                                        <textarea class="form-control" id="new-persona-desc" rows="3" placeholder="Describe the persona's voice and perspective..."></textarea>
                                    </div>
                                    <button class="btn btn-primary" onclick="addPersona()">Add Persona</button>
                                    
                                    <h6 class="mt-4">Current Personas:</h6>
                                    <div id="persona-list" class="list-group mt-2">
                                        <div class="list-group-item">philosopher</div>
                                        <div class="list-group-item">storyteller</div>
                                        <div class="list-group-item">critic</div>
                                        <div class="list-group-item">advocate</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    <h5>🌌 Namespaces</h5>
                                </div>
                                <div class="card-body">
                                    <div class="mb-3">
                                        <label for="new-namespace-name" class="form-label">Name:</label>
                                        <input type="text" class="form-control" id="new-namespace-name" placeholder="e.g., digital-realm">
                                    </div>
                                    <div class="mb-3">
                                        <label for="new-namespace-desc" class="form-label">Description:</label>
                                        <textarea class="form-control" id="new-namespace-desc" rows="3" placeholder="Describe the universe's characteristics..."></textarea>
                                    </div>
                                    <button class="btn btn-primary" onclick="addNamespace()">Add Namespace</button>
                                    
                                    <h6 class="mt-4">Current Namespaces:</h6>
                                    <div id="namespace-list" class="list-group mt-2">
                                        <div class="list-group-item">lamish-galaxy</div>
                                        <div class="list-group-item">medieval-realm</div>
                                        <div class="list-group-item">corporate-dystopia</div>
                                        <div class="list-group-item">natural-world</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row mt-4">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    <h5>🎨 Styles</h5>
                                </div>
                                <div class="card-body">
                                    <div class="mb-3">
                                        <label for="new-style-name" class="form-label">Name:</label>
                                        <input type="text" class="form-control" id="new-style-name" placeholder="e.g., mystical">
                                    </div>
                                    <div class="mb-3">
                                        <label for="new-style-desc" class="form-label">Description:</label>
                                        <textarea class="form-control" id="new-style-desc" rows="3" placeholder="Describe the writing style..."></textarea>
                                    </div>
                                    <button class="btn btn-primary" onclick="addStyle()">Add Style</button>
                                    
                                    <h6 class="mt-4">Current Styles:</h6>
                                    <div id="style-list" class="list-group mt-2">
                                        <div class="list-group-item">academic</div>
                                        <div class="list-group-item">poetic</div>
                                        <div class="list-group-item">technical</div>
                                        <div class="list-group-item">standard</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    <h5>🔧 LLM Configuration</h5>
                                </div>
                                <div class="card-body">
                                    <p>Configure multiple LLM providers securely with macOS Keychain integration.</p>
                                    <a href="http://localhost:8002" target="_blank" class="btn btn-success">
                                        🔐 Open LLM Admin
                                    </a>
                                    <p class="text-muted mt-2"><small>Configure OpenAI, Anthropic, Google, and Ollama providers</small></p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Generation Modal -->
    <div class="modal fade" id="generateModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="generateModalTitle">Generate Suggestions</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <label for="generatePrompt" class="form-label">Describe what you're looking for:</label>
                        <textarea class="form-control" id="generatePrompt" rows="3" 
                                 placeholder="e.g., 'A mystical realm focused on transformation and growth' or 'A skeptical voice that questions assumptions'"></textarea>
                        <small class="form-text text-muted">Be specific about the themes, tone, or characteristics you want.</small>
                    </div>
                    <button type="button" class="btn btn-primary" onclick="generateSuggestions()">
                        <span class="spinner-border spinner-border-sm me-2" id="generateSpinner" style="display: none;"></span>
                        Generate Suggestions
                    </button>
                    
                    <div id="suggestions" class="mt-4" style="display: none;">
                        <h6>Suggestions:</h6>
                        <div id="suggestionsList"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Initialize markdown renderer with LaTeX support
        const md = window.markdownit({
            html: true,
            linkify: true,
            typographer: true
        });
        
        // Function to render markdown with LaTeX
        function renderMarkdown(text) {
            // First, protect LaTeX expressions by replacing them with placeholders
            const latexBlocks = [];
            const latexInline = [];
            
            // Find block LaTeX ($$...$$)
            text = text.replace(/\\$\\$([^$]+)\\$\\$/g, function(match, latex) {
                latexBlocks.push(latex);
                return `__LATEX_BLOCK_${latexBlocks.length - 1}__`;
            });
            
            // Find inline LaTeX ($...$)
            text = text.replace(/\\$([^$]+)\\$/g, function(match, latex) {
                latexInline.push(latex);
                return `__LATEX_INLINE_${latexInline.length - 1}__`;
            });
            
            // Render markdown
            let html = md.render(text);
            
            // Restore and render LaTeX expressions
            html = html.replace(/__LATEX_BLOCK_(\\d+)__/g, function(match, index) {
                try {
                    return katex.renderToString(latexBlocks[index], {
                        displayMode: true,
                        throwOnError: false
                    });
                } catch (e) {
                    return `<span class="text-danger">LaTeX Error: ${latexBlocks[index]}</span>`;
                }
            });
            
            html = html.replace(/__LATEX_INLINE_(\\d+)__/g, function(match, index) {
                try {
                    return katex.renderToString(latexInline[index], {
                        displayMode: false,
                        throwOnError: false
                    });
                } catch (e) {
                    return `<span class="text-danger">LaTeX Error: ${latexInline[index]}</span>`;
                }
            });
            
            return html;
        }
        
        // Tab navigation
        $('.nav-link').click(function(e) {
            e.preventDefault();
            $('.nav-link').removeClass('active');
            $('.tab-content').hide();
            $(this).addClass('active');
            $($(this).attr('href')).show();
        });
        
        function showSpinner(button) {
            button.find('.spinner').show();
            button.prop('disabled', true);
        }
        
        function hideSpinner(button) {
            button.find('.spinner').hide();
            button.prop('disabled', false);
        }
        
        // Projection form
        $('#projection-form').submit(function(e) {
            e.preventDefault();
            const button = $(this).find('button[type="submit"]');
            showSpinner(button);
            
            const data = {
                narrative: $('#narrative').val(),
                persona: $('#persona').val(),
                namespace: $('#namespace').val(),
                style: $('#style').val()
            };
            
            $.ajax({
                url: '/api/projection/create',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(data),
                success: function(response) {
                    hideSpinner(button);
                    if (response.success && response.result) {
                        const result = response.result;
                        const fullText = `# Allegorical Projection\n\n## Final Projection\n${result.final_projection}\n\n## Reflection\n${result.reflection}\n\n*Persona: ${result.persona} | Namespace: ${result.namespace} | Style: ${result.style}*`;
                        
                        $('#projection-result').html(wrapWithActions(`
                            <div class="result">
                                <h4>Allegorical Projection</h4>
                                <div class="mb-3">
                                    <strong>Final Projection:</strong>
                                    <div class="markdown-content">${renderMarkdown(result.final_projection)}</div>
                                </div>
                                <div class="mb-3">
                                    <strong>Reflection:</strong>
                                    <div class="markdown-content">${renderMarkdown(result.reflection)}</div>
                                </div>
                                <small class="text-muted">
                                    Persona: ${result.persona} | Namespace: ${result.namespace} | Style: ${result.style}
                                </small>
                            </div>
                        `, fullText)).show();
                    }
                },
                error: function(xhr) {
                    hideSpinner(button);
                    alert('Error: ' + (xhr.responseJSON?.detail || 'Unknown error'));
                }
            });
        });
        
        // Maieutic form
        $('#maieutic-form').submit(function(e) {
            e.preventDefault();
            const button = $(this).find('button[type="submit"]');
            showSpinner(button);
            
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
                success: function(response) {
                    hideSpinner(button);
                    if (response.success && response.result) {
                        const result = response.result;
                        
                        // Store the original narrative and questions globally
                        window.maieuticData = {
                            originalNarrative: data.narrative,
                            goal: data.goal,
                            questions: result.questions,
                            answers: {}
                        };
                        
                        // Create interactive Q&A interface
                        createInteractiveDialogue(result.questions);
                        
                        // Show new interactive dialogue
                        $('#maieutic-dialogue').show();
                    }
                },
                error: function(xhr) {
                    hideSpinner(button);
                    alert('Error: ' + (xhr.responseJSON?.detail || 'Unknown error'));
                }
            });
        });
        
        // Translation form
        $('#translation-form').submit(function(e) {
            e.preventDefault();
            const button = $(this).find('button[type="submit"]');
            showSpinner(button);
            
            const data = {
                text: $('#translation-text').val(),
                intermediate_language: $('#intermediate-language').val()
            };
            
            $.ajax({
                url: '/api/translation/round-trip',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(data),
                success: function(response) {
                    hideSpinner(button);
                    if (response.success && response.result) {
                        const result = response.result;
                        const fullText = `# Translation Analysis\n\n## Original Text\n${result.original_text}\n\n## Forward Translation (${data.intermediate_language})\n${result.intermediate_text || 'Not available'}\n\n## After Round-trip\n${result.final_text}\n\n## Analysis\n${result.analysis || 'Analysis completed'}\n\n*Semantic drift: ${(result.semantic_drift * 100).toFixed(1)}%*`;
                        
                        $('#translation-result').html(wrapWithActions(`
                            <div class="result">
                                <h4>Translation Analysis</h4>
                                <div class="mb-3">
                                    <strong>Original Text:</strong>
                                    <div class="markdown-content">${renderMarkdown(result.original_text)}</div>
                                </div>
                                <div class="mb-3">
                                    <strong>Forward Translation (${data.intermediate_language}):</strong>
                                    <div class="markdown-content">${renderMarkdown(result.intermediate_text || 'Not available')}</div>
                                </div>
                                <div class="mb-3">
                                    <strong>After Round-trip:</strong>
                                    <div class="markdown-content">${renderMarkdown(result.final_text)}</div>
                                </div>
                                <div class="mb-3">
                                    <strong>Analysis:</strong>
                                    <div class="markdown-content">${renderMarkdown(result.analysis || 'Analysis completed')}</div>
                                </div>
                                <small class="text-muted">
                                    Semantic drift: ${(result.semantic_drift * 100).toFixed(1)}%
                                </small>
                            </div>
                        `, fullText)).show();
                    }
                },
                error: function(xhr) {
                    hideSpinner(button);
                    alert('Error: ' + (xhr.responseJSON?.detail || 'Unknown error'));
                }
            });
        });
        
        // Vision form
        $('#vision-form').submit(function(e) {
            e.preventDefault();
            const button = $(this).find('button[type="submit"]');
            const fileInput = document.getElementById('vision-image');
            const file = fileInput.files[0];
            
            if (!file) {
                alert('Please select an image file.');
                return;
            }
            
            showSpinner(button);
            
            // Convert image to base64
            const reader = new FileReader();
            reader.onload = function(e) {
                const base64Data = e.target.result.split(',')[1]; // Remove data:image/... prefix
                
                const data = {
                    prompt: $('#vision-prompt').val(),
                    model: $('#vision-model').val(),
                    image_data: base64Data
                };
                
                $.ajax({
                    url: '/api/vision/analyze',
                    method: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify(data),
                    success: function(response) {
                        hideSpinner(button);
                        if (response.success && response.result) {
                            const result = response.result;
                            const fullText = `# Vision Analysis\n\n## Prompt\n${data.prompt}\n\n## Analysis\n${result.analysis}\n\n*Model: ${data.model}*`;
                            
                            $('#vision-result').html(wrapWithActions(`
                                <div class="result">
                                    <h4>Vision Analysis Result</h4>
                                    <div class="mb-3">
                                        <strong>Model:</strong> ${data.model}
                                    </div>
                                    <div class="mb-3">
                                        <strong>Prompt:</strong>
                                        <div class="markdown-content">${renderMarkdown(data.prompt)}</div>
                                    </div>
                                    <div class="mb-3">
                                        <strong>Analysis:</strong>
                                        <div class="markdown-content">${renderMarkdown(result.analysis)}</div>
                                    </div>
                                    <div class="mb-3">
                                        <strong>Uploaded Image:</strong><br>
                                        <img src="data:image/jpeg;base64,${data.image_data}" class="img-fluid" style="max-width: 400px; border-radius: 8px;">
                                    </div>
                                </div>
                            `, fullText)).show();
                        }
                    },
                    error: function(xhr) {
                        hideSpinner(button);
                        alert('Error: ' + (xhr.responseJSON?.detail || 'Unknown error'));
                    }
                });
            };
            reader.readAsDataURL(file);
        });
        
        // Generation Modal Functions
        let currentGenerationType = '';
        
        function openGenerateModal(type) {
            currentGenerationType = type;
            document.getElementById('generateModalTitle').textContent = 
                `Generate ${type.charAt(0).toUpperCase() + type.slice(1)} Suggestions`;
            document.getElementById('generatePrompt').value = '';
            document.getElementById('suggestions').style.display = 'none';
            
            // Show modal
            const modal = new bootstrap.Modal(document.getElementById('generateModal'));
            modal.show();
        }
        
        function generateSuggestions() {
            const prompt = document.getElementById('generatePrompt').value.trim();
            if (!prompt) {
                alert('Please enter a description of what you\\'re looking for.');
                return;
            }
            
            const spinner = document.getElementById('generateSpinner');
            spinner.style.display = 'inline-block';
            
            const endpoint = `/api/generate/${currentGenerationType}`;
            
            $.ajax({
                url: endpoint,
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ prompt: prompt }),
                success: function(response) {
                    spinner.style.display = 'none';
                    if (response.success) {
                        displaySuggestions(response.suggestions);
                    } else {
                        alert('Error generating suggestions: ' + response.error);
                    }
                },
                error: function(xhr) {
                    spinner.style.display = 'none';
                    alert('Error: ' + (xhr.responseJSON?.error || 'Unknown error'));
                }
            });
        }
        
        function displaySuggestions(suggestions) {
            const listElement = document.getElementById('suggestionsList');
            let html = '';
            
            suggestions.forEach(function(suggestion, index) {
                html += `
                    <div class="card mb-2">
                        <div class="card-body">
                            <h6 class="card-title">${suggestion.name}</h6>
                            <div class="card-text markdown-content">${renderMarkdown(suggestion.description)}</div>
                            <button class="btn btn-sm btn-primary" onclick="useSuggestion('${suggestion.name}')">
                                Use This
                            </button>
                        </div>
                    </div>
                `;
            });
            
            listElement.innerHTML = html;
            document.getElementById('suggestions').style.display = 'block';
        }
        
        function useSuggestion(name) {
            // Add to the appropriate select dropdown
            const selectId = currentGenerationType;
            const selectElement = document.getElementById(selectId);
            
            // Check if option already exists
            let optionExists = false;
            for (let option of selectElement.options) {
                if (option.value === name) {
                    optionExists = true;
                    break;
                }
            }
            
            // Add new option if it doesn't exist
            if (!optionExists) {
                const newOption = new Option(name.split('-').map(word => 
                    word.charAt(0).toUpperCase() + word.slice(1)).join(' '), name);
                selectElement.add(newOption);
            }
            
            // Select the new option
            selectElement.value = name;
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('generateModal'));
            modal.hide();
        }
        
        // Interactive Maieutic Dialogue Functions
        function createInteractiveDialogue(questions) {
            const container = document.getElementById('question-answers');
            let html = '';
            
            questions.forEach((question, index) => {
                const questionId = `question-${index}`;
                const answerId = `answer-${index}`;
                
                html += `
                    <div class="card question-card mb-3">
                        <div class="card-header">
                            <h6 class="mb-0">
                                <button class="btn btn-link p-0 text-start w-100" type="button" 
                                        data-bs-toggle="collapse" data-bs-target="#${questionId}" 
                                        aria-expanded="true" aria-controls="${questionId}">
                                    <span class="me-2">▼</span>
                                    Question ${index + 1}
                                </button>
                            </h6>
                        </div>
                        <div id="${questionId}" class="collapse show">
                            <div class="card-body">
                                <div class="question-text mb-3 markdown-content content-with-actions">
                                    ${renderMarkdown(question)}
                                    <div class="content-actions">
                                        <button class="action-btn" onclick="copyToClipboard('${escapeForJs(question)}')" title="Copy question">
                                            📋
                                        </button>
                                    </div>
                                </div>
                                <div class="mb-3">
                                    <label for="${answerId}" class="form-label">Your Response:</label>
                                    <textarea class="form-control" id="${answerId}" rows="4" 
                                             placeholder="Enter your thoughts, insights, or answers to this question..."
                                             onchange="saveAnswer(${index}, this.value)"></textarea>
                                </div>
                                <div class="form-text text-muted">
                                    You can answer questions in any order and return to edit them later.
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            container.innerHTML = html;
            
            // Initialize collapse buttons
            const collapseButtons = container.querySelectorAll('[data-bs-toggle="collapse"]');
            collapseButtons.forEach(button => {
                button.addEventListener('click', function() {
                    const icon = this.querySelector('span');
                    const target = document.querySelector(this.getAttribute('data-bs-target'));
                    
                    target.addEventListener('shown.bs.collapse', () => {
                        icon.textContent = '▼';
                    });
                    
                    target.addEventListener('hidden.bs.collapse', () => {
                        icon.textContent = '▶';
                    });
                });
            });
        }
        
        function saveAnswer(questionIndex, answer) {
            if (!window.maieuticData) return;
            window.maieuticData.answers[questionIndex] = answer;
            
            // Update synthesis button state
            const answeredCount = Object.keys(window.maieuticData.answers).filter(
                key => window.maieuticData.answers[key].trim()
            ).length;
            
            const synthesizeBtn = document.getElementById('synthesize-btn');
            if (answeredCount > 0) {
                synthesizeBtn.disabled = false;
                synthesizeBtn.innerHTML = `
                    <span class="spinner-border spinner-border-sm me-2" id="synthesize-spinner" style="display: none;"></span>
                    Synthesize Revised Narrative (${answeredCount} answers)
                `;
            }
        }
        
        function synthesizeDialogue() {
            if (!window.maieuticData) return;
            
            const answeredQuestions = Object.keys(window.maieuticData.answers).filter(
                key => window.maieuticData.answers[key].trim()
            );
            
            if (answeredQuestions.length === 0) {
                alert('Please answer at least one question before synthesizing.');
                return;
            }
            
            // Show spinner
            document.getElementById('synthesize-spinner').style.display = 'inline-block';
            document.getElementById('synthesize-btn').disabled = true;
            
            // Prepare synthesis prompt
            let qaPairs = [];
            answeredQuestions.forEach(index => {
                qaPairs.push({
                    question: window.maieuticData.questions[index],
                    answer: window.maieuticData.answers[index]
                });
            });
            
            const synthesisData = {
                original_narrative: window.maieuticData.originalNarrative,
                goal: window.maieuticData.goal,
                qa_pairs: qaPairs
            };
            
            // Call synthesis API
            $.ajax({
                url: '/api/maieutic/synthesize',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(synthesisData),
                success: function(response) {
                    document.getElementById('synthesize-spinner').style.display = 'none';
                    document.getElementById('synthesize-btn').disabled = false;
                    
                    if (response.success && response.result) {
                        const revisedNarrative = response.result.revised_narrative || response.result.synthesis;
                        const fullText = `# Revised Narrative\n\n${revisedNarrative}`;
                        
                        document.getElementById('revised-narrative').innerHTML = wrapWithActions(
                            renderMarkdown(revisedNarrative), 
                            fullText
                        );
                        document.getElementById('synthesis-result').style.display = 'block';
                        
                        // Scroll to result
                        document.getElementById('synthesis-result').scrollIntoView({ 
                            behavior: 'smooth' 
                        });
                    }
                },
                error: function(xhr) {
                    document.getElementById('synthesize-spinner').style.display = 'none';
                    document.getElementById('synthesize-btn').disabled = false;
                    alert('Error synthesizing: ' + (xhr.responseJSON?.detail || 'Unknown error'));
                }
            });
        }
        
        function resetDialogue() {
            if (confirm('Reset the dialogue and lose all answers?')) {
                window.maieuticData = null;
                document.getElementById('maieutic-dialogue').style.display = 'none';
                document.getElementById('synthesis-result').style.display = 'none';
                
                // Reset form
                document.getElementById('maieutic-form').reset();
            }
        }
        
        // Content Actions (Copy/Save)
        function wrapWithActions(content, rawText) {
            return `
                <div class="content-with-actions">
                    ${content}
                    <div class="content-actions">
                        <button class="action-btn" onclick="copyToClipboard('${escapeForJs(rawText)}')" title="Copy to clipboard">
                            📋
                        </button>
                        <button class="action-btn" onclick="saveToFile('${escapeForJs(rawText)}')" title="Save to file">
                            💾
                        </button>
                    </div>
                </div>
            `;
        }
        
        function escapeForJs(text) {
            return text.replace(/'/g, "\\\\'").replace(/"/g, '\\\\"').replace(/\\n/g, '\\\\n').replace(/\\r/g, '\\\\r');
        }
        
        function copyToClipboard(text) {
            // Unescape the text
            const unescapedText = text.replace(/\\\\'/g, "'").replace(/\\\\"/g, '"').replace(/\\\\n/g, '\\n').replace(/\\\\r/g, '\\r');
            
            navigator.clipboard.writeText(unescapedText).then(function() {
                showCopyFeedback();
            }).catch(function(err) {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = unescapedText;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                showCopyFeedback();
            });
        }
        
        function saveToFile(text) {
            // Unescape the text
            const unescapedText = text.replace(/\\\\'/g, "'").replace(/\\\\"/g, '"').replace(/\\\\n/g, '\\n').replace(/\\\\r/g, '\\r');
            
            const blob = new Blob([unescapedText], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `lpe_content_${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.md`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
        
        function showCopyFeedback() {
            const feedback = document.getElementById('copy-feedback');
            feedback.style.display = 'block';
            setTimeout(() => {
                feedback.style.display = 'none';
            }, 2000);
        }
        
        // Asset Management Functions
        function addPersona() {
            const name = document.getElementById('new-persona-name').value.trim();
            const desc = document.getElementById('new-persona-desc').value.trim();
            
            if (!name || !desc) {
                alert('Please fill in both name and description');
                return;
            }
            
            // Add to persona dropdown
            const personaSelect = document.getElementById('persona');
            const newOption = new Option(name.charAt(0).toUpperCase() + name.slice(1), name);
            personaSelect.add(newOption);
            
            // Add to persona list
            const personaList = document.getElementById('persona-list');
            const newItem = document.createElement('div');
            newItem.className = 'list-group-item d-flex justify-content-between align-items-center';
            newItem.innerHTML = `
                ${name} 
                <button class="btn btn-sm btn-outline-danger" onclick="removeAsset(this, 'persona', '${name}')">×</button>
            `;
            personaList.appendChild(newItem);
            
            // Clear form
            document.getElementById('new-persona-name').value = '';
            document.getElementById('new-persona-desc').value = '';
            
            showCopyFeedback();
        }
        
        function addNamespace() {
            const name = document.getElementById('new-namespace-name').value.trim();
            const desc = document.getElementById('new-namespace-desc').value.trim();
            
            if (!name || !desc) {
                alert('Please fill in both name and description');
                return;
            }
            
            // Add to namespace dropdown
            const namespaceSelect = document.getElementById('namespace');
            const newOption = new Option(name.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' '), name);
            namespaceSelect.add(newOption);
            
            // Add to namespace list
            const namespaceList = document.getElementById('namespace-list');
            const newItem = document.createElement('div');
            newItem.className = 'list-group-item d-flex justify-content-between align-items-center';
            newItem.innerHTML = `
                ${name} 
                <button class="btn btn-sm btn-outline-danger" onclick="removeAsset(this, 'namespace', '${name}')">×</button>
            `;
            namespaceList.appendChild(newItem);
            
            // Clear form
            document.getElementById('new-namespace-name').value = '';
            document.getElementById('new-namespace-desc').value = '';
            
            showCopyFeedback();
        }
        
        function addStyle() {
            const name = document.getElementById('new-style-name').value.trim();
            const desc = document.getElementById('new-style-desc').value.trim();
            
            if (!name || !desc) {
                alert('Please fill in both name and description');
                return;
            }
            
            // Add to style dropdown
            const styleSelect = document.getElementById('style');
            const newOption = new Option(name.charAt(0).toUpperCase() + name.slice(1), name);
            styleSelect.add(newOption);
            
            // Add to style list
            const styleList = document.getElementById('style-list');
            const newItem = document.createElement('div');
            newItem.className = 'list-group-item d-flex justify-content-between align-items-center';
            newItem.innerHTML = `
                ${name} 
                <button class="btn btn-sm btn-outline-danger" onclick="removeAsset(this, 'style', '${name}')">×</button>
            `;
            styleList.appendChild(newItem);
            
            // Clear form
            document.getElementById('new-style-name').value = '';
            document.getElementById('new-style-desc').value = '';
            
            showCopyFeedback();
        }
        
        function removeAsset(button, type, value) {
            if (confirm(`Remove ${type} "${value}"?`)) {
                // Remove from dropdown
                const selectId = type === 'persona' ? 'persona' : type === 'namespace' ? 'namespace' : 'style';
                const select = document.getElementById(selectId);
                for (let i = 0; i < select.options.length; i++) {
                    if (select.options[i].value === value) {
                        select.remove(i);
                        break;
                    }
                }
                
                // Remove from list
                button.parentElement.remove();
            }
        }
    </script>
</body>
</html>"""
        
        self.wfile.write(html.encode('utf-8'))
    
    def log_message(self, format, *args):
        pass  # Suppress logging

PORT = 8000
try:
    with socketserver.TCPServer(("", PORT), ImmediateHandler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nInterface stopped")
except Exception as e:
    print(f"Interface error: {e}")