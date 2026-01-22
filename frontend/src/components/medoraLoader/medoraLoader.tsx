import React from 'react';
import { Sparkles } from 'lucide-react';
import Image from 'next/image';

const MedoraLoader = () => {
  return (
    <div className="flex flex-col items-center justify-center w-full h-96 animate-in fade-in duration-700">
      
      {/* 1. The Animated Icon */}
      <div className="relative w-32 h-32 flex items-center justify-center mb-8">
        
        {/* Outer Glow (Static Ambience) */}
        <div className="absolute inset-0 bg-[#00f2fe] rounded-full blur-3xl opacity-20 animate-pulse"></div>

        {/* Ring 1: Slow Spinner (Outer Data Layer) */}
        <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-[#4facfe]/80 border-r-[#00f2fe]/80 border-l-[#4facfe]/30 shadow-[0_0_15px_rgba(0,242,254,0.2)] animate-spin [animation-duration:3s]"></div>
        
        {/* Ring 2: Fast Reverse Spinner (Inner Processing Layer) */}
        <div className="absolute inset-4 rounded-full border-4 border-transparent border-b-[#00f2fe] border-l-[#4facfe] animate-spin [animation-duration:1.5s] [animation-direction:reverse]"></div>
        
        {/* Center: The AI Core (Your Custom Icon) */}
        {/* Removed bg-white so the icon fills the space completely */}
        <div className="relative z-10 w-20 h-20 rounded-full shadow-[0_0_30px_rgba(0,242,254,0.5)] animate-bounce [animation-duration:2s]">
           
           {/* YOUR CUSTOM IMAGE - Now fills the container */}
           <Image 
             src="/images/medora-icon.png" 
             alt="Medora Logo" 
             fill 
             // object-cover fills the space, rounded-full clips the square image to a circle
             className="object-cover rounded-full"
             priority
           />
           
           {/* Tiny Sparkle Decoration - z-index added to stay on top */}
           <div className="absolute z-20 -top-1 -right-1 bg-white rounded-full p-1 shadow-sm animate-ping [animation-duration:2s]">
              <Sparkles className="w-3 h-3 text-[#4facfe]" />
           </div>
        </div>
      </div>

      {/* 2. Text Feedback */}
      <div className="text-center space-y-3">
        <h3 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-slate-700 to-slate-900">
          Medora is analyzing...
        </h3>
        
        {/* Animated Status Steps */}
        <div className="flex flex-col gap-1 items-center">
           <p className="text-sm font-medium text-[#4facfe] animate-pulse">
             Extracting clinical entities
           </p>
           <p className="text-xs text-slate-400 font-medium opacity-80">
             Checking interactions • Assessing risk scores
           </p>
        </div>
      </div>

    </div>
  );
};

export default MedoraLoader; 