/**
 * API Client for Clinical ML Pipeline
 * Handles all communication with FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface AnalysisRequest {
    input_type: 'text' | 'file';
    content: string;
    patient_id?: string;
}

export interface AnalysisResponse {
    request_id: string;
    clinical_summary: {
        summary_text: string;
        chief_complaint?: string;
        symptoms?: string[];
        negations?: string[];
        timeline?: string;
        clinical_findings?: string;
        red_flags?: Array<{
            flag: string;
            severity: string;
            keywords: string[];
        }>;
    };
    differential_diagnoses: Array<{
        id: number;
        condition: string;
        confidence: number;
        severity: string;
        source: string;
        reasoning: string;
        evidence: Array<{
            source: string;
            excerpt: string;
            similarity: number;
            keywords: string[];
        }>;
        nextSteps: string[];
    }>;
    extracted_data?: {
        atomic_symptoms?: Array<{
            id: string;
            symptom: string;
            detail: string;
            severity: number;
            status: 'present' | 'absent';
            organ: string;
            keywords: string[];
        }>;
        demographics?: {
            age?: number;
            sex?: string;
        };
        triggers?: string[];
        relieving_factors?: string[];
        temporal_pattern?: string;
        risk_factors?: string[];
        clinical_red_flags?: string[];
    };
    metadata?: {
        processing_time_seconds: number;
        model_version?: string;
        timestamp: string;
        time?: string;
        model?: string;
        confidence?: string;
    };
    original_text?: string;
    uncertainty?: {
        level: string;
        basis: string;
        missing_categories: string[];
    };
}

export interface Patient {
    id: string;
    name: string;
    age: number;
    sex: string;
    patient_id: string;
    location?: string;
    status?: 'URGENT' | 'IN PROGRESS' | 'REVIEWED';
    last_updated?: string;
}

class ApiClient {
    private baseUrl: string;

    constructor(baseUrl: string = API_BASE_URL) {
        this.baseUrl = baseUrl;
    }

    /**
     * Analyze clinical note (text input)
     */
    async analyzeText(text: string, patientId?: string): Promise<AnalysisResponse> {
        try {
            const response = await fetch(`${this.baseUrl}/api/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    input_type: 'text',
                    content: text,
                    patient_id: patientId || `TEMP-${Date.now()}`,
                }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Analysis failed');
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    /**
     * Upload and analyze file (PDF, TXT, etc.)
     */
    async uploadFile(file: File, patientId?: string): Promise<AnalysisResponse> {
        try {
            const formData = new FormData();
            formData.append('file', file);
            if (patientId) {
                formData.append('patient_id', patientId);
            }

            const response = await fetch(`${this.baseUrl}/api/analyze/upload`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'File upload failed');
            }

            return await response.json();
        } catch (error) {
            console.error('Upload Error:', error);
            throw error;
        }
    }

    /**
     * Get request status
     */
    async getRequestStatus(requestId: string) {
        const response = await fetch(`${this.baseUrl}/api/status/${requestId}`);
        if (!response.ok) throw new Error('Failed to get status');
        return await response.json();
    }

    /**
     * Get system statistics
     */
    async getSystemStats() {
        const response = await fetch(`${this.baseUrl}/stats`);
        if (!response.ok) throw new Error('Failed to get stats');
        return await response.json();
    }

    /**
     * Health check
     */
    async healthCheck() {
        try {
            const response = await fetch(`${this.baseUrl}/health`, {
                method: 'GET',
            });
            return response.ok;
        } catch {
            return false;
        }
    }

    // Future endpoints (to be implemented)

    async getPatients(): Promise<Patient[]> {
        // TODO: Implement when backend endpoint is ready
        return [];
    }

    async getPatient(id: string): Promise<Patient | null> {
        // TODO: Implement when backend endpoint is ready
        return null;
    }

    async createPatient(patient: Partial<Patient>): Promise<Patient> {
        // TODO: Implement when backend endpoint is ready
        throw new Error('Not implemented');
    }
}

// Export singleton instance
export const api = new ApiClient();

// Export class for testing
export default ApiClient;
