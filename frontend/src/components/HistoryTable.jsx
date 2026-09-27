import { useCallback, useEffect, useState } from "react";
import { clearDetections, fetchDetections } from "../services/api";

export default function HistoryTable({ refreshSignal }) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchDetections(150);
      setRows(data);
      setErrorMsg(null);
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 4000);
    return () => clearInterval(interval);
  }, [load, refreshSignal]);

  const handleClear = async () => {
    await clearDetections();
    load();
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-sm font-semibold text-ink">Detection history</h2>
        <div className="flex items-center gap-2">
          <span className="font-mono text-[11px] text-muted">{rows.length} events</span>
          <button
            onClick={load}
            className="rounded border border-hairline px-2 py-1 font-mono text-[11px] text-muted hover:border-signal hover:text-signal"
          >
            refresh
          </button>
          <button
            onClick={handleClear}
            className="rounded border border-hairline px-2 py-1 font-mono text-[11px] text-muted hover:border-alert hover:text-alert"
          >
            clear
          </button>
        </div>
      </div>

      <div className="mt-2 flex-1 overflow-auto rounded border border-hairline">
        <table className="w-full border-collapse text-left text-xs">
          <thead className="sticky top-0 bg-panel">
            <tr className="font-mono text-[11px] uppercase tracking-wide text-muted">
              <th className="border-b border-hairline px-2 py-1.5">ID</th>
              <th className="border-b border-hairline px-2 py-1.5">Class</th>
              <th className="border-b border-hairline px-2 py-1.5">Confidence</th>
              <th className="border-b border-hairline px-2 py-1.5">In ROI</th>
              <th className="border-b border-hairline px-2 py-1.5">Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-b border-hairline/60 hover:bg-raised">
                <td className="px-2 py-1 font-mono text-muted">{r.id}</td>
                <td className="px-2 py-1 text-ink">{r.object_class}</td>
                <td className="px-2 py-1 font-mono text-ink">{Math.round(r.confidence * 100)}%</td>
                <td className="px-2 py-1">
                  {r.inside_roi ? (
                    <span className="rounded-sm bg-roi/15 px-1.5 py-0.5 font-mono text-[11px] text-roi">yes</span>
                  ) : (
                    <span className="font-mono text-[11px] text-muted">no</span>
                  )}
                </td>
                <td className="px-2 py-1 font-mono text-muted">{r.timestamp.replace("T", " ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!loading && rows.length === 0 && !errorMsg && (
          <p className="p-4 font-mono text-xs text-muted">No detections recorded yet.</p>
        )}
        {errorMsg && <p className="p-4 font-mono text-xs text-alert">{errorMsg}</p>}
      </div>
    </div>
  );
}
