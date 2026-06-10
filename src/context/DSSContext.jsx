import React, { createContext, useReducer, useEffect, useCallback, useRef } from 'react';

/* ════════════════════════════════════════════════════════════════
   DSS STATE CORE — constraint-enforced AHP weight management

   Invariant: w_ph + w_slope + w_water = 1.0 at every state tick.

   The reducer intercepts UPDATE_WEIGHTS and applies RELATIVE SCALING
   NORMALIZATION: when the user moves slider A to value vA, the two
   remaining weights are re-distributed over the residual mass
   (1 - vA) proportionally to their CURRENT ratio. The final member
   is computed as an exact residual, so the vector sum is exactly
   1.0 in IEEE-754 terms — the Pydantic boundary (Σwᵢ = 1.0,
   abs_tol 1e-5) can never be violated by slider motion.
   ════════════════════════════════════════════════════════════════ */

const WEIGHT_KEYS = ['ph', 'slope', 'water'];

/**
 * Relative scaling normalization.
 *
 * @param {{ph:number, slope:number, water:number}} weights  Current vector.
 * @param {'ph'|'slope'|'water'} changedKey                  Slider the user moved.
 * @param {number} rawValue                                  New raw slider value.
 * @returns {{ph:number, slope:number, water:number}}        Normalized vector, Σ = 1.0.
 */
export function normalizeWeights(weights, changedKey, rawValue) {
  // Clamp the driven slider into the valid domain.
  const vA = Math.min(1.0, Math.max(0.0, rawValue));
  const residual = 1.0 - vA;

  const [keyB, keyC] = WEIGHT_KEYS.filter((k) => k !== changedKey);
  const currentB = weights[keyB];
  const currentC = weights[keyC];
  const pairSum = currentB + currentC;

  let vB;
  if (pairSum <= 1e-12) {
    // Degenerate ratio (both companions at zero): split residual equally.
    vB = residual / 2.0;
  } else {
    // Proportional re-distribution preserving the B:C ratio.
    vB = residual * (currentB / pairSum);
  }

  // Exact residual assignment — guarantees the sum closes to 1.0
  // without accumulating floating-point drift across interactions.
  const vC = 1.0 - vA - vB;

  return {
    [changedKey]: vA,
    [keyB]: vB,
    [keyC]: Math.max(0.0, vC)
  };
}

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
    case 'UPDATE_WEIGHTS': {
      const { key, value } = action.payload;
      if (!WEIGHT_KEYS.includes(key)) {
        return state;
      }
      return {
        ...state,
        weights: normalizeWeights(state.weights, key, parseFloat(value))
      };
    }
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

  // Refs mirror the live vector so the fetch closure always reads the
  // freshest post-normalization state without re-binding callbacks.
  const weightsRef = useRef(state.weights);
  const cropRef = useRef(state.cropId);
  weightsRef.current = state.weights;
  cropRef.current = state.cropId;

  const triggerOptimization = useCallback(async () => {
    dispatch({ type: 'FETCH_START' });
    const weights = weightsRef.current;
    try {
      const response = await fetch('http://localhost:8000/api/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          crop_id: cropRef.current,
          weights: {
            ph: weights.ph,
            slope: weights.slope,
            water: weights.water
          }
        })
      });

      if (!response.ok) {
        const errDetail = await response.json();
        const message =
          typeof errDetail.detail === 'string'
            ? errDetail.detail
            : 'Analytical calculation rejected by engine.';
        throw new Error(message);
      }

      const geoData = await response.json();

      // Compute telemetry stats directly from GeoJSON feature records.
      const scores = geoData.features.map((f) => f.properties.score || 0);
      const totalCells = scores.length;
      const mean = scores.reduce((a, b) => a + b, 0) / (totalCells || 1);
      const max = Math.max(...scores, 0);
      const primeCells = scores.filter((s) => s >= 0.75).length;
      const primePercentage = ((primeCells / (totalCells || 1)) * 100).toFixed(1);

      dispatch({
        type: 'FETCH_SUCCESS',
        payload: {
          geoData,
          telemetry: {
            mean: mean.toFixed(4),
            max: max.toFixed(4),
            primeCells,
            totalCells,
            primePercentage
          }
        }
      });
    } catch (err) {
      dispatch({ type: 'FETCH_FAILURE', payload: err.message });
    }
  }, []);

  useEffect(() => {
    triggerOptimization();
  }, [state.cropId, triggerOptimization]);

  return (
    <DSSContext.Provider value={{ state, dispatch, triggerOptimization }}>
      {children}
    </DSSContext.Provider>
  );
};
