import React from "react";
import { 
  Facebook, Twitter, Linkedin, Target, Users, Briefcase, 
  Headphones, HelpCircle, Shield, FileText, BookOpen, Video, Newspaper 
} from "lucide-react";

const Footer = () => {
  // CHANGED: Removed "max-w-[1400px] mx-auto" and added "w-full"
  // kept rounded corners for consistency, but you can remove rounded-[24px] if you want it flush
  const glassContainer = "w-full rounded-[24px] px-8 py-12 shadow-[0_8px_30px_rgba(0,0,0,0.04)] bg-[rgba(255,255,255,0.18)] backdrop-blur-[0.9px] border border-[rgba(255,255,255,0.76)]";
  
  const headingStyle = "font-bold text-[#2d3436] mb-6 text-lg tracking-tight";
  const linkStyle = "flex items-center gap-2 text-sm text-[#636e72] font-medium hover:text-blue-600 transition-colors duration-200 group";
  const iconStyle = "w-4 h-4 text-[#a4b0be] group-hover:text-blue-600 transition-colors";

  return (
    // Added w-full here to ensure the footer tag fills the space
    <footer className="w-full mt-10 pb-6 px-4">
      <div className={glassContainer}>
        {/* We keep a max-width on the INNER grid so the text stays readable and aligned */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 max-w-[1400px] mx-auto">
          
          {/* Column 1: About */}
          <div>
            <h4 className={headingStyle}>About Medora AI</h4>
            <ul className="space-y-4">
              <li><a href="#" className={linkStyle}><Target className={iconStyle} /> Our Mission</a></li>
              <li><a href="#" className={linkStyle}><Users className={iconStyle} /> Team</a></li>
              <li><a href="#" className={linkStyle}><Briefcase className={iconStyle} /> Careers</a></li>
            </ul>
          </div>

          {/* Column 2: Support */}
          <div>
            <h4 className={headingStyle}>Support</h4>
            <ul className="space-y-4">
              <li><a href="#" className={linkStyle}><Headphones className={iconStyle} /> Contact Support</a></li>
              <li><a href="#" className={linkStyle}><HelpCircle className={iconStyle} /> FAQs</a></li>
              <li><a href="#" className={linkStyle}><Shield className={iconStyle} /> Privacy Policy</a></li>
              <li><a href="#" className={linkStyle}><FileText className={iconStyle} /> Terms of Service</a></li>
            </ul>
          </div>

          {/* Column 3: Resources */}
          <div>
            <h4 className={headingStyle}>Resources</h4>
            <ul className="space-y-4">
              <li><a href="#" className={linkStyle}><BookOpen className={iconStyle} /> Documentation</a></li>
              <li><a href="#" className={linkStyle}><Video className={iconStyle} /> Tutorials</a></li>
              <li><a href="#" className={linkStyle}><Newspaper className={iconStyle} /> Blog</a></li>
            </ul>
          </div>

          {/* Column 4: Connect */}
          <div>
            <h4 className={headingStyle}>Connect With Us</h4>
            <div className="flex gap-4 mb-6">
              <a href="#" className="w-10 h-10 rounded-xl bg-white/40 border border-white/60 flex items-center justify-center text-blue-600 shadow-sm hover:bg-blue-600 hover:text-white transition-all hover:scale-110 hover:shadow-md">
                <Facebook className="w-5 h-5" />
              </a>
              <a href="#" className="w-10 h-10 rounded-xl bg-white/40 border border-white/60 flex items-center justify-center text-blue-400 shadow-sm hover:bg-blue-400 hover:text-white transition-all hover:scale-110 hover:shadow-md">
                <Twitter className="w-5 h-5" />
              </a>
              <a href="#" className="w-10 h-10 rounded-xl bg-white/40 border border-white/60 flex items-center justify-center text-blue-700 shadow-sm hover:bg-blue-700 hover:text-white transition-all hover:scale-110 hover:shadow-md">
                <Linkedin className="w-5 h-5" />
              </a>
            </div>
            <p className="text-sm text-[#636e72] leading-relaxed">
              Stay updated with our latest features and healthcare insights.
            </p>
          </div>
        </div>

        {/* Bottom Bar - Also constrained to max-w for alignment */}
        <div className="mt-12 pt-8 border-t border-white/50 flex flex-col md:flex-row items-center justify-between gap-4 max-w-[1400px] mx-auto">
          <p className="text-sm text-[#636e72] font-medium text-center md:text-left">
            © 2026 Medora AI. All rights reserved. | <span className="text-blue-600">Transforming Healthcare</span>
          </p>
          
          <div className="flex items-center gap-2 text-xs font-semibold text-[#636e72] bg-white/40 px-3 py-1.5 rounded-full border border-white/50 shadow-sm">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            System Stable v2.4
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;