"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  Activity,
  ArrowRight,
  Brain,
  CheckCircle,
  ChevronRight,
  FileText,
  Menu,
  Shield,
  Sparkles,
  X,
  Clock,
  Users,
  TrendingUp,
  Play,
  Search,
  Database,
  Lock
} from "lucide-react";
import { Button } from "@/components/ui/button";

// --- Enhanced Glass Styles ---
const glassPanel = "bg-white/10 backdrop-blur-xl border border-white/20 shadow-[0_8px_32px_0_rgba(31,38,135,0.07)]";
const glassCard = "bg-white/40 backdrop-blur-md border border-white/50 shadow-sm hover:shadow-xl transition-all duration-300";

// ✨ Vibrant Glassy Button Style
const glassButtonPrimary = "bg-gradient-to-r from-blue-500/80 to-cyan-500/80 backdrop-blur-md border border-white/20 text-white shadow-lg shadow-blue-500/30 hover:shadow-blue-500/40 hover:scale-[1.02] transition-all duration-300";

const Landing = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  // Scroll effect for Navbar
  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const features = [
    {
      icon: Brain,
      title: "Context-Aware Diagnostics",
      description: "Our RAG engine doesn't just match keywords; it understands clinical nuance, offering differentials with 94% verifiable accuracy.",
      color: "text-indigo-600",
      bg: "bg-indigo-50",
      border: "border-indigo-100"
    },
    {
      icon: Database,
      title: "Zero-Hallucination RAG",
      description: "Every insight is anchored to a specific citation in trusted medical literature. Trace the logic behind every AI suggestion.",
      color: "text-emerald-600",
      bg: "bg-emerald-50",
      border: "border-emerald-100"
    },
    {
      icon: FileText,
      title: "Instant Entity Extraction",
      description: "Turn unstructured dictations into structured data (FHIR compatible) instantly. Auto-populates medications, allergies, and history.",
      color: "text-blue-600",
      bg: "bg-blue-50",
      border: "border-blue-100"
    },
    {
      icon: Shield,
      title: "Enterprise-Grade Security",
      description: "Built for health systems. HIPAA compliant, SOC 2 Type II certified, with on-premise deployment options available.",
      color: "text-purple-600",
      bg: "bg-purple-50",
      border: "border-purple-100"
    },
  ];

  return (
    <div className="min-h-screen bg-[#F3F6FA] font-sans selection:bg-cyan-100 selection:text-cyan-900 overflow-x-hidden relative">
      
      {/* --- Ambient Background Mesh --- */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-gradient-to-r from-blue-200/40 to-cyan-200/40 blur-[120px] animate-pulse" style={{animationDuration: '8s'}} />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-gradient-to-r from-teal-200/40 to-emerald-200/40 blur-[120px] animate-pulse" style={{animationDuration: '10s'}} />
        <div className="absolute top-[40%] left-[30%] w-[30%] h-[30%] rounded-full bg-indigo-200/30 blur-[100px]" />
      </div>

      {/* --- Navbar --- */}
      <nav className={`fixed top-0 w-full z-50 transition-all duration-300 ${scrolled ? "py-3 bg-white/70 backdrop-blur-lg border-b border-white/40 shadow-sm" : "py-6 bg-transparent"}`}>
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
              <Activity className="w-6 h-6" />
            </div>
            <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-800 to-slate-600">Medora</span>
          </div>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-8">
            {["Solutions", "Platform", "Evidence", "Pricing"].map((item) => (
              <a key={item} href={`#${item.toLowerCase()}`} className="text-sm font-medium text-slate-600 hover:text-cyan-600 transition-colors">
                {item}
              </a>
            ))}
          </div>

          {/* CTA */}
          <div className="hidden md:flex items-center gap-4">
            <Link href="/login" className="text-sm font-semibold text-slate-600 hover:text-slate-900">Sign In</Link>
            <Link href="/dashboard">
              <Button className={`rounded-full px-6 ${glassButtonPrimary}`}>
                Start Analysis
              </Button>
            </Link>
          </div>

          {/* Mobile Toggle */}
          <button className="md:hidden p-2 text-slate-600" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
            {mobileMenuOpen ? <X /> : <Menu />}
          </button>
        </div>
      </nav>

      {/* --- Hero Section --- */}
      {/* Positioned higher (pt-20) for better visibility */}
      <section className="relative pt-20 lg:pt-24 pb-20 px-6 z-10">
        <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-16 items-center">
          
          {/* Hero Copy */}
          <div className="space-y-6 animate-in slide-in-from-bottom-8 duration-700 fade-in">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-50 border border-cyan-100 text-cyan-700 text-xs font-bold uppercase tracking-wide">
              <Sparkles className="w-3 h-3" />
              GenAI for Clinical Excellence
            </div>
            
            <h1 className="text-5xl lg:text-7xl font-bold tracking-tight text-slate-800 leading-[1.1]">
              The AI Co-Pilot for <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-500 drop-shadow-sm">
                Diagnostic Certainty.
              </span>
            </h1>
            
            <p className="text-lg text-slate-600 max-w-xl leading-relaxed">
              Medora enhances clinical decision-making by synthesizing patient data with real-time medical evidence. <span className="font-semibold text-slate-900">Zero hallucinations, 100% traceable sources.</span>
            </p>

            <div className="flex flex-col sm:flex-row gap-4 pt-2">
              <Link href="clinician/dashboard2">
                <Button size="lg" className={`h-14 px-8 rounded-full text-base font-semibold ${glassButtonPrimary}`}>
                  Analyze Patient Note
                  <ArrowRight className="ml-2 w-5 h-5" />
                </Button>
              </Link>
              <Button size="lg" variant="outline" className="h-14 px-8 rounded-full border-slate-300 bg-white/50 hover:bg-white text-slate-700 text-base font-semibold backdrop-blur-sm">
                <Play className="mr-2 w-4 h-4" /> View Clinical Demo
              </Button>
            </div>

            <div className="flex items-center gap-6 pt-2 text-sm text-slate-500 font-medium">
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-emerald-500" /> HIPAA Compliant
              </div>
              <div className="flex items-center gap-2">
                <Lock className="w-4 h-4 text-emerald-500" /> SOC 2 Type II
              </div>
            </div>
          </div>

          {/* Hero Visual: The "Glass Stack" - Touch Responsive */}
          <div className="relative h-[600px] w-full hidden lg:block perspective-1000 group">
             {/* Abstract Decorations */}
             <div className="absolute top-0 right-10 w-64 h-64 bg-cyan-400/20 rounded-full blur-3xl animate-pulse" />
             
             {/* Layer 1: The Input (Back) - Added active:scale-95 */}
             <div className={`absolute top-10 right-10 w-96 h-80 ${glassPanel} rounded-2xl p-6 rotate-y-[-5deg] rotate-x-[5deg] scale-90 opacity-60 z-10 transition-transform duration-500 hover:scale-95 active:scale-95 active:rotate-y-0 active:rotate-x-0 cursor-pointer`}>
                <div className="flex items-center gap-3 mb-4 border-b border-white/10 pb-3">
                   <FileText className="text-slate-500 w-5 h-5"/>
                   <div className="h-2 w-24 bg-slate-400/30 rounded-full"/>
                </div>
                <div className="space-y-3">
                   <div className="h-2 w-full bg-slate-400/20 rounded-full"/>
                   <div className="h-2 w-[90%] bg-slate-400/20 rounded-full"/>
                   <div className="h-2 w-[95%] bg-slate-400/20 rounded-full"/>
                   <div className="h-2 w-[80%] bg-slate-400/20 rounded-full"/>
                </div>
             </div>

             {/* Layer 2: The Processing (Middle) - Added active:scale-90 */}
             <div className={`absolute top-28 right-28 w-96 h-80 bg-slate-900/90 backdrop-blur-xl border border-white/10 rounded-2xl p-6 rotate-y-[-5deg] rotate-x-[5deg] scale-95 z-20 shadow-2xl shadow-slate-900/20 transition-transform duration-500 hover:scale-100 active:scale-90 active:rotate-y-0 cursor-pointer`}>
                <div className="flex items-center justify-between mb-6">
                   <div className="flex items-center gap-2">
                      <Brain className="text-cyan-400 w-5 h-5"/>
                      <span className="text-cyan-100 font-semibold text-sm">Processing</span>
                   </div>
                   <div className="animate-pulse flex gap-1">
                      <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full"/>
                      <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animation-delay-200"/>
                      <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animation-delay-400"/>
                   </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                   <div className="p-3 bg-white/5 rounded-lg border border-white/10">
                      <div className="text-xs text-cyan-300 mb-1">Entity Extraction</div>
                      <div className="text-lg font-mono text-white">98.2%</div>
                   </div>
                   <div className="p-3 bg-white/5 rounded-lg border border-white/10">
                      <div className="text-xs text-cyan-300 mb-1">Risk Score</div>
                      <div className="text-lg font-mono text-emerald-400">High</div>
                   </div>
                </div>
                <div className="mt-6 p-3 bg-slate-800/50 rounded-lg border border-slate-700/50 flex items-center gap-3">
                   <div className="w-8 h-8 rounded-full bg-cyan-500/20 flex items-center justify-center">
                      <Search className="w-4 h-4 text-cyan-300"/>
                   </div>
                   <div className="text-xs text-slate-200">
                      Querying <span className="text-white font-medium">UpToDate, PubMed</span>...
                   </div>
                </div>
             </div>

             {/* Layer 3: The Output (Front) - Added active:scale-105 */}
             <div className={`absolute top-52 right-48 w-96 h-auto ${glassPanel} bg-white/80 rounded-2xl p-6 rotate-y-[-5deg] rotate-x-[5deg] z-30 shadow-[0_20px_50px_rgba(0,0,0,0.15)] animate-float transition-transform duration-300 active:scale-105 active:rotate-0 cursor-pointer`}>
                <div className="flex items-center justify-between mb-4">
                   <span className="text-sm font-bold text-slate-800 flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-emerald-500" /> Diagnosis Confidence
                   </span>
                   <span className="text-emerald-600 text-sm font-bold bg-emerald-100 px-2 py-0.5 rounded-md">94% Match</span>
                </div>
                <div className="space-y-3">
                   <div className="p-3 bg-white rounded-xl border border-slate-100 shadow-sm flex items-start gap-3">
                      <div className="w-6 h-6 rounded-full bg-red-100 text-red-600 flex items-center justify-center text-xs font-bold shrink-0">1</div>
                      <div>
                         <div className="text-sm font-bold text-slate-800">Acute Coronary Syndrome</div>
                         <div className="text-xs text-slate-500 mt-1">Supported by ECG changes and history.</div>
                      </div>
                   </div>
                   <div className="p-3 bg-white/60 rounded-xl border border-slate-100 flex items-start gap-3">
                      <div className="w-6 h-6 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center text-xs font-bold shrink-0">2</div>
                      <div>
                         <div className="text-sm font-bold text-slate-700">Pericarditis</div>
                         <div className="text-xs text-slate-500 mt-1">Consider due to positional pain.</div>
                      </div>
                   </div>
                </div>
             </div>
          </div>
        </div>
      </section>

      {/* --- Stats Section (Glass Strip) --- */}
      <section className="relative z-10 px-6">
        <div className="max-w-7xl mx-auto">
          <div className={`${glassPanel} rounded-3xl p-8 lg:p-12 flex flex-col md:flex-row justify-between items-center gap-8 md:gap-4`}>
            {[
              { label: "Providers Trusted", value: "2,500+", icon: Users },
              { label: "Notes Processed", value: "50k+", icon: FileText },
              { label: "Time Saved/Note", value: "4m", icon: Clock },
              { label: "Accuracy Rate", value: "94%", icon: TrendingUp },
            ].map((stat, idx) => (
              <div key={idx} className="flex items-center gap-4 group">
                <div className="w-14 h-14 rounded-2xl bg-white flex items-center justify-center shadow-sm group-hover:scale-110 transition-transform duration-300">
                  <stat.icon className="w-6 h-6 text-cyan-600" />
                </div>
                <div>
                  <div className="text-3xl font-bold text-slate-900">{stat.value}</div>
                  <div className="text-sm text-slate-500 font-medium">{stat.label}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* --- Features Grid --- */}
      <section id="solutions" className="py-24 px-6 relative">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">
              Intelligence that <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-cyan-500">mirrors your thought process.</span>
            </h2>
            <p className="text-slate-600 text-lg">
              Medora isn't just a scribe. It's an analytical engine that runs parallel to your clinical evaluation, checking for blind spots in real-time.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {features.map((feature, i) => (
              <div key={i} className={`${glassCard} p-8 rounded-3xl group relative overflow-hidden`}>
                {/* Background Hover Glow */}
                <div className={`absolute top-0 right-0 w-32 h-32 rounded-full ${feature.bg} blur-3xl group-hover:scale-150 transition-transform duration-500 opacity-50`} />
                
                <div className={`w-12 h-12 rounded-xl ${feature.bg} ${feature.border} border flex items-center justify-center mb-6`}>
                  <feature.icon className={`w-6 h-6 ${feature.color}`} />
                </div>
                
                <h3 className="text-xl font-bold text-slate-900 mb-3 group-hover:text-cyan-700 transition-colors">
                  {feature.title}
                </h3>
                <p className="text-slate-600 leading-relaxed mb-6">
                  {feature.description}
                </p>
                
                <a href="#" className={`inline-flex items-center text-sm font-semibold ${feature.color} hover:underline`}>
                  Explore Feature <ChevronRight className="w-4 h-4 ml-1" />
                </a>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* --- Workflow Section --- */}
      <section className="py-20 px-6 bg-white/50 relative overflow-hidden">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
             <div className="order-2 lg:order-1 relative">
                <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full blur-[100px] opacity-20" />
                <div className={`${glassPanel} p-8 rounded-3xl relative`}>
                    <div className="space-y-6">
                        {/* Step 1 */}
                        <div className="flex gap-4">
                            <div className="flex flex-col items-center">
                                <div className="w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center text-sm font-bold">1</div>
                                <div className="h-full w-0.5 bg-slate-200 my-2" />
                            </div>
                            <div className="pb-8">
                                <h4 className="text-lg font-bold text-slate-900">Input Data</h4>
                                <p className="text-slate-600 mt-1">Dictate notes, upload labs, or paste unstructured text directly into the dashboard.</p>
                            </div>
                        </div>
                        {/* Step 2 */}
                        <div className="flex gap-4">
                            <div className="flex flex-col items-center">
                                <div className="w-8 h-8 rounded-full bg-cyan-600 text-white flex items-center justify-center text-sm font-bold shadow-lg shadow-cyan-500/30">2</div>
                                <div className="h-full w-0.5 bg-slate-200 my-2" />
                            </div>
                            <div className="pb-8">
                                <h4 className="text-lg font-bold text-cyan-700">RAG Analysis</h4>
                                <p className="text-slate-600 mt-1">Our engine cross-references millions of clinical papers to validate symptoms against diseases.</p>
                            </div>
                        </div>
                        {/* Step 3 */}
                        <div className="flex gap-4">
                            <div className="flex flex-col items-center">
                                <div className="w-8 h-8 rounded-full bg-emerald-500 text-white flex items-center justify-center text-sm font-bold">3</div>
                            </div>
                            <div>
                                <h4 className="text-lg font-bold text-slate-900">Clinical Decision</h4>
                                <p className="text-slate-600 mt-1">Receive a risk-stratified report with cited evidence and treatment pathways.</p>
                            </div>
                        </div>
                    </div>
                </div>
             </div>
             
             <div className="order-1 lg:order-2">
                <div className="inline-block px-4 py-1.5 rounded-full bg-cyan-50 text-cyan-700 text-sm font-bold mb-4">
                   Seamless Workflow
                </div>
                <h2 className="text-3xl md:text-5xl font-bold text-slate-900 mb-6">
                   From Chaos to <br/>
                   <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-cyan-500">Structured Insight.</span>
                </h2>
                <p className="text-lg text-slate-600 leading-relaxed mb-8">
                   Stop drowning in EHR clicks. Medora handles the heavy lifting of data synthesis, so you can focus on the patient in front of you. Integrates with Epic, Cerner, and AthenaHealth.
                </p>
                <Button variant="outline" className="rounded-full border-slate-300 text-slate-700 px-6 hover:bg-white">
                   See Integration Docs
                </Button>
             </div>
          </div>
        </div>
      </section>

      {/* --- CTA Box --- */}
      <section className="py-20 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="relative rounded-[2.5rem] overflow-hidden bg-slate-900 px-6 py-16 md:px-16 text-center shadow-2xl shadow-cyan-900/30">
            {/* Background Effects */}
            <div className="absolute top-0 left-0 w-full h-full">
              <div className="absolute top-[-50%] left-[-10%] w-[600px] h-[600px] rounded-full bg-cyan-600/30 blur-[100px]" />
              <div className="absolute bottom-[-50%] right-[-10%] w-[600px] h-[600px] rounded-full bg-blue-600/30 blur-[100px]" />
            </div>

            <div className="relative z-10">
              <h2 className="text-3xl md:text-5xl font-bold text-white mb-6">
                Ready to upgrade your diagnosis?
              </h2>
              <p className="text-cyan-100 text-lg mb-10 max-w-2xl mx-auto">
                Join 2,500+ clinicians who trust Medora for accurate, evidence-based clinical decision support.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link href="/dashboard">
                  <Button size="lg" className={`h-14 px-8 rounded-full text-base font-semibold ${glassButtonPrimary}`}>
                    Get Started for Free
                  </Button>
                </Link>
                <Button size="lg" variant="outline" className="rounded-full border-cyan-400 text-cyan-100 hover:text-white hover:bg-cyan-900/50 h-14 px-8">
                  Contact Sales
                </Button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* --- Footer --- */}
      <footer className="bg-white border-t border-slate-200 pt-16 pb-8 px-6">
        <div className="max-w-7xl mx-auto grid md:grid-cols-4 gap-12 mb-12">
          <div className="col-span-1 md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center text-white">
                <Activity className="w-5 h-5" />
              </div>
              <span className="text-xl font-bold text-slate-900">Medora</span>
            </div>
            <p className="text-slate-500 text-sm">
              The AI standard for clinical decision support. Traceable, accurate, and secure.
            </p>
          </div>
          <div>
            <h4 className="font-bold text-slate-900 mb-4">Product</h4>
            <ul className="space-y-2 text-sm text-slate-600">
              <li><a href="#" className="hover:text-cyan-600">Features</a></li>
              <li><a href="#" className="hover:text-cyan-600">Security</a></li>
              <li><a href="#" className="hover:text-cyan-600">Integrations</a></li>
              <li><a href="#" className="hover:text-cyan-600">Pricing</a></li>
            </ul>
          </div>
          <div>
            <h4 className="font-bold text-slate-900 mb-4">Company</h4>
            <ul className="space-y-2 text-sm text-slate-600">
              <li><a href="#" className="hover:text-cyan-600">About Us</a></li>
              <li><a href="#" className="hover:text-cyan-600">Careers</a></li>
              <li><a href="#" className="hover:text-cyan-600">Blog</a></li>
              <li><a href="#" className="hover:text-cyan-600">Contact</a></li>
            </ul>
          </div>
          <div>
            <h4 className="font-bold text-slate-900 mb-4">Legal</h4>
            <ul className="space-y-2 text-sm text-slate-600">
              <li><a href="#" className="hover:text-cyan-600">Privacy Policy</a></li>
              <li><a href="#" className="hover:text-cyan-600">Terms of Service</a></li>
              <li><a href="#" className="hover:text-cyan-600">BAA Agreement</a></li>
            </ul>
          </div>
        </div>
        <div className="max-w-7xl mx-auto border-t border-slate-100 pt-8 flex flex-col md:flex-row justify-between items-center text-sm text-slate-400">
          <p>&copy; 2024 Medora Health Inc.</p>
          <div className="flex gap-4 mt-4 md:mt-0">
             <span>SOC 2 Type II</span>
             <span>HIPAA Compliant</span>
             <span>GDPR Ready</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;