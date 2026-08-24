'use client';
import { motion } from 'framer-motion';
import { Mic, MicOff } from 'lucide-react';

interface VoiceOrbProps {
  isListening: boolean;
  onClick: () => void;
  supported: boolean;
}

export function VoiceOrb({ isListening, onClick, supported }: VoiceOrbProps) {
  if (!supported) {
    return (
      <div className="w-16 h-16 rounded-full bg-red-900 flex items-center justify-center text-white" title="Speech recognition not supported in this browser">
        <MicOff size={24} />
      </div>
    );
  }

  return (
    <div className="relative flex items-center justify-center w-24 h-24">
      {isListening && (
        <motion.div
          className="absolute inset-0 rounded-full bg-amber-500 opacity-20"
          animate={{ scale: [1, 1.5, 1] }}
          transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
        />
      )}
      <motion.button
        onClick={onClick}
        className={`relative z-10 w-16 h-16 rounded-full flex items-center justify-center shadow-lg transition-colors duration-300 ${isListening ? 'bg-amber-500 text-white shadow-amber-500/50' : 'bg-gray-800 text-amber-500 hover:bg-gray-700'}`}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <Mic size={24} />
      </motion.button>
    </div>
  );
}
