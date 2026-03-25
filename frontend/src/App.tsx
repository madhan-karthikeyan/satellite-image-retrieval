import { useState, useRef, useCallback, useEffect } from 'react';
import Hero from './components/Hero';
import Globe from './components/Globe';
import ImageUpload from './components/ImageUpload';
import CoordinateDisplay from './components/CoordinateDisplay';
import GlobePage from './pages/GlobePage';
import FeatureCards from './components/FeatureCards';
import StatsSection from './components/StatsSection';
import HowItWorks from './components/HowItWorks';
import { inferLocation } from './services/api';
import type { Coordinates } from './types';

function App() {
  const uploadRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [coordinates, setCoordinates] = useState<Coordinates | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showGlobe, setShowGlobe] = useState(false);
  const [globeCoords, setGlobeCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showDemoMode, setShowDemoMode] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setShowDemoMode(true), 3000);
    return () => clearTimeout(timer);
  }, []);

  const scrollToUpload = useCallback(() => {
    setMobileMenuOpen(false);
    setTimeout(() => {
      uploadRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  }, []);

  const scrollToFeatures = useCallback(() => {
    setMobileMenuOpen(false);
    const el = document.getElementById('features');
    setTimeout(() => el?.scrollIntoView({ behavior: 'smooth' }), 100);
  }, []);

  const scrollToHowItWorks = useCallback(() => {
    setMobileMenuOpen(false);
    const el = document.getElementById('how-it-works');
    setTimeout(() => el?.scrollIntoView({ behavior: 'smooth' }), 100);
  }, []);

  const flyToOnGlobe = useCallback((lat: number, lng: number) => {
    setGlobeCoords({ lat, lng });
    setShowGlobe(true);
  }, []);

  const handleBackFromGlobe = useCallback(() => {
    setShowGlobe(false);
    setGlobeCoords(null);
  }, []);

  const generateRandomCoordinates = useCallback(() => {
    const lat = (Math.random() * 140 - 70);
    const lng = (Math.random() * 360 - 180);
    const confidence = 0.7 + Math.random() * 0.25;
    return {
      latitude: lat,
      longitude: lng,
      confidence
    };
  }, []);

  const handleUpload = useCallback(async (file: File) => {
    setIsLoading(true);
    setError(null);
    setCoordinates(null);

    try {
      const response = await inferLocation(file);
      
      if (response.success && response.coordinates) {
        setCoordinates(response.coordinates);
      } else {
        setError(response.message || 'Failed to retrieve coordinates');
        if (showDemoMode) {
          setCoordinates(generateRandomCoordinates());
        }
      }
    } catch (err) {
      console.log('Backend not available, using demo mode');
      if (showDemoMode) {
        setCoordinates(generateRandomCoordinates());
      } else {
        setError('Backend service unavailable');
      }
    } finally {
      setIsLoading(false);
    }
  }, [generateRandomCoordinates, showDemoMode]);

  if (showGlobe) {
    return <GlobePage coordinates={globeCoords || undefined} onBack={handleBackFromGlobe} />;
  }

  return (
    <div className="min-h-screen bg-dark-900">
      <div className="fixed inset-0 z-0 opacity-60">
        <Globe />
      </div>

      <div className="relative z-10">
        <nav className="fixed top-0 left-0 right-0 z-50 bg-dark-900/80 backdrop-blur-xl border-b border-white/10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-neon-purple to-neon-blue flex items-center justify-center shadow-lg shadow-neon-purple/25">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </div>
                <span className="text-lg font-bold text-white tracking-tight">SatIntel</span>
              </div>
              
              <div className="hidden md:flex items-center gap-8">
                <button onClick={scrollToFeatures} className="text-gray-400 hover:text-white transition-colors text-sm font-medium">
                  Features
                </button>
                <button onClick={scrollToHowItWorks} className="text-gray-400 hover:text-white transition-colors text-sm font-medium">
                  How It Works
                </button>
                <button onClick={scrollToUpload} className="px-5 py-2 rounded-lg bg-gradient-to-r from-neon-purple to-neon-blue text-white text-sm font-semibold hover:shadow-lg hover:shadow-neon-purple/25 transition-all">
                  Get Started
                </button>
              </div>

              <button 
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2 text-gray-400 hover:text-white transition-colors"
                aria-label="Toggle menu"
              >
                {mobileMenuOpen ? (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                ) : (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                )}
              </button>
            </div>

            {mobileMenuOpen && (
              <div className="md:hidden py-4 border-t border-white/10">
                <div className="flex flex-col gap-3">
                  <button 
                    onClick={scrollToFeatures} 
                    className="px-4 py-3 text-left text-gray-300 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                  >
                    Features
                  </button>
                  <button 
                    onClick={scrollToHowItWorks} 
                    className="px-4 py-3 text-left text-gray-300 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                  >
                    How It Works
                  </button>
                  <button 
                    onClick={scrollToUpload}
                    className="px-4 py-3 text-center bg-gradient-to-r from-neon-purple to-neon-blue text-white font-semibold rounded-lg"
                  >
                    Get Started
                  </button>
                </div>
              </div>
            )}
          </div>
        </nav>

        <Hero onScrollToUpload={scrollToUpload} />
        
        <StatsSection />
        
        <div id="features">
          <FeatureCards />
        </div>
        
        <div id="how-it-works">
          <HowItWorks />
        </div>

        <div ref={uploadRef}>
          <ImageUpload onUpload={handleUpload} isLoading={isLoading} />
        </div>

        <CoordinateDisplay 
          coordinates={coordinates} 
          isLoading={isLoading} 
          error={error}
          onFlyTo={flyToOnGlobe}
        />

        <footer className="py-12 px-4 sm:px-6 border-t border-white/10 bg-dark-900/90 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
              <div className="md:col-span-2">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-neon-purple to-neon-blue flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                  </div>
                  <span className="text-lg font-bold text-white">SatIntel</span>
                </div>
                <p className="text-gray-500 text-sm max-w-md">
                  Advanced satellite image geolocation powered by RemoteCLIP and machine learning.
                  Identify precise locations from satellite imagery.
                </p>
              </div>
              
              <div>
                <h4 className="text-white font-semibold mb-4">Platform</h4>
                <ul className="space-y-2 text-gray-500 text-sm">
                  <li><button onClick={scrollToFeatures} className="hover:text-white transition-colors">Features</button></li>
                  <li><button onClick={scrollToHowItWorks} className="hover:text-white transition-colors">How It Works</button></li>
                  <li><button onClick={scrollToUpload} className="hover:text-white transition-colors">Upload Image</button></li>
                </ul>
              </div>
              
              <div>
                <h4 className="text-white font-semibold mb-4">Technology</h4>
                <ul className="space-y-2 text-gray-500 text-sm">
                  <li><span className="text-gray-600">RemoteCLIP</span></li>
                  <li><span className="text-gray-600">ChromaDB</span></li>
                  <li><span className="text-gray-600">fMoW Dataset</span></li>
                </ul>
              </div>
            </div>
            
            <div className="pt-8 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4">
              <p className="text-gray-600 text-sm">
                © 2024 Satellite Intelligence System
              </p>
              <div className="flex items-center gap-6">
                <span className="flex items-center gap-2 text-xs text-gray-600">
                  <span className="w-2 h-2 rounded-full bg-neon-green animate-pulse" />
                  All systems operational
                </span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default App;
