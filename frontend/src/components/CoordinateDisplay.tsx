import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import type { Coordinates } from '../types';

interface CoordinateDisplayProps {
  coordinates: Coordinates | null;
  isLoading: boolean;
  error: string | null;
  onFlyTo?: (lat: number, lng: number) => void;
}

const confidenceColors = {
  high: { bg: 'from-neon-green/20 to-emerald-500/20', border: 'border-neon-green/50', text: 'text-neon-green' },
  medium: { bg: 'from-neon-blue/20 to-cyan-500/20', border: 'border-neon-blue/50', text: 'text-neon-blue' },
  low: { bg: 'from-neon-purple/20 to-pink-500/20', border: 'border-neon-purple/50', text: 'text-neon-purple' }
};

const LoadingSkeleton: React.FC = () => (
  <div className="space-y-6 animate-pulse">
    <div className="grid grid-cols-2 gap-4">
      <div className="h-28 bg-white/5 rounded-xl" />
      <div className="h-28 bg-white/5 rounded-xl" />
    </div>
    <div className="h-24 bg-white/5 rounded-xl" />
    <div className="h-16 bg-white/5 rounded-xl" />
  </div>
);

const CoordinateDisplay: React.FC<CoordinateDisplayProps> = ({ coordinates, isLoading, error, onFlyTo }) => {
  const [copied, setCopied] = useState(false);

  if (!coordinates && !isLoading && !error) {
    return null;
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(
      `${coordinates?.latitude.toFixed(6)}, ${coordinates?.longitude.toFixed(6)}`
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const confidenceLevel = coordinates?.confidenceLevel || 
    (coordinates && coordinates.confidence !== undefined && coordinates.confidence >= 0.7 ? 'high' : 
     coordinates && coordinates.confidence !== undefined && coordinates.confidence >= 0.5 ? 'medium' : 'low');
  const colors = confidenceColors[confidenceLevel as keyof typeof confidenceColors] || confidenceColors.medium;

  const sceneDistribution = coordinates?.sceneDistribution || {};
  const totalScenes = Object.values(sceneDistribution).reduce((a, b) => a + b, 0) || 1;

  return (
    <section className="py-16 px-4 sm:px-6">
      <div className="max-w-3xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card overflow-hidden"
        >
          <div className="p-6 sm:p-8 border-b border-white/10">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${colors.bg} border ${colors.border} flex items-center justify-center`}>
                  <svg className={`w-5 h-5 ${colors.text}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">Location Analysis</h3>
                  <p className="text-xs text-gray-500">Satellite Image Geolocation</p>
                </div>
              </div>
              
              {coordinates && !isLoading && (
                <div className={`px-3 py-1 rounded-full text-xs font-semibold bg-gradient-to-r ${colors.bg} border ${colors.border} ${colors.text}`}>
                  {confidenceLevel?.toUpperCase()} CONFIDENCE
                </div>
              )}
            </div>
          </div>

          <div className="p-6 sm:p-8">
            {isLoading && <LoadingSkeleton />}

            {error && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="p-6 rounded-xl bg-red-500/10 border border-red-500/30"
              >
                <div className="flex items-start gap-3 text-red-400">
                  <svg className="w-6 h-6 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <p className="font-medium">Analysis Failed</p>
                    <p className="text-sm text-red-400/80 mt-1">{error}</p>
                  </div>
                </div>
              </motion.div>
            )}

            {coordinates && !isLoading && (
              <div className="space-y-6">
                {(coordinates.country || coordinates.region || coordinates.city || coordinates.continent) && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.05 }}
                    className="p-4 rounded-xl bg-gradient-to-r from-neon-purple/10 to-neon-blue/10 border border-neon-purple/20"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <svg className="w-4 h-4 text-neon-purple" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                      </svg>
                      <span className="text-xs text-gray-400 uppercase tracking-wider">Location</span>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      {coordinates.city && (
                        <span className="text-lg font-semibold text-white">{coordinates.city}</span>
                      )}
                      {coordinates.city && (coordinates.region || coordinates.country) && (
                        <span className="text-gray-500">,</span>
                      )}
                      {coordinates.region && (
                        <span className="text-white/80">{coordinates.region}</span>
                      )}
                      {coordinates.region && coordinates.country && (
                        <span className="text-gray-500">,</span>
                      )}
                      {coordinates.country && (
                        <div className="flex items-center gap-2">
                          <span className="text-white/80">{coordinates.country}</span>
                          {coordinates.countryCode && (
                            <span className="px-1.5 py-0.5 rounded bg-white/10 text-xs text-gray-400">
                              {coordinates.countryCode}
                            </span>
                          )}
                        </div>
                      )}
                      {coordinates.continent && (
                        <span className="ml-2 px-2 py-0.5 rounded-full bg-neon-purple/20 text-xs text-neon-purple">
                          {coordinates.continent}
                        </span>
                      )}
                    </div>
                  </motion.div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 }}
                    className="p-5 rounded-xl bg-white/5 border border-white/10"
                  >
                    <div className="flex items-center gap-2 text-gray-400 text-xs mb-2 uppercase tracking-wider">
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19V5m-7 7l7-7 7 7" />
                      </svg>
                      Latitude
                    </div>
                    <p className="text-2xl sm:text-3xl font-bold text-white font-mono tracking-tight">
                      {coordinates.latitude.toFixed(6)}°
                    </p>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.15 }}
                    className="p-5 rounded-xl bg-white/5 border border-white/10"
                  >
                    <div className="flex items-center gap-2 text-gray-400 text-xs mb-2 uppercase tracking-wider">
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17l-5-5m0 0l-5 5m5-5v12" />
                      </svg>
                      Longitude
                    </div>
                    <p className="text-2xl sm:text-3xl font-bold text-white font-mono tracking-tight">
                      {coordinates.longitude.toFixed(6)}°
                    </p>
                  </motion.div>
                </div>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className={`p-5 rounded-xl bg-gradient-to-r ${colors.bg} border ${colors.border}`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-gray-300 text-sm font-medium">Confidence Score</span>
                    <span className={`${colors.text} font-bold text-lg`}>
                      {Math.round((coordinates.confidence ?? 0) * 100)}%
                    </span>
                  </div>
                  <div className="h-2.5 bg-white/10 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${(coordinates.confidence ?? 0) * 100}%` }}
                      transition={{ delay: 0.4, duration: 0.8, ease: "easeOut" }}
                      className={`h-full bg-gradient-to-r ${colors.bg.replace('/20', '')} rounded-full`}
                    />
                  </div>
                  {coordinates.radiusKm && (
                    <p className="text-xs text-gray-500 mt-2">
                      Confidence radius: ±{Math.round(coordinates.radiusKm)} km
                    </p>
                  )}
                </motion.div>

                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.25 }}
                  className="flex gap-3"
                >
                  <button
                    onClick={() => onFlyTo?.(coordinates.latitude, coordinates.longitude)}
                    className="flex-1 py-3.5 px-5 rounded-xl bg-gradient-to-r from-neon-purple to-neon-blue text-white font-semibold text-sm hover:shadow-lg hover:shadow-neon-purple/25 transition-all flex items-center justify-center gap-2"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    View on Globe
                  </button>
                  <button
                    onClick={handleCopy}
                    className="py-3.5 px-5 rounded-xl bg-white/10 text-white font-semibold text-sm hover:bg-white/20 transition-all flex items-center justify-center gap-2"
                  >
                    <AnimatePresence mode="wait">
                      {copied ? (
                        <motion.svg
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          exit={{ scale: 0 }}
                          className="w-5 h-5 text-neon-green"
                          fill="none" stroke="currentColor" viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </motion.svg>
                      ) : (
                        <motion.svg
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          exit={{ scale: 0 }}
                          className="w-5 h-5"
                          fill="none" stroke="currentColor" viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </motion.svg>
                      )}
                    </AnimatePresence>
                    {copied ? 'Copied!' : 'Copy'}
                  </button>
                </motion.div>

                {coordinates.totalCandidates && coordinates.totalCandidates > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="mt-2"
                  >
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-neon-purple" />
                        {coordinates.clusterSize || 0} matching images
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-neon-blue" />
                        {coordinates.totalCandidates} candidates
                      </span>
                    </div>
                  </motion.div>
                )}

                {Object.keys(sceneDistribution).length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.35 }}
                    className="pt-4 border-t border-white/10"
                  >
                    <h4 className="text-sm font-medium text-gray-300 mb-3">Scene Distribution</h4>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(sceneDistribution)
                        .sort(([, a], [, b]) => b - a)
                        .slice(0, 6)
                        .map(([scene, count]) => (
                          <div
                            key={scene}
                            className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs"
                          >
                            <span className="text-gray-400">{scene}: </span>
                            <span className="text-white font-medium">{count}</span>
                            <span className="text-gray-600 ml-1">
                              ({Math.round((count / totalScenes) * 100)}%)
                            </span>
                          </div>
                        ))}
                    </div>
                  </motion.div>
                )}

                {coordinates.explanation && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="pt-4 border-t border-white/10"
                  >
                    <h4 className="text-sm font-medium text-gray-300 mb-2">AI Analysis</h4>
                    <p className="text-sm text-gray-400 leading-relaxed">
                      {coordinates.explanation}
                    </p>
                  </motion.div>
                )}
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default CoordinateDisplay;
