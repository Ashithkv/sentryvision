import { useMemo, useState } from "react";

const COMMON_CLASSES = ["person", "car", "truck", "bus", "motorcycle", "bicycle", "dog", "cat"];

export default function ObjectSelector({ availableClasses, watchedClasses, onChange }) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const pool = availableClasses.length ? availableClasses : COMMON_CLASSES;
    if (!query.trim()) return pool;
    return pool.filter((c) => c.toLowerCase().includes(query.toLowerCase()));
  }, [availableClasses, query]);

  const toggle = (cls) => {
    const next = watchedClasses.includes(cls)
      ? watchedClasses.filter((c) => c !== cls)
      : [...watchedClasses, cls];
    onChange(next);
  };

  return (
    <div>
      <label className="font-display text-sm font-semibold text-ink">Watched objects</label>
      <p className="mt-1 font-mono text-[11px] text-muted">
        An alert fires when one of these enters the ROI.
      </p>
      <input
        type="text"
        placeholder="filter classes…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="mt-2 w-full rounded border border-hairline bg-panel px-2 py-1 font-mono text-xs text-ink placeholder:text-muted focus:border-signal focus:outline-none"
      />
      <div className="mt-2 max-h-40 overflow-y-auto rounded border border-hairline bg-panel p-1.5">
        {filtered.length === 0 && (
          <p className="p-2 font-mono text-xs text-muted">no classes match "{query}"</p>
        )}
        <div className="grid grid-cols-2 gap-1">
          {filtered.map((cls) => (
            <label
              key={cls}
              className="flex cursor-pointer items-center gap-1.5 rounded px-1.5 py-1 text-xs hover:bg-raised"
            >
              <input
                type="checkbox"
                checked={watchedClasses.includes(cls)}
                onChange={() => toggle(cls)}
                className="accent-signal"
              />
              <span className="truncate text-ink">{cls}</span>
            </label>
          ))}
        </div>
      </div>
      {watchedClasses.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {watchedClasses.map((cls) => (
            <span
              key={cls}
              className="rounded-sm border border-signal/40 bg-signal/10 px-1.5 py-0.5 font-mono text-[11px] text-signal"
            >
              {cls}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
