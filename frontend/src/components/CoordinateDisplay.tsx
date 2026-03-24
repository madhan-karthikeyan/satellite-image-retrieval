import { motion } from 'framer-motion';
import type { Coordinates } from '../types';

interface CoordinateDisplayProps {
  coordinates: Coordinates | null;
  isLoading: boolean;
  error: string | null;
  onFlyTo?: (lat: number, lng: number) => void;
}

const CoordinateDisplay: React.FC<CoordinateDisplayProps> = ({ coordinates, isLoading, error, onFlyTo }) => {
  if (!coordinates && !isLoading && !error) {
    return null;
  }

  return (
    <section className="py-16 px-6">
      <div className="max-w-2xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-8"
        >
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-neon-purple to-neon-blue flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white">Location Data</h3>
          </div>

          {isLoading && (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="relative">
                <div className="w-24 h-24 rounded-full border-4 border-white/10" />
                <div className="absolute inset-0 w-24 h-24 rounded-full border-4 border-transparent border-t-neon-purple animate-spin" />
              </div>
              <p className="mt-6 text-gray-300">Extracting coordinates...</p>
              <p className="text-sm text-gray-500 mt-2">Processing satellite imagery</p>
            </div>
          )}

          {error && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="p-6 rounded-xl bg-red-500/10 border border-red-500/30"
            >
              <div className="flex items-center gap-3 text-red-400">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="font-medium">Error: {error}</p>
              </div>
            </motion.div>
          )}

          {coordinates && !isLoading && (
            <div className="grid md:grid-cols-2 gap-6">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
                className="p-6 rounded-xl bg-white/5 border border-white/10"
              >
                <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19V5m-7 7l7-7 7 7" />
                  </svg>
                  Latitude
                </div>
                <p className="text-3xl font-bold text-white font-mono">
                  {coordinates.latitude.toFixed(6)}°
                </p>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
                className="p-6 rounded-xl bg-white/5 border border-white/10"
              >
                <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17l-5-5m0 0l-5 5m5-5v12" />
                  </svg>
                  Longitude
                </div>
                <p className="text-3xl font-bold text-white font-mono">
                  {coordinates.longitude.toFixed(6)}°
                </p>
              </motion.div>

              {coordinates.confidence !== undefined && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="md:col-span-2 p-6 rounded-xl bg-gradient-to-r from-neon-purple/20 to-neon-blue/20 border border-neon-purple/30"
                >
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-gray-400 text-sm">Confidence Score</span>
                    <span className="text-neon-green font-semibold">
                      {Math.round(coordinates.confidence * 100)}%
                    </span>
                  </div>
                  <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${coordinates.confidence * 100}%` }}
                      transition={{ delay: 0.5, duration: 0.8, ease: "easeOut" }}
                      className="h-full bg-gradient-to-r from-neon-purple via-neon-blue to-neon-cyan"
                    />
                  </div>
                </motion.div>
              )}

              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="md:col-span-2 flex gap-4 mt-4"
              >
                <button
                  onClick={() => onFlyTo?.(coordinates.latitude, coordinates.longitude)}
                  className="flex-1 py-3 px-6 rounded-xl bg-gradient-to-r from-neon-purple to-neon-blue text-white font-semibold hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  View on Globe
                </button>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(
                      `${coordinates.latitude.toFixed(6)}, ${coordinates.longitude.toFixed(6)}`
                    );
                  }}
                  className="py-3 px-6 rounded-xl bg-white/10 text-white font-semibold hover:bg-white/20 transition-colors flex items-center justify-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Copy
                </button>
              </motion.div>
            </div>
          )}
        </motion.div>
      </div>
    </section>
  );
};

export default CoordinateDisplay;
