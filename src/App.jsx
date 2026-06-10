import React from 'react';
import { DSSProvider } from './context/DSSContext';
import ControlPanel from './components/ControlPanel';
import MapCanvas from './components/MapCanvas';
export default function App() {
  return (
    <DSSProvider>
      <div className="w-screen h-screen flex m-0 p-0 overflow-hidden bg-paper">
        <ControlPanel />
        <MapCanvas />
      </div>
    </DSSProvider>
  );
}
