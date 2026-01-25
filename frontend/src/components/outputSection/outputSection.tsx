"use client";

import React, { useState } from "react";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  Brain,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  FileText,
  Heart,
  Search,
  Stethoscope,
  XCircle,
  Wind,
  Droplets,
  Gauge,
  Zap,
  Clock,
  Calendar
} from "lucide-react";
import { AnalysisResponse, AdditionalDataResponse } from "@/lib/api";

// --- STYLES ---
const glassCard = "bg-[rgba(255,255,255,0.18)] backdrop-blur-[0.9px] border border-[rgba(255,255,255,0.76)] shadow-[0_8px_30px_rgba(0,0,0,0.04)] rounded-2xl";
const glassBtn = "flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-xl transition-all font-semibold shadow-sm duration-300";

const activeBtn = "bg-gradient-to-r from-[#4facfe] to-[#00f2fe] text-white shadow-[0_4px_15px_rgba(0,242,254,0.3)] translate-y-[-2px]";
const inactiveBtn = "bg-white/40 text-slate-600 hover:bg-white hover:text-[#00f2fe] border border-white/60";

interface OutputSectionProps {
  isVisible?: boolean;
  data?: AnalysisResponse | null;
  additionalData?: AdditionalDataResponse | null;
  isFetchingAdditional?: boolean;
}


const OutputSection = ({
  isVisible = true,
  data = null,
  additionalData = null,
  isFetchingAdditional = false
}: OutputSectionProps) => {
  // 🔍 DEBUG: Log the API response to check if severity exists
  console.log("🔍 Full API Response:", data);
  console.log("🔍 Differential Diagnoses:", data?.differential_diagnoses);
  if (data?.differential_diagnoses?.[0]) {
    console.log("🔍 First Diagnosis Object:", data.differential_diagnoses[0]);
    console.log("🔍 Severity field:", data.differential_diagnoses[0].severity);
    console.log("🔍 Next Steps field:", data.differential_diagnoses[0].next_steps);
  }

  const [activeTab, setActiveTab] = useState("summary");
  const [highlightedText, setHighlightedText] = useState<string[]>([]);
  const [selectedSymptom, setSelectedSymptom] = useState<any>(null);
  const [expandedEvidence, setExpandedEvidence] = useState<Record<number, boolean>>({});
  const [checkedActions, setCheckedActions] = useState<Record<string, boolean>>({});
  const [analysisVideo, setAnalysisVideo] = useState<string | null>(null);

  if (!isVisible) return null;

  // === USE REAL DATA FROM API (NO MORE MOCK DATA!) ===

  // Original clinical text - check multiple possible locations
  const originalText = data?.original_text || data?.content || "";

  // Patient info
  const patientInfo = {
    id: data?.request_id || "No MRN",
    age: data?.extracted_data?.demographics?.age || "Unknown",
    sex: data?.extracted_data?.demographics?.sex || "Unknown",
    chiefComplaint: data?.clinical_summary?.chief_complaint || data?.summary?.chief_complaint || "Not specified"
  };

  // Metadata
  const metadata = {
    time: data?.metadata?.time ||
      (data?.metadata?.processing_time_seconds ? `${data.metadata.processing_time_seconds.toFixed(1)}s` :
        data?.processing_time_seconds ? `${data.processing_time_seconds.toFixed(1)}s` : "N/A"),
    model: data?.metadata?.model || data?.metadata?.model_version || "Gemini 1.5 Flash (RAG)",
    confidence: (data as any)?.total_evidence_retrieved !== undefined ? `${(data as any).total_evidence_retrieved} Evidence Matches` : "N/A"
  };

  // AI Summary - Backend returns 'summary' not 'clinical_summary'!
  const summaryText = data?.clinical_summary?.summary_text || data?.summary?.summary_text || "No summary available. Backend did not return analysis.";

  // Use additionalData for red flags if available, otherwise fallback to data
  const redFlags = additionalData?.red_flags || data?.clinical_summary?.red_flags || data?.red_flags || [];

  // 🔍 DEBUG: Check red_flags structure
  console.log("🔍 Red Flags from API:", redFlags);
  console.log("🔍 Red Flags type:", typeof redFlags, Array.isArray(redFlags) ? `Array of ${redFlags.length} items` : 'Not an array');

  // Differential Diagnoses - USE REAL DATA ONLY
  const differentialDiagnoses = data?.differential_diagnoses || [];

  // Atomic Symptoms - Extract from BOTH sources
  // Backend returns symptoms in summary.symptoms array AND extracted_data.atomic_symptoms
  const rawSymptoms = data?.summary?.symptoms || data?.clinical_summary?.symptoms || [];
  const atomicSymptomsFromData = data?.extracted_data?.atomic_symptoms || [];

  // Convert summary.symptoms array to atomic symptom format
  const symptomsFromSummary = rawSymptoms.map((symptom: string, idx: number) => ({
    id: `s${idx + 1}`,
    symptom: symptom,
    base_symptom: symptom,
    detail: "",
    severity: null,
    status: "present" as const,
    organ: "general",
    keywords: [symptom]
  }));

  // Combine both sources (prefer extracted_data if available)
  const atomicSymptoms = atomicSymptomsFromData.length > 0 ? atomicSymptomsFromData : symptomsFromSummary;

  // Organ images (static URLs, not mock data)
  const organImages: Record<string, string> = {
    heart: "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Heart_diagram-en.svg/400px-Heart_diagram-en.svg.png",
    lungs: "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Lungs_diagram_detailed.svg/400px-Lungs_diagram_detailed.svg.png",
    stomach: "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Stomach_diagram.svg/300px-Stomach_diagram.svg.png",
    general: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Human_body_silhouette.svg/200px-Human_body_silhouette.svg.png"
  };

  // Simple markdown to HTML converter
  const convertMarkdownToHTML = (markdown: string): string => {
    return markdown
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>') // Bold
      .replace(/\*(.+?)\*/g, '<em>$1</em>') // Italic
      .replace(/^### (.+)$/gm, '<h3 class="font-bold text-lg mt-4 mb-2">$1</h3>') // H3
      .replace(/^## (.+)$/gm, '<h2 class="font-bold text-xl mt-4 mb-2">$1</h2>') // H2
      .replace(/^# (.+)$/gm, '<h1 class="font-bold text-2xl mt-4 mb-2">$1</h1>') // H1
      .replace(/^• (.+)$/gm, '<li class="ml-4">$1</li>') // Bullet points
      .replace(/\n\n/g, '</p><p class="mt-2">') // Paragraphs
      .replace(/\n/g, '<br/>'); // Line breaks
  };

  // Action Plan data from API
  const actionPlan = additionalData?.action_plan || data?.action_plan || {
    immediate: [],
    followUp: []
  };

  const totalActions = (actionPlan.immediate?.length || 0) + (actionPlan.followUp?.length || 0);

  // --- VIDEO LOGIC ---
  const videoMapping = [
    { keywords: ["axial skeleton", "skeleton", "spine", "bone"], filename: "Axial Skeleton.mp4" },
    { keywords: ["brain", "neurological", "head", "headache", "migraine", "cerebral", "mental"], filename: "Brain.mp4" },
    { keywords: ["kidney", "renal", "dialysis", "nephrology"], filename: "Kidney.mp4" },
    { keywords: ["left forearm", "left arm", "forearm"], filename: "Left Forearm.mp4" },
    { keywords: ["lungs", "respiratory", "chest pain", "pneumonia", "asthma", "breath", "cough", "breathing"], filename: "Lungs.mp4" },
    { keywords: ["pancreas", "pancreatic", "insulin", "diabetes"], filename: "Pancreas.mp4" },
    { keywords: ["right leg", "leg pain", "right knee"], filename: "Right Leg.mp4" },
    { keywords: ["vascular", "vein", "artery", "blood flow", "circulatory", "vascular network", "heart", "cardio"], filename: "Vascular Network.mp4" },
    { keywords: ["gastric", "stomach", "gastritis", "gastric function", "abdominal"], filename: "gastric function.mp4" },
    { keywords: ["gut", "intestine", "bowel", "gut health", "digestion"], filename: "gut health.mp4" },
    { keywords: ["wrist", "wrist pain", "carpal"], filename: "wrist pain.mp4" }
  ];

  React.useEffect(() => {
    if (!data) return;

    // Combine all text to search for initial match
    const allText = `${summaryText} ${differentialDiagnoses.map((d: any) => d.condition || d.diagnosis).join(" ")} ${originalText}`.toLowerCase();

    // Find the first matching video
    const match = videoMapping.find(v =>
      v.keywords.some(keyword => allText.includes(keyword.toLowerCase()))
    );

    if (match) {
      console.log("🎥 Initial video match:", match.filename);
      setAnalysisVideo(`/videos/${match.filename}`);
    } else {
      setAnalysisVideo(null);
    }
  }, [data, summaryText, differentialDiagnoses, originalText]);

  // --- LOGIC ---
  const handleSymptomClick = (symptom: any) => {
    setSelectedSymptom(symptom);
    setHighlightedText(symptom.keywords || []);

    // Try to find a more specific video for this symptom
    const organ = (symptom.organ || "").toLowerCase();
    const symptomText = (symptom.symptom || symptom.base_symptom || "").toLowerCase();

    const specificMatch = videoMapping.find(v =>
      v.keywords.some(k => organ.includes(k)) ||
      v.keywords.some(k => symptomText.includes(k))
    );

    if (specificMatch) {
      console.log("🎥 Symptom-specific video match:", specificMatch.filename);
      setAnalysisVideo(`/videos/${specificMatch.filename}`);
    }
  };

  const toggleEvidence = (id: number) => {
    setExpandedEvidence(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const toggleAction = (id: string) => {
    setCheckedActions(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const highlightTextInNote = (text: string, keywords: string[]) => {
    if (!text || !keywords || keywords.length === 0) return text;
    let highlighted = text;
    keywords.forEach(keyword => {
      const regex = new RegExp(`(${keyword})`, 'gi');
      highlighted = highlighted.replace(regex, '<mark class="bg-[#00f2fe]/30 text-slate-900 rounded-sm px-0.5">$1</mark>');
    });
    return highlighted;
  };

  return (
    <div className="w-full text-slate-800 animate-in fade-in duration-700">

      {/* 1. Header Area */}
      <div className="flex flex-col md:flex-row items-center justify-between mb-6 px-1">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Activity className="w-6 h-6 text-[#00f2fe]" /> GenAI Clinical Analysis
          </h2>
          <p className="text-slate-500 text-sm font-medium ml-8">
            Model: {metadata.model} • Time: {metadata.time} • Confidence: {metadata.confidence}
          </p>
        </div>
        <div className="text-right hidden md:block">
          <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Patient MRN</div>
          <div className="text-xl font-bold text-slate-800 font-mono">{patientInfo.id}</div>
        </div>
      </div>

      {/* 2. Navigation Tabs (Sticky) */}
      <div className="sticky top-0 z-50 bg-[#f5f7fa]/95 backdrop-blur-xl border-b border-white/50 py-3 mb-6 -mx-4 px-4 transition-all duration-300">
        <div className="flex gap-4">
          {[
            { id: 'summary', label: 'Clinical Summary', icon: FileText },
            { id: 'diagnosis', label: 'Differential Diagnosis', icon: Brain },
            { id: 'symptoms', label: 'Symptom Analysis', icon: Stethoscope },
            { id: 'evidence', label: 'RAG Evidence', icon: Search },
            { id: 'actionplan', label: 'Action Plan', icon: Zap }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`${glassBtn} ${activeTab === tab.id ? activeBtn : inactiveBtn}`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* 3. Content Area */}

      {/* --- TAB: SUMMARY --- */}
      {activeTab === 'summary' && (
        <div className="flex flex-col gap-6">

          {/* A. AI Summary */}
          <div className={`${glassCard} p-8`}>
            <h3 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
              <Brain className="w-6 h-6 text-purple-600" /> AI Generated Summary
            </h3>
            <div className="bg-blue-50/50 border border-blue-100 rounded-2xl p-6">
              <div
                className="text-lg text-slate-700 leading-relaxed font-medium"
                dangerouslySetInnerHTML={{ __html: convertMarkdownToHTML(summaryText) }}
              />
            </div>
          </div>

          {/* B. Grid: Original Note (Left) & Red Flags (Right) */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

            {/* Original Clinical Note */}
            <div className={`${glassCard} p-6 h-full flex flex-col`}>
              <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5 text-[#00f2fe]" /> Original Clinical Note
              </h3>
              <div className="flex-1 bg-white/50 border border-white/60 rounded-xl p-5 text-slate-700 leading-relaxed font-mono text-sm shadow-inner max-h-[300px] overflow-y-auto">
                {originalText ? (
                  <div dangerouslySetInnerHTML={{ __html: highlightTextInNote(originalText, highlightedText) }} />
                ) : (
                  <p className="text-slate-400 text-center">No clinical note available</p>
                )}
              </div>
              <p className="mt-3 text-center text-[10px] text-slate-400">
                Click a red flag to highlight the source text here.
              </p>
            </div>

            {/* Critical Red Flags */}
            <div className="bg-red-50/80 border border-red-100 rounded-2xl p-6 shadow-sm">
              <h3 className="text-lg font-bold text-red-700 mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-red-600 animate-pulse" /> Critical Red Flags
              </h3>
              <div className="space-y-3">
                {isFetchingAdditional ? (
                  <div className="flex flex-col items-center justify-center py-6 gap-3">
                    <div className="w-8 h-8 border-4 border-red-200 border-t-red-600 rounded-full animate-spin"></div>
                    <p className="text-xs font-bold text-red-700 animate-pulse uppercase tracking-wider">Analyzing risk profile...</p>
                  </div>
                ) : redFlags.length > 0 ? (
                  redFlags.map((flag: any, idx: number) => (
                    <div
                      key={idx}
                      className="bg-white/60 border border-red-200 rounded-xl p-3 cursor-pointer hover:bg-white hover:shadow-md transition-all flex items-start gap-3 group"
                      onClick={() => setHighlightedText(flag.keywords || [])}
                    >
                      <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
                      <div>
                        <span className="font-bold text-slate-800 block group-hover:text-red-700 transition-colors">{flag.flag}</span>
                        <span className="text-xs text-red-400 font-semibold uppercase tracking-wider">{flag.severity}</span>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-slate-500 text-sm text-center py-4">No critical red flags identified</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* --- TAB: DIAGNOSIS --- */}
      {activeTab === 'diagnosis' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 relative">
          <div className="lg:col-span-4 h-full">
            <div className={`${glassCard} p-6 sticky top-24 max-h-[80vh] overflow-y-auto`}>
              <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                <FileText className="w-4 h-4 text-[#00f2fe]" /> Live Context
              </h3>
              <div className="text-xs text-slate-600 font-mono leading-relaxed opacity-90 p-3 bg-white/40 rounded-xl border border-white/50">
                {originalText ? (
                  <div dangerouslySetInnerHTML={{ __html: highlightTextInNote(originalText, highlightedText) }} />
                ) : (
                  <p className="text-slate-400 text-center">No clinical text available</p>
                )}
              </div>
              <div className="mt-4 p-3 bg-blue-50/50 rounded-xl border border-blue-100">
                <p className="text-[10px] text-blue-500 font-bold uppercase mb-1">Tip</p>
                <p className="text-xs text-blue-700">
                  Click any highlighted evidence on the right to locate it instantly in the text above.
                </p>
              </div>
            </div>
          </div>

          <div className="lg:col-span-8 space-y-4">
            {differentialDiagnoses.length > 0 ? (
              differentialDiagnoses.map((diag, idx) => (
                <div key={diag.id || idx} className={`${glassCard} overflow-hidden group`}>
                  <div className="p-6 border-b border-white/50">
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex items-center gap-4">
                        <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-[#4facfe] to-[#00f2fe] text-white font-bold text-lg shadow-lg shadow-blue-500/30">
                          #{idx + 1}
                        </div>
                        <div>
                          <h3 className="text-xl font-bold text-slate-800">{diag.condition || diag.diagnosis || "Unknown Diagnosis"}</h3>
                          <div className="flex gap-2 mt-1">
                            <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border bg-purple-50 text-purple-600 border-purple-100">
                              {diag.source || 'RAG'}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="bg-slate-50/50 rounded-xl p-4 border border-slate-100">
                      <p className="text-sm text-slate-700 font-medium leading-relaxed">
                        <span className="text-purple-600 font-bold mr-1">AI Reasoning:</span>
                        {diag.reasoning || "No reasoning provided"}
                      </p>
                    </div>
                  </div>

                  {/* Evidence Section */}
                  {(diag.evidence || diag.supporting_evidence) && ((diag.evidence?.length || 0) > 0 || (diag.supporting_evidence?.length || 0) > 0) && (
                    <>
                      <div
                        className="bg-white/40 hover:bg-white/60 p-3 cursor-pointer transition-colors flex items-center justify-center gap-2 text-sm font-semibold text-[#00f2fe] hover:text-[#4facfe]"
                        onClick={() => toggleEvidence(diag.id || idx)}
                      >
                        {expandedEvidence[diag.id || idx] ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                        View Evidence Sources ({(diag.evidence || diag.supporting_evidence)?.length || 0})
                      </div>
                      {expandedEvidence[diag.id || idx] && (
                        <div className="p-6 bg-slate-50/80 space-y-3 animate-in slide-in-from-top-2">
                          {(diag.evidence || diag.supporting_evidence)?.map((ev: any, i: number) => (
                            <div
                              key={i}
                              className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm cursor-pointer hover:border-[#4facfe] transition-all"
                              onClick={() => setHighlightedText(ev.keywords || [])}
                            >
                              <div className="flex justify-between items-start mb-2">
                                <span className="text-xs font-bold text-[#00f2fe] bg-blue-50 px-2 py-1 rounded border border-blue-100">
                                  {ev.source || "RAG Source"}
                                </span>
                                <span className="text-xs font-bold text-green-600">
                                  {ev.similarity || ev.similarity_score ? Math.round((ev.similarity || ev.similarity_score) * 100) : 'N/A'}% Match
                                </span>
                              </div>
                              <p className="text-sm text-slate-600 italic">&ldquo;{ev.excerpt || ev.content || "Evidence content"}&rdquo;</p>
                              {ev.citation && (
                                <p className="text-xs text-slate-400 mt-2">Citation: {ev.citation}</p>
                              )}
                            </div>
                          ))}

                          {/* Next Steps */}
                          {(diag.nextSteps || diag.next_steps) && ((diag.nextSteps?.length || 0) > 0 || (diag.next_steps?.length || 0) > 0) && (
                            <div className="mt-4 pt-4 border-t border-slate-200">
                              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 block">Recommended Actions</span>
                              <div className="flex flex-wrap gap-2">
                                {(diag.nextSteps || diag.next_steps)?.map((step: string, i: number) => (
                                  <span
                                    key={i}
                                    className="flex items-center gap-1.5 px-3 py-1.5 bg-green-50 text-green-700 border border-green-200 rounded-lg text-xs font-bold"
                                  >
                                    <CheckCircle className="w-3 h-3" /> {step}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </>
                  )}
                </div>
              ))
            ) : (
              <div className={`${glassCard} p-8 text-center`}>
                <p className="text-slate-500">No differential diagnoses available. Backend did not return diagnosis data.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* --- TAB: SYSTEM ANALYSIS (VIDEO REMOVED PER REQUEST) --- */}

      {/* --- TAB: SYMPTOMS --- --- REDACTED FOR BREVITY --- */}
      {activeTab === 'symptoms' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className={`${glassCard} p-6`}>
              <h3 className="text-lg font-bold text-green-700 mb-4 flex items-center gap-2">
                <CheckCircle className="w-5 h-5" /> Present Symptoms
              </h3>
              <div className="grid gap-3">
                {atomicSymptoms.filter((s: any) => s.status === 'present').length > 0 ? (
                  atomicSymptoms.filter((s: any) => s.status === 'present').map((s: any) => (
                    <div
                      key={s.id}
                      onClick={() => handleSymptomClick(s)}
                      className={`p-4 rounded-xl border cursor-pointer transition-all flex items-center justify-between ${selectedSymptom?.id === s.id ? 'bg-green-50 border-green-400 shadow-md scale-[1.02]' : 'bg-white/40 border-white/60 hover:border-green-300'}`}
                    >
                      <div>
                        <h4 className="font-bold text-slate-800">{s.symptom || s.base_symptom || "Symptom"}</h4>
                        <p className="text-xs text-slate-500">{s.detail || s.quality || ""}</p>
                      </div>
                      <span className="text-xs font-bold bg-red-100 text-red-600 px-2 py-1 rounded border border-red-200">
                        Sev: {s.severity || 'N/A'}/10
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="text-slate-500 text-center py-4">No present symptoms extracted</p>
                )}
              </div>
            </div>

            <div className={`${glassCard} p-6 opacity-80`}>
              <h3 className="text-lg font-bold text-slate-500 mb-4 flex items-center gap-2">
                <XCircle className="w-5 h-5" /> Negated Symptoms
              </h3>
              <div className="flex flex-wrap gap-2">
                {atomicSymptoms.filter((s: any) => s.status === 'absent').length > 0 ? (
                  atomicSymptoms.filter((s: any) => s.status === 'absent').map((s: any) => (
                    <div key={s.id} className="px-3 py-2 bg-slate-100 text-slate-500 rounded-lg border border-slate-200 text-sm font-medium line-through decoration-slate-400">
                      {s.symptom || s.base_symptom || "Symptom"}
                    </div>
                  ))
                ) : (
                  <p className="text-slate-500 text-sm">No negated symptoms identified</p>
                )}
              </div>
            </div>
          </div>

          <div className="lg:col-span-1">
            <div className={`${glassCard} p-6 sticky top-24 text-center`}>
              <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center justify-center gap-2">
                <Heart className="w-5 h-5 text-red-500" /> Organ Impact Map
              </h3>
              {selectedSymptom ? (
                <div className="animate-in fade-in zoom-in duration-300">
                  <div className="bg-blue-50 border border-blue-100 rounded-xl p-3 mb-6 inline-block">
                    <span className="text-xs font-bold text-[#4facfe] uppercase block mb-1">Selected Focus</span>
                    <span className="text-lg font-bold text-[#00f2fe]">{selectedSymptom.symptom || selectedSymptom.base_symptom}</span>
                  </div>
                  <div className="relative w-full aspect-square bg-black rounded-2xl border border-slate-200 overflow-hidden flex items-center justify-center">
                    {analysisVideo ? (
                      <video
                        key={analysisVideo} // Force re-render on video change
                        src={analysisVideo}
                        autoPlay
                        loop
                        muted
                        className="w-full h-full object-cover shadow-2xl"
                      />
                    ) : (
                      <img
                        src={organImages[selectedSymptom.organ] || organImages.general}
                        alt={selectedSymptom.organ}
                        className="max-h-full max-w-full object-contain drop-shadow-xl"
                      />
                    )}
                  </div>
                  <p className="mt-4 text-sm text-slate-500 font-medium">
                    {analysisVideo
                      ? "Dynamic system visualization based on selected symptom."
                      : `Visualizing pathology in the ${selectedSymptom.organ || 'general'} system.`}
                  </p>
                </div>
              ) : (
                <div className="h-64 flex flex-col items-center justify-center text-slate-400 border-2 border-dashed border-slate-200 rounded-2xl">
                  <Stethoscope className="w-12 h-12 mb-3 opacity-50" />
                  <p className="text-sm">Select a symptom to visualize</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* --- TAB: EVIDENCE (All Evidence Chunks) --- */}
      {activeTab === 'evidence' && (
        <div className="space-y-4">
          {differentialDiagnoses.length > 0 ? (
            differentialDiagnoses.map((diag: any, idx: number) => (
              <div key={diag.id || idx} className={`${glassCard} p-6`}>
                <h3 className="text-lg font-bold text-slate-800 mb-4 border-b border-white/50 pb-2 flex items-center justify-between">
                  <span>{diag.condition || diag.diagnosis || "Unknown Diagnosis"}</span>
                  <span className="text-sm font-normal text-slate-500">
                    {(diag.evidence || diag.supporting_evidence)?.length || 0} evidence chunk{(diag.evidence || diag.supporting_evidence)?.length !== 1 ? 's' : ''}
                  </span>
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {(diag.evidence || diag.supporting_evidence)?.length > 0 ? (
                    (diag.evidence || diag.supporting_evidence).map((ev: any, i: number) => (
                      <div key={i} className="bg-white/60 p-4 rounded-xl border border-white/80 hover:shadow-md transition-all">
                        <div className="flex justify-between mb-2">
                          <span className="text-xs font-bold text-[#00f2fe] bg-blue-50 px-2 py-1 rounded border border-blue-100">
                            {ev.source || "RAG Source"}
                          </span>
                          <span className="text-xs font-bold text-green-600">
                            {ev.similarity || ev.similarity_score ? Math.round((ev.similarity || ev.similarity_score) * 100) : 'N/A'}% Match
                          </span>
                        </div>
                        <p className="text-sm text-slate-600 italic">&ldquo;{ev.excerpt || ev.content || "Evidence content"}&rdquo;</p>
                        {ev.citation && (
                          <p className="text-xs text-slate-400 mt-2">Citation: {ev.citation}</p>
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="text-slate-500 text-sm col-span-2 text-center py-4">No evidence chunks available for this diagnosis</p>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className={`${glassCard} p-8 text-center`}>
              <p className="text-slate-500">No evidence available. Backend did not return diagnosis data.</p>
            </div>
          )}
        </div>
      )}

      {/* --- TAB: ACTION PLAN --- */}
      {activeTab === 'actionplan' && (
        <div className="space-y-6">

          {/* Header & Progress Card */}
          <div className={`${glassCard} p-6 border-l-4 border-l-emerald-500`}>
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-2xl bg-emerald-50 flex items-center justify-center text-emerald-600 shadow-sm border border-emerald-100">
                  <Zap className="w-8 h-8 fill-emerald-500/20" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-slate-800 tracking-tight">Clinical Action Plan</h3>
                  <p className="text-sm text-slate-500 font-medium">AI-synthesized pathways for patient recovery</p>
                </div>
              </div>

              <div className="flex flex-col items-end gap-1">
                <div className="flex items-center gap-3">
                  <span className="text-3xl font-black text-slate-800">
                    {Object.values(checkedActions).filter(Boolean).length}
                    <span className="text-slate-300 mx-1">/</span>
                    {totalActions}
                  </span>
                  <div className="px-3 py-1 bg-emerald-50 text-emerald-700 text-[10px] font-black uppercase tracking-wider rounded-full border border-emerald-100 italic">
                    {totalActions > 0 && Math.round((Object.values(checkedActions).filter(Boolean).length / totalActions) * 100)}% Complete
                  </div>
                </div>
                <div className="w-48 h-2.5 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
                  <div
                    className="h-full bg-gradient-to-r from-emerald-400 to-green-500 transition-all duration-700 ease-out shadow-[0_0_12px_rgba(16,185,129,0.3)]"
                    style={{ width: `${totalActions > 0 ? (Object.values(checkedActions).filter(Boolean).length / totalActions) * 100 : 0}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Main Action Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

            {/* Column 1: Immediate Actions */}
            <div className={`${glassCard} overflow-hidden border-t-4 border-t-red-500 h-full`}>
              <div className="p-5 border-b border-white/40 bg-red-50/20">
                <h4 className="font-bold text-red-700 flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 animate-pulse" />
                  Immediate Actions (STAT)
                </h4>
              </div>

              <div className="p-6">
                {isFetchingAdditional ? (
                  <div className="flex flex-col items-center justify-center py-20 gap-4">
                    <div className="w-12 h-12 border-4 border-red-100 border-t-red-500 rounded-full animate-spin"></div>
                    <p className="text-sm font-bold text-red-600 animate-pulse uppercase tracking-widest">Synthesizing STAT items...</p>
                  </div>
                ) : (actionPlan.immediate?.length ?? 0) > 0 ? (
                  <div className="space-y-4">
                    {actionPlan.immediate?.map((action: any) => (
                      <div
                        key={action.id}
                        onClick={() => toggleAction(action.id)}
                        className={`group relative p-4 rounded-2xl border transition-all duration-300 cursor-pointer overflow-hidden ${checkedActions[action.id]
                          ? 'bg-slate-50/50 border-slate-200 ring-1 ring-slate-100'
                          : 'bg-white border-slate-100 hover:border-red-200 hover:shadow-lg hover:shadow-red-500/5'
                          }`}
                      >
                        <div className="flex gap-4 relative z-10">
                          <div className={`mt-0.5 w-6 h-6 rounded-full border-2 flex items-center justify-center shrink-0 transition-all duration-300 ${checkedActions[action.id]
                            ? 'bg-emerald-500 border-emerald-500'
                            : 'border-slate-200 group-hover:border-red-400'
                            }`}>
                            {checkedActions[action.id] && <CheckCircle className="w-4 h-4 text-white" />}
                          </div>
                          <div className="flex-1">
                            <div className={`font-bold transition-all duration-300 ${checkedActions[action.id] ? 'text-slate-400 line-through' : 'text-slate-800'}`}>
                              {action.action}
                            </div>
                            <div className="flex items-center gap-3 mt-2">
                              <span className="flex items-center gap-1 text-[10px] font-black uppercase tracking-tighter text-red-500 bg-red-50 px-2 py-0.5 rounded border border-red-100">
                                <Clock className="w-2.5 h-2.5" /> {action.time || 'STAT'}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-12 flex flex-col items-center text-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-slate-50 flex items-center justify-center text-slate-300">
                      <CheckCircle className="w-6 h-6" />
                    </div>
                    <p className="text-sm text-slate-400 font-medium italic">No immediate actions required.</p>
                  </div>
                )}
              </div>
            </div>

            {/* Column 2: Follow-up Actions */}
            <div className={`${glassCard} overflow-hidden border-t-4 border-t-blue-500 h-full`}>
              <div className="p-5 border-b border-white/40 bg-blue-50/20">
                <h4 className="font-bold text-blue-700 flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  Follow-up Actions
                </h4>
              </div>

              <div className="p-6">
                {isFetchingAdditional ? (
                  <div className="flex flex-col items-center justify-center py-20 gap-4">
                    <div className="w-12 h-12 border-4 border-blue-100 border-t-blue-500 rounded-full animate-spin"></div>
                    <p className="text-sm font-bold text-blue-600 animate-pulse uppercase tracking-widest">Building follow-up pathway...</p>
                  </div>
                ) : (actionPlan.followUp?.length ?? 0) > 0 ? (
                  <div className="space-y-4">
                    {actionPlan.followUp?.map((action: any) => (
                      <div
                        key={action.id}
                        onClick={() => toggleAction(action.id)}
                        className={`group relative p-4 rounded-2xl border transition-all duration-300 cursor-pointer overflow-hidden ${checkedActions[action.id]
                          ? 'bg-slate-50/50 border-slate-200 ring-1 ring-slate-100'
                          : 'bg-white border-slate-100 hover:border-blue-200 hover:shadow-lg hover:shadow-blue-500/5'
                          }`}
                      >
                        <div className="flex gap-4 relative z-10">
                          <div className={`mt-0.5 w-6 h-6 rounded-full border-2 flex items-center justify-center shrink-0 transition-all duration-300 ${checkedActions[action.id]
                            ? 'bg-emerald-500 border-emerald-500'
                            : 'border-slate-200 group-hover:border-blue-400'
                            }`}>
                            {checkedActions[action.id] && <CheckCircle className="w-4 h-4 text-white" />}
                          </div>
                          <div className="flex-1">
                            <div className={`font-bold transition-all duration-300 ${checkedActions[action.id] ? 'text-slate-400 line-through' : 'text-slate-800'}`}>
                              {action.action}
                            </div>
                            <div className="flex items-center gap-3 mt-2">
                              <span className="flex items-center gap-1 text-[10px] font-black uppercase tracking-tighter text-blue-500 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">
                                <Calendar className="w-2.5 h-2.5" /> {action.time || 'Next 24-48h'}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-12 flex flex-col items-center text-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-slate-50 flex items-center justify-center text-slate-300">
                      <CheckCircle className="w-6 h-6" />
                    </div>
                    <p className="text-sm text-slate-400 font-medium italic">No follow-up actions specified.</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Completion Status Footer */}
          <div className="mt-8 flex items-center justify-center">
            {totalActions > 0 && Object.values(checkedActions).filter(Boolean).length === totalActions ? (
              <div className="animate-bounce inline-flex items-center gap-3 px-6 py-4 bg-emerald-50 text-emerald-700 rounded-2xl border border-emerald-200 shadow-xl shadow-emerald-500/10">
                <CheckCircle className="w-6 h-6" />
                <span className="text-lg font-black italic">CLINICAL PROTOCOL FULLY EXECUTED</span>
              </div>
            ) : (
              <div className="text-slate-400 text-sm font-medium italic flex items-center gap-2 opacity-60">
                <div className="w-1.5 h-1.5 rounded-full bg-slate-300 animate-pulse" />
                {totalActions - Object.values(checkedActions).filter(Boolean).length} clinical objectives remaining
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
};

export default OutputSection;
