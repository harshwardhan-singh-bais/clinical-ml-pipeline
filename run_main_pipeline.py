"""
🏥 MAIN CLINICAL ML PIPELINE - HACKATHON READY
==============================================

This is the MAIN PROJECT runner with detailed phase-by-phase logging.
Every step is explained in detail so anyone can understand what's happening.

DATASETS USED:
- StatPearls/PMC: Medical knowledge base (3,397 chunks in pgvector)
- MedCaseReasoning: Clinical reasoning patterns
- Asclepius: Clinical note realism validation
- Augmented Notes: Robustness to noise

TECHNOLOGIES:
- Gemini 2.5 Flash: LLM for synthesis
- Sentence-Transformers: all-mpnet-base-v2 (768-dim embeddings)
- Supabase pgvector: Vector database for retrieval
- RAG Pipeline: Retrieval-Augmented Generation
"""

import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Setup beautiful console logging
class ColoredFormatter(logging.Formatter):
    """Colored console output for better readability"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)

# Configure logging
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = ColoredFormatter(
    '%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
console_handler.setFormatter(console_formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler]
)

logger = logging.getLogger(__name__)

# Import pipeline
from services.clinical_pipeline import ClinicalPipeline
from models.schemas import ClinicalNoteRequest, InputType, ProcessingStatus


def print_banner():
    """Print beautiful startup banner"""
    print("\n" + "="*80)
    print("🏥" * 40)
    print("  CLINICAL ML PIPELINE - MAIN PROJECT EXECUTION")
    print("  GenAI-Powered Clinical Note Summarization")
    print("  & Differential Diagnosis Generation")
    print("🏥" * 40)
    print("="*80 + "\n")


def print_phase_header(phase_num: int, phase_name: str):
    """Print phase header"""
    print("\n" + "─"*80)
    print(f"📍 PHASE {phase_num}: {phase_name}")
    print("─"*80)


def explain_step(emoji: str, title: str, explanation: str):
    """Explain what's happening in simple terms"""
    print(f"\n{emoji} {title}")
    print(f"   → {explanation}")


def get_user_input() -> str:
    """Get clinical note input from user"""
    print("\n" + "="*80)
    print("📝 INPUT REQUIRED")
    print("="*80)
    print("\nPlease paste your clinical note below.")
    print("Press ENTER twice when done, or type 'EXAMPLE' for sample input:\n")
    
    lines = []
    empty_count = 0
    
    while True:
        line = input()
        
        if line.strip().upper() == 'EXAMPLE':
            return """
While oncology specialists lean towards the palliative systemic therapy, convinced 
that most cases are already metastasizing at disease presentation and that surgery 
is a part of a palliative regimen to only 20% of the patients. However, surgery is 
still considered the only cure for the disease with absent alternatives, backed by 
the relatively improved survival.

Gastrectomy with systemic therapy, either radiotherapy or chemotherapy, seems a 
promising approach in some cases of localized linitis plastica. It is associated 
with increased overall survival.

Patient is a 58-year-old male presenting with progressive dysphagia, early satiety, 
and 15-pound weight loss over 3 months. Upper endoscopy revealed diffuse gastric 
wall thickening consistent with linitis plastica pattern.
"""
        
        if not line.strip():
            empty_count += 1
            if empty_count >= 2:
                break
        else:
            empty_count = 0
            lines.append(line)
    
    return "\n".join(lines)


def save_output(response: Any, input_text: str, output_num: int = 1):
    """Save formatted output to text file"""
    
    filename = f"OUTPUT{output_num}.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("🏥 CLINICAL ML PIPELINE - OUTPUT REPORT\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"Generated: {timestamp}\n")
        f.write(f"Status: {response.status}\n")
        f.write(f"Processing Time: {response.processing_time_seconds:.2f} seconds\n")
        f.write(f"Request ID: {response.request_id}\n\n")
        
        f.write("="*80 + "\n")
        f.write("📥 INPUT CLINICAL NOTE\n")
        f.write("="*80 + "\n\n")
        f.write(input_text.strip() + "\n\n")
        
        f.write("="*80 + "\n")
        f.write("📊 CLINICAL SUMMARY\n")
        f.write("="*80 + "\n\n")
        
        if response.summary:
            f.write(f"Chief Complaint: {response.summary.chief_complaint}\n")
            f.write(f"Timeline: {response.summary.timeline}\n")
            f.write(f"Key Symptoms: {', '.join(response.summary.symptoms)}\n\n")
            f.write(f"Clinical Findings:\n{response.summary.clinical_findings}\n\n")
            f.write(f"Narrative Summary:\n{response.summary.summary_text}\n\n")
        
        f.write("="*80 + "\n")
        f.write("🔬 DIFFERENTIAL DIAGNOSES\n")
        f.write("="*80 + "\n\n")
        
        for dx in response.differential_diagnoses:
            f.write(f"\n{'─'*80}\n")
            f.write(f"RANK #{dx.priority}: {dx.diagnosis}\n")
            f.write(f"{'─'*80}\n\n")
            
            f.write(f"Description:\n{dx.description}\n\n")
            
            f.write(f"Confidence Score: {dx.confidence.overall_confidence:.2f}\n")
            f.write(f"Evidence Strength: {dx.confidence.evidence_strength:.2f}\n")
            f.write(f"Citation Count: {dx.confidence.citation_count}\n\n")
            
            f.write("Patient Evidence Supporting This Diagnosis:\n")
            for item in dx.patient_justification:
                f.write(f"  • {item}\n")
            f.write("\n")
            
            if dx.supporting_evidence:
                f.write("StatPearls/PMC Evidence Citations:\n")
                for i, cite in enumerate(dx.supporting_evidence, 1):
                    f.write(f"\n  Citation {i}:\n")
                    f.write(f"    Chunk ID: {cite.chunk_id}\n")
                    f.write(f"    PMCID: {cite.pmcid}\n")
                    f.write(f"    Similarity: {cite.similarity_score:.4f}\n")
                    f.write(f"    Text: {cite.text_snippet}\n")
            
            f.write(f"\nClinical Reasoning:\n{dx.reasoning}\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("📈 METADATA & QUALITY METRICS\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"Total Evidence Retrieved: {response.total_evidence_retrieved} chunks\n")
        f.write(f"Processing Status: {response.status}\n")
        
        if response.warning_messages:
            f.write("\nWarnings:\n")
            for warn in response.warning_messages:
                f.write(f"  ⚠️  {warn}\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("🔧 TECHNICAL STACK\n")
        f.write("="*80 + "\n\n")
        
        f.write("DATASETS:\n")
        f.write("  • StatPearls/PMC: 3,397 medical literature chunks (pgvector)\n")
        f.write("  • MedCaseReasoning: Clinical reasoning patterns\n")
        f.write("  • Asclepius: Clinical note validation\n")
        f.write("  • Augmented Notes: Noise robustness\n\n")
        
        f.write("MODELS:\n")
        f.write("  • LLM: Google Gemini 2.5 Flash\n")
        f.write("  • Embeddings: sentence-transformers/all-mpnet-base-v2 (768-dim)\n")
        f.write("  • Database: Supabase pgvector (cosine similarity)\n\n")
        
        f.write("PIPELINE PHASES: 29 total phases executed\n")
        f.write("  Phase 1-2:   Environment setup & request intake\n")
        f.write("  Phase 3-4:   Document processing & normalization\n")
        f.write("  Phase 5-6:   Medical-aware chunking & embedding\n")
        f.write("  Phase 7-9:   Knowledge base retrieval (RAG)\n")
        f.write("  Phase 10-13: LLM synthesis with evidence grounding\n")
        f.write("  Phase 14-18: Validation, confidence scoring, audit logging\n")
        f.write("  Phase 19-29: Safety checks, formatting, delivery\n\n")
        
        f.write("="*80 + "\n")
        f.write("✅ END OF REPORT\n")
        f.write("="*80 + "\n")
    
    logger.info(f"✅ Output saved to: {filename}")
    return filename


def main():
    """Main pipeline execution"""
    
    print_banner()
    
    # Get input
    clinical_note = get_user_input()
    
    if not clinical_note.strip():
        logger.error("❌ No input provided. Exiting.")
        return
    
    logger.info(f"✅ Input received: {len(clinical_note)} characters\n")
    
    # ========== PHASE 1: INITIALIZATION ==========
    print_phase_header(1, "PIPELINE INITIALIZATION")
    
    explain_step(
        "🔧", "Loading Environment Variables",
        "Reading API keys from .env file (GEMINI_API_KEY, SUPABASE_URL, etc.)"
    )
    
    explain_step(
        "🤖", "Initializing AI Models",
        "Loading Gemini LLM and sentence-transformers embedding model (768 dimensions)"
    )
    
    explain_step(
        "💾", "Connecting to Vector Database",
        "Establishing connection to Supabase pgvector with 3,397 StatPearls chunks"
    )
    
    logger.info("\n🚀 Initializing Clinical Pipeline...")
    pipeline = ClinicalPipeline()
    logger.info("✅ Pipeline initialized successfully!\n")
    
    # ========== PHASE 2: REQUEST CREATION ==========
    print_phase_header(2, "REQUEST INTAKE")
    
    explain_step(
        "📝", "Creating Request Object",
        "Packaging your clinical note into a structured request format"
    )
    
    request = ClinicalNoteRequest(
        patient_id=f"hackathon_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        content=clinical_note,
        input_type=InputType.TEXT
    )
    
    logger.info(f"✅ Request created: {request.patient_id}\n")
    
    # ========== PHASE 3-29: PIPELINE EXECUTION ==========
    print_phase_header(3, "DOCUMENT PROCESSING & CLINICAL ANALYSIS")
    
    explain_step(
        "📄", "Phase 3: Document Ingestion",
        "Converting input to plain text (already text, so this is quick)"
    )
    
    explain_step(
        "🧹", "Phase 4: Text Normalization",
        "Cleaning whitespace, preserving medical sections, standardizing format"
    )
    
    explain_step(
        "🔍", "Phase 11A: Signal Extraction",
        "Using Gemini to identify symptoms, labs, timeline, vitals from your note"
    )
    
    explain_step(
        "💡", "Phase 11B: Hypothesis Generation",
        "Generating initial differential diagnosis hypotheses based on clinical patterns"
    )
    
    explain_step(
        "🧮", "Phase 6: Creating Embeddings",
        "Converting your clinical note to 768-dimensional vector using sentence-transformers"
    )
    
    explain_step(
        "🔎", "Phase 9: RAG Retrieval",
        "Searching StatPearls database for similar medical literature (cosine similarity)"
    )
    
    explain_step(
        "🤖", "Phase 12-13: LLM Synthesis",
        "Gemini analyzes patient note + StatPearls evidence → generates summary + differentials"
    )
    
    explain_step(
        "✅", "Phase 14-15: Validation & Scoring",
        "Checking for contradictions, computing confidence scores based on evidence strength"
    )
    
    logger.info("\n🔄 Executing full pipeline (this may take 30-60 seconds)...\n")
    
    start_time = datetime.now()
    
    try:
        response = pipeline.process_clinical_note(request)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"\n✅ Pipeline completed in {duration:.2f} seconds!")
        logger.info(f"   Status: {response.status}")
        logger.info(f"   Evidence retrieved: {response.total_evidence_retrieved} chunks")
        logger.info(f"   Diagnoses generated: {len(response.differential_diagnoses)}")
        
        # ========== SAVE OUTPUT ==========
        print_phase_header(29, "OUTPUT GENERATION")
        
        explain_step(
            "💾", "Saving Formatted Output",
            "Writing comprehensive report to OUTPUT1.txt with all details"
        )
        
        output_file = save_output(response, clinical_note, output_num=1)
        
        # Print summary
        print("\n" + "="*80)
        print("🎉 PIPELINE EXECUTION COMPLETE!")
        print("="*80)
        print(f"\n✅ Status: {response.status}")
        print(f"✅ Processing time: {response.processing_time_seconds:.2f}s")
        print(f"✅ Evidence retrieved: {response.total_evidence_retrieved} chunks")
        print(f"✅ Differential diagnoses: {len(response.differential_diagnoses)}")
        print(f"✅ Output saved to: {output_file}")
        
        if response.summary:
            print(f"\n📋 Summary Preview:")
            print(f"   Chief Complaint: {response.summary.chief_complaint}")
            print(f"   Timeline: {response.summary.timeline}")
        
        if response.differential_diagnoses:
            print(f"\n🔬 Top 3 Diagnoses:")
            for dx in response.differential_diagnoses[:3]:
                print(f"   {dx.priority}. {dx.diagnosis} (confidence: {dx.confidence.overall_confidence:.2f})")
        
        print("\n" + "="*80)
        print(f"📁 Full detailed report available in: {output_file}")
        print("="*80 + "\n")
        
        # Also save JSON version
        json_file = f"OUTPUT{1}_raw.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(response.model_dump(), f, indent=2, default=str)
        logger.info(f"📁 JSON version saved to: {json_file}")
        
    except Exception as e:
        logger.error(f"\n❌ Pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
