import React, { createContext, useReducer, useEffect } from 'react';
const initialState = {
  cropId: 'CRP-01',
  weights: { ph: 0.40, slope: 0.35, water: 0.25 },
  geoData: null,
  telemetry: { mean: 0, max: 0, primeCells: 0, totalCells: 0, primePercentage: '0.0' },
  loading: false,
  error: null
};
function dssReducer(state, action) {
  switch (action.type) {
    case 'SET_CROP':
      return { ...state, cropId: action.payload };
    case 'UPDATE_WEIGHTS':
      return { ...state, weights: { ...state.weights, ...action.payload } };
    case 'FETCH_START':
      return { ...state, loading: true, error: null };
    case 'FETCH_SUCCESS':
      return {
        ...state,
        loading: false,
        geoData: action.payload.geoData,
        telemetry: action.payload.telemetry
      };
    case 'FETCH_FAILURE':
      return { ...state, loading: false, error: action.payload };
    default:
      return state;
  }
}
export const DSSContext = createContext();
export const DSSProvider = ({ children }) => {
  const [state, dispatch] = useReducer(dssReducer, initialState);
  const triggerOptimization = async () => {
    dispatch({ type: 'FETCH_START' });
    try {
      const response = await fetch('http://localhost:8000/api/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          crop_id: state.cropId,
          weights: {
            ph: parseFloat(state.weights.ph),
            slope: parseFloat(state.weights.slope),
            water: parseFloat(state.weights.water)
          }
        })
      });

      if (!response.ok) {
        const errDetail = await response.json();
        throw new Error(errDetail.detail || 'Analytical calculation rejected by engine.');
      }

      const geoData = await response.json();

      // Compute telemetry stats directly from GeoJSON feature records
      const scores = geoData.features.map(f => f.properties.score || 0);
      const totalCells = scores.length;
      const mean = scores.reduce((a, b) => a + b, 0) / (totalCells || 1);
      const max = Math.max(...scores, 0);
      const primeCells = scores.filter(s => s >= 0.75).length;
      const primePercentage = ((primeCells / (totalCells || 1)) * 100).toFixed(1);
      dispatch({
        type: 'FETCH_SUCCESS',
        payload: {
          geoData,
          telemetry: { mean: mean.toFixed(4), max: max.toFixed(4), primeCells, totalCells, primePercentage }
        }
      });
    } catch (err) {
      dispatch({ type: 'FETCH_FAILURE', payload: err.message });
    }
  };
  useEffect(() => {
    triggerOptimization();
  }, [state.cropId]);
  return (
    <DSSContext.Provider value={{ state, dispatch, triggerOptimization }}>
      {children}
    </DSSContext.Provider>
  );
};
