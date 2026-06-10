import React, { useContext } from 'react';
import { DSSContext } from '../context/DSSContext';
export default function ControlPanel() {
  const { state, dispatch, triggerOptimization } = useContext(DSSContext);
  const { weights, cropId, telemetry, loading, error } = state;
  const handleSliderChange = (field, value) => {
    const val = parseFloat(value);
    dispatch({ type: 'UPDATE_WEIGHTS', payload: { [field]: val } });
  };
  return (
    <div className="w-[30%] h-screen bg-paper border-r border-ink flex flex-col justify-between p-8 box-border select-none overflow-y-auto">
      <div className="flex flex-col gap-8">
        {/* Masthead */}
        <header className="flex flex-col gap-1">
          <h1 className="text-xl font-bold tracking-tight font-sans uppercase m-0">Agri-DSS</h1>
          <p className="text-xs font-mono text-muted uppercase tracking-wider m-0">Spatial Suitability Matrix Engine</p>
        </header>
        <hr className="border-0 border-b border-ink m-0" />
        {/* Crop Selection Grid */}
        <div className="flex flex-col gap-3">
          <label className="text-xs font-mono font-bold uppercase tracking-wider text-muted">Analysis Domain Model</label>
          <div className="flex flex-col gap-1">
            {[
              { id: 'CRP-01', name: 'Olea Europaea (Olive Matrix)' },
              { id: 'CRP-02', name: 'Citrus Sinensis (Orchard Grid)' },
              { id: 'CRP-03', name: 'Solanum Lycopersicum (Greenhouse)' }
            ].map((crop) => (
              <button
                key={crop.id}
                onClick={() => dispatch({ type: 'SET_CROP', payload: crop.id })}
                className={`w-full text-left font-mono text-xs p-3 rounded-none border transition-all duration-150 ${
                  cropId === crop.id
                    ? 'bg-ink text-paper border-ink font-bold'
                    : 'bg-transparent text-ink border-hairline hover:border-ink'
                }`}
              >
                [{crop.id}] {crop.name}
              </button>
            ))}
          </div>
        </div>
        {/* Dynamic AHP Matrix Controls */}
        <div className="flex flex-col gap-5">
          <label className="text-xs font-mono font-bold uppercase tracking-wider text-muted">Analytical Hierarchy Inputs (Σ=1.0)</label>

          {[
            { key: 'ph', label: 'w1 · Soil pH Layer' },
            { key: 'slope', label: 'w2 · Topographic Slope' },
            { key: 'water', label: 'w3 · Hydrographic Proximity' }
          ].map((slider) => (
            <div key={slider.key} className="flex flex-col gap-2">
              <div className="flex justify-between font-mono text-xs">
                <span>{slider.label}</span>
                <span className="font-bold">{(weights[slider.key]).toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={weights[slider.key]}
                onChange={(e) => handleSliderChange(slider.key, e.target.value)}
                className="w-full"
              />
            </div>
          ))}
        </div>
        {/* Error Telemetry Frame */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-500 text-red-700 font-mono text-xs rounded-none">
            [CRITICAL_ERROR] {error}
          </div>
        )}
      </div>
      {/* Real-time Telemetry Dashboard Monitor */}
      <div className="flex flex-col gap-6">
        <div className="grid grid-cols-2 gap-4 border-t border-b border-hairline py-4 font-mono text-xs">
          <div>
            <span className="text-muted block uppercase text-[10px]">Matrix.Mean</span>
            <span className="font-bold text-base">{telemetry.mean}</span>
          </div>
          <div>
            <span className="text-muted block uppercase text-[10px]">Matrix.Max</span>
            <span className="font-bold text-base">{telemetry.max}</span>
          </div>
          <div>
            <span className="text-muted block uppercase text-[10px]">Cells.Cached</span>
            <span className="font-bold text-base">{telemetry.totalCells}</span>
          </div>
          <div>
            <span className="text-muted block uppercase text-[10px]">Prime.Zone</span>
            <span className={`font-bold text-base ${telemetry.primeCells > 0 ? 'text-emeraldIgnition bg-ink px-1' : ''}`}>
              {telemetry.primePercentage}%
            </span>
          </div>
        </div>
        <button
          onClick={triggerOptimization}
          disabled={loading}
          className={`w-full py-4 text-xs font-mono font-bold uppercase tracking-widest transition-all duration-150 border rounded-none ${
            loading
              ? 'bg-hairline text-muted border-hairline cursor-wait'
              : 'bg-emeraldIgnition text-ink border-emeraldIgnition hover:bg-ink hover:text-emeraldIgnition hover:border-ink shadow-none'
          }`}
        >
          {loading ? 'Crunching Spatial Vectors...' : 'Execute Regional Optimization'}
        </button>
      </div>
    </div>
  );
}
