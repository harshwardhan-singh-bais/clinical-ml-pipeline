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
  Gauge
} from "lucide-react";

// --- STYLES ---
const glassCard = "bg-[rgba(255,255,255,0.18)] backdrop-blur-[0.9px] border border-[rgba(255,255,255,0.76)] shadow-[0_8px_30px_rgba(0,0,0,0.04)] rounded-2xl";
const glassBtn = "flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-xl transition-all font-semibold shadow-sm duration-300";

const activeBtn = "bg-gradient-to-r from-[#4facfe] to-[#00f2fe] text-white shadow-[0_4px_15px_rgba(0,242,254,0.3)] translate-y-[-2px]";
const inactiveBtn = "bg-white/40 text-slate-600 hover:bg-white hover:text-[#00f2fe] border border-white/60";

const OutputSection = ({ isVisible = true }) => {
  const [activeTab, setActiveTab] = useState("summary");
  const [highlightedText, setHighlightedText] = useState<string[]>([]);
  const [selectedSymptom, setSelectedSymptom] = useState<any>(null);
  const [expandedEvidence, setExpandedEvidence] = useState<Record<number, boolean>>({});

  if (!isVisible) return null;

  // --- DATA STORE ---
  const clinicalNote = {
    originalText: `Patient is a 58-year-old male presenting with substernal chest pain for the past 3 hours. Pain is described as burning and pressure-like, rated 7/10 in severity, radiating to the left arm and jaw. Pain worsens with exertion and improves slightly with rest. Patient reports associated diaphoresis and nausea. Denies shortness of breath, palpitations, or syncope. Past medical history significant for hypertension and hyperlipidemia. Current medications include lisinopril 10mg daily and atorvastatin 40mg nightly. Patient reports smoking 1 pack per day for 30 years. Family history positive for coronary artery disease (father had MI at age 62).`,
    patientInfo: { id: "MRN-482916", age: 58, sex: "Male", chiefComplaint: "Chest Pain - 3h duration" },
    metadata: { time: "1.4s", model: "Medora-v2.4 (RAG)", confidence: "High" }
  };

  const aiSummary = {
    text: "58-year-old male with 30-pack-year smoking history and cardiovascular risk factors presents with acute substernal chest pain (7/10) radiating to left arm/jaw, associated with diaphoresis. Clinical presentation is highly concerning for acute coronary syndrome (ACS).",
    redFlags: [
      { flag: "Radiating Chest Pain (Left Arm/Jaw)", severity: "critical", keywords: ["radiating", "left arm", "jaw"] },
      { flag: "Associated Diaphoresis", severity: "critical", keywords: ["diaphoresis"] },
      { flag: "Exertional Pattern", severity: "critical", keywords: ["exertion"] }
    ]
  };

  const differentialDiagnoses = [
    {
      id: 1,
      condition: "Acute Coronary Syndrome (STEMI/NSTEMI)",
      confidence: 87,
      severity: "critical",
      source: "RAG + LLM",
      reasoning: "Classic anginal pain with radiation, significant risk factors (Smoking, HTN), and autonomic symptoms strongly suggest myocardial ischemia.",
      evidence: [
        { source: "UpToDate 2024", excerpt: "Typical angina presents as substernal discomfort radiating to arm/jaw with diaphoresis.", similarity: 94, keywords: ["substernal", "radiation", "diaphoresis"] },
        { source: "StatPearls", excerpt: "Smoking and family history significantly increase ACS likelihood.", similarity: 89, keywords: ["smoking", "family history"] }
      ],
      nextSteps: ["STAT ECG (12-lead)", "Cardiac Biomarkers (Troponin)", "Aspirin 325mg PO"]
    },
    {
      id: 2,
      condition: "Gastroesophageal Reflux (GERD)",
      confidence: 34,
      severity: "moderate",
      source: "Rule-Based",
      reasoning: "Burning character suggests esophageal origin, but radiation and diaphoresis make this less likely as primary cause.",
      evidence: [
        { source: "Mayo Clinic", excerpt: "GERD presents with substernal burning worsening with recumbency.", similarity: 62, keywords: ["burning", "substernal"] }
      ],
      nextSteps: ["GI Cocktail Trial", "Monitor for postprandial patterns"]
    },
    {
        id: 3,
        condition: "Musculoskeletal Chest Pain",
        confidence: 15,
        severity: "low",
        source: "Rule-Based",
        reasoning: "Pain reproducible with palpation would suggest this, but patient history lacks trauma.",
        evidence: [
          { source: "ClinicalKey", excerpt: "Musculoskeletal pain is often reproducible and localized.", similarity: 45, keywords: ["chest pain"] }
        ],
        nextSteps: ["Physical Exam (Palpation)"]
      }
  ];

  const atomicSymptoms = [
    { id: "s1", symptom: "Chest Pain", detail: "Substernal, Burning, 7/10", severity: 7, status: "present", organ: "heart", keywords: ["chest pain", "substernal", "burning"] },
    { id: "s2", symptom: "Diaphoresis", detail: "Profuse sweating", severity: 6, status: "present", organ: "general", keywords: ["diaphoresis"] },
    { id: "s3", symptom: "Nausea", detail: "Associated symptom", severity: 4, status: "present", organ: "stomach", keywords: ["nausea"] },
    { id: "s4", symptom: "Dyspnea", detail: "Patient denies", severity: 0, status: "absent", organ: "lungs", keywords: ["shortness of breath", "denies"] }
  ];

  const organImages: Record<string, string> = {
    heart: "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Heart_diagram-en.svg/400px-Heart_diagram-en.svg.png",
    lungs: "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Lungs_diagram_detailed.svg/400px-Lungs_diagram_detailed.svg.png",
    stomach: "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Stomach_diagram.svg/300px-Stomach_diagram.svg.png",
    general: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Human_body_silhouette.svg/200px-Human_body_silhouette.svg.png"
  };

  // --- LOGIC ---
  const handleSymptomClick = (symptom: any) => {
    setSelectedSymptom(symptom);
    setHighlightedText(symptom.keywords);
  };

  const toggleEvidence = (id: number) => {
    setExpandedEvidence(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const highlightTextInNote = (text: string, keywords: string[]) => {
    if (!keywords || keywords.length === 0) return text;
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
            <Activity className="w-6 h-6 text-[#00f2fe]" />
            GenAI Clinical Analysis
          </h2>
          <p className="text-slate-500 text-sm font-medium ml-8">
            Model: {clinicalNote.metadata.model} • Time: {clinicalNote.metadata.time}
          </p>
        </div>
        <div className="text-right hidden md:block">
          <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Patient MRN</div>
          <div className="text-xl font-bold text-slate-800 font-mono">{clinicalNote.patientInfo.id}</div>
        </div>
      </div>

      {/* 2. Navigation Tabs (Sticky) */}
      <div className="sticky top-0 z-50 bg-[#f5f7fa]/95 backdrop-blur-xl border-b border-white/50 py-3 mb-6 -mx-4 px-4 transition-all duration-300">
        <div className="flex gap-4">
          {[
            { id: 'summary', label: 'Clinical Summary', icon: FileText },
            { id: 'diagnosis', label: 'Differential Diagnosis', icon: Brain },
            { id: 'symptoms', label: 'Symptom Analysis', icon: Stethoscope },
            { id: 'evidence', label: 'RAG Evidence', icon: Search }
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
      
      {/* --- TAB: SUMMARY (UPDATED LAYOUT) --- */}
      {activeTab === 'summary' && (
        <div className="flex flex-col gap-6">
          
          {/* A. AI Summary (Now Full Width Top) */}
          <div className={`${glassCard} p-8`}>
            <h3 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
              <Brain className="w-6 h-6 text-purple-600" /> AI Generated Summary
            </h3>
            <div className="bg-blue-50/50 border border-blue-100 rounded-2xl p-6">
              <p className="text-lg text-slate-700 leading-relaxed font-medium">
                {aiSummary.text}
              </p>
            </div>
          </div>

          {/* B. Grid: Original Note (Left) & Red Flags (Right) */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Original Clinical Note (Moved to Bottom Left) */}
            <div className={`${glassCard} p-6 h-full flex flex-col`}>
              <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5 text-[#00f2fe]" /> Original Clinical Note
              </h3>
              <div className="flex-1 bg-white/50 border border-white/60 rounded-xl p-5 text-slate-700 leading-relaxed font-mono text-sm shadow-inner max-h-[300px] overflow-y-auto">
                <div dangerouslySetInnerHTML={{ __html: highlightTextInNote(clinicalNote.originalText, highlightedText) }} />
              </div>
              <p className="mt-3 text-center text-[10px] text-slate-400">
                Click a red flag to highlight the source text here.
              </p>
            </div>

            {/* Critical Red Flags (Unchanged) */}
            <div className="bg-red-50/80 border border-red-100 rounded-2xl p-6 shadow-sm">
              <h3 className="text-lg font-bold text-red-700 mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-red-600 animate-pulse" /> Critical Red Flags
              </h3>
              <div className="space-y-3">
                {aiSummary.redFlags.map((flag, idx) => (
                  <div 
                    key={idx} 
                    className="bg-white/60 border border-red-200 rounded-xl p-3 cursor-pointer hover:bg-white hover:shadow-md transition-all flex items-start gap-3 group"
                    onClick={() => setHighlightedText(flag.keywords)}
                  >
                    <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
                    <div>
                      <span className="font-bold text-slate-800 block group-hover:text-red-700 transition-colors">{flag.flag}</span>
                      <span className="text-xs text-red-400 font-semibold uppercase tracking-wider">{flag.severity}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* --- TAB: DIAGNOSIS (Unchanged) --- */}
      {activeTab === 'diagnosis' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 relative">
          <div className="lg:col-span-4 h-full">
             <div className={`${glassCard} p-6 sticky top-24 max-h-[80vh] overflow-y-auto`}>
                <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                   <FileText className="w-4 h-4 text-[#00f2fe]" /> Live Context
                </h3>
                <div className="text-xs text-slate-600 font-mono leading-relaxed opacity-90 p-3 bg-white/40 rounded-xl border border-white/50">
                   <div dangerouslySetInnerHTML={{ __html: highlightTextInNote(clinicalNote.originalText, highlightedText) }} />
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
            {differentialDiagnoses.map((diag, idx) => (
              <div key={diag.id} className={`${glassCard} overflow-hidden group`}>
                <div className="p-6 border-b border-white/50">
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-[#4facfe] to-[#00f2fe] text-white font-bold text-lg shadow-lg shadow-blue-500/30">
                        #{idx + 1}
                      </div>
                      <div>
                        <h3 className="text-xl font-bold text-slate-800">{diag.condition}</h3>
                        <div className="flex gap-2 mt-1">
                          <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border ${diag.severity === 'critical' ? 'bg-red-100 text-red-600 border-red-200' : 'bg-orange-100 text-orange-600 border-orange-200'}`}>
                            {diag.severity}
                          </span>
                          <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border bg-purple-50 text-purple-600 border-purple-100">
                            {diag.source}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-bold text-slate-400 uppercase">Confidence</div>
                      <div className="text-2xl font-bold text-slate-800">{diag.confidence}%</div>
                      <div className="w-24 h-1.5 bg-slate-200 rounded-full mt-1 overflow-hidden">
                        <div className={`h-full rounded-full ${diag.confidence > 80 ? 'bg-green-500' : 'bg-orange-500'}`} style={{ width: `${diag.confidence}%` }}></div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-slate-50/50 rounded-xl p-4 border border-slate-100">
                    <p className="text-sm text-slate-700 font-medium leading-relaxed">
                      <span className="text-purple-600 font-bold mr-1">AI Reasoning:</span> {diag.reasoning}
                    </p>
                  </div>
                </div>

                <div 
                  className="bg-white/40 hover:bg-white/60 p-3 cursor-pointer transition-colors flex items-center justify-center gap-2 text-sm font-semibold text-[#00f2fe] hover:text-[#4facfe]"
                  onClick={() => toggleEvidence(diag.id)}
                >
                  {expandedEvidence[diag.id] ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  View Evidence Sources ({diag.evidence.length})
                </div>

                {expandedEvidence[diag.id] && (
                  <div className="p-6 bg-slate-50/80 space-y-3 animate-in slide-in-from-top-2">
                    {diag.evidence.map((ev, i) => (
                      <div key={i} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm cursor-pointer hover:border-[#4facfe] transition-all" onClick={() => setHighlightedText(ev.keywords)}>
                        <div className="flex justify-between items-start mb-2">
                          <span className="text-xs font-bold text-[#00f2fe] bg-blue-50 px-2 py-1 rounded border border-blue-100">{ev.source}</span>
                          <span className="text-xs font-bold text-green-600">{ev.similarity}% Match</span>
                        </div>
                        <p className="text-sm text-slate-600 italic">"{ev.excerpt}"</p>
                      </div>
                    ))}
                    <div className="mt-4 pt-4 border-t border-slate-200">
                      <span className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 block">Recommended Actions</span>
                      <div className="flex flex-wrap gap-2">
                        {diag.nextSteps.map((step, i) => (
                          <span key={i} className="flex items-center gap-1.5 px-3 py-1.5 bg-green-50 text-green-700 border border-green-200 rounded-lg text-xs font-bold">
                            <CheckCircle className="w-3 h-3" /> {step}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* --- TAB: SYMPTOMS (Unchanged) --- */}
      {activeTab === 'symptoms' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className={`${glassCard} p-6`}>
              <h3 className="text-lg font-bold text-green-700 mb-4 flex items-center gap-2">
                <CheckCircle className="w-5 h-5" /> Present Symptoms
              </h3>
              <div className="grid gap-3">
                {atomicSymptoms.filter(s => s.status === 'present').map(s => (
                  <div 
                    key={s.id}
                    onClick={() => handleSymptomClick(s)} 
                    className={`p-4 rounded-xl border cursor-pointer transition-all flex items-center justify-between ${selectedSymptom?.id === s.id ? 'bg-green-50 border-green-400 shadow-md scale-[1.02]' : 'bg-white/40 border-white/60 hover:border-green-300'}`}
                  >
                    <div>
                      <h4 className="font-bold text-slate-800">{s.symptom}</h4>
                      <p className="text-xs text-slate-500">{s.detail}</p>
                    </div>
                    <span className="text-xs font-bold bg-red-100 text-red-600 px-2 py-1 rounded border border-red-200">Sev: {s.severity}/10</span>
                  </div>
                ))}
              </div>
            </div>

            <div className={`${glassCard} p-6 opacity-80`}>
              <h3 className="text-lg font-bold text-slate-500 mb-4 flex items-center gap-2">
                <XCircle className="w-5 h-5" /> Negated Symptoms
              </h3>
              <div className="flex flex-wrap gap-2">
                {atomicSymptoms.filter(s => s.status === 'absent').map(s => (
                  <div key={s.id} className="px-3 py-2 bg-slate-100 text-slate-500 rounded-lg border border-slate-200 text-sm font-medium line-through decoration-slate-400">
                    {s.symptom}
                  </div>
                ))}
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
                    <span className="text-lg font-bold text-[#00f2fe]">{selectedSymptom.symptom}</span>
                  </div>
                  <div className="relative w-full aspect-square bg-white rounded-2xl border border-slate-200 p-4 flex items-center justify-center">
                    

[Image of human heart diagram]

                    <img 
                      src={organImages[selectedSymptom.organ]} 
                      alt={selectedSymptom.organ} 
                      className="max-h-full max-w-full object-contain drop-shadow-xl"
                    />
                  </div>
                  <p className="mt-4 text-sm text-slate-500 font-medium">
                    Visualizing pathology in the <span className="capitalize font-bold text-slate-700">{selectedSymptom.organ}</span> system.
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

      {/* --- TAB: EVIDENCE (Unchanged) --- */}
      {activeTab === 'evidence' && (
        <div className="space-y-4">
           {differentialDiagnoses.map(diag => (
             <div key={diag.id} className={`${glassCard} p-6`}>
               <h3 className="text-lg font-bold text-slate-800 mb-4 border-b border-white/50 pb-2">{diag.condition}</h3>
               <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                 {diag.evidence.map((ev, i) => (
                   <div key={i} className="bg-white/60 p-4 rounded-xl border border-white/80 hover:shadow-md transition-all">
                      <div className="flex justify-between mb-2">
                        <span className="text-xs font-bold text-[#00f2fe] bg-blue-50 px-2 py-1 rounded border border-blue-100">{ev.source}</span>
                        <span className="text-xs font-bold text-green-600">{ev.similarity}% Match</span>
                      </div>
                      <p className="text-sm text-slate-600 italic">"{ev.excerpt}"</p>
                   </div>
                 ))}
               </div>
             </div>
           ))}
        </div>
      )}

    </div>
  );
};

export default OutputSection;