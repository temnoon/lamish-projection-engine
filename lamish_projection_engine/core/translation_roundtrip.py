"""Back-translation facility for analyzing language transformations."""
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from lamish_projection_engine.core.llm import get_llm_provider, LLMProvider
from lamish_projection_engine.core.projection import Projection

logger = logging.getLogger(__name__)


class TranslationDirection(Enum):
    """Direction of translation."""
    FORWARD = "forward"  # Source language -> Target language
    BACKWARD = "backward"  # Target language -> Source language


@dataclass
class LanguageTranslation:
    """Represents a single language translation."""
    source_text: str
    target_text: str
    source_language: str
    target_language: str
    direction: TranslationDirection
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoundTripResult:
    """Result of a complete round-trip translation."""
    original_text: str
    final_text: str
    intermediate_language: str
    translations: List[LanguageTranslation] = field(default_factory=list)
    semantic_drift: float = 0.0  # Measure of meaning change
    linguistic_analysis: Dict[str, Any] = field(default_factory=dict)
    preserved_elements: List[str] = field(default_factory=list)
    lost_elements: List[str] = field(default_factory=list)
    gained_elements: List[str] = field(default_factory=list)


class LanguageRoundTripAnalyzer:
    """Analyzes narratives through language translation round-trips."""
    
    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or get_llm_provider()
        self.supported_languages = [
            "spanish", "french", "german", "italian", "portuguese", "russian",
            "chinese", "japanese", "korean", "arabic", "hebrew", "hindi",
            "dutch", "swedish", "norwegian", "danish", "polish", "czech"
        ]
    
    def perform_round_trip(self, text: str, intermediate_language: str, 
                          source_language: str = "english") -> RoundTripResult:
        """Perform a complete round-trip translation."""
        if intermediate_language not in self.supported_languages:
            raise ValueError(f"Unsupported language: {intermediate_language}")
        
        result = RoundTripResult(
            original_text=text,
            final_text="",
            intermediate_language=intermediate_language
        )
        
        try:
            # Forward translation
            logger.info(f"Translating from {source_language} to {intermediate_language}")
            forward_translation = self._translate_text(
                text, source_language, intermediate_language, TranslationDirection.FORWARD
            )
            result.translations.append(forward_translation)
            
            # Backward translation
            logger.info(f"Translating back from {intermediate_language} to {source_language}")
            backward_translation = self._translate_text(
                forward_translation.target_text, intermediate_language, source_language, 
                TranslationDirection.BACKWARD
            )
            result.translations.append(backward_translation)
            result.final_text = backward_translation.target_text
            
            # Analyze the transformation
            result.semantic_drift = self._calculate_semantic_drift(text, result.final_text)
            result.linguistic_analysis = self._analyze_linguistic_changes(text, result.final_text)
            result.preserved_elements, result.lost_elements, result.gained_elements = \
                self._analyze_element_changes(text, result.final_text)
            
            logger.info(f"Round-trip complete. Semantic drift: {result.semantic_drift:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"Round-trip translation failed: {e}")
            raise
    
    def _translate_text(self, text: str, source_lang: str, target_lang: str, 
                       direction: TranslationDirection) -> LanguageTranslation:
        """Translate text between two languages."""
        system_prompt = f"""You are a professional translator specializing in {source_lang} to {target_lang} translation.
Provide accurate, natural translations that preserve meaning and cultural context.
Translate the text preserving its narrative structure and emotional tone."""
        
        prompt = f"""Translate this {source_lang} text to {target_lang}:

{text}

Translation:"""
        
        try:
            translated = self.provider.generate(prompt, system_prompt)
            
            return LanguageTranslation(
                source_text=text,
                target_text=translated.strip(),
                source_language=source_lang,
                target_language=target_lang,
                direction=direction,
                confidence=0.85  # Default confidence
            )
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise
    
    def _calculate_semantic_drift(self, original: str, final: str) -> float:
        """Calculate semantic drift between original and final text."""
        try:
            system_prompt = """You are analyzing semantic similarity between two texts.
Rate the semantic similarity on a scale from 0.0 (completely different meaning) to 1.0 (identical meaning).
Consider meaning preservation, not just word similarity."""
            
            prompt = f"""Compare these two texts for semantic similarity:

Original: {original}

Final: {final}

Semantic similarity score (0.0-1.0):"""
            
            response = self.provider.generate(prompt, system_prompt)
            
            # Extract numeric score
            import re
            match = re.search(r'(\d*\.?\d+)', response)
            if match:
                score = float(match.group(1))
                return max(0.0, min(1.0, score))  # Clamp to valid range
            
            return 0.5  # Default if parsing fails
            
        except Exception as e:
            logger.error(f"Semantic drift calculation failed: {e}")
            return 0.5
    
    def _analyze_linguistic_changes(self, original: str, final: str) -> Dict[str, Any]:
        """Analyze linguistic changes between original and final text."""
        try:
            system_prompt = """You are a linguistic analyst. Analyze the linguistic changes between two texts.
Focus on changes in tone, style, complexity, and structural patterns."""
            
            prompt = f"""Analyze the linguistic changes between these texts:

Original: {original}

Final: {final}

Provide analysis in this JSON format:
{{
    "tone_change": "description of tone changes",
    "style_change": "description of style changes", 
    "complexity_change": "simpler/more_complex/similar",
    "structural_changes": ["list", "of", "structural", "changes"],
    "notable_patterns": ["list", "of", "notable", "patterns"]
}}"""

            response = self.provider.generate(prompt, system_prompt)
            
            # Try to parse JSON response
            import json
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # Fallback to basic analysis
                return {
                    "tone_change": "Analysis unavailable",
                    "style_change": "Analysis unavailable",
                    "complexity_change": "unknown",
                    "structural_changes": [],
                    "notable_patterns": []
                }
                
        except Exception as e:
            logger.error(f"Linguistic analysis failed: {e}")
            return {}
    
    def _analyze_element_changes(self, original: str, final: str) -> Tuple[List[str], List[str], List[str]]:
        """Analyze what elements were preserved, lost, or gained."""
        try:
            system_prompt = """You are analyzing content changes between two texts.
Identify what meaning elements were preserved, lost, or newly introduced."""
            
            prompt = f"""Compare these texts for content changes:

Original: {original}

Final: {final}

List the changes in this format:
PRESERVED: [elements that remained the same]
LOST: [elements that disappeared]
GAINED: [new elements that appeared]"""

            response = self.provider.generate(prompt, system_prompt)
            
            preserved = []
            lost = []
            gained = []
            
            # Parse response
            lines = response.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('PRESERVED:'):
                    current_section = 'preserved'
                    content = line.replace('PRESERVED:', '').strip()
                    if content and content != '[]':
                        preserved.extend(self._parse_element_list(content))
                elif line.startswith('LOST:'):
                    current_section = 'lost'
                    content = line.replace('LOST:', '').strip()
                    if content and content != '[]':
                        lost.extend(self._parse_element_list(content))
                elif line.startswith('GAINED:'):
                    current_section = 'gained'
                    content = line.replace('GAINED:', '').strip()
                    if content and content != '[]':
                        gained.extend(self._parse_element_list(content))
                elif current_section and line:
                    # Continuation of current section
                    if current_section == 'preserved':
                        preserved.extend(self._parse_element_list(line))
                    elif current_section == 'lost':
                        lost.extend(self._parse_element_list(line))
                    elif current_section == 'gained':
                        gained.extend(self._parse_element_list(line))
            
            return preserved, lost, gained
            
        except Exception as e:
            logger.error(f"Element analysis failed: {e}")
            return [], [], []
    
    def _parse_element_list(self, text: str) -> List[str]:
        """Parse a list of elements from text."""
        # Remove brackets and split by commas
        text = text.strip('[]').strip()
        if not text:
            return []
        
        elements = [elem.strip().strip('"\'') for elem in text.split(',')]
        return [elem for elem in elements if elem]
    
    def analyze_projection_round_trip(self, projection: Projection, 
                                    intermediate_language: str) -> RoundTripResult:
        """Analyze a projection through language round-trip."""
        return self.perform_round_trip(
            projection.final_projection, 
            intermediate_language
        )
    
    def multi_language_analysis(self, text: str, languages: List[str]) -> Dict[str, RoundTripResult]:
        """Perform round-trip analysis through multiple languages."""
        results = {}
        
        for lang in languages:
            if lang in self.supported_languages:
                try:
                    result = self.perform_round_trip(text, lang)
                    results[lang] = result
                    logger.info(f"Completed round-trip analysis for {lang}")
                except Exception as e:
                    logger.error(f"Round-trip analysis failed for {lang}: {e}")
                    
        return results
    
    def find_stable_meaning_core(self, text: str, 
                               test_languages: Optional[List[str]] = None) -> Dict[str, Any]:
        """Find the stable semantic core by testing multiple language round-trips."""
        test_languages = test_languages or ["spanish", "french", "german", "chinese", "arabic"]
        
        results = self.multi_language_analysis(text, test_languages)
        
        # Analyze common preserved elements
        all_preserved = []
        all_lost = []
        drift_scores = []
        
        for lang, result in results.items():
            all_preserved.extend(result.preserved_elements)
            all_lost.extend(result.lost_elements)
            drift_scores.append(result.semantic_drift)
        
        # Find most commonly preserved elements
        from collections import Counter
        preserved_counts = Counter(all_preserved)
        lost_counts = Counter(all_lost)
        
        stable_core = {
            "average_drift": sum(drift_scores) / len(drift_scores) if drift_scores else 0,
            "most_stable_elements": [elem for elem, count in preserved_counts.most_common(5)],
            "most_volatile_elements": [elem for elem, count in lost_counts.most_common(5)],
            "language_results": {lang: result.semantic_drift for lang, result in results.items()},
            "stability_score": 1.0 - (sum(drift_scores) / len(drift_scores)) if drift_scores else 0
        }
        
        return stable_core


def test_round_trip_translation():
    """Test the round-trip translation system."""
    analyzer = LanguageRoundTripAnalyzer()
    
    test_text = """Sam Altman dropped out of Stanford after two years to found his first company, 
    which raised over $30 million in venture funding. He later became president of Y Combinator 
    and now leads OpenAI in the AI revolution."""
    
    # Test single round-trip
    result = analyzer.perform_round_trip(test_text, "spanish")
    
    print(f"Original: {result.original_text}")
    print(f"Final: {result.final_text}")
    print(f"Semantic drift: {result.semantic_drift}")
    print(f"Preserved: {result.preserved_elements}")
    print(f"Lost: {result.lost_elements}")
    
    # Test stable core analysis
    stable_core = analyzer.find_stable_meaning_core(test_text)
    print(f"Stability analysis: {stable_core}")


if __name__ == "__main__":
    test_round_trip_translation()