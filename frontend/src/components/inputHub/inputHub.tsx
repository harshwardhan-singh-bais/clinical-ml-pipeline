"use client";

import React, { useState, useRef } from "react";
import { FileText, Image, Upload, Sparkles, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { AnalysisResponse } from "@/lib/api";

// 1. Define the props interface
interface InputHubProps {
  onAnalyze: (text: string) => void | Promise<void>;
  isAnalyzing: boolean;
  onUploadStart?: () => void;
  onUploadComplete?: (data: AnalysisResponse) => void;
  onUploadError?: (error: any) => void;
  value?: string;
  onChange?: (text: string) => void;
}

// 2. Accept props in the component
const InputHub = ({ onAnalyze, isAnalyzing, onUploadStart, onUploadComplete, onUploadError }: InputHubProps) => {
  const [inputText, setInputText] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const pdfInputRef = useRef<HTMLInputElement>(null);

  const handleClear = () => setInputText("");

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Check file type
    const validImageTypes = ['image/png', 'image/jpeg', 'image/jpg'];
    if (!validImageTypes.includes(file.type)) {
      alert('Please upload a PNG, JPG, or JPEG image');
      return;
    }

    if (onUploadStart) onUploadStart();
    setIsUploading(true);
    try {
      // Upload image and get analysis
      const result = await api.uploadFile(file);

      // Call the parent callback to update state
      if (onUploadComplete) {
        onUploadComplete(result);
      }
    } catch (error: any) {
      console.error('Image upload failed:', error);
      if (onUploadError) onUploadError(error);
      else alert(error.message || 'Failed to process image');
      setIsUploading(false);
    } finally {
      // If we are still mounted
      setIsUploading(false);
      if (imageInputRef.current) {
        imageInputRef.current.value = '';
      }
    }
  };

  const handlePdfUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Check file type
    if (file.type !== 'application/pdf' && !file.name.endsWith('.pdf')) {
      alert('Please upload a PDF file');
      return;
    }

    if (onUploadStart) onUploadStart();
    setIsUploading(true);
    try {
      // Upload PDF and get analysis
      const result = await api.uploadFile(file);

      // Call the parent callback to update state
      if (onUploadComplete) {
        onUploadComplete(result);
      }
    } catch (error: any) {
      console.error('PDF upload failed:', error);
      if (onUploadError) onUploadError(error);
      else alert(error.message || 'Failed to process PDF');
      setIsUploading(false);
    } finally {
      setIsUploading(false);
      if (pdfInputRef.current) {
        pdfInputRef.current.value = '';
      }
    }
  };

  const placeholderText = "Type or paste clinical notes here...\n\nExample:\nPatient: 67-year-old male\nChief Complaint: Acute chest pain";
  const glassBtnStyle = "flex-1 flex items-center justify-center gap-3 py-4 px-6 rounded-2xl border transition-all duration-300 font-semibold shadow-sm bg-[rgba(255,255,255,0.18)] border-[rgba(255,255,255,0.76)] backdrop-blur-[0.9px] text-slate-700 hover:bg-[rgba(255,255,255,0.3)] hover:border-white hover:-translate-y-0.5 hover:shadow-md";
  const uploadingStyle = "flex-1 flex items-center justify-center gap-3 py-4 px-6 rounded-2xl border transition-all duration-300 font-semibold shadow-sm bg-blue-500/10 border-blue-200 backdrop-blur-[0.9px] text-blue-600";

  return (
    <div className="w-full h-full">
      <div className="h-full flex flex-col rounded-3xl p-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] bg-[rgba(255,255,255,0.18)] backdrop-blur-[0.9px] border border-[rgba(255,255,255,0.76)]">

        {/* Header and Input Area */}
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

        {/* Upload Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 mb-6 shrink-0">
          {/* Upload Image Button */}
          <input
            ref={imageInputRef}
            type="file"
            accept="image/png,image/jpeg,image/jpg"
            onChange={handleImageUpload}
            className="hidden"
            id="image-upload"
          />
          <button
            onClick={() => imageInputRef.current?.click()}
            disabled={isUploading || isAnalyzing}
            className={isUploading ? uploadingStyle : glassBtnStyle}
          >
            {isUploading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <Image className="w-5 h-5" />
                <span>Upload Image</span>
              </>
            )}
          </button>

          {/* Upload PDF Button */}
          <input
            ref={pdfInputRef}
            type="file"
            accept="application/pdf,.pdf"
            onChange={handlePdfUpload}
            className="hidden"
            id="pdf-upload"
          />
          <button
            onClick={() => pdfInputRef.current?.click()}
            disabled={isUploading || isAnalyzing}
            className={glassBtnStyle}
          >
            <Upload className="w-5 h-5" />
            <span>Upload PDF</span>
          </button>
        </div>

        <div className="flex justify-between items-center pt-5 border-t border-slate-100/50 shrink-0">
          <button onClick={handleClear} className="px-5 py-2 text-sm font-semibold text-slate-500 hover:text-slate-700 hover:bg-slate-100/50 rounded-xl transition-colors">
            Reset Form
          </button>

          {/* Analyze Button */}
          <button
            onClick={() => onAnalyze(inputText)}
            disabled={!inputText || isAnalyzing || isUploading}
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