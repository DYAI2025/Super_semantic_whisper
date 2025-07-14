import React, { useState } from 'react';

interface AudioFile {
  name: string;
  path: string;
}

interface AudioTranscriberProps {
  onTranscribe: (files: AudioFile[], mode: 'plain' | 'semantic') => void;
}

export const AudioTranscriber: React.FC<AudioTranscriberProps> = ({ onTranscribe }) => {
  const [directory, setDirectory] = useState('');
  const [files, setFiles] = useState<AudioFile[]>([]);
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [mode, setMode] = useState<'plain' | 'semantic'>('plain');
  const [progress, setProgress] = useState(0);

  const handleSelectDir = async () => {
    // Placeholder for electron dialog
    const dir = prompt('Ordnerpfad eingeben');
    if (dir) {
      setDirectory(dir);
      // TODO: Replace with backend call
      setFiles([{ name: 'example.mp3', path: dir + '/example.mp3' }]);
    }
  };

  const startTranscription = () => {
    const selectedFiles = files.filter(f => selected[f.path]);
    onTranscribe(selectedFiles, mode);
    setProgress(100); // placeholder
  };

  return (
    <div className="p-2 space-y-2">
      <button className="px-2 py-1 bg-blue-600 text-white rounded" onClick={handleSelectDir}>Ordner wählen</button>
      {directory && <div className="text-sm text-gray-600">{directory}</div>}
      <div className="max-h-40 overflow-auto border p-2">
        {files.map(f => (
          <div key={f.path} className="flex items-center space-x-2">
            <input type="checkbox" onChange={e => setSelected(s => ({ ...s, [f.path]: e.target.checked }))} />
            <span>{f.name}</span>
          </div>
        ))}
      </div>
      <div className="flex items-center space-x-4">
        <label>
          <input type="radio" checked={mode === 'plain'} onChange={() => setMode('plain')} /> Reine Transkription
        </label>
        <label>
          <input type="radio" checked={mode === 'semantic'} onChange={() => setMode('semantic')} /> Semantische Transkription
        </label>
      </div>
      <button className="px-2 py-1 bg-green-600 text-white rounded" onClick={startTranscription}>Transkribieren</button>
      {progress > 0 && <div className="w-full bg-gray-200 h-2"><div className="bg-blue-500 h-2" style={{ width: `${progress}%` }}></div></div>}
    </div>
  );
};
