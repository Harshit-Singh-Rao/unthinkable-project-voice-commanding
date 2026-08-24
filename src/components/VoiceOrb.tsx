'use client';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, Loader2 } from 'lucide-react';

interface VoiceOrbProps {
  isListening: boolean;
  isProcessing: boolean;
  onClick: () => void;
  supported: boolean;
}

export function VoiceOrb({ isListening, isProcessing, onClick, supported }: VoiceOrbProps) {
  if (!supported) {
    return (
      <div className="flex flex-col items-center gap-3">
        <div className="w-24 h-24 rounded-full bg-red-900/50 border border-red-700 flex items-center justify-center text-red-400">
          <MicOff size={32} />
        </div>
        <p className="text-red-400 text-xs">Speech not supported in this browser</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative flex items-center justify-center w-32 h-32">

        {/* Outermost slow pulse - only when listening */}
        <AnimatePresence>
          {isListening && (
            <motion.div
              key="pulse-outer"
              className="absolute inset-0 rounded-full bg-amber-500/10 border border-amber-500/20"
              initial={{ scale: 1, opacity: 0 }}
              animate={{ scale: [1, 1.7, 1], opacity: [0.6, 0, 0.6] }}
              transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
            />
          )}
        </AnimatePresence>

        {/* Middle pulse ring */}
        <AnimatePresence>
          {isListening && (
            <motion.div
              key="pulse-mid"
              className="absolute inset-2 rounded-full bg-amber-500/15 border border-amber-500/30"
              initial={{ scale: 1, opacity: 0 }}
              animate={{ scale: [1, 1.4, 1], opacity: [0.8, 0, 0.8] }}
              transition={{ repeat: Infinity, duration: 1.5, ease: 'easeInOut', delay: 0.3 }}
            />
          )}
        </AnimatePresence>

        {/* Core button */}
        <motion.button
          onClick={onClick}
          disabled={isProcessing}
          className={`relative z-10 w-20 h-20 rounded-full flex items-center justify-center shadow-2xl transition-all duration-300 cursor-pointer
            ${isListening
              ? 'bg-amber-500 text-black shadow-amber-500/50 shadow-lg'
              : isProcessing
                ? 'bg-gray-700 text-amber-400'
                : 'bg-gray-800 text-amber-500 hover:bg-gray-700 hover:shadow-amber-500/20 hover:shadow-lg'
            }`}
          whileHover={!isListening && !isProcessing ? { scale: 1.08 } : {}}
          whileTap={{ scale: 0.93 }}
          animate={isListening ? { boxShadow: ['0 0 0 0px rgba(245,158,11,0.4)', '0 0 0 12px rgba(245,158,11,0)', '0 0 0 0px rgba(245,158,11,0.4)'] } : {}}
          transition={isListening ? { repeat: Infinity, duration: 1.5 } : {}}
        >
          {isProcessing ? (
            <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}>
              <Loader2 size={28} />
            </motion.div>
          ) : (
            <Mic size={28} />
          )}
        </motion.button>
      </div>

      {/* Status text below orb */}
      <AnimatePresence mode="wait">
        {isListening && (
          <motion.p
            key="listening"
            className="text-amber-400 text-sm font-medium tracking-wide flex items-center gap-2"
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
          >
            <motion.span
              className="inline-block w-2 h-2 rounded-full bg-amber-400"
              animate={{ opacity: [1, 0, 1] }}
              transition={{ repeat: Infinity, duration: 0.8 }}
            />
            Listening…
          </motion.p>
        )}
        {isProcessing && (
          <motion.p
            key="processing"
            className="text-gray-400 text-sm tracking-wide"
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
          >
            Processing…
          </motion.p>
        )}
        {!isListening && !isProcessing && (
          <motion.p
            key="idle"
            className="text-gray-600 text-xs"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            Tap to speak
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  );
}
