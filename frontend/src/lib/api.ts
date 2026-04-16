
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:7860";
export interface AnomalyRequest {
  equipment_id: string;
  [key: string]: number | string; 
}
export interface OutlierDetectionPayload {
  equipment_id: string;
  anomaly_score: number;
  is_anomaly: boolean;
  threshold: number;
  regen_divergence_score: number;
}
export interface RULRequest {
  equipment_id: string;
  window: number[][]; 
}
export interface RULResponse {
  equipment_id: string;
  forecasted_days_left: number;
  confidence_lower: number;
  confidence_upper: number;
  model_version: string;
}
export interface EquipmentStatus {
  equipment_id: string;
  forecasted_days_left: number;
}
export interface ScheduleRequest {
  equipment: EquipmentStatus[];
  max_days: number;
  max_techs_per_day: number;
}
export interface RepairTimetableRow {
  equipment_id: string;
  scheduled_day: number;
  estimated_cost: number;
}
export interface RepairTimetablePayload {
  status: string;
  aggregate_financial_impact: number;
  schedule: RepairTimetableRow[];
}
export interface SystemStatusPayload {
  status: string;
  version: string;
  models_loaded: boolean;
  uptime_seconds: number;
}
async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  const token = typeof window !== "undefined" ? localStorage.getItem("api_token") : null;
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(url, { ...options, headers });

  if (!res.ok) {
    const errBody = await res.text();
    throw new Error(`API Error ${res.status}: ${errBody}`);
  }
  return res.json();
}
export const api = {
  health: () => apiFetch<SystemStatusPayload>("/health"),
  evalSensorOutliers: (data: AnomalyRequest) =>
    apiFetch<OutlierDetectionPayload>("/predict/anomaly", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  estimateRemainingLife: (data: RULRequest) =>
    apiFetch<RULResponse>("/predict/rul", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  optimizeRepairCycles: (data: ScheduleRequest) =>
    apiFetch<RepairTimetablePayload>("/schedule/maintenance", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};
