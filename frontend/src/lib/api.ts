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
    clinical_summary?: {
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
    summary?: { // Backend uses this field name
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
    red_flags?: Array<{ // Backend might put this at root level
        flag: string;
        severity: string;
        keywords: string[];
    }>;
    differential_diagnoses: Array<{
        id: number;
        condition?: string;
        diagnosis?: string; // Backend uses this field name sometimes
        confidence?: {
            overall_confidence: number;
            evidence_strength: number;
            reasoning_consistency: number;
            citation_count: number;
            uncertainty?: number;
            lower_bound?: number;
            upper_bound?: number;
            uncertainty_sources?: string[];
        };
        confidence_score?: number; // Fallback if confidence object doesn't exist
        severity: string;
        source: string;
        reasoning: string;
        evidence?: Array<{
            source: string;
            excerpt?: string;
            content?: string; // Backend uses this field name sometimes
            similarity?: number;
            similarity_score?: number; // Backend uses this field name sometimes
            keywords?: string[];
            citation?: string;
        }>;
        supporting_evidence?: Array<{ // Backend uses this field name sometimes
            source: string;
            excerpt?: string;
            content?: string;
            similarity?: number;
            similarity_score?: number;
            keywords?: string[];
            citation?: string;
        }>;
        nextSteps?: string[];
        next_steps?: string[]; // Backend uses this field name sometimes
    }>;
    extracted_data?: {
        atomic_symptoms?: Array<{
            id: string;
            symptom?: string;
            base_symptom?: string; // Backend uses this field name sometimes
            detail?: string;
            quality?: string; // Backend uses this field name sometimes
            severity?: number;
            status: 'present' | 'absent';
            organ?: string;
            keywords?: string[];
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
        processing_time_seconds?: number;
        model_version?: string;
        timestamp?: string;
        time?: string;
        model?: string;
        confidence?: string;
    };
    processing_time_seconds?: number; // Backend puts this at root level
    original_text?: string;
    content?: string; // Backend might use this field name
    action_plan?: {
        immediate?: Array<{
            id: string;
            action: string;
            time?: string;
        }>;
        followUp?: Array<{
            id: string;
            action: string;
            time?: string;
        }>;
    };
    uncertainty?: {
        level: string;
        basis: string;
        missing_categories: string[];
    };
    total_evidence_retrieved?: number;
}

export interface AdditionalDataResponse {
    request_id: string;
    red_flags: Array<{
        flag: string;
        severity: string;
        keywords: string[];
    }>;
    action_plan: {
        immediate?: Array<{
            id: string;
            action: string;
            time?: string;
        }>;
        followUp?: Array<{
            id: string;
            action: string;
            time?: string;
        }>;
    };
    error?: string;
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
                // Handle both string and object error details
                const errorMessage = typeof error.detail === 'object'
                    ? JSON.stringify(error.detail)
                    : (error.detail || 'Analysis failed');

                // Don't throw Error (triggers Next.js overlay), return rejected promise
                return Promise.reject({
                    message: errorMessage,
                    status: response.status
                });
            }

            return await response.json();
        } catch (error: any) {
            // Check if it's our custom rejection
            if (error.message && error.status) {
                return Promise.reject(error);
            }
            console.error('API Error:', error);
            return Promise.reject({
                message: 'Network error or server unavailable',
                status: 0
            });
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
     * Get additional analysis info (Red Flags and Action Plan)
     * This is the "Call #2" in the progressive loading strategy.
     */
    async getAdditionalInfo(requestId: string): Promise<AdditionalDataResponse> {
        try {
            const response = await fetch(`${this.baseUrl}/api/analyze/additional/${requestId}`);
            if (!response.ok) {
                throw new Error('Failed to fetch additional info');
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching additional info:', error);
            return {
                request_id: requestId,
                red_flags: [],
                action_plan: { immediate: [], followUp: [] }
            };
        }
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
