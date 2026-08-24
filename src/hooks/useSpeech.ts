'use client';
import { useState, useEffect, useRef, useCallback } from 'react';

interface SpeechOptions {
  onResult: (text: string) => void;
  lang?: string;
}

export function useSpeech({ onResult, lang = 'en-US' }: SpeechOptions) {
  const [isListening, setIsListening] = useState(false);
  const [supported, setSupported] = useState(true);
  const recognitionRef = useRef<any>(null);
  // Store the callback in a ref so the useEffect never needs to re-run when
  // handleCommand re-creates (it closes over items/history state). Without
  // this, every render aborts and recreates the SpeechRecognition object,
  // which kills any in-progress session.
  const onResultRef = useRef(onResult);
  useEffect(() => {
    onResultRef.current = onResult;
  }, [onResult]);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    // @ts-ignore
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = lang === 'hi' ? 'hi-IN' : 'en-US';

    recognition.onresult = (event: any) => {
      const text = event.results[0][0].transcript;
      // Always call the latest callback without needing it as a dep
      onResultRef.current(text);
      setIsListening(false);
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
        recognitionRef.current = null;
      }
    };
  // Only re-run if the language changes — NOT when onResult changes
  }, [lang]);

  const startListening = useCallback(() => {
    if (!recognitionRef.current) return;
    try {
      recognitionRef.current.start();
      setIsListening(true);
    } catch (e) {
      console.error('Failed to start recognition:', e);
      setIsListening(false);
    }
  }, []);

  const stopListening = useCallback(() => {
    if (!recognitionRef.current) return;
    recognitionRef.current.stop();
    setIsListening(false);
  }, []);

  return { isListening, supported, startListening, stopListening };
}
