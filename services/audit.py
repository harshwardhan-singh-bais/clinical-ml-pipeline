"""
Audit Logging Service
Phase 18: Data Persistence & Audit Logs

Provides:
- Request/response logging
- Traceability
- Compliance tracking
- Debugging support
"""

import logging
import hashlib
import json
from datetime import datetime
from typing import Dict, Optional
from supabase import Client
from models.schemas import AuditLogEntry, ProcessingStatus
from config.settings import settings

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Audit logging service for compliance and traceability.
    
    Phase 18: Data Persistence & Audit Logs
    
    Stores:
    - Input hash (for integrity)
    - Retrieved PMC IDs
    - Output JSON
    - Processing metadata
    - Timestamps
    """
    
    AUDIT_TABLE = "audit_logs"
    
    def __init__(self, supabase_client: Client = None):
        """
        Initialize audit logger.
        
        Args:
            supabase_client: Supabase client (optional)
        """
        if supabase_client:
            self.client = supabase_client
        else:
            # Create new client if not provided
            from supabase import create_client
            self.client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
        
        logger.info("AuditLogger initialized")
    
    def _compute_input_hash(self, text: str) -> str:
        """
        Compute SHA256 hash of input text.
        
        Phase 18: Input integrity tracking
        
        Args:
            text: Input text
        
        Returns:
            SHA256 hash (hex)
        """
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def create_audit_log(
        self,
        request_id: str,
        patient_id: Optional[str],
        input_text: str,
        retrieved_evidence: list,
        output_data: Dict,
        processing_time_seconds: float,
        status: ProcessingStatus,
        error_details: Optional[str] = None
    ) -> bool:
        """
        Create audit log entry.
        
        Phase 18: Log creation
        
        Args:
            request_id: Unique request identifier
            patient_id: Patient identifier (optional)
            input_text: Original input text
            retrieved_evidence: List of retrieved PMC chunks
            output_data: Final output dictionary
            processing_time_seconds: Total processing time
            status: Processing status
            error_details: Error message if failed
        
        Returns:
            True if successful
        """
        try:
            # Compute input hash
            input_hash = self._compute_input_hash(input_text)
            
            # Extract PMC IDs from evidence
            retrieved_pmc_ids = [
                e.get("pmcid", "unknown")
                for e in retrieved_evidence
            ]
            
            # Serialize output JSON (handle datetime objects)
            def json_serializer(obj):
                """Custom JSON serializer for datetime objects."""
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Type {type(obj)} not serializable")
            
            output_json = json.dumps(output_data, default=json_serializer)
            
            # Create audit log entry
            audit_entry = {
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "patient_id": patient_id,
                "input_hash": input_hash,
                "retrieved_pmc_ids": retrieved_pmc_ids,
                "output_json": output_json,
                "processing_time_seconds": processing_time_seconds,
                "status": status.value,
                "error_details": error_details
            }
            
            # Insert into Supabase
            response = self.client.table(self.AUDIT_TABLE).insert(audit_entry).execute()
            
            logger.info(f"Audit log created for request: {request_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            # Don't fail the main request if audit logging fails
            return False
    
    def get_audit_log(self, request_id: str) -> Optional[Dict]:
        """
        Retrieve audit log by request ID.
        
        Args:
            request_id: Request identifier
        
        Returns:
            Audit log entry or None
        """
        try:
            response = self.client.table(self.AUDIT_TABLE)\
                .select("*")\
                .eq("request_id", request_id)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve audit log: {e}")
            return None
    
    def get_recent_logs(self, limit: int = 100) -> list:
        """
        Get recent audit logs.
        
        Args:
            limit: Maximum number of logs to retrieve
        
        Returns:
            List of audit log entries
        """
        try:
            response = self.client.table(self.AUDIT_TABLE)\
                .select("*")\
                .order("timestamp", desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Failed to retrieve recent logs: {e}")
            return []
    
    def get_patient_logs(self, patient_id: str) -> list:
        """
        Get all audit logs for a specific patient.
        
        Args:
            patient_id: Patient identifier
        
        Returns:
            List of audit log entries for patient
        """
        try:
            response = self.client.table(self.AUDIT_TABLE)\
                .select("*")\
                .eq("patient_id", patient_id)\
                .order("timestamp", desc=True)\
                .execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Failed to retrieve patient logs: {e}")
            return []
    
    def create_audit_table_schema(self) -> str:
        """
        SQL schema for audit logs table.
        
        Run this in Supabase SQL Editor to create the table.
        
        Returns:
            SQL schema string
        """
        schema = """
        -- Audit logs table for Phase 18: Data Persistence & Audit Logs
        CREATE TABLE IF NOT EXISTS audit_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            request_id TEXT UNIQUE NOT NULL,
            timestamp TIMESTAMPTZ NOT NULL,
            patient_id TEXT,
            input_hash TEXT NOT NULL,
            retrieved_pmc_ids TEXT[],
            output_json JSONB NOT NULL,
            processing_time_seconds FLOAT NOT NULL,
            status TEXT NOT NULL,
            error_details TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Indexes for faster queries
        CREATE INDEX IF NOT EXISTS audit_logs_request_id_idx ON audit_logs(request_id);
        CREATE INDEX IF NOT EXISTS audit_logs_patient_id_idx ON audit_logs(patient_id);
        CREATE INDEX IF NOT EXISTS audit_logs_timestamp_idx ON audit_logs(timestamp DESC);
        CREATE INDEX IF NOT EXISTS audit_logs_status_idx ON audit_logs(status);
        
        -- Enable Row Level Security (optional)
        ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
        """
        
        logger.info("Audit logs table schema:")
        logger.info(schema)
        
        return schema


# ========== LIGHTWEIGHT LOGGING (FILE-BASED FALLBACK) ==========

class FileAuditLogger:
    """
    File-based audit logger (fallback if Supabase unavailable).
    """
    
    def __init__(self, log_file: str = "audit_logs.jsonl"):
        """
        Initialize file-based audit logger.
        
        Args:
            log_file: Path to audit log file
        """
        self.log_file = log_file
        logger.info(f"FileAuditLogger initialized: {log_file}")
    
    def log_request(
        self,
        request_id: str,
        input_text: str,
        output_data: Dict,
        processing_time: float,
        status: ProcessingStatus
    ):
        """
        Log request to file.
        
        Args:
            request_id: Request ID
            input_text: Input text
            output_data: Output data
            processing_time: Processing time
            status: Status
        """
        try:
            log_entry = {
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "input_hash": hashlib.sha256(input_text.encode()).hexdigest(),
                "input_length": len(input_text),
                "output_diagnoses_count": len(output_data.get("differential_diagnoses", [])),
                "processing_time_seconds": processing_time,
                "status": status.value
            }
            
            # Append to JSONL file
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            logger.debug(f"Logged request to file: {request_id}")
            
        except Exception as e:
            logger.error(f"Failed to log to file: {e}")
