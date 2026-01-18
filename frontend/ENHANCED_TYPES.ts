/**
 * Enhanced API Response Types
 * Add these to your existing AnalysisResponse interface in src/lib/api.ts
 */

// ADD THESE NEW INTERFACES:

export interface ExtractedVital {
    name: string;
    value: string;
    unit: string;
    status: 'normal' | 'high' | 'low';
    icon: string;
    normal: string;
}

export interface RiskScore {
    name: string;
    value: number;
    max: number;
    risk: 'High' | 'Intermediate' | 'Low';
    color: string;
    desc: string;
}

export interface KeyEntities {
    medications: Array<{
        name: string;
        dose: string;
        freq: string;
        class: string;
    }>;
    history: Array<{
        condition: string;
        status: string;
    }>;
    social: Array<{
        factor: string;
        detail: string;
        risk: string;
    }>;
}

export interface ActionPlan {
    immediate: Array<{
        id: string;
        action: string;
        priority: string;
        time: string;
    }>;
    labs: Array<{
        id: string;
        test: string;
        time: string;
    }>;
    referrals: Array<{
        id: string;
        spec: string;
        urgency: string;
        reason: string;
    }>;
}

export interface MissingDataField {
    field: string;
    importance: 'Critical' | 'High' | 'Medium' | 'Low';
}

// UPDATE YOUR EXISTING AnalysisResponse INTERFACE:
// Add these fields:

export interface AnalysisResponse {
    // ... existing fields ...

    // NEW: Enhanced fields for advanced UI
    extracted_vitals?: ExtractedVital[];
    risk_scores?: RiskScore[];
    key_entities?: KeyEntities;
    action_plan?: ActionPlan;
    missing_data?: MissingDataField[];
    original_text?: string;
}
