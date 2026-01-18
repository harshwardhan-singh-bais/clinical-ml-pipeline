"use client";

import React from "react";
import {
  Activity,
  AlertTriangle,
  Check,
  ClipboardList,
  Zap
} from "lucide-react";

// --- Sub-Components (Moved to Top for Safety) ---

const VitalCard = ({ label, value, unit, status }: any) => {
  const isAbnormal = status === "high" || status === "low";
  return (
    <div
      className={`rounded-2xl p-3 flex flex-col justify-between border transition-all hover:scale-105 ${
        isAbnormal
          ? "bg-red-50/50 border-red-100"
          : "bg-white/40 border-white/40"
      }`}
    >
      <span
        className={`text-[10px] font-bold uppercase tracking-wider ${
          isAbnormal ? "text-red-600" : "text-slate-500"
        }`}
      >
        {label}
      </span>
      <div>
        <span
          className={`text-lg font-bold ${
            isAbnormal ? "text-red-700" : "text-slate-800"
          }`}
        >
          {value}
        </span>
        <span className="text-[10px] text-slate-500 ml-0.5">{unit}</span>
      </div>
    </div>
  );
};

const RiskItem = ({ label, level, score, color }: any) => (
  <div>
    <div className="flex justify-between text-xs font-semibold mb-1">
      <span className="text-slate-700">{label}</span>
      <span className="text-slate-500">{level}</span>
    </div>
    <div className="h-1.5 w-full bg-slate-200 rounded-full overflow-hidden">
      <div
        className={`h-full ${color} rounded-full`}
        style={{ width: `${score}%` }}
      ></div>
    </div>
  </div>
);

// --- Main Component ---

interface OutputSectionProps {
  isVisible?: boolean;
}

const analysisData = {
  diagnosis: {
    primary: "Acute Coronary Syndrome",
    confidence: 94,
    severity: "Critical",
    summary:
      "Patient presents with classic ACS symptoms: acute retrosternal chest pain radiating to the left arm, diaphoresis, and elevated troponin. Immediate intervention required.",
  },
  vitals: {
    bp: { value: "140/90", unit: "mmHg", status: "high" },
    hr: { value: "98", unit: "bpm", status: "normal" },
    spo2: { value: "96", unit: "%", status: "normal" },
    temp: { value: "37.2", unit: "°C", status: "normal" },
    rr: { value: "22", unit: "/min", status: "high" },
  },
  risks: {
    sepsis: { score: 12, level: "Low" },
    readmission: { score: 34, level: "Moderate" },
    missing: ["Smoking history", "Family cardiac history"],
  },
  plan: [
    { type: "Lab", item: "Troponin I (Serial)", urgent: true },
    { type: "Lab", item: "ECG 12-lead", urgent: true },
    { type: "Rx", item: "Aspirin 325mg STAT", urgent: true },
    { type: "Rx", item: "Nitroglycerin PRN", urgent: false },
    { type: "Ref", item: "Cardiology Consult", urgent: true },
  ],
};

const glassStyle =
  "bg-[rgba(255,255,255,0.18)] rounded-[24px] shadow-[0_8px_30px_rgba(0,0,0,0.04)] backdrop-blur-[0.9px] border border-[rgba(255,255,255,0.76)]";

const OutputSection: React.FC<OutputSectionProps> = ({ isVisible = true }) => {
  if (!isVisible) return null;

  return (
    // Added text-slate-900 to ensure text isn't white-on-white
    <div className="w-full text-slate-900">
      
      {/* Section Header */}
      <div className="flex items-center justify-between mb-6 px-2">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Zap className="w-6 h-6 text-yellow-500 fill-yellow-500" />
            AI Analysis Results
          </h2>
          <p className="text-slate-500 text-sm font-medium ml-8">
            Generated in 1.2s • Model Confidence 94%
          </p>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 rounded-xl bg-white/40 border border-white/60 text-sm font-semibold text-slate-600 hover:bg-white hover:text-blue-600 transition-all">
            Export PDF
          </button>
          <button className="px-4 py-2 rounded-xl bg-blue-600 text-sm font-semibold text-white shadow-lg shadow-blue-500/30 hover:bg-blue-700 transition-all">
            Save to EHR
          </button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* --- COL 1: Diagnosis & Vitals (Left Side) --- */}
        <div className="col-span-12 lg:col-span-8 flex flex-col gap-6">
          
          {/* 1. Primary Diagnosis Hero Card */}
          <div className={`${glassStyle} p-8 relative overflow-hidden group`}>
            {/* Decorative background blob */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-red-500/5 rounded-full blur-3xl -z-10 group-hover:bg-red-500/10 transition-colors duration-500"></div>

            <div className="flex justify-between items-start mb-6">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-red-50 border border-red-100 flex items-center justify-center shadow-sm">
                  <Activity className="w-8 h-8 text-red-500" />
                </div>
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="text-2xl font-bold text-slate-800 tracking-tight">
                      {analysisData.diagnosis.primary}
                    </h3>
                    <span className="px-3 py-1 rounded-full bg-red-100 text-red-600 text-xs font-bold border border-red-200 uppercase tracking-wide">
                      {analysisData.diagnosis.severity}
                    </span>
                  </div>
                  <p className="text-slate-500 font-medium text-sm">
                    ICD-10: I20.0 (Predicted)
                  </p>
                </div>
              </div>
              
              {/* Confidence Circle */}
              <div className="flex flex-col items-center">
                <div className="relative w-16 h-16 flex items-center justify-center">
                  <svg className="w-full h-full -rotate-90">
                    <circle
                      cx="32"
                      cy="32"
                      r="28"
                      stroke="#e2e8f0"
                      strokeWidth="6"
                      fill="none"
                    />
                    <circle
                      cx="32"
                      cy="32"
                      r="28"
                      stroke="#ef4444"
                      strokeWidth="6"
                      fill="none"
                      strokeDasharray="175"
                      strokeDashoffset="10"
                      strokeLinecap="round"
                    />
                  </svg>
                  <span className="absolute text-sm font-bold text-slate-800">
                    94%
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white/40 rounded-xl p-5 border border-white/50">
              <p className="text-slate-700 leading-relaxed font-medium">
                {analysisData.diagnosis.summary}
              </p>
            </div>
          </div>

          {/* 2. Vitals Strip */}
          <div className={`${glassStyle} p-6`}>
            <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4" /> Extracted Vitals
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <VitalCard
                label="BP"
                value={analysisData.vitals.bp.value}
                unit={analysisData.vitals.bp.unit}
                status={analysisData.vitals.bp.status}
              />
              <VitalCard
                label="HR"
                value={analysisData.vitals.hr.value}
                unit={analysisData.vitals.hr.unit}
                status={analysisData.vitals.hr.status}
              />
              <VitalCard
                label="SpO2"
                value={analysisData.vitals.spo2.value}
                unit={analysisData.vitals.spo2.unit}
                status={analysisData.vitals.spo2.status}
              />
              <VitalCard
                label="Temp"
                value={analysisData.vitals.temp.value}
                unit={analysisData.vitals.temp.unit}
                status={analysisData.vitals.temp.status}
              />
              <VitalCard
                label="RR"
                value={analysisData.vitals.rr.value}
                unit={analysisData.vitals.rr.unit}
                status={analysisData.vitals.rr.status}
              />
            </div>
          </div>
        </div>

        {/* --- COL 2: Action Plan & Risks (Right Side) --- */}
        <div className="col-span-12 lg:col-span-4 flex flex-col gap-6">
          {/* 3. Clinical Plan Checklist */}
          <div className={`${glassStyle} p-6 flex-1 flex flex-col`}>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
                <ClipboardList className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-slate-800">
                Suggested Plan
              </h3>
            </div>

            <div className="flex-1 space-y-3">
              {analysisData.plan.map((item, i) => (
                <div
                  key={i}
                  className="group flex items-center justify-between p-3 rounded-xl hover:bg-white/60 border border-transparent hover:border-blue-100 transition-all cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-1.5 h-1.5 rounded-full ${
                        item.urgent ? "bg-red-500" : "bg-slate-300"
                      }`}
                    ></div>
                    <div>
                      <p className="text-sm font-semibold text-slate-700 group-hover:text-blue-700">
                        {item.item}
                      </p>
                      <p className="text-[10px] font-bold text-slate-400 uppercase">
                        {item.type}
                      </p>
                    </div>
                  </div>
                  <button className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-300 hover:bg-green-500 hover:text-white transition-all">
                    <Check className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>

            <button className="mt-6 w-full py-3 rounded-xl border-2 border-dashed border-slate-300 text-slate-400 text-sm font-semibold hover:border-blue-400 hover:text-blue-500 transition-all flex items-center justify-center gap-2">
              <span className="text-lg">+</span> Add Custom Order
            </button>
          </div>

          {/* 4. Risk & QA Flags */}
          <div className={`${glassStyle} p-6`}>
            <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">
              Risk Flags
            </h4>

            <div className="space-y-4 mb-6">
              <RiskItem
                label="Sepsis"
                level="Low"
                score={12}
                color="bg-green-500"
              />
              <RiskItem
                label="Readmission"
                level="Moderate"
                score={34}
                color="bg-orange-500"
              />
            </div>

            <div className="bg-amber-50 rounded-xl p-4 border border-amber-100">
              <div className="flex items-center gap-2 mb-2 text-amber-700 font-bold text-xs uppercase tracking-wide">
                <AlertTriangle className="w-3 h-3" /> Missing Data
              </div>
              <ul className="list-disc list-inside text-xs text-amber-800/80 space-y-1 font-medium">
                {analysisData.risks.missing.map((m, i) => (
                  <li key={i}>{m}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OutputSection;