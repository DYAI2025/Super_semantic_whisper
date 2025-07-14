import React, { useState } from 'react';

export interface Marker {
  id: string;
  name: string;
  description: string;
  children?: Marker[];
}

interface MarkerLibraryProps {
  markers: Marker[];
  onToggle: (id: string, active: boolean) => void;
}

const MarkerItem: React.FC<{ marker: Marker; onToggle: (id: string, active: boolean) => void }> = ({ marker, onToggle }) => {
  const [expanded, setExpanded] = useState(false);
  const [active, setActive] = useState(false);

  const toggle = () => {
    const newActive = !active;
    setActive(newActive);
    onToggle(marker.id, newActive);
  };

  return (
    <div className="ml-4">
      <div className="flex items-center space-x-2">
        {marker.children && (
          <button onClick={() => setExpanded(!expanded)} className="text-xs">
            {expanded ? '-' : '+'}
          </button>
        )}
        <input type="checkbox" checked={active} onChange={toggle} />
        <span className="font-medium" title={marker.description}>{marker.name}</span>
      </div>
      {expanded && marker.children && (
        <div className="ml-4 border-l border-gray-300 pl-2">
          {marker.children.map(child => (
            <MarkerItem key={child.id} marker={child} onToggle={onToggle} />
          ))}
        </div>
      )}
    </div>
  );
};

export const MarkerLibrary: React.FC<MarkerLibraryProps> = ({ markers, onToggle }) => {
  const [filter, setFilter] = useState('');
  const filtered = markers.filter(m => m.name.toLowerCase().includes(filter.toLowerCase()));

  return (
    <div className="p-2 space-y-2">
      <input
        className="w-full p-1 border rounded"
        placeholder="Marker suchen..."
        value={filter}
        onChange={e => setFilter(e.target.value)}
      />
      <div className="max-h-80 overflow-auto">
        {filtered.map(marker => (
          <MarkerItem key={marker.id} marker={marker} onToggle={onToggle} />
        ))}
      </div>
    </div>
  );
};
