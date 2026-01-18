import React from 'react';
import {
  Building2,
  Headphones,
  Phone,
  Mail,
  FileText,
  Users,
  Activity,
  Settings,
  MapPin,
  Search,
  PlayCircle,
  ArrowRight,
  BookOpen,
  FilePlus,
  FolderOpen,
  CalendarCheck,
  HeartPulse,
  MessageSquare,
  BarChart2,
  ChevronRight,
  Clock,
  Target,
  Briefcase,
  HelpCircle,
  Shield,
  Video,
  Newspaper,
  Facebook,
  Twitter,
  Linkedin
} from 'lucide-react';

const ClinicalDashboard = () => {
  return (
    <div className="bg-primary min-h-screen font-sans text-slate-800">
      {/* Embedded Styles to match the original HTML's custom Tailwind config and CSS */}
      <style>{`
        /* Custom Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        /* Custom Colors simulation */
        .bg-primary { background-color: #E0F2FE; }
        .bg-secondary { background-color: #BFDBFE; }
        .text-accent { color: #60A5FA; }
        .bg-accent { background-color: #60A5FA; }
        .text-text-dark { color: #1E3A8A; }
        .bg-text-dark { background-color: #1E3A8A; }
        .text-text-light { color: #3B82F6; }
        .bg-gray-light { background-color: #F8FAFC; }
        .border-gray-medium { border-color: #CBD5E1; }
        .text-gray-medium { color: #CBD5E1; }
        .text-gray-dark { color: #4B5563; }
        .border-secondary { border-color: #BFDBFE; }

        /* Custom Scrollbar */
        ::-webkit-scrollbar {
          width: 8px;
          height: 8px;
        }
        ::-webkit-scrollbar-track {
          background: #f1f5f9;
        }
        ::-webkit-scrollbar-thumb {
          background: linear-gradient(180deg, #60A5FA, #93C5FD);
          border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb:hover {
          background: linear-gradient(180deg, #3B82F6, #60A5FA);
        }

        /* Animations & Effects */
        .hero-bg {
          background-color: #E0F2FE;
          background-image:
            radial-gradient(#BFDBFE 1px, transparent 1px),
            radial-gradient(#BFDBFE 1px, transparent 1px);
          background-size: 2rem 2rem;
          background-position: 0 0, 1rem 1rem;
        }

        .glass-effect {
          background: rgba(255, 255, 255, 0.9);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .animate-float {
          animation: float 6s ease-in-out infinite;
        }

        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-10px); }
        }

        .gradient-text {
          background: linear-gradient(135deg, #3B82F6 0%, #1E3A8A 50%, #3B82F6 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          background-size: 200% auto;
          animation: gradient-flow 5s ease-in-out infinite;
        }

        @keyframes gradient-flow {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }

        .hero-shadow {
          box-shadow: 0 25px 50px -12px rgba(30, 58, 138, 0.35), 0 0 20px rgba(96, 165, 250, 0.4);
        }

        .hover-scale {
          transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .hover-scale:hover {
          transform: scale(1.05);
          box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }

        @keyframes slideAndExpand {
          from {
            opacity: 0;
            transform: translateY(-15px);
            width: 75%;
          }
          to {
            opacity: 1;
            transform: translateY(0);
            width: 100%;
          }
        }

        .animate-search-bar {
          animation: slideAndExpand 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
          animation-delay: 0.2s;
          margin-left: auto;
          margin-right: auto;
        }
      `}</style>

      {/* Header */}
      <header className="bg-text-dark text-white py-3 shadow-lg">
        <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex justify-between items-center text-sm">
          <div className="flex items-center space-x-6">
            <a href="#" className="hover:text-secondary transition-colors flex items-center">
              <Building2 className="w-4 h-4 mr-1.5" />
              Investors
            </a>
            <a href="#" className="hover:text-secondary transition-colors flex items-center">
              <Headphones className="w-4 h-4 mr-1.5" />
              Contact Us
            </a>
          </div>
          <div className="flex items-center space-x-6">
            <span className="flex items-center hover:text-secondary transition-colors cursor-pointer">
              <Phone className="w-4 h-4 mr-1.5" /> 011 4988 5050
            </span>
            <span className="flex items-center hover:text-secondary transition-colors cursor-pointer">
              <Mail className="w-4 h-4 mr-1.5" /> customer.care@clinical.ai
            </span>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="glass-effect sticky top-0 z-50 shadow-xl border-b border-gray-200">
        <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <div className="flex-shrink-0 flex items-center">
              <div className="relative">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="text-accent h-8 w-8"
                >
                  <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"></path>
                </svg>
              </div>
              <span className="text-3xl font-extrabold gradient-text ml-3">Clinical.ai</span>
            </div>

            <div className="hidden lg:flex flex-grow justify-center space-x-2">
              <a href="#" className="flex flex-col items-center px-6 py-3 text-text-light hover:text-accent group relative">
                <div className="absolute inset-0 bg-secondary rounded-lg opacity-0 group-hover:opacity-50 transition-opacity"></div>
                <FileText className="w-6 h-6 mb-1 relative z-10" />
                <span className="text-sm font-semibold relative z-10">New Analysis</span>
                <div className="absolute bottom-0 w-full h-1 bg-accent rounded-full"></div>
              </a>
              <a href="#" className="flex flex-col items-center px-6 py-3 text-text-light hover:text-accent group relative">
                <div className="absolute inset-0 bg-secondary rounded-lg opacity-0 group-hover:opacity-50 transition-opacity"></div>
                <Users className="w-6 h-6 mb-1 relative z-10" />
                <span className="text-sm font-semibold relative z-10">Patient Records</span>
              </a>
              <a href="#" className="flex flex-col items-center px-6 py-3 text-text-light hover:text-accent group relative">
                <div className="absolute inset-0 bg-secondary rounded-lg opacity-0 group-hover:opacity-50 transition-opacity"></div>
                <Activity className="w-6 h-6 mb-1 relative z-10" />
                <span className="text-sm font-semibold relative z-10">My Dashboard</span>
              </a>
              <a href="#" className="flex flex-col items-center px-6 py-3 text-text-light hover:text-accent group relative">
                <div className="absolute inset-0 bg-secondary rounded-lg opacity-0 group-hover:opacity-50 transition-opacity"></div>
                <Settings className="w-6 h-6 mb-1 relative z-10" />
                <span className="text-sm font-semibold relative z-10">Settings</span>
              </a>
            </div>

            <div className="flex items-center space-x-4">
              <div className="hidden md:flex items-center space-x-3 bg-secondary px-4 py-2 rounded-xl border border-gray-medium">
                <span className="text-text-dark font-semibold">Dr. Evans</span>
                <div className="relative">
                  <img
                    src="https://placehold.co/40x40/60A5FA/FFFFFF?text=DE"
                    alt="Dr. Evans"
                    className="w-10 h-10 rounded-full border-2 border-white shadow-lg"
                  />
                  <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-white"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10">
        
        {/* Search Bar Animation */}
        <div className="mb-10 max-w-4xl mx-auto">
          <div className="animate-search-bar bg-white p-2 rounded-full shadow-md flex items-center border border-gray-medium">
            <div className="flex items-center px-4 py-2 border-r border-gray-medium">
              <MapPin className="w-5 h-5 text-accent mr-3" />
              <span className="text-text-dark font-medium text-md">New Delhi</span>
            </div>
            <div className="flex-grow flex items-center pl-4">
              <Search className="w-5 h-5 text-gray-medium mr-3" />
              <input
                type="text"
                placeholder="Search patients by name or ID..."
                className="w-full h-full focus:outline-none bg-transparent text-text-dark placeholder-gray-medium text-md"
              />
            </div>
          </div>
        </div>

        {/* Hero Section */}
        <div className="relative hero-bg rounded-3xl p-12 md:p-16 overflow-hidden mb-10 border border-secondary hero-shadow">
          <div className="relative z-10 flex flex-col md:flex-row items-center justify-between text-text-dark">
            <div className="text-center md:text-left max-w-2xl">
              <h1 className="text-5xl md:text-6xl font-extrabold leading-tight mb-6 gradient-text">
                AI-Powered Clinical Analysis Platform
              </h1>
              <p className="text-xl md:text-2xl mb-8 text-gray-dark leading-relaxed">
                Process unstructured clinical notes, lab reports, and imaging data into actionable, structured insights.
                Our platform ensures HIPAA compliance, 99.8% data extraction accuracy, and up to 5x faster workflow.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <a
                  href="#"
                  className="bg-accent text-white font-bold py-4 px-8 rounded-xl shadow-lg hover:bg-blue-400 transform hover:-translate-y-1 transition-all duration-300 flex items-center justify-center text-lg"
                >
                  <PlayCircle className="w-6 h-6 mr-3" />
                  Start New Analysis
                  <ArrowRight className="w-5 h-5 ml-3" />
                </a>
                <button className="bg-white border-2 border-secondary text-text-dark font-bold py-4 px-8 rounded-xl hover:bg-gray-light transition-all duration-300 flex items-center justify-center text-lg">
                  <BookOpen className="w-6 h-6 mr-3" />
                  Read Docs
                </button>
              </div>
            </div>

            <div className="mt-12 md:mt-0 md:ml-12 flex-shrink-0 w-full max-w-sm animate-float">
              <div className="bg-white/60 backdrop-blur-md border border-secondary rounded-xl p-6 shadow-xl">
                <h3 className="text-lg font-semibold text-accent mb-4 tracking-wider">PLATFORM METRICS</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-baseline">
                    <span className="text-text-dark">Model Accuracy:</span>
                    <span className="font-mono text-xl text-green-600">90.8%</span>
                  </div>
                  <div className="flex justify-between items-baseline">
                    <span className="text-text-dark">Avg. Processing:</span>
                    <span className="font-mono text-xl text-green-600">~2.5s/report</span>
                  </div>
                  <div className="flex justify-between items-baseline">
                    <span className="text-text-dark">System Uptime:</span>
                    <span className="font-mono text-xl text-green-600">91.34%</span>
                  </div>
                  <div className="flex justify-between items-baseline">
                    <span className="text-text-dark">Compliance:</span>
                    <span className="font-mono text-xl text-green-600">HIPAA Certified</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-3xl shadow-xl p-8 md:p-10 mb-10 border border-secondary">
          <div className="flex justify-between items-center mb-8">
            <h2 className="text-3xl font-bold text-text-dark">Quick Actions</h2>
            <span className="text-sm text-gray-dark bg-gray-light px-4 py-2 rounded-full border border-gray-medium">
              6 Available
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-6">
            <a href="#" className="hover-scale flex flex-col items-center p-6 rounded-2xl bg-primary group cursor-pointer border border-secondary">
              <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-accent text-white shadow-lg group-hover:shadow-xl transition-shadow">
                <FilePlus className="w-8 h-8" />
              </div>
              <span className="mt-4 font-semibold text-text-dark text-sm text-center">Upload Note</span>
            </a>

            <a href="#" className="hover-scale flex flex-col items-center p-6 rounded-2xl bg-primary group cursor-pointer border border-secondary">
              <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-accent text-white shadow-lg group-hover:shadow-xl transition-shadow">
                <FolderOpen className="w-8 h-8" />
              </div>
              <span className="mt-4 font-semibold text-text-dark text-sm text-center">Patient Files</span>
            </a>

            <a href="#" className="hover-scale flex flex-col items-center p-6 rounded-2xl bg-primary group cursor-pointer border border-secondary">
              <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-accent text-white shadow-lg group-hover:shadow-xl transition-shadow">
                <CalendarCheck className="w-8 h-8" />
              </div>
              <span className="mt-4 font-semibold text-text-dark text-sm text-center">Appointments</span>
            </a>

            <a href="#" className="hover-scale flex flex-col items-center p-6 rounded-2xl bg-primary group cursor-pointer border border-secondary">
              <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-accent text-white shadow-lg group-hover:shadow-xl transition-shadow">
                <HeartPulse className="w-8 h-8" />
              </div>
              <span className="mt-4 font-semibold text-text-dark text-sm text-center">Critical Alerts</span>
            </a>

            <a href="#" className="hover-scale flex flex-col items-center p-6 rounded-2xl bg-primary group cursor-pointer border border-secondary">
              <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-accent text-white shadow-lg group-hover:shadow-xl transition-shadow">
                <MessageSquare className="w-8 h-8" />
              </div>
              <span className="mt-4 font-semibold text-text-dark text-sm text-center">Messages</span>
            </a>

            <a href="#" className="hover-scale flex flex-col items-center p-6 rounded-2xl bg-primary group cursor-pointer border border-secondary">
              <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-accent text-white shadow-lg group-hover:shadow-xl transition-shadow">
                <BarChart2 className="w-8 h-8" />
              </div>
              <span className="mt-4 font-semibold text-text-dark text-sm text-center">Analytics</span>
            </a>
          </div>
        </div>

        {/* Patient Queue */}
        <div className="bg-white rounded-3xl shadow-xl overflow-hidden border border-secondary">
          <div className="p-8 border-b border-secondary flex justify-between items-center bg-gray-light">
            <div>
              <h2 className="text-3xl font-bold text-text-dark mb-2">Active Patient Queue</h2>
              <p className="text-text-light">12 patients awaiting review</p>
            </div>
            <a href="#" className="text-lg font-semibold text-accent hover:text-blue-700 flex items-center bg-white px-6 py-3 rounded-xl shadow-md hover:shadow-lg transition-all">
              View All <ChevronRight className="w-5 h-5 ml-2" />
            </a>
          </div>

          <div className="p-8">
            <div className="mb-8 flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0 gap-4">
              <div className="w-full md:w-2/5">
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Search className="w-5 h-5 text-gray-medium" />
                  </div>
                  <input
                    type="search"
                    id="patient-search"
                    placeholder="Search patients by name or ID..."
                    className="w-full pl-12 pr-4 py-3 rounded-xl border-2 border-gray-medium focus:border-accent focus:outline-none focus:ring-4 focus:ring-secondary shadow-sm transition-all"
                  />
                </div>
              </div>
              <div className="flex items-center space-x-4 bg-gray-light px-5 py-3 rounded-xl border border-gray-medium">
                <label htmlFor="sort-by" className="text-sm font-semibold text-text-dark">Sort by:</label>
                <select id="sort-by" className="rounded-lg border-2 border-gray-medium py-2 pl-3 pr-8 text-sm focus:border-accent focus:outline-none focus:ring-2 focus:ring-secondary bg-white font-medium text-text-dark">
                  <option value="status">Status</option>
                  <option value="name">Patient Name</option>
                  <option value="update">Last Update</option>
                </select>
              </div>
            </div>

            <div id="patient-grid" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 max-h-[500px] overflow-y-auto pr-4">
              
              {/* Card 1 */}
              <div className="bg-gray-light rounded-2xl shadow-md hover:shadow-xl transition-shadow border border-gray-200 flex flex-col">
                <div className="flex justify-between items-center p-5 border-b border-gray-200">
                  <h3 className="text-lg font-bold text-text-dark">Robert Johnson</h3>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 bg-red-500 rounded-full"></span>
                    <span className="text-xs font-bold text-red-600">URGENT</span>
                  </div>
                </div>
                <div className="p-5 flex-grow">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Patient ID</p>
                      <p className="font-semibold text-text-dark">12345 | 72M</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Location</p>
                      <p className="font-semibold text-text-dark">Room 302</p>
                    </div>
                  </div>
                </div>
                <div className="px-5 pb-5 flex justify-between items-center">
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Clock className="w-4 h-4" />
                    <span>11:15 AM, Today</span>
                  </div>
                  <a href="#" className="py-2 px-4 rounded-lg border-2 border-red-500 text-red-500 font-semibold hover:bg-red-500 hover:text-white transition-colors text-sm">
                    View Analysis
                  </a>
                </div>
              </div>

              {/* Card 2 */}
              <div className="bg-gray-light rounded-2xl shadow-md hover:shadow-xl transition-shadow border border-gray-200 flex flex-col">
                <div className="flex justify-between items-center p-5 border-b border-gray-200">
                  <h3 className="text-lg font-bold text-text-dark">Sarah Connor</h3>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 bg-blue-500 rounded-full"></span>
                    <span className="text-xs font-bold text-blue-600">IN PROGRESS</span>
                  </div>
                </div>
                <div className="p-5 flex-grow">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Patient ID</p>
                      <p className="font-semibold text-text-dark">67890 | 45F</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Location</p>
                      <p className="font-semibold text-text-dark">Room 304</p>
                    </div>
                  </div>
                </div>
                <div className="px-5 pb-5 flex justify-between items-center">
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Clock className="w-4 h-4" />
                    <span>09:30 AM, Today</span>
                  </div>
                  <a href="#" className="py-2 px-4 rounded-lg border-2 border-blue-500 text-blue-500 font-semibold hover:bg-blue-500 hover:text-white transition-colors text-sm">
                    Continue Review
                  </a>
                </div>
              </div>

              {/* Card 3 */}
              <div className="bg-gray-light rounded-2xl shadow-md hover:shadow-xl transition-shadow border border-gray-200 flex flex-col">
                <div className="flex justify-between items-center p-5 border-b border-gray-200">
                  <h3 className="text-lg font-bold text-text-dark">Michael Chen</h3>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 bg-green-500 rounded-full"></span>
                    <span className="text-xs font-bold text-green-600">REVIEWED</span>
                  </div>
                </div>
                <div className="p-5 flex-grow">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Patient ID</p>
                      <p className="font-semibold text-text-dark">54321 | 68M</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Location</p>
                      <p className="font-semibold text-text-dark">Room 305</p>
                    </div>
                  </div>
                </div>
                <div className="px-5 pb-5 flex justify-between items-center">
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Clock className="w-4 h-4" />
                    <span>08:10 AM, Today</span>
                  </div>
                  <a href="#" className="py-2 px-4 rounded-lg border-2 border-green-500 text-green-500 font-semibold hover:bg-green-500 hover:text-white transition-colors text-sm">
                    View History
                  </a>
                </div>
              </div>

              {/* Card 4 */}
              <div className="bg-gray-light rounded-2xl shadow-md hover:shadow-xl transition-shadow border border-gray-200 flex flex-col">
                <div className="flex justify-between items-center p-5 border-b border-gray-200">
                  <h3 className="text-lg font-bold text-text-dark">Emily Davis</h3>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 bg-orange-500 rounded-full"></span>
                    <span className="text-xs font-bold text-orange-600">URGENT</span>
                  </div>
                </div>
                <div className="p-5 flex-grow">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Patient ID</p>
                      <p className="font-semibold text-text-dark">98765 | 55F</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Location</p>
                      <p className="font-semibold text-text-dark">Room 307</p>
                    </div>
                  </div>
                </div>
                <div className="px-5 pb-5 flex justify-between items-center">
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Clock className="w-4 h-4" />
                    <span>Yesterday, 4:30 PM</span>
                  </div>
                  <a href="#" className="py-2 px-4 rounded-lg border-2 border-orange-500 text-orange-500 font-semibold hover:bg-orange-500 hover:text-white transition-colors text-sm">
                    View Analysis
                  </a>
                </div>
              </div>

              {/* Card 5 */}
              <div className="bg-gray-light rounded-2xl shadow-md hover:shadow-xl transition-shadow border border-gray-200 flex flex-col">
                <div className="flex justify-between items-center p-5 border-b border-gray-200">
                  <h3 className="text-lg font-bold text-text-dark">David Lee</h3>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 bg-green-500 rounded-full"></span>
                    <span className="text-xs font-bold text-green-600">REVIEWED</span>
                  </div>
                </div>
                <div className="p-5 flex-grow">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Patient ID</p>
                      <p className="font-semibold text-text-dark">11223 | 81M</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Location</p>
                      <p className="font-semibold text-text-dark">Room 308</p>
                    </div>
                  </div>
                </div>
                <div className="px-5 pb-5 flex justify-between items-center">
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Clock className="w-4 h-4" />
                    <span>Yesterday, 2:15 PM</span>
                  </div>
                  <a href="#" className="py-2 px-4 rounded-lg border-2 border-green-500 text-green-500 font-semibold hover:bg-green-500 hover:text-white transition-colors text-sm">
                    View History
                  </a>
                </div>
              </div>

              {/* Card 6 */}
              <div className="bg-gray-light rounded-2xl shadow-md hover:shadow-xl transition-shadow border border-gray-200 flex flex-col">
                <div className="flex justify-between items-center p-5 border-b border-gray-200">
                  <h3 className="text-lg font-bold text-text-dark">Maria Garcia</h3>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 bg-blue-500 rounded-full"></span>
                    <span className="text-xs font-bold text-blue-600">IN PROGRESS</span>
                  </div>
                </div>
                <div className="p-5 flex-grow">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Patient ID</p>
                      <p className="font-semibold text-text-dark">66778 | 39F</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Location</p>
                      <p className="font-semibold text-text-dark">Room 310</p>
                    </div>
                  </div>
                </div>
                <div className="px-5 pb-5 flex justify-between items-center">
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Clock className="w-4 h-4" />
                    <span>Yesterday, 1:00 PM</span>
                  </div>
                  <a href="#" className="py-2 px-4 rounded-lg border-2 border-blue-500 text-blue-500 font-semibold hover:bg-blue-500 hover:text-white transition-colors text-sm">
                    Continue Review
                  </a>
                </div>
              </div>

              {/* Card 7 */}
              <div className="bg-gray-light rounded-2xl shadow-md hover:shadow-xl transition-shadow border border-gray-200 flex flex-col">
                <div className="flex justify-between items-center p-5 border-b border-gray-200">
                  <h3 className="text-lg font-bold text-text-dark">James Wilson</h3>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 bg-red-500 rounded-full"></span>
                    <span className="text-xs font-bold text-red-600">URGENT</span>
                  </div>
                </div>
                <div className="p-5 flex-grow">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Patient ID</p>
                      <p className="font-semibold text-text-dark">33445 | 67M</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Location</p>
                      <p className="font-semibold text-text-dark">Room 401</p>
                    </div>
                  </div>
                </div>
                <div className="px-5 pb-5 flex justify-between items-center">
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Clock className="w-4 h-4" />
                    <span>2 days ago</span>
                  </div>
                  <a href="#" className="py-2 px-4 rounded-lg border-2 border-red-500 text-red-500 font-semibold hover:bg-red-500 hover:text-white transition-colors text-sm">
                    View Analysis
                  </a>
                </div>
              </div>

              {/* Card 8 */}
              <div className="bg-gray-light rounded-2xl shadow-md hover:shadow-xl transition-shadow border border-gray-200 flex flex-col">
                <div className="flex justify-between items-center p-5 border-b border-gray-200">
                  <h3 className="text-lg font-bold text-text-dark">Olivia Martinez</h3>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 bg-blue-500 rounded-full"></span>
                    <span className="text-xs font-bold text-blue-600">IN PROGRESS</span>
                  </div>
                </div>
                <div className="p-5 flex-grow">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Patient ID</p>
                      <p className="font-semibold text-text-dark">10102 | 29F</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Location</p>
                      <p className="font-semibold text-text-dark">Room 402</p>
                    </div>
                  </div>
                </div>
                <div className="px-5 pb-5 flex justify-between items-center">
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Clock className="w-4 h-4" />
                    <span>2 days ago</span>
                  </div>
                  <a href="#" className="py-2 px-4 rounded-lg border-2 border-blue-500 text-blue-500 font-semibold hover:bg-blue-500 hover:text-white transition-colors text-sm">
                    Continue Review
                  </a>
                </div>
              </div>

              {/* Card 9 */}
              <div className="bg-gray-light rounded-2xl shadow-md hover:shadow-xl transition-shadow border border-gray-200 flex flex-col">
                <div className="flex justify-between items-center p-5 border-b border-gray-200">
                  <h3 className="text-lg font-bold text-text-dark">William Anderson</h3>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 bg-green-500 rounded-full"></span>
                    <span className="text-xs font-bold text-green-600">REVIEWED</span>
                  </div>
                </div>
                <div className="p-5 flex-grow">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Patient ID</p>
                      <p className="font-semibold text-text-dark">55667 | 75M</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Location</p>
                      <p className="font-semibold text-text-dark">Room 403</p>
                    </div>
                  </div>
                </div>
                <div className="px-5 pb-5 flex justify-between items-center">
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Clock className="w-4 h-4" />
                    <span>3 days ago</span>
                  </div>
                  <a href="#" className="py-2 px-4 rounded-lg border-2 border-green-500 text-green-500 font-semibold hover:bg-green-500 hover:text-white transition-colors text-sm">
                    View History
                  </a>
                </div>
              </div>

              {/* Card 10 */}
              <div className="bg-gray-light rounded-2xl shadow-md hover:shadow-xl transition-shadow border border-gray-200 flex flex-col">
                <div className="flex justify-between items-center p-5 border-b border-gray-200">
                  <h3 className="text-lg font-bold text-text-dark">Sophia Thomas</h3>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 bg-blue-500 rounded-full"></span>
                    <span className="text-xs font-bold text-blue-600">IN PROGRESS</span>
                  </div>
                </div>
                <div className="p-5 flex-grow">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Patient ID</p>
                      <p className="font-semibold text-text-dark">88990 | 42F</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Location</p>
                      <p className="font-semibold text-text-dark">Room 405</p>
                    </div>
                  </div>
                </div>
                <div className="px-5 pb-5 flex justify-between items-center">
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Clock className="w-4 h-4" />
                    <span>3 days ago</span>
                  </div>
                  <a href="#" className="py-2 px-4 rounded-lg border-2 border-blue-500 text-blue-500 font-semibold hover:bg-blue-500 hover:text-white transition-colors text-sm">
                    Continue Review
                  </a>
                </div>
              </div>

              {/* Card 11 */}
              <div className="bg-gray-light rounded-2xl shadow-md hover:shadow-xl transition-shadow border border-gray-200 flex flex-col">
                <div className="flex justify-between items-center p-5 border-b border-gray-200">
                  <h3 className="text-lg font-bold text-text-dark">Benjamin Jackson</h3>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 bg-green-500 rounded-full"></span>
                    <span className="text-xs font-bold text-green-600">REVIEWED</span>
                  </div>
                </div>
                <div className="p-5 flex-grow">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Patient ID</p>
                      <p className="font-semibold text-text-dark">12121 | 58M</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Location</p>
                      <p className="font-semibold text-text-dark">Room 408</p>
                    </div>
                  </div>
                </div>
                <div className="px-5 pb-5 flex justify-between items-center">
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Clock className="w-4 h-4" />
                    <span>4 days ago</span>
                  </div>
                  <a href="#" className="py-2 px-4 rounded-lg border-2 border-green-500 text-green-500 font-semibold hover:bg-green-500 hover:text-white transition-colors text-sm">
                    View History
                  </a>
                </div>
              </div>

              {/* Card 12 */}
              <div className="bg-gray-light rounded-2xl shadow-md hover:shadow-xl transition-shadow border border-gray-200 flex flex-col">
                <div className="flex justify-between items-center p-5 border-b border-gray-200">
                  <h3 className="text-lg font-bold text-text-dark">Ava White</h3>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 bg-red-500 rounded-full"></span>
                    <span className="text-xs font-bold text-red-600">URGENT</span>
                  </div>
                </div>
                <div className="p-5 flex-grow">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">Patient ID</p>
                      <p className="font-semibold text-text-dark">45456 | 61F</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Location</p>
                      <p className="font-semibold text-text-dark">Room 501</p>
                    </div>
                  </div>
                </div>
                <div className="px-5 pb-5 flex justify-between items-center">
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Clock className="w-4 h-4" />
                    <span>5 days ago</span>
                  </div>
                  <a href="#" className="py-2 px-4 rounded-lg border-2 border-red-500 text-red-500 font-semibold hover:bg-red-500 hover:text-white transition-colors text-sm">
                    View Analysis
                  </a>
                </div>
              </div>

            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-16 py-12 bg-text-dark text-gray-light">
        <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 grid grid-cols-1 md:grid-cols-4 gap-10 text-center md:text-left">
          <div>
            <h4 className="font-bold text-white mb-4 text-lg">About Clinical.ai</h4>
            <ul className="space-y-3 text-sm">
              <li>
                <a href="#" className="hover:text-secondary transition-colors flex items-center justify-center md:justify-start">
                  <Target className="w-4 h-4 mr-2" />Our Mission
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-secondary transition-colors flex items-center justify-center md:justify-start">
                  <Users className="w-4 h-4 mr-2" />Team
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-secondary transition-colors flex items-center justify-center md:justify-start">
                  <Briefcase className="w-4 h-4 mr-2" />Careers
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="font-bold text-white mb-4 text-lg">Support</h4>
            <ul className="space-y-3 text-sm">
              <li>
                <a href="#" className="hover:text-secondary transition-colors flex items-center justify-center md:justify-start">
                  <Headphones className="w-4 h-4 mr-2" />Contact Support
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-secondary transition-colors flex items-center justify-center md:justify-start">
                  <HelpCircle className="w-4 h-4 mr-2" />FAQs
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-secondary transition-colors flex items-center justify-center md:justify-start">
                  <Shield className="w-4 h-4 mr-2" />Privacy Policy
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-secondary transition-colors flex items-center justify-center md:justify-start">
                  <FileText className="w-4 h-4 mr-2" />Terms of Service
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="font-bold text-white mb-4 text-lg">Resources</h4>
            <ul className="space-y-3 text-sm">
              <li>
                <a href="#" className="hover:text-secondary transition-colors flex items-center justify-center md:justify-start">
                  <BookOpen className="w-4 h-4 mr-2" />Documentation
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-secondary transition-colors flex items-center justify-center md:justify-start">
                  <Video className="w-4 h-4 mr-2" />Tutorials
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-secondary transition-colors flex items-center justify-center md:justify-start">
                  <Newspaper className="w-4 h-4 mr-2" />Blog
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="font-bold text-white mb-4 text-lg">Connect With Us</h4>
            <div className="flex justify-center md:justify-start space-x-4 mb-4">
              <a href="#" className="w-10 h-10 bg-accent hover:bg-blue-400 rounded-full flex items-center justify-center transition-colors">
                <Facebook className="w-5 h-5" />
              </a>
              <a href="#" className="w-10 h-10 bg-blue-400 hover:bg-blue-500 rounded-full flex items-center justify-center transition-colors">
                <Twitter className="w-5 h-5" />
              </a>
              <a href="#" className="w-10 h-10 bg-blue-600 hover:bg-blue-700 rounded-full flex items-center justify-center transition-colors">
                <Linkedin className="w-5 h-5" />
              </a>
            </div>
            <p className="text-sm text-gray-medium">Stay updated with our latest features and healthcare insights.</p>
          </div>
        </div>
        <div className="mt-10 border-t border-gray-dark pt-8 text-center">
          <p className="text-sm text-gray-medium">
            &copy; 2025 Clinical.ai Inc. All rights reserved. | Transforming Healthcare with AI
          </p>
        </div>
      </footer>
    </div>
  );
};

export default ClinicalDashboard;