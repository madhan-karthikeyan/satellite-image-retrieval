import { useEffect, useRef, useState } from 'react';

interface GlobePageProps {
  coordinates?: { lat: number; lng: number };
  onBack?: () => void;
}

const GlobePage: React.FC<GlobePageProps> = ({ coordinates, onBack }) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const handleIframeLoad = () => {
      setIsLoading(false);
      
      if (coordinates) {
        setTimeout(() => {
          if (iframeRef.current?.contentWindow) {
            const latInput = iframeRef.current.contentWindow.document.getElementById('lat');
            const lonInput = iframeRef.current.contentWindow.document.getElementById('lon');
            
            if (latInput && lonInput) {
              (latInput as HTMLInputElement).value = coordinates.lat.toString();
              (lonInput as HTMLInputElement).value = coordinates.lng.toString();
              
              const button = iframeRef.current.contentWindow.document.querySelector('button');
              if (button) {
                (button as HTMLButtonElement).click();
              }
            }
          }
        }, 1000);
      }
    };

    const iframe = iframeRef.current;
    if (iframe) {
      iframe.addEventListener('load', handleIframeLoad);
    }

    return () => {
      if (iframe) {
        iframe.removeEventListener('load', handleIframeLoad);
      }
    };
  }, [coordinates]);

  return (
    <div className="fixed inset-0 z-50 bg-dark-900">
      <div className="absolute top-4 left-4 z-50">
        <button
          onClick={onBack}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/10 border border-white/20 text-white hover:bg-white/20 transition-colors backdrop-blur-lg"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back
        </button>
      </div>

      {coordinates && (
        <div className="absolute top-4 right-4 z-50 px-4 py-2 rounded-xl bg-neon-purple/20 border border-neon-purple/50 text-white backdrop-blur-lg">
          <span className="text-sm">
            📍 {coordinates.lat.toFixed(4)}°, {coordinates.lng.toFixed(4)}°
          </span>
        </div>
      )}

      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-dark-900 z-10">
          <div className="flex flex-col items-center gap-4">
            <div className="w-12 h-12 border-4 border-neon-purple/30 border-t-neon-purple rounded-full animate-spin" />
            <p className="text-gray-400">Loading globe...</p>
          </div>
        </div>
      )}

      <iframe
        ref={iframeRef}
        src="/globe.html"
        className="w-full h-full border-none"
        title="Globe"
        allow="fullscreen"
      />
    </div>
  );
};

export default GlobePage;
