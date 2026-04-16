"use client";
import { useState, useEffect, useCallback, useMemo } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, AreaChart, Area, Legend, ReferenceLine, Label,
} from "recharts";
import {
  Activity, AlertTriangle, Calendar, ChevronRight, Clock, Factory,
  Gauge, Heart, LayoutDashboard, Settings, Shield, TrendingDown, Wrench, Zap,
  FileText, Bell, Loader2, Plus, Download,
} from "lucide-react";
import {
  api,
  type SystemStatusPayload,
  type OutlierDetectionPayload,
  type RepairTimetablePayload,
  type RepairTimetableRow,
} from "@/lib/api";

const MACHINERY_UNITS: Record<string, { rul: number; status: string; anomaly: number; health: number }> = {
  Unit_1: { rul: 90, status: "Healthy", anomaly: 0.12, health: 94 },
  Unit_2: { rul: 15, status: "Warning", anomaly: 0.67, health: 58 },
  Unit_3: { rul: 2, status: "Critical", anomaly: 0.93, health: 12 },
  Unit_4: { rul: 120, status: "Healthy", anomaly: 0.08, health: 97 },
  Unit_5: { rul: 85, status: "Healthy", anomaly: 0.15, health: 91 },
  Unit_6: { rul: 42, status: "Healthy", anomaly: 0.31, health: 76 },
  Unit_7: { rul: 8, status: "Warning", anomaly: 0.78, health: 34 },
  Unit_8: { rul: 55, status: "Healthy", anomaly: 0.22, health: 82 },
};

const NAV_ITEMS = [
  { id: "overview", label: "Overview", emoji: "🏠" },
  { id: "equipment", label: "Equipment Detail", emoji: "🔍" },
  { id: "schedule", label: "Maintenance Schedule", emoji: "📋" },
  { id: "systemNotifications", label: "Alerts", emoji: "🔔" },
  { id: "reports", label: "Reports", emoji: "📊" },
];

const COLORS = { healthy: "#34d399", warning: "#fbbf24", critical: "#f87171" };
const TOOLTIP_STYLE = { background: "#1e1b4b", border: "1px solid rgba(99,102,241,0.3)", borderRadius: 10, color: "#e2e8f0" };

// Simulated next service day per unit
const NEXT_SERVICE: Record<string, number> = {
  Unit_1: 10, Unit_2: 4, Unit_3: 1, Unit_4: 15, Unit_5: 8, Unit_6: 6, Unit_7: 3, Unit_8: 12,
};

function badgeCls(status: string) {
  return `badge badge-${status.toLowerCase()}`;
}
function barColor(health: number) {
  return health > 70 ? COLORS.healthy : health > 30 ? COLORS.warning : COLORS.critical;
}
function statusColor(status: string) {
  return status === "Healthy" ? COLORS.healthy : status === "Warning" ? COLORS.warning : COLORS.critical;
}

/* Generate simulated sensor timeseries data for a unit & sensor */
function genSensorData(eqId: string, sensorIdx: number) {
  const eq = MACHINERY_UNITS[eqId];
  const base = 20 + (sensorIdx % 5) * 3;
  const noise = eq ? (100 - eq.health) * 0.05 : 1;
  return Array.from({ length: 50 }, (_, i) => ({
    t: i,
    value: +(base + Math.sin(i * 0.3) * 2 + (Math.random() - 0.5) * noise * 4 + (i > 38 ? (Math.random() * noise * 6) : 0)).toFixed(2),
  }));
}

/* Generate simulated RUL forecast line */
function genRulForecast(eqId: string) {
  const eq = MACHINERY_UNITS[eqId];
  const startRul = eq ? Math.min(eq.rul + 30, 120) : 100;
  return Array.from({ length: 30 }, (_, i) => ({
    day: i + 1,
    rul: Math.max(0, +(startRul - i * (startRul / 35) + (Math.random() - 0.5) * 4).toFixed(1)),
  }));
}

/* Generate simulated correlation matrix */
function genCorrelation() {
  const sensors = Array.from({ length: 7 }, (_, i) => `sensor_${i + 1}`);
  const rows: { row: string; col: string; val: number }[] = [];
  for (const r of sensors) {
    for (const c of sensors) {
      rows.push({ row: r, col: c, val: r === c ? 1 : +((Math.random() * 2 - 1)).toFixed(2) });
    }
  }
  return { sensors, data: rows };
}

function heatColor(v: number) {
  if (v >= 0.5) return `rgba(167, 139, 250, ${0.3 + v * 0.7})`;
  if (v >= 0) return `rgba(167, 139, 250, ${0.15 + v * 0.4})`;
  if (v >= -0.5) return `rgba(219, 171, 255, ${0.15 + Math.abs(v) * 0.3})`;
  return `rgba(248, 180, 255, ${0.2 + Math.abs(v) * 0.5})`;
}

/* Download a CSV string as a file */
function downloadCSV(filename: string, csvContent: string) {
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function ColdStartBanner({ loading }: { loading: boolean }) {
  if (!loading) return null;
  return (
    <div className="fixed top-0 inset-x-0 z-50 flex items-center justify-center gap-3 py-3 bg-indigo-900/90 backdrop-blur text-sm text-indigo-200 border-b border-indigo-700/40">
      <Loader2 className="w-4 h-4 animate-spin" />
      Connecting to PredictX API… The Hugging Face Space may take 30–60 seconds to wake up.
    </div>
  );
}

export default function Dashboard() {
  const [activeView, setActiveView] = useState("overview");
  const [apiHealthCheckStatus, setApiHealthCheckStatus] = useState<SystemStatusPayload | null>(null);
  const [isPlatformWaking, setIsPlatformWaking] = useState(true);
  const [maintenanceTimetable, setMaintenanceTimetable] = useState<RepairTimetablePayload | null>(null);
  const [irregularityOutput, setIrregularityOutput] = useState<OutlierDetectionPayload | null>(null);
  const [loadingSchedule, setLoadingSchedule] = useState(false);
  const [loadingAnomaly, setLoadingAnomaly] = useState(false);

  // Equipment Detail state
  const [selectedEquipment, setSelectedEquipment] = useState("Unit_1");
  const [selectedSensor, setSelectedSensor] = useState("sensor_1");

  // Alert Rule form state
  const [alertSensorTarget, setAlertSensorTarget] = useState("sensor_1");
  const [alertThreshold, setAlertThreshold] = useState("100.00");
  const [alertSeverity, setAlertSeverity] = useState("Info");
  const [alertNotifyVia, setAlertNotifyVia] = useState("Choose options");
  const [deployedRules, setDeployedRules] = useState<{ sensor: string; threshold: string; severity: string; notify: string; time: string }[]>([]);

  const deployAlertRule = useCallback(() => {
    if (alertNotifyVia === "Choose options") {
      alert("Please select a notification channel.");
      return;
    }
    setDeployedRules((prev) => [
      { sensor: alertSensorTarget, threshold: alertThreshold, severity: alertSeverity, notify: alertNotifyVia, time: new Date().toLocaleTimeString() },
      ...prev,
    ]);
    // Reset form
    setAlertSensorTarget("sensor_1");
    setAlertThreshold("100.00");
    setAlertSeverity("Info");
    setAlertNotifyVia("Choose options");
  }, [alertSensorTarget, alertThreshold, alertSeverity, alertNotifyVia]);

  // Sync time
  const [syncTime, setSyncTime] = useState("");

  useEffect(() => {
    let isMounted = true;
    const check = async () => {
      try {
        const h = await api.health();
        if (isMounted) {
          setApiHealthCheckStatus(h);
          setIsPlatformWaking(false);
          setSyncTime(new Date().toLocaleTimeString());
        }
      } catch {
        if (isMounted) setTimeout(check, 5000); // retry on cold start
      }
    };
    check();
    return () => { isMounted = false; };
  }, []);

  const fetchSchedule = useCallback(async () => {
    setLoadingSchedule(true);
    try {
      const res = await api.optimizeRepairCycles({
        equipment: Object.entries(MACHINERY_UNITS).map(([id, e]) => ({ equipment_id: id, forecasted_days_left: e.rul })),
        max_days: 30,
        max_techs_per_day: 2,
      });
      setMaintenanceTimetable(res);
    } catch (err) { console.error(err); }
    setLoadingSchedule(false);
  }, []);

  const testAnomaly = useCallback(async (eqId: string) => {
    setLoadingAnomaly(true);
    const sensors: Record<string, number | string> = { equipment_id: eqId };
    for (let i = 1; i <= 21; i++) sensors[`sensor_${i}`] = 25 + Math.random() * 30;
    try {
      const res = await api.evalSensorOutliers(sensors as any);
      setIrregularityOutput(res);
    } catch (err) { console.error(err); }
    setLoadingAnomaly(false);
  }, []);

  // Auto-run anomaly check when equipment changes
  useEffect(() => {
    testAnomaly(selectedEquipment);
  }, [selectedEquipment, testAnomaly]);

  // Auto-fetch schedule when navigating to schedule tab
  useEffect(() => {
    if (activeView === "schedule" && !maintenanceTimetable && !loadingSchedule) {
      fetchSchedule();
    }
  }, [activeView, maintenanceTimetable, loadingSchedule, fetchSchedule]);

  const functioningCount = Object.values(MACHINERY_UNITS).filter((e) => e.status === "Healthy").length;
  const degradedCount = Object.values(MACHINERY_UNITS).filter((e) => e.status === "Warning").length;
  const failingCount = Object.values(MACHINERY_UNITS).filter((e) => e.status === "Critical").length;
  const meanLifeExpectancy = Math.round(Object.values(MACHINERY_UNITS).reduce((s, e) => s + e.rul, 0) / Object.keys(MACHINERY_UNITS).length);

  const compositionChartVals = [
    { name: "Healthy", value: functioningCount, color: COLORS.healthy },
    { name: "Warning", value: degradedCount, color: COLORS.warning },
    { name: "Critical", value: failingCount, color: COLORS.critical },
  ];

  const lifeDistributionStats = Object.entries(MACHINERY_UNITS)
    .map(([id, e]) => ({ name: id, rul: e.rul, status: e.status }))
    .sort((a, b) => a.rul - b.rul);

  const monthlyMetricsProgression = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].map(
    (m, i) => ({ month: m, failures: [8, 6, 9, 5, 4, 3, 2, 3, 1, 2, 1, 1][i], prevented: [2, 3, 5, 4, 5, 6, 7, 6, 8, 7, 8, 9][i] })
  );

  const absoluteErrorChart = Array.from({ length: 12 }, (_, i) => ({ week: i + 1, mae: [12, 10, 9, 8.5, 7, 6.5, 5.8, 5.2, 4.8, 4.5, 4.2, 3.9][i] }));

  const systemNotifications = [
    { eq: "Unit_3", sev: "CRITICAL", msg: "RUL below critical threshold (2 days)", ago: "2 min ago", color: COLORS.critical },
    { eq: "Unit_7", sev: "WARNING", msg: "Anomaly score exceeds 0.75", ago: "8 min ago", color: COLORS.warning },
    { eq: "Unit_2", sev: "WARNING", msg: "Sensor drift detected on sensor_3", ago: "23 min ago", color: COLORS.warning },
  ];

  // Simulated data for equipment charts
  const sensorData = useMemo(() => genSensorData(selectedEquipment, parseInt(selectedSensor.replace("sensor_", ""))), [selectedEquipment, selectedSensor]);
  const rulForecast = useMemo(() => genRulForecast(selectedEquipment), [selectedEquipment]);
  const correlation = useMemo(() => genCorrelation(), []);
  const currentEq = MACHINERY_UNITS[selectedEquipment];

  // Build gantt data for schedule timeline
  const ganttData = useMemo(() => {
    return Object.entries(MACHINERY_UNITS)
      .map(([id, e]) => {
        const sched = maintenanceTimetable?.schedule.find(s => s.equipment_id === id);
        return {
          name: id,
          day: sched?.scheduled_day ?? NEXT_SERVICE[id] ?? 0,
          rul: e.rul,
          status: e.status,
          fill: statusColor(e.status),
        };
      })
      .sort((a, b) => a.rul - b.rul);
  }, [maintenanceTimetable]);

  return (
    <div className="flex min-h-screen">
      <ColdStartBanner loading={isPlatformWaking} />

      {/* ── Sidebar ── */}
      <aside className="hidden lg:flex w-64 flex-col border-r border-[var(--border-glass)] bg-gradient-to-b from-[rgba(15,23,42,0.95)] to-[rgba(30,27,75,0.9)] fixed h-screen z-40">
        <div className="px-6 pt-6 pb-2">
          <div className="flex items-center gap-3">
            <Settings className="w-7 h-7 text-indigo-400 animate-[spin_6s_linear_infinite]" />
            <div>
              <div className="text-xl font-black bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">PredictX</div>
              <div className="text-[10px] tracking-[2px] text-slate-500 uppercase">Maintenance AI Platform</div>
            </div>
          </div>
        </div>
        <div className="h-px mx-5 my-4 bg-gradient-to-r from-indigo-500/20 to-transparent" />
        <nav className="flex-1 px-4 space-y-1">
          {NAV_ITEMS.map((n) => (
            <button key={n.id} onClick={() => setActiveView(n.id)} className={`sidebar-link w-full ${activeView === n.id ? "active" : ""}`}>
              <div className="nav-dot" style={{ background: activeView === n.id ? "#f87171" : "rgba(100,116,139,0.3)" }} />
              <span className="nav-emoji">{n.emoji}</span>
              {n.label}
            </button>
          ))}
        </nav>
        <div className="px-6 pb-6 text-xs text-slate-600 space-y-1">
          {syncTime && <div>Last sync: {syncTime}</div>}
          <div>Pipeline: <span className="text-emerald-400">● Live</span></div>
          {apiHealthCheckStatus && <div>API: v{apiHealthCheckStatus.version} • {Math.round(apiHealthCheckStatus.uptime_seconds)}s up</div>}
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="flex-1 lg:ml-64 p-6 md:p-10 space-y-8">

        {/* ═══ OVERVIEW ═══ */}
        {activeView === "overview" && (
          <>
            {/* Project Overview */}
            <div className="glass-card !border-indigo-500/20">
              <div className="flex flex-col md:flex-row md:items-center gap-6">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/20 flex items-center justify-center">
                      <Settings className="w-5 h-5 text-indigo-400" />
                    </div>
                    <div>
                      <h1 className="text-2xl font-black bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">PredictX — Predictive Maintenance</h1>
                      <p className="text-[10px] tracking-[2px] text-slate-500 uppercase">AI-Powered Industrial Asset Intelligence</p>
                    </div>
                  </div>
                  <p className="text-sm text-slate-400 leading-relaxed">
                    PredictX is an end-to-end predictive maintenance platform that uses <span className="text-indigo-400 font-medium">deep learning models</span> (LSTM-Attention networks &amp; Recurrent Autoencoders) to continuously monitor industrial equipment health.
                    It detects anomalies in real-time sensor telemetry, forecasts <span className="text-purple-400 font-medium">Remaining Useful Life (RUL)</span> for each asset, and generates cost-optimized maintenance schedules using <span className="text-emerald-400 font-medium">Mixed-Integer Linear Programming (MILP)</span> — reducing unplanned downtime by up to 23% and saving $142K+ annually.
                  </p>
                </div>
                <div className="flex flex-col gap-2 md:min-w-[200px]">
                  <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-indigo-500/10 border border-indigo-500/15">
                    <Zap className="w-3.5 h-3.5 text-indigo-400" />
                    <span className="text-xs font-medium text-indigo-300">Anomaly Detection</span>
                  </div>
                  <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-purple-500/10 border border-purple-500/15">
                    <Activity className="w-3.5 h-3.5 text-purple-400" />
                    <span className="text-xs font-medium text-purple-300">RUL Forecasting</span>
                  </div>
                  <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/15">
                    <Calendar className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-xs font-medium text-emerald-300">Schedule Optimization</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { val: Object.keys(MACHINERY_UNITS).length, label: "Total Assets" },
                { val: functioningCount, label: "Operational", delta: `↑ ${functioningCount}`, deltaGood: true },
                { val: degradedCount + failingCount, label: "Alerts Active", delta: `↑ ${failingCount} critical`, deltaGood: false },
                { val: `${meanLifeExpectancy}d`, label: "Avg Fleet RUL", delta: "↑ 3d from last week", deltaGood: true },
              ].map((m, i) => (
                <div key={i} className="metric-card">
                  <div className="text-3xl font-extrabold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">{m.val}</div>
                  <div className="text-[11px] tracking-[1.2px] text-slate-500 uppercase mt-1">{m.label}</div>
                  {m.delta && <div className={`text-xs mt-1 font-semibold ${m.deltaGood ? "text-emerald-400" : "text-red-400"}`}>{m.delta}</div>}
                </div>
              ))}
            </div>

            {/* Status Matrix + Fleet Health Donut */}
            <div className="grid lg:grid-cols-5 gap-6">
              <div className="lg:col-span-3 glass-card overflow-x-auto">
                <div className="section-header">
                  <span className="text-lg">📋</span>
                  <span className="font-bold">Equipment Status Matrix</span>
                  <span className="line" />
                </div>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-xs text-indigo-400 uppercase tracking-wider">
                      <th className="text-left py-3 px-4">Asset ID</th>
                      <th className="text-left py-3 px-4">Status</th>
                      <th className="text-left py-3 px-4">RUL</th>
                      <th className="text-left py-3 px-4">Health Score</th>
                      <th className="text-left py-3 px-4">Next Service</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(MACHINERY_UNITS).map(([id, e]) => (
                      <tr key={id} className="border-t border-white/5 hover:bg-white/[0.02]">
                        <td className="py-3 px-4 font-semibold">{id}</td>
                        <td className="py-3 px-4"><span className={badgeCls(e.status)}>{e.status}</span></td>
                        <td className="py-3 px-4">{e.rul} days</td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <div className="health-bar-bg"><div className="health-bar-fill" style={{ width: `${e.health}%`, background: barColor(e.health) }} /></div>
                            <span className="text-xs" style={{ color: barColor(e.health) }}>{e.health}%</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-slate-400">Day {NEXT_SERVICE[id]}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="lg:col-span-2 glass-card flex flex-col items-center justify-center">
                <div className="section-header w-full">
                  <span className="text-lg">🎯</span>
                  <span className="font-bold">Fleet Health Distribution</span>
                  <span className="line" />
                </div>
                <div className="relative">
                  <ResponsiveContainer width={260} height={240}>
                    <PieChart>
                      <Pie data={compositionChartVals} cx="50%" cy="50%" innerRadius={65} outerRadius={95} paddingAngle={4} dataKey="value" stroke="#0a0e1a" strokeWidth={3}>
                        {compositionChartVals.map((d, i) => <Cell key={i} fill={d.color} />)}
                      </Pie>
                      <Tooltip contentStyle={TOOLTIP_STYLE} />
                    </PieChart>
                  </ResponsiveContainer>
                  {/* Center label */}
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="text-center">
                      <div className="text-2xl font-extrabold text-slate-200">{functioningCount}/{Object.keys(MACHINERY_UNITS).length}</div>
                      <div className="text-xs text-slate-500">Online</div>
                    </div>
                  </div>
                </div>
                <div className="flex gap-4 mt-2 text-xs">
                  {compositionChartVals.map((d) => (
                    <div key={d.name} className="flex items-center gap-1.5">
                      <div className="w-2.5 h-2.5 rounded-sm" style={{ background: d.color }} />
                      <span className="text-slate-400">{d.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* RUL Distribution */}
            <div className="glass-card">
              <div className="section-header"><span className="text-lg">📊</span><span className="font-bold">RUL Distribution</span><span className="line" /></div>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={lifeDistributionStats} layout="vertical" margin={{ left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                  <XAxis type="number" stroke="#64748b" fontSize={11} />
                  <YAxis type="category" dataKey="name" stroke="#64748b" fontSize={11} width={60} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <Bar dataKey="rul" radius={[0, 6, 6, 0]}>
                    {lifeDistributionStats.map((d, i) => <Cell key={i} fill={d.status === "Healthy" ? COLORS.healthy : d.status === "Warning" ? COLORS.warning : COLORS.critical} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </>
        )}

        {/* ═══ EQUIPMENT DETAIL ═══ */}
        {activeView === "equipment" && (
          <>
            <header>
              <h1 className="text-2xl font-black bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">Equipment Deep Dive</h1>
              <p className="text-xs tracking-[2px] text-slate-500 uppercase mt-1">Sensor telemetry & RUL forecasting</p>
            </header>

            {/* Equipment Selector */}
            <div>
              <label className="text-xs text-slate-500 uppercase tracking-wider block mb-2">Select Equipment</label>
              <select
                className="custom-select"
                value={selectedEquipment}
                onChange={(e) => setSelectedEquipment(e.target.value)}
              >
                {Object.keys(MACHINERY_UNITS).map((id) => <option key={id} value={id}>{id}</option>)}
              </select>
            </div>

            {/* 4 KPI Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="metric-card">
                <div className="text-2xl mb-2">🔧</div>
                <span className={badgeCls(currentEq.status)}>{currentEq.status}</span>
                <div className="text-[11px] tracking-[1.2px] text-slate-500 uppercase mt-2">Status</div>
              </div>
              <div className="metric-card">
                <div className="text-2xl mb-2">⚙️</div>
                <div className="text-3xl font-extrabold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">{currentEq.rul}d</div>
                <div className="text-[11px] tracking-[1.2px] text-slate-500 uppercase mt-1">Predicted RUL</div>
              </div>
              <div className="metric-card">
                <div className="text-2xl mb-2">🎯</div>
                <div className="text-3xl font-extrabold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">{irregularityOutput?.equipment_id === selectedEquipment ? irregularityOutput.anomaly_score : currentEq.anomaly}</div>
                <div className="text-[11px] tracking-[1.2px] text-slate-500 uppercase mt-1">Anomaly Score</div>
              </div>
              <div className="metric-card">
                <div className="text-2xl mb-2">💚</div>
                <div className="text-3xl font-extrabold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">{currentEq.health}%</div>
                <div className="text-[11px] tracking-[1.2px] text-slate-500 uppercase mt-1">Health Index</div>
              </div>
            </div>

            {loadingAnomaly && <div className="flex justify-center py-4"><div className="spinner" /></div>}

            {/* Sensor Telemetry + RUL Forecast */}
            <div className="grid lg:grid-cols-2 gap-6">
              <div className="glass-card">
                <div className="section-header"><span className="text-lg">📈</span><span className="font-bold">Sensor Telemetry</span><span className="line" /></div>
                <select
                  className="custom-select mb-4"
                  value={selectedSensor}
                  onChange={(e) => setSelectedSensor(e.target.value)}
                >
                  {Array.from({ length: 21 }, (_, i) => `sensor_${i + 1}`).map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
                <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">{selectedSensor.toUpperCase()}</div>
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={sensorData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                    <XAxis dataKey="t" stroke="#64748b" fontSize={10} />
                    <YAxis stroke="#64748b" fontSize={10} />
                    <Tooltip contentStyle={TOOLTIP_STYLE} />
                    <Line type="monotone" dataKey="value" stroke="#818cf8" strokeWidth={1.5} dot={false} />
                    {/* Anomaly window highlight */}
                    <ReferenceLine x={38} stroke="#f87171" strokeDasharray="4 4" label={{ value: "Anomaly Window", fill: "#f87171", fontSize: 10, position: "top" }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="glass-card">
                <div className="section-header"><span className="text-lg">⚙️</span><span className="font-bold">RUL Forecast</span><span className="line" /></div>
                <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Remaining Useful Life</div>
                <ResponsiveContainer width="100%" height={263}>
                  <LineChart data={rulForecast}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                    <XAxis dataKey="day" stroke="#64748b" fontSize={10} />
                    <YAxis stroke="#64748b" fontSize={10} domain={[0, 120]} />
                    <Tooltip contentStyle={TOOLTIP_STYLE} />
                    <Line type="monotone" dataKey="rul" stroke="#a78bfa" strokeWidth={2} dot={false} />
                    <ReferenceLine y={40} stroke="#fbbf24" strokeDasharray="6 3">
                      <Label value="Warning Zone" fill="#fbbf24" fontSize={10} position="right" />
                    </ReferenceLine>
                    <ReferenceLine y={15} stroke="#f87171" strokeDasharray="6 3">
                      <Label value="Critical Threshold" fill="#f87171" fontSize={10} position="right" />
                    </ReferenceLine>
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Sensor Correlation Heatmap */}
            <div className="glass-card">
              <div className="section-header"><span className="text-lg">🔗</span><span className="font-bold">Sensor Correlation Heatmap</span><span className="line" /></div>
              <div className="flex gap-3">
                {/* Y-axis labels */}
                <div className="flex flex-col pt-7 pb-0 shrink-0">
                  {correlation.sensors.map((s) => (
                    <div key={s} className="flex-1 flex items-center justify-end text-[11px] text-slate-400 pr-1 min-h-[44px]">{s}</div>
                  ))}
                </div>
                {/* Grid area */}
                <div className="flex-1 min-w-0">
                  {/* X-axis labels */}
                  <div className="grid mb-1" style={{ gridTemplateColumns: `repeat(${correlation.sensors.length}, 1fr)` }}>
                    {correlation.sensors.map((s) => (
                      <div key={s} className="text-center text-[11px] text-slate-400">{s}</div>
                    ))}
                  </div>
                  {/* Cells */}
                  {correlation.sensors.map((row) => (
                    <div key={row} className="grid" style={{ gridTemplateColumns: `repeat(${correlation.sensors.length}, 1fr)` }}>
                      {correlation.sensors.map((col) => {
                        const cell = correlation.data.find(d => d.row === row && d.col === col);
                        return (
                          <div
                            key={`${row}-${col}`}
                            className="heatmap-cell flex items-center justify-center text-[11px] text-white/70 font-mono min-h-[44px]"
                            style={{ background: heatColor(cell?.val ?? 0) }}
                            title={`${row} × ${col}: ${cell?.val}`}
                          >
                            {cell?.val.toFixed(1)}
                          </div>
                        );
                      })}
                    </div>
                  ))}
                </div>
                {/* Color scale */}
                <div className="flex flex-col justify-between pt-7 pb-0 shrink-0 w-5">
                  <div className="text-[10px] text-slate-400 text-center">1</div>
                  <div className="w-4 flex-1 my-1 rounded mx-auto" style={{ background: "linear-gradient(to bottom, rgba(167,139,250,0.9), rgba(167,139,250,0.2), rgba(219,171,255,0.3), rgba(248,180,255,0.6))" }} />
                  <div className="text-[10px] text-slate-400 text-center">-1</div>
                </div>
              </div>
            </div>
          </>
        )}

        {/* ═══ SCHEDULE ═══ */}
        {activeView === "schedule" && (
          <>
            <header>
              <div className="flex items-center gap-3">
                <span className="text-2xl">📋</span>
                <div>
                  <h1 className="text-2xl font-black bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">MILP Optimized Schedule</h1>
                  <p className="text-xs tracking-[2px] text-slate-500 uppercase mt-1">Mixed-Integer Linear Programming • PuLP Solver</p>
                </div>
              </div>
            </header>

            {loadingSchedule && <div className="flex justify-center py-10"><div className="spinner" /></div>}

            {maintenanceTimetable && (
              <>
                {/* KPI Row */}
                <div className="grid md:grid-cols-3 gap-4">
                  <div className="metric-card">
                    <div className="text-2xl mb-2">💰</div>
                    <div className="text-3xl font-extrabold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">${maintenanceTimetable.aggregate_financial_impact.toLocaleString()}</div>
                    <div className="text-[11px] tracking-[1.2px] text-slate-500 uppercase mt-1">Optimized Total Cost</div>
                  </div>
                  <div className="metric-card">
                    <div className="text-2xl mb-2">✅</div>
                    <div className="text-3xl font-extrabold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">{maintenanceTimetable.status}</div>
                    <div className="text-[11px] tracking-[1.2px] text-slate-500 uppercase mt-1">Solver Status</div>
                  </div>
                  <div className="metric-card">
                    <div className="text-2xl mb-2">🔧</div>
                    <div className="text-3xl font-extrabold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">2/day</div>
                    <div className="text-[11px] tracking-[1.2px] text-slate-500 uppercase mt-1">Tech Capacity</div>
                  </div>
                </div>

                {/* Maintenance Timeline (Gantt-style horizontal bar chart) */}
                <div className="glass-card">
                  <div className="section-header"><span className="text-lg">📋</span><span className="font-bold">Maintenance Timeline</span><span className="line" /></div>
                  <ResponsiveContainer width="100%" height={360}>
                    <BarChart data={ganttData} layout="vertical" margin={{ left: 20, right: 130, bottom: 25 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                      <XAxis
                        type="number"
                        stroke="#64748b"
                        fontSize={11}
                        domain={[0, 30]}
                        ticks={[0, 4, 8, 12, 16, 20, 24, 28]}
                        tickFormatter={(day: number) => {
                          const d = new Date();
                          d.setDate(d.getDate() + day);
                          return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
                        }}
                        label={{ value: new Date().getFullYear().toString(), position: "insideBottomLeft", fill: "#64748b", fontSize: 10, dy: 14, dx: -10 }}
                      />
                      <YAxis type="category" dataKey="name" stroke="#64748b" fontSize={11} width={60} label={{ value: "Equipment", angle: -90, position: "insideLeft", fill: "#64748b", fontSize: 11, dx: -10 }} />
                      <Tooltip
                        contentStyle={TOOLTIP_STYLE}
                        labelStyle={{ color: "#86efac" }}
                        itemStyle={{ color: "#86efac" }}
                        formatter={(v: any) => {
                          const day = Number(v) || 0;
                          const d = new Date();
                          d.setDate(d.getDate() + day);
                          return [d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }), "Scheduled"];
                        }}
                      />
                      <Legend
                        layout="vertical"
                        align="right"
                        verticalAlign="top"
                        wrapperStyle={{ paddingLeft: 20, top: 10, right: 0, lineHeight: "22px" }}
                        content={() => (
                          <div style={{ textAlign: "left" }}>
                            <div style={{ color: "#94a3b8", fontSize: "11px", fontWeight: 700, marginBottom: 10, letterSpacing: "1px", textTransform: "uppercase" }}>Status</div>
                            {[
                              { label: "Critical", color: COLORS.critical },
                              { label: "Warning", color: COLORS.warning },
                              { label: "Healthy", color: COLORS.healthy },
                            ].map((item) => (
                              <div key={item.label} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                                <div style={{ width: 12, height: 12, borderRadius: 2, background: item.color, flexShrink: 0 }} />
                                <span style={{ color: "#86efac", fontSize: "12px" }}>{item.label}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      />
                      <Bar dataKey="day" radius={[0, 4, 4, 0]} barSize={16} legendType="none">
                        {ganttData.map((d, i) => <Cell key={i} fill={d.fill} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Schedule Table */}
                <div className="glass-card overflow-x-auto">
                  <div className="section-header"><span className="text-lg">📋</span><span className="font-bold">Schedule Details</span><span className="line" /></div>
                  <table className="w-full text-sm">
                    <thead><tr className="text-xs text-indigo-400 uppercase tracking-wider"><th className="text-left py-3 px-4">Equipment</th><th className="text-left py-3 px-4">Scheduled Day</th><th className="text-left py-3 px-4">Date</th><th className="text-left py-3 px-4">Current RUL</th><th className="text-left py-3 px-4">Est. Cost</th></tr></thead>
                    <tbody>
                      {maintenanceTimetable.schedule.sort((a, b) => a.scheduled_day - b.scheduled_day).map((s: RepairTimetableRow) => {
                        const eq = MACHINERY_UNITS[s.equipment_id];
                        const schedDate = new Date();
                        schedDate.setDate(schedDate.getDate() + s.scheduled_day);
                        return (
                          <tr key={s.equipment_id} className="border-t border-white/5 hover:bg-white/[0.02]">
                            <td className="py-3 px-4 font-semibold">{s.equipment_id}</td>
                            <td className="py-3 px-4">Day {s.scheduled_day}</td>
                            <td className="py-3 px-4 text-slate-300">{schedDate.toLocaleDateString("en-US", { month: "short", day: "2-digit", year: "numeric" })}</td>
                            <td className="py-3 px-4"><span className={badgeCls(eq?.status || "Healthy")} style={{ marginRight: 6 }}>●</span>{eq?.rul ?? "?"}d</td>
                            <td className="py-3 px-4">${s.estimated_cost.toLocaleString()}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </>
            )}

            {!maintenanceTimetable && !loadingSchedule && (
              <button onClick={fetchSchedule} className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-500 text-white font-semibold hover:shadow-[0_0_25px_rgba(129,140,248,0.3)] transition disabled:opacity-50">
                <Wrench className="w-4 h-4" /> Run Schedule Optimizer
              </button>
            )}
          </>
        )}

        {/* ═══ ALERTS ═══ */}
        {activeView === "systemNotifications" && (
          <>
            <header>
              <h1 className="text-2xl font-black bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">Alert Center</h1>
              <p className="text-xs tracking-[2px] text-slate-500 uppercase mt-1">Intelligent monitoring rules</p>
            </header>

            {/* Active Alerts */}
            <div className="flex items-center gap-2 mt-2 mb-1">
              <span className="text-lg">🚨</span>
              <span className="text-sm font-bold text-slate-200 tracking-wide">Active Alerts</span>
            </div>
            <div className="space-y-3">
              {systemNotifications.map((a, i) => (
                <div key={i} className="glass-card !py-4 !px-5 flex justify-between items-center" style={{ borderLeft: `3px solid ${a.color}` }}>
                  <div><span className="font-bold" style={{ color: a.color }}>[{a.sev}]</span> <span className="font-semibold">{a.eq}</span> — {a.msg}</div>
                  <span className="text-xs text-slate-600">{a.ago}</span>
                </div>
              ))}
            </div>

            {/* Create Alert Rule */}
            <div className="glass-card">
              <div className="section-header"><Plus className="w-5 h-5 text-indigo-400" /><span className="font-bold">Create Alert Rule</span><span className="line" /></div>
              <div className="grid md:grid-cols-2 gap-5">
                <div>
                  <label className="text-xs text-slate-500 uppercase tracking-wider block mb-2">Sensor Target</label>
                  <select className="custom-select" value={alertSensorTarget} onChange={(e) => setAlertSensorTarget(e.target.value)}>
                    {Array.from({ length: 21 }, (_, i) => `sensor_${i + 1}`).map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-500 uppercase tracking-wider block mb-2">Threshold Value</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      className="custom-input flex-1"
                      value={alertThreshold}
                      onChange={(e) => setAlertThreshold(e.target.value)}
                    />
                    <button className="px-3 py-2 rounded-xl bg-[rgba(15,23,42,0.8)] border border-[var(--border-glass)] text-slate-400 hover:text-white transition" onClick={() => setAlertThreshold((p) => (parseFloat(p) - 1).toFixed(2))}>−</button>
                    <button className="px-3 py-2 rounded-xl bg-[rgba(15,23,42,0.8)] border border-[var(--border-glass)] text-slate-400 hover:text-white transition" onClick={() => setAlertThreshold((p) => (parseFloat(p) + 1).toFixed(2))}>+</button>
                  </div>
                </div>
                <div>
                  <label className="text-xs text-slate-500 uppercase tracking-wider block mb-2">Severity</label>
                  <select className="custom-select" value={alertSeverity} onChange={(e) => setAlertSeverity(e.target.value)}>
                    <option>Info</option>
                    <option>Warning</option>
                    <option>Critical</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-500 uppercase tracking-wider block mb-2">Notify Via</label>
                  <select className="custom-select" value={alertNotifyVia} onChange={(e) => setAlertNotifyVia(e.target.value)}>
                    <option>Choose options</option>
                    <option>Email</option>
                    <option>Slack</option>
                    <option>Webhook</option>
                  </select>
                </div>
              </div>
              <button
                onClick={deployAlertRule}
                className="mt-5 flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-red-500 to-rose-500 text-white font-semibold hover:shadow-[0_0_25px_rgba(248,113,113,0.3)] hover:scale-[1.02] active:scale-95 transition cursor-pointer"
              >
                <Zap className="w-4 h-4" /> Deploy Alert Rule
              </button>
            </div>

            {/* Deployed Rules */}
            {deployedRules.length > 0 && (
              <div className="glass-card">
                <div className="section-header"><Shield className="w-5 h-5 text-emerald-400" /><span className="font-bold">Deployed Rules</span><span className="line" /></div>
                <div className="space-y-2">
                  {deployedRules.map((r, i) => (
                    <div key={i} className="flex items-center justify-between py-3 px-4 rounded-xl border border-emerald-500/15 bg-emerald-500/5">
                      <div className="flex items-center gap-3">
                        <span className="text-emerald-400 text-sm">✓</span>
                        <span className="text-sm font-medium text-slate-300">{r.sensor}</span>
                        <span className="text-xs text-slate-500">≥ {r.threshold}</span>
                        <span className={`badge text-[10px] !py-0.5 !px-2 ${r.severity === "Critical" ? "badge-critical" : r.severity === "Warning" ? "badge-warning" : "badge-healthy"}`}>{r.severity}</span>
                        <span className="text-xs text-slate-500">via {r.notify}</span>
                      </div>
                      <span className="text-[10px] text-slate-600">{r.time}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* ═══ REPORTS ═══ */}
        {activeView === "reports" && (
          <>
            <header>
              <h1 className="text-2xl font-black bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">Analytics & Reports</h1>
              <p className="text-xs tracking-[2px] text-slate-500 uppercase mt-1">Performance intelligence</p>
            </header>
            <div className="grid md:grid-cols-3 gap-4">
              <div className="metric-card"><div className="text-2xl">📉</div><div className="text-3xl font-extrabold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">23%</div><div className="text-[11px] tracking-[1.2px] text-slate-500 uppercase mt-1">Downtime Reduction</div></div>
              <div className="metric-card"><div className="text-2xl">💵</div><div className="text-3xl font-extrabold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">$142K</div><div className="text-[11px] tracking-[1.2px] text-slate-500 uppercase mt-1">Cost Savings YTD</div></div>
              <div className="metric-card"><div className="text-2xl">🎯</div><div className="text-3xl font-extrabold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">94.2%</div><div className="text-[11px] tracking-[1.2px] text-slate-500 uppercase mt-1">Model Accuracy</div></div>
            </div>
            <div className="grid lg:grid-cols-2 gap-6">
              <div className="glass-card">
                <div className="section-header"><TrendingDown className="w-5 h-5 text-emerald-400" /><span className="font-bold">Monthly Failure Trend</span><span className="line" /></div>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={monthlyMetricsProgression}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                    <XAxis dataKey="month" stroke="#64748b" fontSize={11} />
                    <YAxis stroke="#64748b" fontSize={11} />
                    <Tooltip contentStyle={TOOLTIP_STYLE} />
                    <Legend formatter={(v) => <span className="text-slate-400 text-xs">{v}</span>} />
                    <Bar dataKey="failures" name="Unplanned" fill={COLORS.critical} radius={[4, 4, 0, 0]} stackId="a" />
                    <Bar dataKey="prevented" name="Prevented by AI" fill={COLORS.healthy} radius={[4, 4, 0, 0]} stackId="a" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="glass-card">
                <div className="section-header"><Gauge className="w-5 h-5 text-purple-400" /><span className="font-bold">Model Performance (MAE)</span><span className="line" /></div>
                <ResponsiveContainer width="100%" height={280}>
                  <AreaChart data={absoluteErrorChart}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                    <XAxis dataKey="week" stroke="#64748b" fontSize={11} />
                    <YAxis stroke="#64748b" fontSize={11} />
                    <Tooltip contentStyle={TOOLTIP_STYLE} />
                    <Area type="monotone" dataKey="mae" stroke="#a78bfa" strokeWidth={3} fill="rgba(167,139,250,0.1)" dot={{ r: 4, fill: "#a78bfa", stroke: "#0a0e1a", strokeWidth: 2 }} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Export Reports */}
            <div className="glass-card">
              <div className="section-header">
                <span className="text-lg">📥</span>
                <span className="font-bold">Export Reports</span>
                <span className="line" />
              </div>
              <div className="flex flex-wrap gap-4">
                {[
                  {
                    label: "Weekly Ops Report",
                    icon: "📊",
                    action: () => {
                      const header = "Equipment,Status,RUL (days),Health %,Anomaly Score,Next Service Day";
                      const rows = Object.entries(MACHINERY_UNITS).map(([id, e]) =>
                        `${id},${e.status},${e.rul},${e.health},${e.anomaly},Day ${NEXT_SERVICE[id]}`
                      );
                      downloadCSV(`weekly_ops_report_${new Date().toISOString().slice(0, 10)}.csv`, [header, ...rows].join("\n"));
                    },
                  },
                  {
                    label: "Drift Analysis Report",
                    icon: "📈",
                    action: () => {
                      const header = "Equipment,Status,Anomaly Score,Health %,Risk Level";
                      const rows = Object.entries(MACHINERY_UNITS).map(([id, e]) => {
                        const risk = e.anomaly > 0.7 ? "High" : e.anomaly > 0.4 ? "Medium" : "Low";
                        return `${id},${e.status},${e.anomaly},${e.health},${risk}`;
                      });
                      downloadCSV(`drift_analysis_${new Date().toISOString().slice(0, 10)}.csv`, [header, ...rows].join("\n"));
                    },
                  },
                  {
                    label: "Maintenance Schedule",
                    icon: "🔧",
                    action: () => {
                      if (!maintenanceTimetable) {
                        alert("Please generate a maintenance schedule first from the Maintenance Schedule page.");
                        return;
                      }
                      const header = "Equipment,Scheduled Day,Date,Current RUL (days),Status,Estimated Cost";
                      const rows = maintenanceTimetable.schedule
                        .sort((a, b) => a.scheduled_day - b.scheduled_day)
                        .map((s) => {
                          const eq = MACHINERY_UNITS[s.equipment_id];
                          const d = new Date();
                          d.setDate(d.getDate() + s.scheduled_day);
                          return `${s.equipment_id},Day ${s.scheduled_day},${d.toLocaleDateString("en-US", { month: "short", day: "2-digit", year: "numeric" })},${eq?.rul ?? "?"},${eq?.status ?? "Unknown"},$${s.estimated_cost.toLocaleString()}`;
                        });
                      downloadCSV(`maintenance_schedule_${new Date().toISOString().slice(0, 10)}.csv`, [header, ...rows].join("\n"));
                    },
                  },
                ].map((r) => (
                  <button
                    key={r.label}
                    onClick={r.action}
                    className="flex items-center gap-2 px-5 py-3 rounded-xl bg-[rgba(15,23,42,0.7)] border border-[var(--border-glass)] hover:border-indigo-500/40 hover:bg-indigo-500/10 text-sm font-medium text-slate-300 hover:text-white transition-all duration-200 cursor-pointer group"
                  >
                    <Download className="w-4 h-4 text-indigo-400 group-hover:text-indigo-300 transition" />
                    <span>{r.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}