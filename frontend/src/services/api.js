const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export async function fetchDetections(limit = 100) {
  const res = await fetch(`${API_BASE}/detections?limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to fetch detections (${res.status})`);
  const data = await res.json();
  return data.detections;
}

export async function clearDetections() {
  const res = await fetch(`${API_BASE}/detections`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Failed to clear detections (${res.status})`);
  return res.json();
}

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.ok;
}
