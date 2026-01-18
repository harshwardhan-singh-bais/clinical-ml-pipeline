"use client";

import React, { useState } from "react";
import { FileText, Mic, Upload, Sparkles, Loader2 } from "lucide-react";

// 1. Define the props interface
interface InputHubProps {
  onAnalyze: (text: string) => void | Promise<void>; // Function passed from parent with text parameter
  isAnalyzing: boolean;  // Loading state passed from parent
  value?: string;  // Optional controlled input value
  onChange?: (text: string) => void;  // Optional change handler
}

// 2. Accept props in the component
const InputHub = ({ onAnalyze, isAnalyzing }: InputHubProps) => {
  const [inputText, setInputText] = useState("");
  const [isRecording, setIsRecording] = useState(false);

  const handleClear = () => setInputText("");
  const handleVoiceInput = () => setIsRecording(!isRecording);

  const placeholderText = "Type or paste clinical notes here...\n\nExample:\nPatient: 67-year-old male\nChief Complaint: Acute chest pain";
  const glassBtnStyle = "flex-1 flex items-center justify-center gap-3 py-4 px-6 rounded-2xl border transition-all duration-300 font-semibold shadow-sm bg-[rgba(255,255,255,0.18)] border-[rgba(255,255,255,0.76)] backdrop-blur-[0.9px] text-slate-700 hover:bg-[rgba(255,255,255,0.3)] hover:border-white hover:-translate-y-0.5 hover:shadow-md";
  const recordingStyle = "flex-1 flex items-center justify-center gap-3 py-4 px-6 rounded-2xl border transition-all duration-300 font-semibold shadow-sm bg-red-500/10 border-red-200 backdrop-blur-[0.9px] text-red-600 animate-pulse";

  return (
    <div className="w-full h-full">
      <div className="h-full flex flex-col rounded-3xl p-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] bg-[rgba(255,255,255,0.18)] backdrop-blur-[0.9px] border border-[rgba(255,255,255,0.76)]">

        {/* Header and Input Area (Same as before) ... */}
        <div className="flex items-center gap-4 mb-6 shrink-0">
          <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center border border-blue-100 shadow-sm">
            <FileText className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-800">Patient Report Input</h2>
            <p className="text-sm text-slate-400">Paste clinical notes, symptoms, or upload documents</p>
          </div>
        </div>

        <div className="relative mb-5 flex-1 min-h-[220px]">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={placeholderText}
            className="w-full h-full p-5 rounded-2xl resize-none transition-all duration-300 bg-slate-50/50 hover:bg-slate-50 border-2 border-slate-100 focus:border-blue-200 text-slate-700 placeholder-slate-400 font-medium text-base leading-relaxed focus:ring-4 focus:ring-blue-500/10 focus:outline-none"
          />
          <div className="absolute bottom-4 right-4 text-xs font-medium text-slate-400 bg-white/70 px-2 py-1 rounded-md">
            {inputText.length} chars
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 mb-6 shrink-0">
          <button onClick={handleVoiceInput} className={isRecording ? recordingStyle : glassBtnStyle}>
            <Mic className={`w-5 h-5 ${isRecording ? "animate-pulse" : ""}`} />
            <span>{isRecording ? "Recording..." : "Voice Input"}</span>
          </button>
          <button className={glassBtnStyle}>
            <Upload className="w-5 h-5" />
            <span>Upload PDF</span>
          </button>
        </div>

        <div className="flex justify-between items-center pt-5 border-t border-slate-100/50 shrink-0">
          <button onClick={handleClear} className="px-5 py-2 text-sm font-semibold text-slate-500 hover:text-slate-700 hover:bg-slate-100/50 rounded-xl transition-colors">
            Reset Form
          </button>

          {/* 3. Update the Button to use the Prop */}
          <button
            onClick={() => onAnalyze(inputText)} // Calls parent function with text
            disabled={!inputText || isAnalyzing}
            className="px-7 py-3.5 text-sm font-bold text-white rounded-xl shadow-lg shadow-blue-500/20 transition-all flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none hover:shadow-blue-500/40 hover:-translate-y-0.5 active:translate-y-0"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" /> Analyzing...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" /> Analyze Report
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default InputHub;