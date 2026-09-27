export default function ConfidenceSlider({ value, onChange }) {
  return (
    <div>
      <div className="flex items-center justify-between">
        <label className="font-display text-sm font-semibold text-ink">Confidence threshold</label>
        <span className="font-mono text-xs text-signal">{Math.round(value * 100)}%</span>
      </div>
      <input
        type="range"
        min="0.05"
        max="0.95"
        step="0.05"
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="mt-2 w-full accent-signal"
      />
      <p className="mt-1 font-mono text-[11px] text-muted">
        Detections below this confidence are dropped before drawing.
      </p>
    </div>
  );
}
