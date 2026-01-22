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
import { AnalysisResponse } from "@/lib/api";

// --- STYLES ---
const glassCard = "bg-[rgba(255,255,255,0.18)] backdrop-blur-[0.9px] border border-[rgba(255,255,255,0.76)] shadow-[0_8px_30px_rgba(0,0,0,0.04)] rounded-2xl";
const glassBtn = "flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-xl transition-all font-semibold shadow-sm duration-300";

const activeBtn = "bg-gradient-to-r from-[#4facfe] to-[#00f2fe] text-white shadow-[0_4px_15px_rgba(0,242,254,0.3)] translate-y-[-2px]";
const inactiveBtn = "bg-white/40 text-slate-600 hover:bg-white hover:text-[#00f2fe] border border-white/60";

interface OutputSectionProps {
  isVisible?: boolean;
  data?: AnalysisResponse | null;
}


const OutputSection = ({ isVisible = true, data = null }: OutputSectionProps) => {
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
    confidence: data?.metadata?.confidence || "N/A"
  };

  // AI Summary - Backend returns 'summary' not 'clinical_summary'!
  const summaryText = data?.clinical_summary?.summary_text || data?.summary?.summary_text || "No summary available. Backend did not return analysis.";
  const redFlags = data?.clinical_summary?.red_flags || data?.red_flags || [];

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
  const actionPlan = data?.action_plan || {
    immediate: [],
    followUp: []
  };

  const totalActions = (actionPlan.immediate?.length || 0) + (actionPlan.followUp?.length || 0);

  // --- LOGIC ---
  const handleSymptomClick = (symptom: any) => {
    setSelectedSymptom(symptom);
    setHighlightedText(symptom.keywords || []);
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
            Model: {metadata.model} • Time: {metadata.time}
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
                {redFlags.length > 0 ? (
                  redFlags.map((flag, idx) => (
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
                            <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border ${diag.severity === 'critical' ? 'bg-red-100 text-red-600 border-red-200' : 'bg-orange-100 text-orange-600 border-orange-200'}`}>
                              {diag.severity || 'moderate'}
                            </span>
                            <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border bg-purple-50 text-purple-600 border-purple-100">
                              {diag.source || 'RAG'}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-xs font-bold text-slate-400 uppercase">Confidence</div>
                        <div className="text-2xl font-bold text-slate-800">
                          {(() => {
                            // confidence is an object with overall_confidence field
                            const confObj = diag.confidence;
                            const conf = confObj?.overall_confidence || diag.confidence_score || 0;
                            // Convert to percentage (0-1 scale → 0-100)
                            const percentage = conf > 1 ? conf : Math.round(conf * 100);
                            return `${percentage}%`;
                          })()}
                        </div>
                        <div className="w-24 h-1.5 bg-slate-200 rounded-full mt-1 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${(() => {
                              const confObj = diag.confidence;
                              const conf = confObj?.overall_confidence || diag.confidence_score || 0;
                              const percentage = conf > 1 ? conf : conf * 100;
                              return percentage > 80 ? 'bg-green-500' : 'bg-orange-500';
                            })()}`}
                            style={{
                              width: `${(() => {
                                const confObj = diag.confidence;
                                const conf = confObj?.overall_confidence || diag.confidence_score || 0;
                                return conf > 1 ? conf : Math.round(conf * 100);
                              })()}%`
                            }}
                          ></div>
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

      {/* --- TAB: SYMPTOMS --- */}
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
                  <div className="relative w-full aspect-square bg-white rounded-2xl border border-slate-200 p-4 flex items-center justify-center">
                    <img
                      src={organImages[selectedSymptom.organ] || organImages.general}
                      alt={selectedSymptom.organ}
                      className="max-h-full max-w-full object-contain drop-shadow-xl"
                    />
                  </div>
                  <p className="mt-4 text-sm text-slate-500 font-medium">
                    Visualizing pathology in the <span className="capitalize font-bold text-slate-700">{selectedSymptom.organ || 'general'}</span> system.
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

          {/* Header */}
          <div className={`${glassCard} p-6`}>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-2xl font-bold text-slate-800 flex items-center gap-3">
                <Zap className="w-7 h-7 text-amber-500" />
                Clinical Action Plan
              </h3>
              <div className="text-right">
                <div className="text-xs font-bold text-slate-400 uppercase">Completed</div>
                <div className="text-2xl font-bold text-slate-800">
                  {Object.values(checkedActions).filter(Boolean).length} / {totalActions}
                </div>
                <div className="w-24 h-2 bg-slate-200 rounded-full mt-1 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-green-400 to-emerald-500 rounded-full transition-all duration-500"
                    style={{
                      width: `${totalActions > 0 ? (Object.values(checkedActions).filter(Boolean).length / totalActions) * 100 : 0}%`
                    }}
                  ></div>
                </div>
              </div>
            </div>
            <p className="text-sm text-slate-600">
              AI-generated clinical actions based on the differential diagnosis. Check off items as you complete them.
            </p>
          </div>

          {/* Immediate Actions (STAT) */}
          <div className={`${glassCard} p-6`}>
            <h4 className="font-semibold text-lg flex items-center gap-2 mb-4 text-red-700">
              <Zap className="h-5 w-5 text-amber-600" /> Immediate Actions (STAT)
            </h4>
            {(actionPlan.immediate?.length ?? 0) > 0 ? (
              <div className="space-y-3">
                {actionPlan.immediate?.map((action: any) => (
                  <label
                    key={action.id}
                    onClick={() => toggleAction(action.id)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all flex items-center gap-3 ${checkedActions[action.id]
                      ? 'bg-white/30 border-white shadow-inner'
                      : 'bg-white/10 border-white/30 hover:bg-white/20'
                      }`}
                  >
                    {checkedActions[action.id] ? (
                      <CheckCircle className="h-5 w-5 text-green-400 shrink-0" />
                    ) : (
                      <div className="h-5 w-5 rounded-full border-2 border-white/40 shrink-0" />
                    )}
                    <div className="flex-1">
                      <div className="font-medium text-slate-800">{action.action}</div>
                      <div className="text-sm opacity-80 text-slate-600 flex items-center gap-1 mt-1">
                        <Clock className="w-3 h-3" />
                        {action.time || 'STAT'}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 text-center py-8 bg-white/20 rounded-xl border border-white/30">
                No immediate actions required at this time.
              </p>
            )}
          </div>

          {/* Follow-up Actions */}
          <div className={`${glassCard} p-6`}>
            <h4 className="font-semibold text-lg flex items-center gap-2 mb-4 text-blue-700">
              <Calendar className="h-5 w-5 text-blue-600" /> Follow-up Actions
            </h4>
            {(actionPlan.followUp?.length ?? 0) > 0 ? (
              <div className="space-y-3">
                {actionPlan.followUp?.map((action: any) => (
                  <label
                    key={action.id}
                    onClick={() => toggleAction(action.id)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all flex items-center gap-3 ${checkedActions[action.id]
                      ? 'bg-white/30 border-white shadow-inner'
                      : 'bg-white/10 border-white/30 hover:bg-white/20'
                      }`}
                  >
                    {checkedActions[action.id] ? (
                      <CheckCircle className="h-5 w-5 text-green-400 shrink-0" />
                    ) : (
                      <div className="h-5 w-5 rounded-full border-2 border-white/40 shrink-0" />
                    )}
                    <div className="flex-1">
                      <div className="font-medium text-slate-800">{action.action}</div>
                      <div className="text-sm opacity-80 text-slate-600 flex items-center gap-1 mt-1">
                        <Calendar className="w-3 h-3" />
                        {action.time || 'Within 24-48 hours'}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 text-center py-8 bg-white/20 rounded-xl border border-white/30">
                No follow-up actions specified.
              </p>
            )}
          </div>

          {/* Progress Summary */}
          <div className="mt-6 p-6 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border border-green-200 text-center">
            <div className="text-4xl font-bold text-emerald-700">
              {Object.values(checkedActions).filter(Boolean).length} / {totalActions}
            </div>
            <div className="text-sm font-semibold text-emerald-600 mt-1">Actions Completed</div>
            <div className="mt-3 text-xs text-slate-600">
              {totalActions > 0 && Object.values(checkedActions).filter(Boolean).length === totalActions ? (
                <span className="font-bold text-green-600">✅ All actions completed!</span>
              ) : (
                <span>Keep going! {totalActions - Object.values(checkedActions).filter(Boolean).length} items remaining.</span>
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default OutputSection;
