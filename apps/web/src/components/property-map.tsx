'use client';

import * as React from 'react';

declare const L: any;

export function PropertyMap({ lat, lon, address, className }: {
  lat: number | null | undefined;
  lon: number | null | undefined;
  address?: string;
  className?: string;
}) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const mapRef = React.useRef<any>(null);
  const [leafletLoaded, setLeafletLoaded] = React.useState(false);

  // Load Leaflet CSS and JS from CDN
  React.useEffect(() => {
    if (typeof window === 'undefined') return;

    // Check if already loaded
    if ((window as any).__leafletLoaded) {
      setLeafletLoaded(true);
      return;
    }

    // Insert CSS
    if (!document.querySelector('link[href*="leaflet@1.9.4"]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
      document.head.appendChild(link);
    }

    // Insert JS
    if (!document.querySelector('script[src*="leaflet@1.9.4"]')) {
      const script = document.createElement('script');
      script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
      script.onload = () => {
        (window as any).__leafletLoaded = true;
        setLeafletLoaded(true);
      };
      document.head.appendChild(script);
    } else {
      // Script tag exists but may not have fired onload yet; poll briefly
      const interval = setInterval(() => {
        if ((window as any).__leafletLoaded) {
          clearInterval(interval);
          setLeafletLoaded(true);
        }
      }, 100);
      return () => clearInterval(interval);
    }
  }, []);

  // Init map after Leaflet is loaded
  React.useEffect(() => {
    if (!leafletLoaded) return;
    if (!containerRef.current) return;
    if (lat == null || lon == null) return;
    if (mapRef.current) return; // prevent double-init

    // Fix default icon path issue
    L.Icon.Default.prototype.options.iconUrl =
      'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png';
    L.Icon.Default.prototype.options.iconRetinaUrl =
      'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png';
    L.Icon.Default.prototype.options.shadowUrl =
      'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png';

    const map = L.map(containerRef.current).setView([lat, lon], 15);

    L.tileLayer(
      'https://cache.kartverket.no/v1/wmts/1.0.0/topo/default/webmercator/{z}/{y}/{x}.png',
      {
        attribution: '© <a href="https://kartverket.no">Kartverket</a>',
        maxZoom: 18,
      }
    ).addTo(map);

    const circle = L.circleMarker([lat, lon], {
      radius: 10,
      color: '#2563eb',
      fillColor: '#3b82f6',
      fillOpacity: 0.8,
      weight: 2,
    }).addTo(map);

    if (address) {
      circle.bindTooltip(address, { permanent: false, direction: 'top' });
    }

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [leafletLoaded, lat, lon, address]);

  if (lat == null || lon == null) return null;

  return (
    <div className={className}>
      {!leafletLoaded && (
        <div
          className="flex items-center justify-center rounded-xl border border-slate-200 bg-slate-100 text-sm text-slate-500"
          style={{ height: 300 }}
        >
          Laster kart...
        </div>
      )}
      <div
        ref={containerRef}
        style={{ height: 300, display: leafletLoaded ? 'block' : 'none' }}
        className="rounded-xl border border-slate-200"
      />
    </div>
  );
}
