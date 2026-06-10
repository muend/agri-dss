import React, { useContext, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, GeoJSON, useMap } from 'react-leaflet';
import L from 'leaflet';
import { DSSContext } from '../context/DSSContext';
import 'leaflet/dist/leaflet.css';
// Spatial adjustment child sub-component to bind boundaries programmatically
function BoundsController({ data }) {
  const map = useMap();
  useEffect(() => {
    if (data && data.features && data.features.length > 0) {
      const layer = L.geoJSON(data);
      map.fitBounds(layer.getBounds(), { padding: [30, 30] });
    }
  }, [data, map]);
  return null;
}
export default function MapCanvas() {
  const { state } = useContext(DSSContext);
  const { geoData } = state;
  const geojsonRef = useRef(null);
  useEffect(() => {
    if (geojsonRef.current) {
      geojsonRef.current.clearLayers();
      if (geoData) {
        geojsonRef.current.addData(geoData);
      }
    }
  }, [geoData]);
  // Swiss style high-contrast color ramp orchestration
  const getStyle = (feature) => {
    const score = feature.properties.score || 0;
    if (score >= 0.75) {
      return {
        fillColor: '#00E676',
        fillOpacity: 0.65,
        weight: 1.5,
        color: '#00E676',
        dashArray: ''
      };
    }
    // Grayscale spectrum layout for below absolute threshold bounds
    const alpha = Math.max(0.1, score);
    return {
      fillColor: '#262626',
      fillOpacity: alpha * 0.4,
      weight: 0.5,
      color: '#404040',
      dashArray: '2, 4'
    };
  };
  return (
    <div className="w-[70%] h-screen relative bg-ink">
      {/* 4-Corner Monospaced HUD Elements */}
      <div className="absolute top-4 left-4 z-[1000] font-mono text-[10px] text-paper bg-ink/80 px-2 py-1 select-none pointer-events-none uppercase tracking-wider border border-muted/20">
        SYS.LOC // 36.18N - 37.12N : 29.30E - 30.85E
      </div>
      <div className="absolute top-4 right-4 z-[1000] font-mono text-[10px] text-paper bg-ink/80 px-2 py-1 select-none pointer-events-none uppercase tracking-wider border border-muted/20">
        EPSG:4326 WGS84
      </div>
      <div className="absolute bottom-4 left-4 z-[1000] font-mono text-[10px] text-paper bg-ink/80 px-2 py-1 select-none pointer-events-none uppercase tracking-wider border border-muted/20">
        Basemap: CartoDB Dark Matter
      </div>
      <div className="absolute bottom-4 right-4 z-[1000] font-mono text-[10px] text-emeraldIgnition bg-ink px-2 py-1 select-none pointer-events-none uppercase font-bold tracking-wider border border-emeraldIgnition animate-pulse">
        ● ENGINE ONLINE
      </div>
      <MapContainer
        center={[36.65, 30.07]}
        zoom={9}
        className="w-full h-full"
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.carto.com/">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        {geoData && (
          <>
            <GeoJSON
              ref={geojsonRef}
              data={geoData}
              style={getStyle}
            />
            <BoundsController data={geoData} />
          </>
        )}
      </MapContainer>
    </div>
  );
}
