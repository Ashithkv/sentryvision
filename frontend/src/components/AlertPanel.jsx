function timeAgo(isoString) {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(isoString).getTime()) / 1000));
  if (seconds < 5) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  return `${Math.floor(seconds / 60)}m ago`;
}

export default function AlertPanel({ alerts }) {
  return (
    <div>
      <div className="flex items-center justify-between">
        <h2 className="font-display text-sm font-semibold text-ink">Alerts</h2>
        {alerts.length > 0 && (
          <span className="rounded-sm bg-alert/15 px-1.5 py-0.5 font-mono text-[11px] text-alert">
            {alerts.length}
          </span>
        )}
      </div>
      <div className="mt-2 max-h-48 space-y-1.5 overflow-y-auto pr-1">
        {alerts.length === 0 ? (
          <p className="rounded border border-dashed border-hairline p-3 font-mono text-xs text-muted">
            No alerts yet. A watched object entering the ROI will show up here.
          </p>
        ) : (
          alerts.map((a, i) => (
            <div
              key={`${a.timestamp}-${i}`}
              className="flex items-start justify-between rounded border border-alert/30 bg-alert/10 px-2 py-1.5"
            >
              <div>
                <p className="text-xs font-medium text-ink">{a.message}</p>
                <p className="font-mono text-[11px] text-muted">{timeAgo(a.timestamp)}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
