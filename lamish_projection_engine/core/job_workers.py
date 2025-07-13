"""Job workers for long-running LPE operations."""
import asyncio
import logging
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import traceback

from lamish_projection_engine.core.jobs import get_job_manager, JobType, JobStatus
from lamish_projection_engine.core.projection import ProjectionEngine
from lamish_projection_engine.core.translation_roundtrip import LanguageRoundTripAnalyzer
from lamish_projection_engine.core.maieutic import MaieuticDialogue
from lamish_projection_engine.config.dynamic_attributes import ConfigurationManager

logger = logging.getLogger(__name__)


class ProjectionJobWorker:
    """Handles projection creation as background jobs."""
    
    def __init__(self):
        self.job_manager = get_job_manager()
        self.projection_engine = ProjectionEngine()
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    async def create_projection_job(self, narrative: str, persona: Optional[str] = None,
                                   namespace: Optional[str] = None, style: Optional[str] = None,
                                   show_steps: bool = True) -> str:
        """Create a projection job and start processing."""
        input_data = {
            "narrative": narrative,
            "persona": persona,
            "namespace": namespace,
            "style": style,
            "show_steps": show_steps
        }
        
        job_id = self.job_manager.create_job(
            JobType.PROJECTION,
            f"Creating allegorical projection",
            f"Transforming narrative: {narrative[:50]}{'...' if len(narrative) > 50 else ''}",
            input_data
        )
        
        # Start the job in background
        asyncio.create_task(self._process_projection_job(job_id))
        
        return job_id
    
    async def _process_projection_job(self, job_id: str):
        """Process projection job in background."""
        try:
            self.job_manager.start_job(job_id)
            job = self.job_manager.get_job(job_id)
            
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            input_data = job.input_data
            
            # Step 1: Initialize configuration
            await self._update_progress(job_id, "Initializing configuration", 1, 6, 
                                       "Loading persona, namespace, and style settings")
            
            config_manager = ConfigurationManager()
            persona_attr = config_manager.get_attribute("persona")
            namespace_attr = config_manager.get_attribute("namespace")
            style_attr = config_manager.get_attribute("language_style")
            
            persona = input_data.get("persona") or (persona_attr.fields.get("base_type", {}).value if persona_attr else "neutral")
            namespace = input_data.get("namespace") or (namespace_attr.fields.get("base_setting", {}).value if namespace_attr else "lamish-galaxy")
            style = input_data.get("style") or (style_attr.fields.get("base_style", {}).value if style_attr else "standard")
            
            # Step 2: Run projection in executor
            await self._update_progress(job_id, "Creating projection", 2, 6,
                                       f"Transforming to {namespace} with {persona} persona")
            
            projection = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.projection_engine.create_projection,
                input_data["narrative"],
                persona,
                namespace,
                style,
                input_data.get("show_steps", True)
            )
            
            # Step 3: Process steps if available
            if hasattr(projection, 'steps') and projection.steps:
                for i, step in enumerate(projection.steps):
                    step_num = i + 3
                    await self._update_progress(job_id, f"Processing step: {step.name}", 
                                               step_num, 6, f"Step: {step.name}")
                    
                    # Small delay to show progress
                    await asyncio.sleep(0.1)
            
            # Step 4: Finalize result
            await self._update_progress(job_id, "Finalizing projection", 5, 6,
                                       "Preparing final result and metadata")
            
            result_data = {
                "projection": projection.to_dict(),
                "persona": persona,
                "namespace": namespace,
                "style": style,
                "final_projection": projection.final_projection,
                "reflection": projection.reflection,
                "steps": [step.to_dict() for step in projection.steps] if hasattr(projection, 'steps') and projection.steps else []
            }
            
            # Step 5: Complete
            await self._update_progress(job_id, "Completed", 6, 6, "Projection ready")
            
            self.job_manager.complete_job(job_id, result_data)
            
            logger.info(f"Projection job {job_id} completed successfully")
            
        except Exception as e:
            error_msg = f"Projection job failed: {str(e)}"
            logger.error(f"Job {job_id} error: {error_msg}")
            logger.error(traceback.format_exc())
            
            self.job_manager.fail_job(job_id, error_msg)
    
    async def _update_progress(self, job_id: str, step: str, current: int, total: int, details: str):
        """Update job progress."""
        self.job_manager.update_progress(job_id, step, current, total, details)


class TranslationJobWorker:
    """Handles round-trip translation as background jobs."""
    
    def __init__(self):
        self.job_manager = get_job_manager()
        self.analyzer = LanguageRoundTripAnalyzer()
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    async def create_translation_job(self, text: str, intermediate_language: str, 
                                   source_language: str = "english") -> str:
        """Create a translation analysis job and start processing."""
        input_data = {
            "text": text,
            "intermediate_language": intermediate_language,
            "source_language": source_language
        }
        
        job_id = self.job_manager.create_job(
            JobType.TRANSLATION,
            f"Round-trip translation analysis",
            f"Analyzing: {text[:50]}{'...' if len(text) > 50 else ''} via {intermediate_language}",
            input_data
        )
        
        # Start the job in background
        asyncio.create_task(self._process_translation_job(job_id))
        
        return job_id
    
    async def _process_translation_job(self, job_id: str):
        """Process translation job in background."""
        try:
            self.job_manager.start_job(job_id)
            job = self.job_manager.get_job(job_id)
            
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            input_data = job.input_data
            
            # Step 1: Initialize
            await self._update_progress(job_id, "Initializing translation analysis", 1, 5,
                                       f"Preparing to translate via {input_data['intermediate_language']}")
            
            # Step 2: Forward translation
            await self._update_progress(job_id, "Forward translation", 2, 5,
                                       f"Translating from {input_data['source_language']} to {input_data['intermediate_language']}")
            
            # Step 3: Backward translation  
            await self._update_progress(job_id, "Backward translation", 3, 5,
                                       f"Translating back to {input_data['source_language']}")
            
            # Step 4: Analysis
            await self._update_progress(job_id, "Analyzing semantic drift", 4, 5,
                                       "Computing preservation and loss metrics")
            
            # Run the actual round-trip analysis
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.analyzer.perform_round_trip,
                input_data["text"],
                input_data["intermediate_language"],
                input_data["source_language"]
            )
            
            # Step 5: Complete
            await self._update_progress(job_id, "Analysis complete", 5, 5,
                                       f"Semantic drift: {result.semantic_drift:.1%}")
            
            result_data = {
                "original_text": result.original_text,
                "final_text": result.final_text,
                "intermediate_language": result.intermediate_language,
                "semantic_drift": result.semantic_drift,
                "preserved_elements": result.preserved_elements,
                "lost_elements": result.lost_elements,
                "gained_elements": result.gained_elements,
                "linguistic_analysis": result.linguistic_analysis
            }
            
            self.job_manager.complete_job(job_id, result_data)
            
            logger.info(f"Translation job {job_id} completed successfully")
            
        except Exception as e:
            error_msg = f"Translation job failed: {str(e)}"
            logger.error(f"Job {job_id} error: {error_msg}")
            logger.error(traceback.format_exc())
            
            self.job_manager.fail_job(job_id, error_msg)
    
    async def _update_progress(self, job_id: str, step: str, current: int, total: int, details: str):
        """Update job progress."""
        self.job_manager.update_progress(job_id, step, current, total, details)


class MaieuticJobWorker:
    """Handles maieutic dialogue as background jobs."""
    
    def __init__(self):
        self.job_manager = get_job_manager()
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    async def create_maieutic_job(self, narrative: str, goal: str = "understand",
                                 max_turns: int = 5) -> str:
        """Create a maieutic dialogue job and start processing."""
        input_data = {
            "narrative": narrative,
            "goal": goal,
            "max_turns": max_turns
        }
        
        job_id = self.job_manager.create_job(
            JobType.MAIEUTIC,
            f"Maieutic dialogue session",
            f"Exploring: {narrative[:50]}{'...' if len(narrative) > 50 else ''} (goal: {goal})",
            input_data
        )
        
        # Start the job in background
        asyncio.create_task(self._process_maieutic_job(job_id))
        
        return job_id
    
    async def _process_maieutic_job(self, job_id: str):
        """Process maieutic dialogue job in background."""
        try:
            self.job_manager.start_job(job_id)
            job = self.job_manager.get_job(job_id)
            
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            input_data = job.input_data
            
            # Step 1: Initialize session
            await self._update_progress(job_id, "Starting dialogue session", 1, input_data["max_turns"] + 2,
                                       f"Initializing Socratic exploration with goal: {input_data['goal']}")
            
            dialogue = MaieuticDialogue()
            session = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                dialogue.start_session,
                input_data["narrative"],
                input_data["goal"]
            )
            
            # Generate questions for the session
            questions = []
            for turn in range(input_data["max_turns"]):
                step_num = turn + 2
                await self._update_progress(job_id, f"Generating question {turn + 1}", step_num, 
                                           input_data["max_turns"] + 2,
                                           f"Creating Socratic question for depth level {turn}")
                
                question = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    dialogue.generate_question,
                    turn
                )
                
                questions.append({
                    "number": turn + 1,
                    "question": question,
                    "depth_level": turn
                })
            
            # Step final: Complete
            await self._update_progress(job_id, "Dialogue prepared", input_data["max_turns"] + 2,
                                       input_data["max_turns"] + 2,
                                       f"Ready for interactive exploration")
            
            result_data = {
                "session_id": id(session),
                "session": session.to_dict(),
                "questions": questions,
                "narrative": input_data["narrative"],
                "goal": input_data["goal"],
                "max_turns": input_data["max_turns"]
            }
            
            self.job_manager.complete_job(job_id, result_data)
            
            logger.info(f"Maieutic job {job_id} completed successfully")
            
        except Exception as e:
            error_msg = f"Maieutic job failed: {str(e)}"
            logger.error(f"Job {job_id} error: {error_msg}")
            logger.error(traceback.format_exc())
            
            self.job_manager.fail_job(job_id, error_msg)
    
    async def _update_progress(self, job_id: str, step: str, current: int, total: int, details: str):
        """Update job progress."""
        self.job_manager.update_progress(job_id, step, current, total, details)


# Global worker instances
projection_worker = ProjectionJobWorker()
translation_worker = TranslationJobWorker()
maieutic_worker = MaieuticJobWorker()