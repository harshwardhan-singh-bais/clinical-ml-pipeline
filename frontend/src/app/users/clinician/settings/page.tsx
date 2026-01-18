"use client";

import React, { useState } from "react";
import { Poppins } from 'next/font/google';
import Sidebar from "@/components/sidebar/sidebar"; // Import your Sidebar
import Footer from "@/components/footer/footer";
import { 
  User, Bell, Shield, Globe, Palette, Save, RotateCcw, 
  Smartphone, Mail, Lock, Eye, Cpu 
} from "lucide-react";

// Load Font
const poppins = Poppins({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  display: 'swap',
});

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("general");

  // Reusing your specific Glass Style
  const glassCardStyle = "bg-[rgba(255,255,255,0.18)] rounded-[24px] p-8 shadow-[0_8px_30px_rgba(0,0,0,0.04)] backdrop-blur-[0.9px] border border-[rgba(255,255,255,0.76)]";
  
  // Input Styles
  const inputStyle = "w-full p-3 rounded-xl bg-white/50 border border-white/60 text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all";
  const labelStyle = "block text-sm font-bold text-slate-600 mb-2";

  return (
    // 1. ROOT CONTAINER: Added the Flex wrapper and Background Gradient
    <div className={`${poppins.className} flex h-screen w-full overflow-hidden bg-[linear-gradient(135deg,#f5f7fa_0%,#c3cfe2_100%)] text-[#2d3436]`}>
      
      {/* 2. SIDEBAR: Added the Sidebar Component */}
      <Sidebar />

      {/* 3. MAIN CONTENT: Same structure as Dashboard */}
      <main className="flex-1 overflow-y-auto px-10 py-8">
        <div className="mx-auto max-w-[1200px] flex flex-col min-h-screen">
          
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-[#2d3436]">Settings</h1>
            <p className="mt-1 text-sm text-[#636e72]">Manage your profile, preferences, and security settings.</p>
          </div>

          {/* Navigation Tabs */}
          <div className="flex gap-2 overflow-x-auto pb-2 mb-8 no-scrollbar">
            {[
              { id: "general", label: "General", icon: User },
              { id: "alerts", label: "Notifications", icon: Bell },
              { id: "display", label: "Appearance", icon: Palette },
              { id: "security", label: "Security", icon: Shield },
              { id: "system", label: "System", icon: Cpu },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-6 py-3 rounded-2xl font-semibold transition-all duration-300 ${
                  activeTab === tab.id
                    ? "bg-blue-600 text-white shadow-lg shadow-blue-500/30"
                    : "bg-white/40 text-slate-600 hover:bg-white hover:text-blue-600"
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>

          {/* Content Area */}
          <div className="flex-1">
            
            {/* --- GENERAL TAB --- */}
            {activeTab === "general" && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className={glassCardStyle}>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
                      <User className="w-5 h-5" />
                    </div>
                    <h3 className="text-lg font-bold text-slate-800">Profile Information</h3>
                  </div>
                  
                  <div className="space-y-5">
                    <div>
                      <label className={labelStyle}>Full Name</label>
                      <input type="text" className={inputStyle} defaultValue="Dr. Ayoub" />
                    </div>
                    <div>
                      <label className={labelStyle}>Specialization</label>
                      <input type="text" className={inputStyle} defaultValue="Cardiology" />
                    </div>
                    <div>
                      <label className={labelStyle}>Hospital ID</label>
                      <input type="text" className={inputStyle} defaultValue="CL-8839-X" disabled />
                    </div>
                  </div>
                </div>

                <div className={glassCardStyle}>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
                      <Globe className="w-5 h-5" />
                    </div>
                    <h3 className="text-lg font-bold text-slate-800">Regional Settings</h3>
                  </div>
                  
                  <div className="space-y-5">
                    <div>
                      <label className={labelStyle}>Time Zone</label>
                      <select className={inputStyle}>
                        <option>UTC -05:00 (Eastern Time)</option>
                        <option>UTC +00:00 (GMT)</option>
                        <option>UTC +01:00 (Central European)</option>
                      </select>
                    </div>
                    <div>
                      <label className={labelStyle}>Language</label>
                      <select className={inputStyle}>
                        <option>English (US)</option>
                        <option>French</option>
                        <option>Spanish</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* --- ALERTS TAB --- */}
            {activeTab === "alerts" && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className={glassCardStyle}>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 rounded-xl bg-purple-50 flex items-center justify-center text-purple-600">
                      <Mail className="w-5 h-5" />
                    </div>
                    <h3 className="text-lg font-bold text-slate-800">Email Notifications</h3>
                  </div>
                  
                  <div className="space-y-4">
                    <ToggleItem label="Critical Diagnosis Alerts" checked={true} />
                    <ToggleItem label="Weekly Summary Reports" checked={true} />
                    <ToggleItem label="System Maintenance" checked={false} />
                  </div>
                </div>

                <div className={glassCardStyle}>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 rounded-xl bg-purple-50 flex items-center justify-center text-purple-600">
                      <Smartphone className="w-5 h-5" />
                    </div>
                    <h3 className="text-lg font-bold text-slate-800">Push Notifications</h3>
                  </div>
                  
                  <div className="space-y-4">
                    <ToggleItem label="New Patient Assigned" checked={true} />
                    <ToggleItem label="Lab Results Ready" checked={true} />
                    <ToggleItem label="Patient Updates" checked={false} />
                  </div>
                </div>
              </div>
            )}

            {/* --- DISPLAY TAB --- */}
            {activeTab === "display" && (
              <div className={`w-full max-w-2xl ${glassCardStyle} animate-in fade-in slide-in-from-bottom-4 duration-500`}>
                 <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 rounded-xl bg-orange-50 flex items-center justify-center text-orange-600">
                      <Eye className="w-5 h-5" />
                    </div>
                    <h3 className="text-lg font-bold text-slate-800">Interface Customization</h3>
                  </div>

                  <div className="space-y-6">
                     <div className="flex items-center justify-between p-4 rounded-xl bg-white/40 border border-white/60">
                        <span className="font-semibold text-slate-700">Theme Preference</span>
                        <div className="flex gap-2">
                           <button className="px-4 py-2 rounded-lg bg-slate-800 text-white text-xs font-bold">Dark</button>
                           <button className="px-4 py-2 rounded-lg bg-white text-slate-800 border shadow-sm text-xs font-bold">Light</button>
                           <button className="px-4 py-2 rounded-lg bg-blue-100 text-blue-600 border border-blue-200 text-xs font-bold">System</button>
                        </div>
                     </div>

                     <ToggleItem label="High Contrast Mode" checked={false} />
                     <ToggleItem label="Reduce Motion" checked={false} />
                     <ToggleItem label="Compact Sidebar" checked={false} />
                  </div>
              </div>
            )}

            {/* --- SECURITY TAB --- */}
            {activeTab === "security" && (
               <div className={`w-full max-w-2xl ${glassCardStyle} animate-in fade-in slide-in-from-bottom-4 duration-500`}>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 rounded-xl bg-red-50 flex items-center justify-center text-red-600">
                      <Lock className="w-5 h-5" />
                    </div>
                    <h3 className="text-lg font-bold text-slate-800">Security & Privacy</h3>
                  </div>

                  <div className="space-y-5">
                     <div>
                        <label className={labelStyle}>Current Password</label>
                        <input type="password" className={inputStyle} placeholder="••••••••" />
                     </div>
                     <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className={labelStyle}>New Password</label>
                          <input type="password" className={inputStyle} placeholder="••••••••" />
                        </div>
                        <div>
                          <label className={labelStyle}>Confirm Password</label>
                          <input type="password" className={inputStyle} placeholder="••••••••" />
                        </div>
                     </div>
                     
                     <div className="pt-4 border-t border-slate-200/50">
                        <ToggleItem label="Two-Factor Authentication (2FA)" checked={true} />
                        <p className="text-xs text-slate-400 mt-1 ml-14">Secure your account with an extra layer of protection.</p>
                     </div>
                  </div>
               </div>
            )}

          </div>

          {/* Sticky Action Bar */}
          <div className="sticky bottom-0 mt-8 p-4 rounded-2xl bg-white/70 backdrop-blur-xl border border-white/60 shadow-lg flex justify-end gap-4">
             <button className="px-6 py-2.5 rounded-xl text-slate-600 font-semibold hover:bg-slate-100 transition-colors flex items-center gap-2">
               <RotateCcw className="w-4 h-4" /> Reset
             </button>
             <button className="px-8 py-2.5 rounded-xl bg-blue-600 text-white font-semibold shadow-lg shadow-blue-500/30 hover:bg-blue-700 transition-all flex items-center gap-2">
               <Save className="w-4 h-4" /> Save Changes
             </button>
          </div>

          <Footer />
        </div>
      </main>
    </div>
  );
}

// --- Helper Component for Toggles ---
const ToggleItem = ({ label, checked }: { label: string; checked: boolean }) => (
  <div className="flex items-center justify-between p-2">
    <span className="font-semibold text-slate-700">{label}</span>
    <label className="relative inline-flex items-center cursor-pointer">
      <input type="checkbox" className="sr-only peer" defaultChecked={checked} />
      <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
    </label>
  </div>
);