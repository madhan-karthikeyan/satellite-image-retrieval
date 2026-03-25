import { motion } from 'framer-motion';

const steps = [
  {
    number: '01',
    title: 'Upload Image',
    description: 'Drag and drop your satellite image or click to browse. We support JPG, PNG, and WEBP formats up to 10MB.',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    )
  },
  {
    number: '02',
    title: 'AI Processing',
    description: 'Our RemoteCLIP model extracts deep semantic features from your image using state-of-the-art vision-language alignment.',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    )
  },
  {
    number: '03',
    title: 'Vector Search',
    description: 'Your image embedding is matched against our indexed database of 20,000+ satellite images using ChromaDB.',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    )
  },
  {
    number: '04',
    title: 'Get Results',
    description: 'Receive precise GPS coordinates with confidence scores, scene classification, and visualization on an interactive globe.',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    )
  }
];

const HowItWorks: React.FC = () => {
  return (
    <section className="py-24 px-4 sm:px-6 bg-dark-800/50">
      <div className="max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            <span className="bg-gradient-to-r from-neon-blue to-neon-cyan bg-clip-text text-transparent">
              How It Works
            </span>
          </h2>
          <p className="text-gray-400 max-w-2xl mx-auto">
            Four simple steps from image upload to precise geolocation results.
          </p>
        </motion.div>

        <div className="relative">
          <div className="hidden lg:block absolute top-1/2 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-y-1/2" />
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
            {steps.map((step, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.15, duration: 0.5 }}
                className="relative"
              >
                <div className="glass-card p-6 h-full hover:border-neon-blue/30 transition-all duration-300">
                  <div className="flex items-start gap-4 mb-4">
                    <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-gradient-to-br from-neon-purple to-neon-blue flex items-center justify-center text-white">
                      {step.icon}
                    </div>
                    <span className="text-4xl font-bold text-white/5">{step.number}</span>
                  </div>
                  
                  <h3 className="text-lg font-semibold text-white mb-3">{step.title}</h3>
                  <p className="text-sm text-gray-400 leading-relaxed">{step.description}</p>
                  
                  {index < steps.length - 1 && (
                    <div className="hidden lg:block absolute -right-4 top-1/2 -translate-y-1/2 w-8 h-8 z-10">
                      <svg className="w-full h-full text-neon-purple" viewBox="0 0 32 32" fill="none">
                        <path d="M12 16l8 8m0-8l-8 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.6, duration: 0.6 }}
          className="mt-16 glass-card p-8 text-center"
        >
          <div className="flex flex-wrap justify-center gap-8 mb-6">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-neon-purple" />
              <span className="text-sm text-gray-400">RemoteCLIP ViT-L/14</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-neon-blue" />
              <span className="text-sm text-gray-400">ChromaDB Vector Search</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-neon-cyan" />
              <span className="text-sm text-gray-400">fMoW Dataset</span>
            </div>
          </div>
          <p className="text-gray-500 text-sm">
            Powered by advanced computer vision models trained on millions of satellite images.
          </p>
        </motion.div>
      </div>
    </section>
  );
};

export default HowItWorks;
