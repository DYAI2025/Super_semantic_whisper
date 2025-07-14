import React, { useState } from 'react';
import { MarkerLibrary, Marker } from './components/MarkerLibrary';
import { AudioTranscriber } from './components/AudioTranscriber';
import { TextAnalyzer } from './components/TextAnalyzer';
import { analyzeText, transcribeAudio } from './api';

const sampleMarkers: Marker[] = [
  {
    id: 'MM_DISTANZIERUNG',
    name: 'Distanzierung',
    description: 'Zeigt Distanzierungsverhalten an',
    children: [
      { id: 'CL_CONFLICT', name: 'Konfliktvermeidung', description: 'Konflikte werden vermieden' },
    ],
  },
  {
    id: 'MM_MANIPULATION',
    name: 'Manipulation',
    description: 'Zeigt manipulatives Verhalten an',
    children: [
      { id: 'CL_GUILT', name: 'Schuldzuweisung', description: 'Schuld wird verteilt' },
    ],
  },
];

export const App: React.FC = () => {
  const [activeMarkers, setActiveMarkers] = useState<Record<string, boolean>>({});
  const [transcripts, setTranscripts] = useState<string[]>([]);

  const handleToggleMarker = (id: string, active: boolean) => {
    setActiveMarkers(m => ({ ...m, [id]: active }));
  };

  const handleTranscribe = async (files: { path: string }[], mode: 'plain' | 'semantic') => {
    const result = await transcribeAudio(files, mode);
    setTranscripts(result.map(r => r.text));
  };

  const handleAnalyze = async (text: string) => {
    return analyzeText(text);
  };

  return (
    <div className="flex h-screen">
      <div className="w-1/3 border-r overflow-auto">
        <h2 className="text-lg font-bold p-2">Marker Control Center</h2>
        <MarkerLibrary markers={sampleMarkers} onToggle={handleToggleMarker} />
      </div>
      <div className="w-1/3 border-r overflow-auto">
        <h2 className="text-lg font-bold p-2">Audio Transcription Engine</h2>
        <AudioTranscriber onTranscribe={handleTranscribe} />
        {transcripts.map((t, i) => (
          <div key={i} className="p-2 text-sm border-t">{t}</div>
        ))}
      </div>
      <div className="flex-1 overflow-auto">
        <h2 className="text-lg font-bold p-2">Text & Chat Analysis Hub</h2>
        <TextAnalyzer onAnalyze={handleAnalyze} />
      </div>
    </div>
  );
};
