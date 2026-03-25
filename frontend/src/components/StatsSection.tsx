import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

const stats = [
  { value: '20K+', label: 'Satellite Images Indexed', icon: '🛰️' },
  { value: '<2s', label: 'Average Response Time', icon: '⚡' },
  { value: '768D', label: 'Embedding Dimensions', icon: '🎯' },
  { value: '95%', label: 'Retrieval Accuracy', icon: '✓' }
];

const StatsSection: React.FC = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [counters, setCounters] = useState(stats.map(() => 0));

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      { threshold: 0.3 }
    );

    const element = document.getElementById('stats-section');
    if (element) observer.observe(element);

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (isVisible) {
      const duration = 2000;
      const steps = 60;
      const interval = duration / steps;
      
      let step = 0;
      const timer = setInterval(() => {
        step++;
        setCounters(stats.map((stat) => {
          const progress = step / steps;
          const easeOut = 1 - Math.pow(1 - progress, 3);
          if (stat.value.includes('K')) {
            return Math.round(20 * easeOut);
          } else if (stat.value.includes('s')) {
            return Math.round(2 * easeOut * 10) / 10;
          } else if (stat.value.includes('D')) {
            return Math.round(768 * easeOut);
          } else if (stat.value.includes('%')) {
            return Math.round(95 * easeOut);
          }
          return 0;
        }));
        
        if (step >= steps) clearInterval(timer);
      }, interval);

      return () => clearInterval(timer);
    }
  }, [isVisible]);

  const formatValue = (stat: typeof stats[0], index: number) => {
    if (stat.value.includes('K')) return `${counters[index]}K+`;
    if (stat.value.includes('s')) return `<${counters[index].toFixed(1)}s`;
    if (stat.value.includes('D')) return `${counters[index]}D`;
    if (stat.value.includes('%')) return `${counters[index]}%`;
    return stat.value;
  };

  return (
    <section id="stats-section" className="py-16 px-4 sm:px-6">
      <div className="max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="relative"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-neon-purple/10 via-neon-blue/10 to-neon-cyan/10 blur-3xl" />
          
          <div className="relative glass-card p-8 sm:p-10">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 sm:gap-12">
              {stats.map((stat, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, scale: 0.9 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1, duration: 0.5 }}
                  className="text-center"
                >
                  <div className="text-3xl sm:text-4xl mb-2">{stat.icon}</div>
                  <motion.div 
                    className="text-2xl sm:text-4xl font-bold bg-gradient-to-r from-neon-purple via-neon-blue to-neon-cyan bg-clip-text text-transparent mb-2"
                  >
                    {formatValue(stat, index)}
                  </motion.div>
                  <div className="text-xs sm:text-sm text-gray-500">{stat.label}</div>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default StatsSection;
