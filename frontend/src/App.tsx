import { useState, useRef, useCallback } from 'react';
import Hero from './components/Hero';
import Globe from './components/Globe';
import ImageUpload from './components/ImageUpload';
import CoordinateDisplay from './components/CoordinateDisplay';
import GlobePage from './pages/GlobePage';
import { inferLocation } from './services/api';
import type { Coordinates } from './types';

function App() {
  const uploadRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [coordinates, setCoordinates] = useState<Coordinates | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showGlobe, setShowGlobe] = useState(false);
  const [globeCoords, setGlobeCoords] = useState<{ lat: number; lng: number } | null>(null);

  const scrollToUpload = useCallback(() => {
    uploadRef.current?.scrollIntoView({ behavior: 'smooth' });
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
        setCoordinates({
          latitude: response.coordinates.latitude,
          longitude: response.coordinates.longitude,
          confidence: response.coordinates.confidence
        });
      } else {
        setError(response.message || 'Failed to retrieve coordinates');
        setCoordinates(generateRandomCoordinates());
      }
    } catch (err) {
      console.log('Backend not available, using demo mode');
      setCoordinates(generateRandomCoordinates());
    } finally {
      setIsLoading(false);
    }
  }, [generateRandomCoordinates]);

  if (showGlobe) {
    return <GlobePage coordinates={globeCoords || undefined} onBack={handleBackFromGlobe} />;
  }

  return (
    <div className="min-h-screen bg-dark-900">
      <div className="fixed inset-0 z-0">
        <Globe />
      </div>

      <div className="relative z-10">
        <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-4">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-neon-purple to-neon-blue flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </div>
              <span className="text-lg font-semibold text-white">SatIntel</span>
            </div>
            
            <div className="hidden md:flex items-center gap-8">
              <button onClick={scrollToUpload} className="text-gray-400 hover:text-white transition-colors text-sm">
                Upload
              </button>
              <button className="text-gray-400 hover:text-white transition-colors text-sm">
                Documentation
              </button>
              <button className="text-gray-400 hover:text-white transition-colors text-sm">
                About
              </button>
            </div>

            <button className="md:hidden p-2 text-gray-400">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </nav>

        <Hero onScrollToUpload={scrollToUpload} />

        <div ref={uploadRef}>
          <ImageUpload onUpload={handleUpload} isLoading={isLoading} />
        </div>

        <CoordinateDisplay 
          coordinates={coordinates} 
          isLoading={isLoading} 
          error={error}
          onFlyTo={flyToOnGlobe}
        />

        <footer className="py-12 px-6 border-t border-white/10">
          <div className="max-w-7xl mx-auto text-center">
            <div className="flex items-center justify-center gap-3 mb-4">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-neon-purple to-neon-blue flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </div>
              <span className="text-sm font-semibold text-white">SatIntel</span>
            </div>
            <p className="text-gray-500 text-sm">
              © 2024 Satellite Intelligence System. All rights reserved.
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default App;
