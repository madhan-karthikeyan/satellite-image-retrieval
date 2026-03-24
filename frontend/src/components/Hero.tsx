import { motion } from 'framer-motion';

interface HeroProps {
  onScrollToUpload: () => void;
}

const Hero: React.FC<HeroProps> = ({ onScrollToUpload }) => {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      <div className="absolute inset-0 z-0">
        <div className="absolute inset-0 bg-gradient-to-b from-dark-900/80 via-dark-900/60 to-dark-900 z-10" />
        <div className="absolute inset-0 bg-gradient-to-r from-neon-purple/10 via-transparent to-neon-cyan/10 z-10" />
      </div>

      <motion.div 
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="relative z-20 text-center px-6 max-w-4xl mx-auto"
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-8"
        >
          <span className="w-2 h-2 rounded-full bg-neon-green animate-pulse" />
          <span className="text-sm text-gray-300">Live Satellite Data</span>
        </motion.div>

        <motion.h1 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent"
        >
          Satellite Intelligence
          <span className="block mt-2 bg-gradient-to-r from-neon-purple via-neon-blue to-neon-cyan bg-clip-text text-transparent">
            System
          </span>
        </motion.h1>

        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.6 }}
          className="text-lg md:text-xl text-gray-400 mb-10 max-w-2xl mx-auto leading-relaxed"
        >
          Upload satellite imagery and instantly retrieve precise geographic coordinates 
          with our advanced AI-powered geolocation engine.
        </motion.p>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.6 }}
          className="flex flex-col sm:flex-row gap-4 justify-center"
        >
          <button
            onClick={onScrollToUpload}
            className="group relative px-8 py-4 rounded-xl font-semibold text-white overflow-hidden transition-all duration-300 hover:scale-105"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-neon-purple via-neon-blue to-neon-cyan" />
            <div className="absolute inset-0 bg-gradient-to-r from-neon-purple via-neon-blue to-neon-cyan opacity-80 group-hover:opacity-100 transition-opacity" />
            <div className="absolute inset-0 bg-white/20 blur-xl group-hover:bg-white/30 transition-all" />
            <span className="relative flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              Upload Image
            </span>
          </button>

          <button
            className="px-8 py-4 rounded-xl font-semibold text-gray-300 border border-white/20 bg-white/5 hover:bg-white/10 hover:border-white/30 transition-all duration-300 backdrop-blur-sm"
          >
            <span className="flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Learn More
            </span>
          </button>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1, duration: 0.8 }}
          className="mt-16 flex items-center justify-center gap-8 text-sm text-gray-500"
        >
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-neon-green" fill="currentColor" viewBox="0 0 20 20">
              <circle cx="10" cy="10" r="4" />
            </svg>
            <span>Real-time Processing</span>
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-neon-blue" fill="currentColor" viewBox="0 0 20 20">
              <circle cx="10" cy="10" r="4" />
            </svg>
            <span>High Accuracy</span>
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-neon-purple" fill="currentColor" viewBox="0 0 20 20">
              <circle cx="10" cy="10" r="4" />
            </svg>
            <span>Secure & Private</span>
          </div>
        </motion.div>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2, duration: 1 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2 z-20"
      >
        <button
          onClick={onScrollToUpload}
          className="p-2 rounded-full border border-white/20 bg-white/5 hover:bg-white/10 transition-all duration-300 animate-bounce"
        >
          <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </button>
      </motion.div>
    </section>
  );
};

export default Hero;
