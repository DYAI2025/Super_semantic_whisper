import React from 'react';
import { Marker } from './MarkerLibrary';

interface AnalysisChunk {
  markers: Marker[];
}

interface TimelineProps {
  chunks: AnalysisChunk[];
}

const COLORS: Record<string, string> = {
  MM_DISTANZIERUNG: 'bg-blue-400',
  MM_MANIPULATION: 'bg-violet-500',
};

export const Timeline: React.FC<TimelineProps> = ({ chunks }) => {
  return (
    <div className="flex space-x-1 w-full h-4">
      {chunks.map((chunk, i) => {
        const meta = chunk.markers[0]?.id || 'default';
        const color = COLORS[meta] || 'bg-gray-300';
        return <div key={i} className={`${color} flex-1 cursor-pointer`} title={meta}></div>;
      })}
    </div>
  );
};
