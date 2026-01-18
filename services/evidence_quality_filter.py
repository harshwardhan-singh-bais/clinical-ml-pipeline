"""
Evidence Quality Filter
Ensures retrieved evidence is DIAGNOSTIC, not just similar text
"""

import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EvidenceQuality:
    """Evidence quality assessment"""
    is_diagnostic: bool
    evidence_types: List[str]
    quality_score: float
    reason: str


class EvidenceQualityFilter:
    """
    Filter evidence chunks to ensure they provide DIAGNOSTIC value,
    not just semantic similarity.
    
    Prevents RAG hallucination with citations.
    """
    
    def __init__(self):
        """Load evidence keywords and rules."""
        logger.info("Initializing Evidence Quality Filter...")
        
        kb_path = Path(__file__).parent.parent / "config" / "clinical_knowledge_base.json"
        with open(kb_path, 'r') as f:
            kb = json.load(f)
        
        self.evidence_keywords = kb['evidence_keywords']
        
        logger.info("✅ Evidence quality filter ready")
    
    def assess_chunk_quality(self, chunk_text: str, chunk_metadata: Dict = None) -> EvidenceQuality:
        """
        Assess if a chunk provides diagnostic value.
        
        Args:
            chunk_text: The evidence text
            chunk_metadata: Metadata (section type, source, etc.)
            
        Returns:
            EvidenceQuality assessment
        """
        chunk_metadata = chunk_metadata or {}
        
        # Detect evidence types present
        evidence_types = []
        
        for ev_type, keywords in self.evidence_keywords.items():
            if self._contains_keywords(chunk_text, keywords):
                evidence_types.append(ev_type)
        
        # Check section metadata
        section_type = chunk_metadata.get('section_type', '').lower()
        if 'diagnostic' in section_type or 'evaluation' in section_type:
            if 'diagnostic_criteria' not in evidence_types:
                evidence_types.append('diagnostic_criteria')
        
        # Diagnostic evidence types (highest value)
        diagnostic_types = ['diagnostic_criteria', 'typical_symptoms', 'exclusion_features']
        
        # Is this diagnostic?
        is_diagnostic = any(et in diagnostic_types for et in evidence_types)
        
        # Quality score
        quality_score = self._calculate_quality_score(evidence_types, section_type)
        
        # Reason
        if is_diagnostic:
            reason = f"Contains {', '.join(evidence_types[:2])} information"
        else:
            reason = "No diagnostic criteria found - management/background only"
        
        return EvidenceQuality(
            is_diagnostic=is_diagnostic,
            evidence_types=evidence_types,
            quality_score=quality_score,
            reason=reason
        )
    
    def filter_evidence_chunks(
        self,
        chunks: List[Dict],
        diagnosis: str,
        min_quality_score: float = 0.5
    ) -> List[Dict]:
        """
        Filter chunks to keep only diagnostically valuable evidence.
        
        Args:
            chunks: List of evidence chunks
            diagnosis: Diagnosis being evaluated
            min_quality_score: Minimum quality threshold
            
        Returns:
            Filtered list of high-quality chunks
        """
        filtered = []
        
        for chunk in chunks:
            chunk_text = chunk.get('text', chunk.get('content', ''))
            chunk_metadata = {
                'section_type': chunk.get('section_type', ''),
                'source': chunk.get('source', ''),
                'title': chunk.get('title', '')
            }
            
            quality = self.assess_chunk_quality(chunk_text, chunk_metadata)
            
            # Only keep diagnostic evidence
            if quality.is_diagnostic and quality.quality_score >= min_quality_score:
                # Add quality metadata
                chunk['evidence_quality'] = {
                    'score': quality.quality_score,
                    'types': quality.evidence_types,
                    'reason': quality.reason
                }
                filtered.append(chunk)
                
                logger.debug(f"✅ Kept chunk: {quality.reason} (score={quality.quality_score:.2f})")
            else:
                logger.debug(f"❌ Filtered out: {quality.reason}")
        
        logger.info(f"Evidence filtering: {len(chunks)} → {len(filtered)} high-quality chunks")
        
        return filtered
    
    def _contains_keywords(self, text: str, keywords: List[str]) -> bool:
        """Check if text contains any of the keywords."""
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in keywords)
    
    def _calculate_quality_score(self, evidence_types: List[str], section_type: str) -> float:
        """
        Calculate evidence quality score (0-1).
        
        Higher score = more diagnostic value
        """
        score = 0.0
        
        # Evidence type scores
        type_weights = {
            'diagnostic_criteria': 1.0,
            'typical_symptoms': 0.9,
            'exclusion_features': 0.8,
            'management': 0.3
        }
        
        for ev_type in evidence_types:
            score += type_weights.get(ev_type, 0.1)
        
        # Section type bonus
        diagnostic_sections = ['diagnostic', 'evaluation', 'presentation', 'clinical']
        if any(sec in section_type.lower() for sec in diagnostic_sections):
            score += 0.2
        
        # Normalize to 0-1
        return min(score, 1.0)
    
    def explain_filtering(self, original_count: int, filtered_count: int) -> str:
        """Generate explanation of filtering results."""
        if filtered_count == 0:
            return "⚠️ No diagnostic evidence found - results may be unreliable"
        
        filtered_pct = (filtered_count / original_count * 100) if original_count > 0 else 0
        
        if filtered_pct < 30:
            return f"⚠️ Only {filtered_count}/{original_count} chunks contain diagnostic criteria"
        else:
            return f"✅ {filtered_count}/{original_count} chunks provide diagnostic value"
