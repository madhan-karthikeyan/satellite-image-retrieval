import { useEffect, useRef, useState } from 'react';

declare global {
  interface Window {
    Cesium: any;
  }
}

interface GlobeProps {
  onCoordinatesChange?: (lat: number, lng: number) => void;
}

const Globe: React.FC<GlobeProps> = ({ onCoordinatesChange }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadCesium = async () => {
      if (!containerRef.current || viewerRef.current) return;

      const cesiumToken = import.meta.env.VITE_CESIUM_TOKEN;
      
      if (!cesiumToken) {
        setError('Cesium token not configured');
        setIsLoading(false);
        return;
      }

      try {
        const script = document.createElement('script');
        script.src = 'https://cesium.com/downloads/cesiumjs/releases/1.111/Build/Cesium/Cesium.js';
        script.async = true;
        
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = 'https://cesium.com/downloads/cesiumjs/releases/1.111/Build/Cesium/Widgets/widgets.css';
        document.head.appendChild(link);

        await new Promise<void>((resolve, reject) => {
          script.onload = () => resolve();
          script.onerror = () => reject(new Error('Failed to load Cesium'));
          document.body.appendChild(script);
        });

        window.Cesium.Ion.defaultAccessToken = cesiumToken;

        const viewer = new window.Cesium.Viewer(containerRef.current, {
          animation: false,
          timeline: false,
          baseLayerPicker: false,
          geocoder: false,
          sceneModePicker: false,
          navigationHelpButton: false,
          homeButton: false,
          fullscreenButton: false,
          selectionIndicator: false,
          infoBox: false,
        });

        viewer.scene.globe.enableLighting = true;
        viewer.scene.skyBox.show = true;

        let rotating = true;
        viewer.clock.onTick.addEventListener(() => {
          if (rotating) {
            viewer.scene.camera.rotate(window.Cesium.Cartesian3.UNIT_Z, 0.0003);
          }
        });

        (window as any).globeViewer = viewer;
        (window as any).globeRotating = rotating;
        viewerRef.current = viewer;
        setIsLoading(false);
        
        if (onCoordinatesChange) {
          (window as any).globeOnCoordinatesChange = onCoordinatesChange;
        }
      } catch (err) {
        console.error('Failed to initialize Cesium:', err);
        setError('Failed to load globe visualization');
        setIsLoading(false);
      }
    };

    loadCesium();

    return () => {
      if (viewerRef.current) {
        viewerRef.current.destroy();
        viewerRef.current = null;
      }
    };
  }, [onCoordinatesChange]);

  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data?.type === 'COORDINATES_FROM_GLOBE' && onCoordinatesChange) {
        const { lat, lng } = event.data;
        onCoordinatesChange(lat, lng);
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [onCoordinatesChange]);

  return (
    <div className="relative w-full h-full">
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-dark-900 z-10">
          <div className="flex flex-col items-center gap-4">
            <div className="w-12 h-12 border-4 border-neon-purple/30 border-t-neon-purple rounded-full animate-spin" />
            <p className="text-gray-400 text-sm">Loading globe...</p>
          </div>
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-dark-900 z-10">
          <div className="flex flex-col items-center gap-4 text-center px-4">
            <svg className="w-12 h-12 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-gray-500 text-sm">{error}</p>
          </div>
        </div>
      )}
      <div 
        ref={containerRef} 
        className="w-full h-full"
        style={{ background: '#0a0a0a' }}
      />
    </div>
  );
};

export const flyToCoordinates = (lat: number, lng: number) => {
  const viewer = (window as any).globeViewer;
  if (!viewer) return;

  (window as any).globeRotating = false;
  viewer.entities.removeAll();

  const entity = viewer.entities.add({
    position: window.Cesium.Cartesian3.fromDegrees(lng, lat),
    point: {
      pixelSize: 14,
      color: window.Cesium.Color.CYAN,
      outlineColor: window.Cesium.Color.WHITE,
      outlineWidth: 3,
    },
  });

  viewer.flyTo(entity, {
    duration: 2,
    offset: new window.Cesium.HeadingPitchRange(
      0,
      window.Cesium.Math.toRadians(-90),
      800
    )
  });
};

export default Globe;
