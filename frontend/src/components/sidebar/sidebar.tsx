"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const Sidebar = () => {
  const pathname = usePathname();

  // Define your menu items and their specific routes here
  const navItems = [
    { 
      name: "Dashboard", 
      icon: "fa-solid fa-border-all", // <--- Added "fa-solid" here
      path: "/users/clinician/dashboard2" 
    },
    { 
      name: "Appointments", 
      icon: "fa-regular fa-calendar-check", 
      path: "/users/clinician/appointments" 
    },
    { 
      name: "Analytics", 
      icon: "fa-solid fa-chart-pie", 
      path: "/users/clinician/analytics" 
    },
    { 
      name: "Reports", 
      icon: "fa-regular fa-file-lines", 
      path: "/users/clinician/reports" 
    },
    { 
      name: "Settings", 
      icon: "fa-solid fa-gear", 
      path: "/users/clinician/settings" 
    },
  ];
  // Styles reused from your previous design
  const activeStyle = "border-2 border-white bg-gradient-to-b from-[#4facfe] to-[#00f2fe] text-white shadow-[0_8px_15px_rgba(0,242,254,0.3)] scale-110";
  const inactiveStyle = "bg-white/60 text-[#2d3436] shadow-sm hover:scale-110 hover:bg-white hover:text-[#2563eb]";
  const baseItemStyle = "group flex h-12 w-12 cursor-pointer items-center justify-center rounded-full transition-all duration-300";

  return (
    <nav className="flex w-[90px] flex-col items-center justify-between border-r border-white/20 bg-transparent py-8 backdrop-blur-md z-50 h-full">
      
      {/* Top: Logo */}
      <div className="flex h-[70px] w-[45px] flex-col items-center justify-center rounded-2xl border border-white/30 bg-gradient-to-b from-[#4facfe] to-[#00f2fe] text-white shadow-[0_8px_12px_rgba(79,172,254,0.3)] shrink-0 cursor-pointer hover:shadow-lg transition-shadow">
        <i className="fa-solid fa-plus mb-1 text-xl"></i>
        <i className="fa-solid fa-wave-square text-[10px]"></i>
      </div>

      {/* Center: Nav Links */}
      <div className="flex flex-1 w-full flex-col items-center justify-center">
        <ul className="flex flex-col items-center gap-4 relative">
          {/* Vertical Line */}
          <div className="absolute left-1/2 top-2 bottom-2 w-[1px] -translate-x-1/2 bg-[#a4b0be]/30 -z-10"></div>
          
          {navItems.map((item) => {
            // Check if active (You can use .startsWith for sub-pages if needed)
            const isActive = pathname === item.path;

            return (
              <li key={item.name}>
                <Link href={item.path}>
                  <div className={`${baseItemStyle} ${isActive ? activeStyle : inactiveStyle}`}>
                    <i className={`${item.icon} text-lg ${!isActive && 'text-xl'}`}></i>
                  </div>
                </Link>
              </li>
            );
          })}
        </ul>
      </div>

      {/* Bottom: Profile */}
      <div className="shrink-0 cursor-pointer hover:scale-105 transition-transform">
        <img 
          src="https://images.unsplash.com/photo-1599566150163-29194dcaad36?ixlib=rb-1.2.1&auto=format&fit=crop&w=100&q=80" 
          alt="User" 
          className="h-12 w-12 rounded-full border-2 border-white object-cover shadow-md"
        />
      </div>
    </nav>
  );
};

export default Sidebar;