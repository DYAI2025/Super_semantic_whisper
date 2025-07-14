import React, { useState } from 'react';
import { Marker } from './MarkerLibrary';
import { Timeline } from './Timeline';

interface AnalysisChunk {
  text: string;
  markers: Marker[];
  summary: string;
}

interface TextAnalyzerProps {
  onAnalyze: (text: string) => Promise<AnalysisChunk[]>;
}

export const TextAnalyzer: React.FC<TextAnalyzerProps> = ({ onAnalyze }) => {
  const [text, setText] = useState('');
  const [chunks, setChunks] = useState<AnalysisChunk[]>([]);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    setLoading(true);
    const result = await onAnalyze(text);
    setChunks(result);
    setLoading(false);
  };

  return (
    <div className="p-2 space-y-2">
      <textarea className="w-full h-40 border p-2" value={text} onChange={e => setText(e.target.value)} placeholder="Text hier eingeben..." />
      <button className="px-2 py-1 bg-purple-600 text-white rounded" onClick={handleAnalyze}>Analysieren</button>
      {loading && <div>Analysiere...</div>}
      <div className="space-y-4">
        {chunks.map((c, i) => (
          <div key={i} className="border p-2 rounded">
            <div>{c.text}</div>
            <div className="text-sm text-gray-700">{c.summary}</div>
          </div>
        ))}
      </div>
      {chunks.length > 0 && <Timeline chunks={chunks} />}
    </div>
  );
};
