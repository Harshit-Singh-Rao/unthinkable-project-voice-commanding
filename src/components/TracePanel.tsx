'use client';

interface TraceItem {
  clause: string;
  intent: string;
  confidence: number;
  source: string;
  low_confidence: boolean;
  item?: string;
  quantity?: number;
  unit?: string;
  brand?: string;
  price?: any;
  hindi: boolean;
  normalized?: string;
}

interface TracePanelProps {
  traces: TraceItem[];
}

export function TracePanel({ traces }: TracePanelProps) {
  if (!traces || traces.length === 0) return null;

  return (
    <div className="w-full max-w-md mx-auto mt-8 bg-gray-950 rounded-lg p-4 border border-gray-800 text-xs font-mono text-gray-400">
      <h4 className="text-gray-500 mb-2 uppercase tracking-widest border-b border-gray-800 pb-2">Parse Trace</h4>
      <div className="space-y-4">
        {traces.map((trace, idx) => (
          <div key={idx} className="space-y-1">
            <div className="text-gray-300">"{trace.clause}"</div>
            <div className="grid grid-cols-2 gap-2 text-gray-500">
              <div>Intent: <span className="text-amber-500">{trace.intent}</span></div>
              <div>Conf: {(trace.confidence * 100).toFixed(1)}%</div>
              {trace.item && <div>Item: {trace.item}</div>}
              {trace.quantity && <div>Qty: {trace.quantity} {trace.unit || ''}</div>}
              {trace.brand && <div>Brand: {trace.brand}</div>}
            </div>
            {trace.hindi && <div className="text-blue-400 mt-1">Hindi normalized: {trace.normalized}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}
