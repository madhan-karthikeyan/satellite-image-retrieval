import { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface ImageUploadProps {
  onUpload: (file: File) => Promise<void>;
  isLoading: boolean;
}

const ImageUpload: React.FC<ImageUploadProps> = ({ onUpload, isLoading }) => {
  const [dragActive, setDragActive] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const validateAndProcessFile = useCallback((file: File) => {
    setError(null);
    
    if (!file.type.startsWith('image/')) {
      setError('Please upload an image file (JPG, PNG, WEBP)');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);

    onUpload(file);
  }, [onUpload]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndProcessFile(e.dataTransfer.files[0]);
    }
  }, [validateAndProcessFile]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndProcessFile(e.target.files[0]);
    }
  }, [validateAndProcessFile]);

  const handleClick = () => {
    inputRef.current?.click();
  };

  const handleReset = () => {
    setPreview(null);
    setError(null);
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  return (
    <section className="py-24 px-6">
      <div className="max-w-3xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            <span className="bg-gradient-to-r from-neon-purple to-neon-blue bg-clip-text text-transparent">
              Upload Satellite Image
            </span>
          </h2>
          <p className="text-gray-400">Drag and drop or click to select your image</p>
        </motion.div>

        <AnimatePresence mode="wait">
          {!preview ? (
            <motion.div
              key="upload-area"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.3 }}
            >
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={handleClick}
                className={`
                  relative cursor-pointer rounded-2xl border-2 border-dashed transition-all duration-300
                  ${dragActive 
                    ? 'border-neon-purple bg-neon-purple/10 scale-[1.02]' 
                    : 'border-white/20 hover:border-neon-purple/50 hover:bg-white/5'
                  }
                `}
              >
                <input
                  ref={inputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleChange}
                  className="hidden"
                />

                <div className="flex flex-col items-center justify-center py-16 px-6">
                  <div className={`
                    w-20 h-20 rounded-full flex items-center justify-center mb-6 transition-all duration-300
                    ${dragActive ? 'bg-neon-purple/20' : 'bg-white/10'}
                  `}>
                    <svg 
                      className={`w-10 h-10 transition-colors duration-300 ${dragActive ? 'text-neon-purple' : 'text-gray-400'}`} 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                        strokeWidth={1.5} 
                        d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" 
                      />
                    </svg>
                  </div>

                  <p className="text-lg text-gray-300 mb-2">
                    {dragActive ? 'Drop your image here' : 'Drag & drop your satellite image'}
                  </p>
                  <p className="text-sm text-gray-500">
                    or click to browse • JPG, PNG, WEBP up to 10MB
                  </p>
                </div>

                {dragActive && (
                  <div className="absolute inset-0 rounded-2xl bg-neon-purple/5 animate-pulse pointer-events-none" />
                )}
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="preview-area"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.3 }}
            >
              <div className="glass-card p-6">
                <div className="relative rounded-xl overflow-hidden mb-6">
                  <img
                    src={preview}
                    alt="Preview"
                    className="w-full h-64 object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                  
                  {!isLoading && (
                    <button
                      onClick={handleReset}
                      className="absolute top-4 right-4 p-2 rounded-full bg-black/50 backdrop-blur-sm text-white hover:bg-black/70 transition-colors"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                </div>

                {isLoading && (
                  <div className="flex flex-col items-center justify-center py-8">
                    <div className="w-16 h-16 border-4 border-neon-purple/30 border-t-neon-purple rounded-full animate-spin mb-4" />
                    <p className="text-gray-300">Analyzing satellite image...</p>
                    <p className="text-sm text-gray-500 mt-2">This may take a few seconds</p>
                  </div>
                )}

                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-4 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm"
                  >
                    {error}
                  </motion.div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </section>
  );
};

export default ImageUpload;
