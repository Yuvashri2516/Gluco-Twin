import React from 'react';
import { ShieldAlert, Info } from 'lucide-react';

/**
 * Mandatory Persistent Safety Banner
 * Displays exact required notice across all views.
 */
export default function SyntheticNotice() {
  return (
    <aside className="safety-banner" aria-label="Clinical Demonstration Disclaimer">
      <div className="safety-banner-left">
        <span className="safety-tag">
          <ShieldAlert size={12} style={{ display: 'inline', marginRight: 4, verticalAlign: 'text-top' }} />
          DEMO
        </span>
        <span style={{ fontWeight: 600 }}>
          Synthetic Demonstration Environment — Not for Diagnostic Use
        </span>
      </div>
      <div className="safety-banner-right">
        <span>
          <Info size={12} style={{ display: 'inline', marginRight: 4, verticalAlign: 'text-top' }} />
          Simulated IoT Streams & Synthea Records Only
        </span>
        <span style={{ opacity: 0.6 }}>•</span>
        <span>Version 0.1.0-alpha</span>
      </div>
    </aside>
  );
}
