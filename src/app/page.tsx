'use client';

import { useState, useEffect } from 'react';
import { VoiceOrb } from '@/components/VoiceOrb';
import { ShoppingList, ShoppingItem } from '@/components/ShoppingList';
import { TracePanel } from '@/components/TracePanel';
import { useSpeech } from '@/hooks/useSpeech';

export default function Home() {
  const [items, setItems] = useState<ShoppingItem[]>([]);
  const [history, setHistory] = useState<Record<string, unknown>[]>([]);
  const [messages, setMessages] = useState<{type: string, text: string}[]>([]);
  const [trace, setTrace] = useState<Record<string, unknown>[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // Load state from local storage on mount
  useEffect(() => {
    const savedItems = localStorage.getItem('shopping_items');
    const savedHistory = localStorage.getItem('shopping_history');
    if (savedItems) setItems(JSON.parse(savedItems));
    if (savedHistory) setHistory(JSON.parse(savedHistory));
  }, []);

  // Save state to local storage when it changes
  useEffect(() => {
    localStorage.setItem('shopping_items', JSON.stringify(items));
    localStorage.setItem('shopping_history', JSON.stringify(history));
  }, [items, history]);

  // Auto-clear messages after 4 seconds
  useEffect(() => {
    if (messages.length > 0) {
      const timer = setTimeout(() => setMessages([]), 4000);
      return () => clearTimeout(timer);
    }
  }, [messages]);

  const handleCommand = async (text: string) => {
    setIsProcessing(true);
    try {
      const res = await fetch('/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, lang: 'en', items, history }),
      });

      if (!res.ok) throw new Error(`API Error ${res.status}`);

      const data = await res.json();

      if (data.items !== undefined) setItems(data.items);
      if (data.history !== undefined) setHistory(data.history);
      if (data.messages) setMessages(data.messages);
      if (data.trace) setTrace(data.trace);

    } catch (err) {
      console.error(err);
      setMessages([{ type: 'error', text: 'Could not reach the backend. Please try again.' }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const { isListening, supported, startListening, stopListening } = useSpeech({
    onResult: handleCommand
  });

  const toggleListening = () => {
    if (isProcessing) return;
    if (isListening) stopListening();
    else startListening();
  };

  return (
    <main className="min-h-screen bg-black text-gray-100 flex flex-col items-center py-10 px-4">
      <div className="text-center mb-10">
        <h1 className="text-5xl font-bold text-amber-500 tracking-tight">EchoList</h1>
        <p className="text-gray-500 mt-2 text-sm">Voice-Activated Shopping Assistant</p>
      </div>

      <div className="mb-10">
        <VoiceOrb
          isListening={isListening}
          isProcessing={isProcessing}
          onClick={toggleListening}
          supported={supported}
        />
      </div>

      <div className="w-full max-w-md mb-6 min-h-[40px]">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`p-3 rounded-lg mb-2 text-sm text-center border ${
              m.type === 'error'
                ? 'bg-red-950 text-red-400 border-red-900'
                : 'bg-green-950 text-green-400 border-green-900'
            }`}
          >
            {m.text}
          </div>
        ))}
      </div>

      <ShoppingList items={items} />

      {trace.length > 0 && <TracePanel traces={trace} />}
    </main>
  );
}
