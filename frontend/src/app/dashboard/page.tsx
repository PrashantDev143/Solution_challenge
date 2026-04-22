"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { explain, getReport } from "@/lib/api";
import { BiasedGroup, ExplainResponse, ScanResponse } from "@/lib/types";

const SEVERITY_COLORS: Record<string, string> = {
  high: "#dc2626",
  medium: "#f59e0b",
  low: "#10b981",
};

const MAX_GROUPS_FOR_CHARTS = 8;

const FEATURE_LABELS: Record<string, string> = {
  gender: "Gender",
  region: "Region",
  education: "Education",
  income_bucket: "Income",
  age_bucket: "Age",
};

function toTitleCase(value: string): string {
  return value
    .split(" ")
    .filter(Boolean)
    .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1).toLowerCase())
    .join(" ");
}

function formatGroupValue(value: string): string {
  return toTitleCase(value.replaceAll("_", " "));
}

function prettifyGroupLabel(label: string): string {
  const parts = label.split(" + ");
  const formatted = parts.map((part) => {
    const [rawKey, rawValue = ""] = part.split("=");
    const key = FEATURE_LABELS[rawKey] ?? toTitleCase(rawKey.replaceAll("_", " "));
    const value = formatGroupValue(rawValue);
    return `${key} = ${value}`;
  });
  return formatted.join(" + ");
}

function compactGroupLabel(label: string, maxLength = 28): string {
  const pretty = prettifyGroupLabel(label);
  if (pretty.length <= maxLength) {
    return pretty;
  }
  return `${pretty.slice(0, maxLength - 1)}...`;
}

function severityBreakdown(groups: BiasedGroup[]) {
  const counts: Record<string, number> = { high: 0, medium: 0, low: 0 };
  for (const group of groups) {
    counts[group.severity] = (counts[group.severity] ?? 0) + 1;
  }
  return Object.entries(counts).map(([severity, count]) => ({ severity, count }));
}

export default function DashboardPage() {
  const [report, setReport] = useState<ScanResponse | null>(null);
  const [selectedGroup, setSelectedGroup] = useState<BiasedGroup | null>(null);
  const [explanation, setExplanation] = useState<ExplainResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isExplaining, setIsExplaining] = useState(false);

  const refresh = async () => {
    try {
      setLoading(true);
      setError(null);
      const latest = await getReport();
      if (!latest) {
        throw new Error("No scan report available");
      }
      setReport(latest);
      setSelectedGroup(latest.top_biased_groups[0] ?? null);
      localStorage.setItem("biasxray_scan_report", JSON.stringify(latest));
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to load report. Please run a scan first.";
      setError(errorMsg);
      
      // Try to load from cache as fallback
      const cached = localStorage.getItem("biasxray_scan_report");
      if (cached) {
        try {
          setReport(JSON.parse(cached) as ScanResponse);
          setError(null); // Clear error if cached data loads successfully
        } catch (parseErr) {
          console.error("Failed to parse cached report:", parseErr);
        }
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const pieData = useMemo(
    () => severityBreakdown((report?.top_biased_groups ?? []).slice(0, MAX_GROUPS_FOR_CHARTS)),
    [report?.top_biased_groups],
  );

  const displayedGroups = useMemo(
    () => (report?.top_biased_groups ?? []).slice(0, MAX_GROUPS_FOR_CHARTS),
    [report?.top_biased_groups],
  );

  const requestExplanation = async () => {
    if (!selectedGroup) {
      return;
    }

    try {
      setIsExplaining(true);
      setError(null);
      const result = await explain({
        group: prettifyGroupLabel(selectedGroup.group),
        count: selectedGroup.count,
        approval_rate: selectedGroup.approval_rate,
        baseline_rate: selectedGroup.baseline_rate,
        difference: selectedGroup.difference,
        severity: selectedGroup.severity,
        ranking_reason: selectedGroup.ranking_reason,
      });
      setExplanation(result);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Could not generate explanation. Please try again.";
      setError(errorMsg);
      console.error("Explanation error:", err);
    } finally {
      setIsExplaining(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse rounded-xl bg-slate-200 p-6 h-20"></div>
        <div className="grid gap-4 md:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="animate-pulse rounded-xl bg-slate-200 h-24"></div>
          ))}
        </div>
        <div className="rounded-xl bg-white p-6 text-sm text-slate-600">
          <div className="flex items-center gap-2">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-700"></div>
            Loading dashboard...
          </div>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">
        <p className="font-semibold mb-2">No Scan Data Available</p>
        <p>{error ?? "No scan report found yet. Please upload a dataset and run a scan first."}</p>
        <button
          onClick={() => window.location.href = "/upload"}
          className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-white hover:bg-red-700"
        >
          Go to Upload
        </button>
      </div>
    );
  }

  return (
    <section className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-semibold text-slate-900">Bias Dashboard</h1>
          <p className="mt-1 text-sm text-slate-600">Monitor fairness metrics, biased groups, and risk severity.</p>
        </div>
        <button
          onClick={() => void refresh()}
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
        >
          Refresh
        </button>
      </div>

      {error && <div className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800">{error}</div>}

      <div className="grid gap-4 md:grid-cols-4">
        {[
          { label: "Total Rows", value: report.total_rows },
          { label: "Groups Scanned", value: report.groups_scanned },
          { label: "Biased Groups", value: report.biased_groups_found },
          { label: "Fairness Score", value: report.fairness_score },
        ].map((card) => (
          <div key={card.label} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-xs uppercase tracking-wide text-slate-500">{card.label}</p>
            <p className="mt-1 text-2xl font-bold text-slate-900">{card.value}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="font-display text-lg font-semibold text-slate-900">Top Biased Groups</h2>
          <div className="mt-4" style={{ height: "400px" }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={displayedGroups} margin={{ top: 20, right: 30, left: 50, bottom: 80 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="group"
                  interval={0}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  tickFormatter={(value) => compactGroupLabel(String(value), 20)}
                  tick={{ fontSize: 11 }}
                  width={100}
                />
                <YAxis 
                  width={50}
                  label={{ value: "Approval Gap %", angle: -90, position: "insideLeft" }}
                />
                <Tooltip 
                  formatter={(value) => `${(Number(value) * 100).toFixed(2)}%`} 
                  labelFormatter={(label) => prettifyGroupLabel(String(label))}
                  contentStyle={{ backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "8px" }}
                />
                <Legend wrapperStyle={{ paddingTop: "15px" }} />
                <Bar 
                  dataKey="difference" 
                  name="Approval Gap"
                  isAnimationActive={true}
                  animationDuration={800}
                  animationEasing="ease-in-out"
                  radius={[8, 8, 0, 0]}
                >
                  {displayedGroups.map((entry) => (
                    <Cell key={entry.group} fill={SEVERITY_COLORS[entry.severity] ?? "#64748b"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="font-display text-lg font-semibold text-slate-900">Severity Breakdown</h2>
          <div className="mt-4" style={{ height: "400px" }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie 
                  data={pieData} 
                  dataKey="count" 
                  nameKey="severity" 
                  outerRadius={100} 
                  label={({ severity, count }) => `${severity}: ${count}`}
                  isAnimationActive={true}
                  animationDuration={800}
                  animationEasing="ease-out"
                >
                  {pieData.map((entry) => (
                    <Cell key={entry.severity} fill={SEVERITY_COLORS[entry.severity] ?? "#64748b"} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value) => [`${value} groups`, "Count"]}
                  contentStyle={{ backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "8px" }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="font-display text-lg font-semibold text-slate-900">Group Details</h2>
        <div className="mt-3 overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-slate-600">
                <th className="px-3 py-2">Group</th>
                <th className="px-3 py-2">Count</th>
                <th className="px-3 py-2">Approval Rate</th>
                <th className="px-3 py-2">Difference</th>
                <th className="px-3 py-2">Severity</th>
              </tr>
            </thead>
            <tbody>
              {displayedGroups.map((group) => (
                <tr
                  key={group.group}
                  className="cursor-pointer border-b border-slate-100 hover:bg-slate-50"
                  onClick={() => {
                    setSelectedGroup(group);
                    setExplanation(null);
                  }}
                >
                  <td className="px-3 py-2 text-slate-800">{prettifyGroupLabel(group.group)}</td>
                  <td className="px-3 py-2 text-slate-600">{group.count}</td>
                  <td className="px-3 py-2 text-slate-600">{group.approval_rate}</td>
                  <td className="px-3 py-2 text-slate-600">{group.difference}</td>
                  <td className="px-3 py-2">
                    <span
                      className="rounded-full px-2 py-1 text-xs font-semibold text-white"
                      style={{ backgroundColor: SEVERITY_COLORS[group.severity] ?? "#64748b" }}
                    >
                      {group.severity}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between gap-3">
          <h2 className="font-display text-lg font-semibold text-slate-900">Gemini Explanation</h2>
          <button
            onClick={() => void requestExplanation()}
            disabled={!selectedGroup || isExplaining}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {isExplaining ? "Generating..." : "Generate Explanation"}
          </button>
        </div>

        {selectedGroup ? (
          <p className="mt-2 text-sm text-slate-600">Selected group: {prettifyGroupLabel(selectedGroup.group)}</p>
        ) : (
          <p className="mt-2 text-sm text-slate-500">Choose a group from the table to explain.</p>
        )}

        {explanation && (
          <div className="mt-4 space-y-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm text-slate-700">{explanation.explanation}</p>
            <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
              {explanation.recommendations.map((item, index) => (
                <li key={`${item}-${index}`}>{item}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </section>
  );
}
