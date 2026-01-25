"use client";

import React, { useState, useEffect } from 'react';
import { Sparkles } from 'lucide-react';
import Image from 'next/image';

const MedoraLoader = () => {
  // --- LOGIC: Cycling Code Pairs ---
  const codePairs = [
    { left: "Extracting entities...", right: "NER_Model_v2.4.init()" },
    { left: "Checking interactions...", right: "PharmacologyDB.query(meds)" },
    { left: "Assessing risk scores...", right: "Calc(TIMI, HEART) -> High" },
    { left: "Synthesizing plan...", right: "RAG_Evidence.fetch(sources)" },
  ];

  const [currentPair, setCurrentPair] = useState(0);

  useEffect(() => {
    // Cycle through text pairs every 1.8 seconds for readability
    const interval = setInterval(() => {
      setCurrentPair((prev) => (prev + 1) % codePairs.length);
    }, 1800);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center w-full h-96 animate-in fade-in duration-700 relative overflow-hidden">
      
      {/* 1. The Animated Icon */}
      <div className="relative w-32 h-32 flex items-center justify-center mb-8 z-10">
        <div className="absolute inset-0 bg-[#00f2fe] rounded-full blur-3xl opacity-20 animate-pulse"></div>
        <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-[#4facfe]/80 border-r-[#00f2fe]/80 border-l-[#4facfe]/30 shadow-[0_0_15px_rgba(0,242,254,0.2)] animate-spin [animation-duration:3s]"></div>
        <div className="absolute inset-4 rounded-full border-4 border-transparent border-b-[#00f2fe] border-l-[#4facfe] animate-spin [animation-duration:1.5s] [animation-direction:reverse]"></div>
        
        <div className="relative z-10 w-20 h-20 rounded-full shadow-[0_0_30px_rgba(0,242,254,0.5)] animate-bounce [animation-duration:2s]">
           <Image 
             src="/images/medora-icon.png" 
             alt="Medora Logo" 
             fill 
             className="object-cover rounded-full"
             priority
           />
           <div className="absolute z-20 -top-1 -right-1 bg-white rounded-full p-1 shadow-sm animate-ping [animation-duration:2s]">
              <Sparkles className="w-3 h-3 text-[#4facfe]" />
           </div>
        </div>
      </div>

      {/* 2. Text Feedback with Code Animation */}
      <div className="text-center space-y-6 z-10 w-full max-w-md px-4">
        
        {/* Title */}
        <h3 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-slate-700 to-slate-900">
          Medora is analyzing...
        </h3>
        
        {/* Animated Code Lines Container */}
        <div className="flex flex-col items-center gap-1.5 h-12 justify-center">
           {/* Primary Logic Line */}
           <div key={`L-${currentPair}`} className="font-mono text-sm font-medium text-[#4facfe] animate-in slide-in-from-bottom-2 fade-in duration-300">
              <span className="opacity-50 mr-2">{`>`}</span>
              {codePairs[currentPair].left}
           </div>

           {/* Secondary/System Line */}
           <div key={`R-${currentPair}`} className="font-mono text-xs text-slate-400 opacity-80 animate-in slide-in-from-bottom-1 fade-in duration-300 delay-75">
              <span className="opacity-50 mr-2">{`//`}</span>
              {codePairs[currentPair].right}
           </div>
        </div>

        {/* 3. NEW: Loading Bar */}
        <div className="w-64 h-1.5 bg-slate-100 rounded-full mx-auto overflow-hidden shadow-inner border border-slate-200/60">
            {/* The moving gradient bar */}
            <div className="h-full bg-gradient-to-r from-[#4facfe] via-[#00f2fe] to-[#4facfe] w-1/3 rounded-full animate-[translateX_1.5s_ease-in-out_infinite] shadow-[0_0_10px_rgba(0,242,254,0.5)]"></div>
        </div>

      </div>

    </div>
  );
};

export default MedoraLoader;