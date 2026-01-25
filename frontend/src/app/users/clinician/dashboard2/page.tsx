"use client";

import React, { useState } from 'react';
import { Poppins } from 'next/font/google';
import InputHub from '@/components/inputHub/inputHub';
import OutputSection from '@/components/outputSection/outputSection';
import Footer from '@/components/footer/footer';
import Sidebar from '@/components/sidebar/sidebar';
import MedoraLoader from '@/components/medoraLoader/medoraLoader';
import { api, type AnalysisResponse, type AdditionalDataResponse } from '@/lib/api';

// Load the font
const poppins = Poppins({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  display: 'swap',
});

export default function HealthDashboard() {
  // State to track if analysis is complete
  const [hasAnalyzed, setHasAnalyzed] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisData, setAnalysisData] = useState<AnalysisResponse | null>(null);
  const [additionalData, setAdditionalData] = useState<AdditionalDataResponse | null>(null);
  const [isFetchingAdditional, setIsFetchingAdditional] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorDetails, setErrorDetails] = useState<any>(null);
  const [inputText, setInputText] = useState('');
  const [showErrorModal, setShowErrorModal] = useState(false);

  // The specific glass style you requested
  const glassStyle = "bg-[rgba(255,255,255,0.18)] rounded-[16px] shadow-[0_4px_30px_rgba(0,0,0,0.1)] backdrop-blur-[0.9px] border border-[rgba(255,255,255,0.76)]";

  const handleAnalysisError = (err: any) => {
    // Parse validation error from backend (silently, no console spam)
    let errorMessage = 'Failed to analyze clinical note. Please try again.';
    let details = null;

    if (err.message) {
      try {
        // The error message is now the stringified detail object
        const errorData = JSON.parse(err.message);

        // Check if it's already the detail object (no nesting)
        if (errorData.error && errorData.error_type) {
          errorMessage = errorData.error;
          details = errorData;
        }
        // Legacy: check if it has detail property
        else if (errorData.detail) {
          if (typeof errorData.detail === 'object') {
            errorMessage = errorData.detail.error || errorMessage;
            details = errorData.detail;
          } else {
            errorMessage = errorData.detail;
          }
        }
      } catch {
        // Not JSON, use message as-is
        errorMessage = err.message;
      }
    }

    // Only log unexpected errors (not validation errors)
    if (!details) {
      console.error('❌ Analysis error:', err);
    }

    setError(errorMessage);
    setErrorDetails(details);
    setShowErrorModal(true);
    setIsAnalyzing(false); // Ensure loading state is cleared on error
  };

  // Function to handle the transition
  const handleAnalyze = async (text: string) => {
    setIsAnalyzing(true);
    setError(null);
    setErrorDetails(null);
    setShowErrorModal(false);
    setInputText(text); // Store the input text

    try {
      // Call real API
      const result = await api.analyzeText(text);

      console.log('✅ API Response:', result);
      console.log('📊 Diagnoses:', result?.differential_diagnoses);
      console.log('📝 Summary:', result?.clinical_summary || result?.summary);

      // Add original_text to response if not present
      if (!result.original_text && !result.content) {
        result.original_text = text;
      }

      setAnalysisData(result);
      setHasAnalyzed(true);
      setIsAnalyzing(false);

      // ✨ Call #2: Fetch Additional Info (Red Flags and Action Plan) in background
      if (result.request_id) {
        fetchAdditionalInfo(result.request_id);
      }
    } catch (err: any) {
      handleAnalysisError(err);
    }
  };

  const fetchAdditionalInfo = async (requestId: string) => {
    setIsFetchingAdditional(true);
    try {
      console.log('✨ Fetching additional deep insights (Call #2)...');
      const result = await api.getAdditionalInfo(requestId);
      console.log('✅ Additional Data:', result);
      setAdditionalData(result);
    } catch (err) {
      console.error('❌ Error fetching additional info:', err);
    } finally {
      setIsFetchingAdditional(false);
    }
  };

  // Function to go back to input
  const handleReset = () => {
    setHasAnalyzed(false);
    setAnalysisData(null);
    setError(null);
    setErrorDetails(null);
    setShowErrorModal(false);
  };

  return (
    <div className={`${poppins.className} flex h-screen w-full overflow-hidden bg-[linear-gradient(135deg,#f5f7fa_0%,#c3cfe2_100%)] text-[#2d3436]`}>

      {/* --- SIDEBAR --- */}
      <Sidebar />

      {/* --- MAIN CONTENT --- */}
      <main className="flex-1 overflow-y-auto px-10 py-8">
        <div className="mx-auto max-w-[1400px] h-full flex flex-col">

          {/* Header */}
          <header className="mb-8 flex h-[60px] items-center justify-between shrink-0">
            <div>
              <h1 className="text-3xl font-semibold text-[#2d3436]">Good Morning, Ayoub!</h1>
              <p className="mt-1 text-sm text-[#636e72]">Monday, January 05, 2026 • Updated 10m ago</p>
            </div>
            <div className="flex items-center gap-5">
              <div className={`flex h-[50px] w-[350px] items-center px-5 transition-all focus-within:bg-white/60 ${glassStyle}`}>
                <i className="fa-solid fa-magnifying-glass text-[#636e72] text-base"></i>
                <input
                  type="text"
                  placeholder="Search..."
                  className="ml-4 w-full bg-transparent text-base text-[#2d3436] outline-none placeholder:text-[#636e72]"
                />
              </div>
              <button className={`relative flex h-12 w-12 items-center justify-center transition-transform hover:scale-105 hover:bg-white ${glassStyle} rounded-full`}>
                <i className="fa-regular fa-bell text-lg"></i>
                <span className="absolute right-3 top-3 h-2 w-2 rounded-full border border-white bg-[#ff7675]"></span>
              </button>
              <button className={`flex h-12 w-12 items-center justify-center transition-transform hover:scale-105 hover:bg-white ${glassStyle} rounded-full`}>
                <i className="fa-regular fa-message text-lg"></i>
              </button>
            </div>
          </header>

          <div className="flex-1 flex flex-col gap-6">

            {/* --- CONDITIONAL VIEW LOGIC --- */}
            {hasAnalyzed ? (
              // --- VIEW 2: OUTPUT MODE ---
              <div className="w-full flex flex-col gap-6 animate-in fade-in zoom-in-95 duration-500">
                {!isAnalyzing && (
                  <button onClick={handleReset} className="self-start text-sm font-semibold text-slate-500 hover:text-blue-600 flex items-center gap-2 mb-2 transition-colors animate-enter fade-in-left">
                    <i className="fa-solid fa-arrow-left"></i> Back to Input
                  </button>
                )}
                {isAnalyzing ? (
                  <div className="w-full bg-[rgba(255,255,255,0.18)] backdrop-blur-[0.9px] border border-white/60 shadow-xl rounded-3xl p-12 min-h-[600px] flex items-center justify-center animate-enter fade-in">
                    <MedoraLoader />
                  </div>
                ) : (
                  <OutputSection
                    isVisible={true}
                    data={analysisData}
                    additionalData={additionalData}
                    isFetchingAdditional={isFetchingAdditional}
                  />
                )}
              </div>
            ) : isAnalyzing ? (
              // --- VIEW: ANALYZING ---
              <div className="w-full bg-[rgba(255,255,255,0.18)] backdrop-blur-[0.9px] border border-white/60 shadow-xl rounded-3xl p-12 min-h-[600px] flex items-center justify-center animate-enter fade-in">
                <MedoraLoader />
              </div>
            ) : (
              // --- VIEW 1: INPUT MODE ---
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-in fade-in slide-in-from-left-4 duration-500">

                {/* LEFT: Input Hub */}
                <div className="lg:col-span-8 flex flex-col">
                  <InputHub
                    onAnalyze={handleAnalyze}
                    isAnalyzing={isAnalyzing}
                    onUploadStart={() => setIsAnalyzing(true)}
                    onUploadComplete={(data) => {
                      console.log('✅ Upload Success:', data);
                      setAnalysisData(data);
                      setHasAnalyzed(true);
                      setIsAnalyzing(false);

                      // ✨ Trigger Call #2 for uploads too
                      if (data.request_id) {
                        fetchAdditionalInfo(data.request_id);
                      }
                    }}
                    onUploadError={handleAnalysisError}
                  />
                </div>

                {/* RIGHT: Patient Safety & Progress */}
                <div className="lg:col-span-4 flex flex-col gap-6">

                  {/* Widget 1: Safety Profile */}
                  <div className={`flex flex-1 min-h-[160px] flex-col justify-between p-5 transition-transform hover:-translate-y-1 ${glassStyle} animate-in fade-in zoom-in-95 duration-700 delay-200 fill-mode-backwards`}>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#ff7675]/10 text-[#ff7675]">
                          <i className="fa-solid fa-shield-virus text-lg"></i>
                        </div>
                        <div>
                          <h3 className="text-lg font-bold text-[#2d3436]">Safety</h3>
                          <span className="text-xs font-bold text-[#ff7675] uppercase tracking-wide">High Alert</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="block text-xs font-bold text-[#636e72] uppercase">Blood</span>
                        <span className="block text-xl font-bold text-[#2d3436] leading-none">O+</span>
                      </div>
                    </div>
                    <div className="mt-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[#636e72] mb-2 block">Allergies</span>
                      <div className="flex flex-wrap gap-2">
                        <span className="px-2 py-1 rounded-md bg-red-50 text-red-600 border border-red-100 text-xs font-bold flex items-center gap-1">
                          <i className="fa-solid fa-circle-exclamation text-[10px]"></i> Penicillin
                        </span>
                        <span className="px-2 py-1 rounded-md bg-orange-50 text-orange-600 border border-orange-100 text-xs font-bold">
                          Peanuts
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Widget 2: Active Meds */}
                  <div className={`flex flex-1 min-h-[160px] flex-col justify-between p-5 transition-transform hover:-translate-y-1 ${glassStyle} animate-in fade-in zoom-in-95 duration-700 delay-300 fill-mode-backwards`}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#74b9ff]/10 text-[#0984e3]">
                          <i className="fa-solid fa-pills text-lg"></i>
                        </div>
                        <div>
                          <h3 className="text-lg font-bold text-[#2d3436]">Meds</h3>
                          <span className="text-xs text-[#636e72]">Active</span>
                        </div>
                      </div>
                      <span className="h-8 w-8 flex items-center justify-center rounded-full bg-slate-100 text-xs font-bold text-[#2d3436]">3</span>
                    </div>
                    <div className="flex flex-col gap-2">
                      <div className="flex items-center justify-between p-1.5 rounded hover:bg-white/40 cursor-pointer">
                        <div className="flex items-center gap-2">
                          <div className="h-1.5 w-1.5 rounded-full bg-green-400"></div>
                          <span className="text-sm font-bold text-[#2d3436]">Lisinopril</span>
                        </div>
                        <span className="text-[10px] font-mono text-[#636e72]">10mg</span>
                      </div>
                      <div className="flex items-center justify-between p-1.5 rounded hover:bg-white/40 cursor-pointer">
                        <div className="flex items-center gap-2">
                          <div className="h-1.5 w-1.5 rounded-full bg-green-400"></div>
                          <span className="text-sm font-bold text-[#2d3436]">Atorvastatin</span>
                        </div>
                        <span className="text-[10px] font-mono text-[#636e72]">40mg</span>
                      </div>
                    </div>
                  </div>

                  {/* Widget 3: Progress radial */}
                  <div className={`flex flex-1 min-h-[160px] flex-col justify-between p-5 transition-transform hover:-translate-y-1 ${glassStyle} animate-in fade-in zoom-in-95 duration-700 delay-500 fill-mode-backwards`}>
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#55efc4]/10 text-[#00b894]">
                        <i className="fa-solid fa-clipboard-check text-lg"></i>
                      </div>
                      <div>
                        <h3 className="text-lg font-bold text-[#2d3436]">Progress</h3>
                        <span className="text-xs text-[#636e72]">Daily Reports</span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between mt-2">
                      <div className="relative h-20 w-20">
                        <svg className="h-full w-full -rotate-90 transform" viewBox="0 0 36 36">
                          <path
                            className="text-slate-200"
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="3"
                          />
                          <path
                            className="text-[#00b894] drop-shadow-sm"
                            strokeDasharray="75, 100"
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="3"
                            strokeLinecap="round"
                          />
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className="text-xs font-bold text-[#2d3436]">75%</span>
                        </div>
                      </div>
                      <div className="flex flex-col items-end">
                        <span className="text-2xl font-bold text-[#2d3436]">9<span className="text-slate-400 text-lg">/12</span></span>
                        <span className="text-[10px] font-bold text-[#00b894] bg-[#55efc4]/10 px-2 py-0.5 rounded-full">On Track</span>
                        <span className="text-[10px] text-[#636e72] mt-1">3 Pending</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* --- BOTTOM SECTION: Body Conditions (Rest) --- */}
            {/* We keep this visible in Input Mode, but hide it in Output Mode to focus on results */}
            {!hasAnalyzed && (
              <div className={`flex flex-col p-8 ${glassStyle}`}>
                <div className="mb-6">
                  <h2 className="text-xl font-bold text-[#2d3436]">Body Conditions</h2>
                  <span className="text-sm text-[#636e72]">124 Metrics Analyzed</span>
                </div>

                <div className="grid flex-1 grid-cols-1 lg:grid-cols-[2fr_1fr] gap-6">
                  {/* Left Subgrid */}
                  <div className="grid grid-cols-2 grid-rows-[auto_auto] gap-6">
                    {/* Weight */}
                    <div className={`flex items-center justify-between p-5 ${glassStyle}`}>
                      <div>
                        <h3 className="mb-1 text-lg font-bold text-[#2d3436]">Weight</h3>
                        <span className="text-sm font-medium text-[#636e72]">Lost 0.4kg</span>
                        <div className="mt-4 flex h-12 items-end gap-1.5">
                          <div className="w-1.5 rounded-sm bg-[#b2bec3] h-[20%]"></div>
                          <div className="w-1.5 rounded-sm bg-[#b2bec3] h-[40%]"></div>
                          <div className="w-1.5 rounded-sm bg-[#b2bec3] h-[30%]"></div>
                          <div className="w-1.5 rounded-sm bg-[#b2bec3] h-[60%]"></div>
                          <div className="w-1.5 rounded-sm bg-[#2d3436] h-[80%]"></div>
                          <div className="w-1.5 rounded-sm bg-[#b2bec3] h-[40%]"></div>
                        </div>
                      </div>
                      <div className="flex min-w-[110px] flex-col items-center justify-center rounded-[20px] bg-white px-6 py-4 shadow-sm">
                        <span className="text-3xl font-bold leading-none text-[#2d3436]">74.2</span>
                        <span className="text-sm font-medium text-[#a4b0be]">kg</span>
                      </div>
                    </div>

                    {/* Food */}
                    <div className={`flex items-center justify-between p-5 ${glassStyle}`}>
                      <div>
                        <h3 className="mb-1 text-lg font-bold text-[#2d3436]">Food</h3>
                        <span className="text-sm font-medium text-[#636e72]">254/1342 kCal</span>
                        <div className="mt-4 flex h-12 items-end gap-1.5">
                          <div className="w-1.5 rounded-sm bg-[#b2bec3] h-[30%]"></div>
                          <div className="w-1.5 rounded-sm bg-[#b2bec3] h-[50%]"></div>
                          <div className="w-1.5 rounded-sm bg-[#b2bec3] h-[20%]"></div>
                          <div className="w-1.5 rounded-sm bg-[#2d3436] h-[60%]"></div>
                          <div className="w-1.5 rounded-sm bg-[#b2bec3] h-[30%]"></div>
                        </div>
                      </div>
                      <div className="flex min-w-[110px] flex-col items-center justify-center rounded-[20px] bg-white px-6 py-4 shadow-sm">
                        <span className="text-3xl font-bold leading-none text-[#2d3436]">253</span>
                        <span className="text-sm font-medium text-[#a4b0be]">kCal</span>
                      </div>
                    </div>

                    {/* Sleep Row */}
                    <div className={`col-span-2 flex items-center justify-between p-5 ${glassStyle}`}>
                      <div>
                        <h3 className="mb-1 text-lg font-bold text-[#2d3436]">Sleep time</h3>
                        <span className="text-sm font-medium text-[#636e72]">6h 31m</span>
                      </div>
                      <div className="relative h-10 w-[240px] rounded-full border border-white/60 bg-white/50">
                        <div className="absolute left-[30%] flex h-full w-1/2 items-center justify-center rounded-full bg-[#2d3436] text-xs font-semibold text-white shadow-md">
                          00:30 - 08:00
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Right Column: Activity */}
                  <div className={`flex flex-col items-center justify-center text-center p-6 ${glassStyle}`}>
                    <h3 className="self-start text-lg font-bold text-[#2d3436]">Activity</h3>
                    <span className="self-start text-sm font-medium text-[#636e72]">654 Steps left</span>
                    <div className="relative mt-6 h-48 w-48">
                      <svg className="h-full w-full -rotate-90 transform">
                        <circle cx="96" cy="96" r="80" fill="none" stroke="#dfe6e9" strokeWidth="16" />
                        <circle
                          cx="96"
                          cy="96"
                          r="80"
                          fill="none"
                          stroke="#2563eb"
                          strokeWidth="16"
                          strokeDasharray="500"
                          strokeDashoffset="100"
                          strokeLinecap="round"
                        />
                      </svg>
                      <div className="absolute left-1/2 top-1/2 flex -translate-x-1/2 -translate-y-1/2 flex-col items-center">
                        <span className="text-4xl font-bold leading-none text-[#2d3436]">6839</span>
                        <span className="text-sm font-medium text-[#a4b0be]">Steps</span>
                      </div>
                    </div>
                    <span className="mt-6 text-sm font-medium text-[#636e72]">Goal: 10,000 Steps</span>
                  </div>
                </div>
              </div>
            )}

          </div>

          {/* Footer (Outside max-w container to stretch full width) */}
          <Footer />
        </div>
      </main>

      {/* ===  ERROR MODAL === */}
      {showErrorModal && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-300">
          <div className="relative w-full max-w-md mx-4 bg-white rounded-2xl shadow-2xl animate-in zoom-in-95 duration-300">

            {/* Header */}
            <div className={`rounded-t-2xl p-6 text-white ${errorDetails?.error_type === 'quota_exhausted' || errorDetails?.error_type === 'api_key_error'
              ? 'bg-gradient-to-r from-yellow-500 to-orange-500'
              : 'bg-gradient-to-r from-red-500 to-orange-500'
              }`}>
              <div className="flex items-center gap-3">
                <div className="flex-shrink-0 w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                  {errorDetails?.error_type === 'quota_exhausted' ? (
                    <i className="fa-solid fa-clock text-2xl"></i>
                  ) : errorDetails?.error_type === 'api_key_error' ? (
                    <i className="fa-solid fa-key text-2xl"></i>
                  ) : (
                    <i className="fa-solid fa-exclamation-triangle text-2xl"></i>
                  )}
                </div>
                <div>
                  <h3 className="text-xl font-bold">
                    {errorDetails?.error_type === 'quota_exhausted' && 'Service Limit Reached'}
                    {errorDetails?.error_type === 'api_key_error' && 'Service Unavailable'}
                    {errorDetails?.error_type === 'server_error' && 'Server Error'}
                    {errorDetails?.error_type === 'gibberish' && 'Invalid Input'}
                    {errorDetails?.error_type === 'not_medical' && 'Invalid Input'}
                    {errorDetails?.error_type === 'too_short' && 'Invalid Input'}
                    {errorDetails?.error_type === 'empty_input' && 'Invalid Input'}
                    {!errorDetails?.error_type && 'Error'}
                  </h3>
                  <p className="text-sm text-white/80 mt-1">
                    {errorDetails?.error_type === 'quota_exhausted' && 'AI Analysis Quota Exhausted'}
                    {errorDetails?.error_type === 'api_key_error' && 'Authentication Failed'}
                    {errorDetails?.error_type === 'server_error' && 'Unexpected Error'}
                    {errorDetails?.error_type === 'gibberish' && 'Gibberish Detected'}
                    {errorDetails?.error_type === 'not_medical' && 'Not a Medical Note'}
                    {errorDetails?.error_type === 'too_short' && 'Input Too Short'}
                    {errorDetails?.error_type === 'empty_input' && 'Empty Input'}
                    {!errorDetails?.error_type && 'Validation Error'}
                  </p>
                </div>
              </div>
            </div>

            {/* Body */}
            <div className="p-6">
              <div className="mb-4">
                <h4 className="font-semibold text-slate-800 mb-2">Error Message:</h4>
                <p className="text-slate-600 text-sm leading-relaxed bg-red-50 border border-red-100 rounded-lg p-3">
                  {error}
                </p>
              </div>

              {errorDetails?.suggestion && (
                <div className="mb-4">
                  <h4 className="font-semibold text-slate-800 mb-2 flex items-center gap-2">
                    <i className="fa-solid fa-lightbulb text-yellow-500"></i>
                    Suggestion:
                  </h4>
                  <p className="text-slate-600 text-sm leading-relaxed bg-yellow-50 border border-yellow-100 rounded-lg p-3">
                    {errorDetails.suggestion}
                  </p>
                </div>
              )}

              {/* Details */}
              {errorDetails?.error_type && (
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs font-mono">
                  <div className="text-slate-500 mb-1">Error Details:</div>
                  <div className="text-slate-700">
                    {errorDetails.error_type === 'too_short' && (
                      <div>Length: {errorDetails.length} / {errorDetails.min_required} chars</div>
                    )}
                    {errorDetails.error_type === 'not_medical' && (
                      <div>Medical Score: {errorDetails.medical_score} / {errorDetails.threshold}</div>
                    )}
                    {errorDetails.error_type === 'gibberish' && (
                      <div>Pattern: {typeof errorDetails.details?.details === 'string' ? errorDetails.details.details.substring(0, 50) : 'Unusual pattern detected'}</div>
                    )}
                    {errorDetails.error_type === 'quota_exhausted' && (
                      <div>
                        <div>Service: {errorDetails.details?.service || 'Google Gemini API'}</div>
                        <div>Retry After: {errorDetails.details?.retry_after || '24 hours'}</div>
                      </div>
                    )}
                    {errorDetails.error_type === 'api_key_error' && (
                      <div>Service: {errorDetails.details?.service || 'Google Gemini API'}</div>
                    )}
                    {errorDetails.error_type === 'server_error' && errorDetails.details?.message && (
                      <div>Message: {errorDetails.details.message}</div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-6 pb-6 flex gap-3">
              <button
                onClick={() => setShowErrorModal(false)}
                className="flex-1 bg-gradient-to-r from-blue-500 to-indigo-500 text-white font-semibold py-3 px-6 rounded-xl hover:from-blue-600 hover:to-indigo-600 transition-all shadow-lg hover:shadow-xl"
              >
                <i className="fa-solid fa-pen-to-square mr-2"></i>
                Try Again
              </button>
            </div>

            {/* Close Button */}
            <button
              onClick={() => setShowErrorModal(false)}
              className="absolute top-4 right-4 w-8 h-8 bg-white/20 hover:bg-white/30 rounded-full flex items-center justify-center text-white transition-colors"
            >
              <i className="fa-solid fa-times"></i>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}