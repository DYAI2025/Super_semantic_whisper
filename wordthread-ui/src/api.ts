export interface TranscriptionResult {
  text: string;
}

export async function transcribeAudio(files: { path: string }[], mode: 'plain' | 'semantic'): Promise<TranscriptionResult[]> {
  // TODO: connect to backend
  console.log('Transcribing', files, mode);
  return files.map(f => ({ text: `Transcription of ${f.path}` }));
}

export async function analyzeText(text: string) {
  // TODO: connect to backend
  console.log('Analyzing text', text);
  return [
    { text, markers: [], summary: 'Beispielzusammenfassung' }
  ];
}
