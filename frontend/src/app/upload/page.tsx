"use client";

import { ChangeEvent, DragEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { getReport, scanBias, uploadCsv } from "@/lib/api";
import { ScanResponse, UploadResponse } from "@/lib/types";

function prettyHeader(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (m) => m.toUpperCase());
}

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const previewColumns = useMemo(() => uploadResult?.columns ?? [], [uploadResult]);

  const onFileSelect = (selected: File | null) => {
    if (!selected) {
      return;
    }
    if (!selected.name.toLowerCase().endsWith(".csv")) {
      setError("Only .csv files are supported.");
      setFile(null);
      return;
    }

    setError(null);
    setUploadResult(null);
    setScanResult(null);
    setFile(selected);
  };

  const onInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0] ?? null;
    onFileSelect(selected);
  };

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    onFileSelect(event.dataTransfer.files?.[0] ?? null);
  };

  const onUpload = async () => {
    if (!file) {
      setError("Please choose a CSV file first.");
      return;
    }

    try {
      setIsUploading(true);
      setError(null);
      setScanResult(null);

      // Reset stale client-side state before replacing dataset/report.
      localStorage.removeItem("biasxray_scan_report");

      const uploaded = await uploadCsv(file);
      setUploadResult(uploaded);
      localStorage.setItem("biasxray_dataset_path", uploaded.temp_path);

      await scanBias({ dataset_path: uploaded.temp_path });

      // Fetch latest persisted report so dashboard opens with fresh backend state.
      const latestReport = await getReport();
      setScanResult(latestReport as ScanResponse);
      localStorage.setItem("biasxray_scan_report", JSON.stringify(latestReport));

      router.push(`/dashboard?refresh=${Date.now()}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <section className="space-y-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="font-display text-3xl font-semibold text-slate-900">Upload Dataset</h1>
        <p className="mt-2 text-sm text-slate-600">
          Drop a CSV file to start a fairness audit. BiasX-Ray will preview data and run an initial scan.
        </p>

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={onDrop}
          className={`mt-6 rounded-2xl border-2 border-dashed p-8 text-center transition ${
            isDragging
              ? "border-teal-500 bg-teal-50"
              : "border-slate-300 bg-slate-50 hover:border-teal-400"
          }`}
        >
          <p className="text-sm text-slate-700">Drag and drop your CSV file here</p>
          <p className="mt-1 text-xs text-slate-500">or</p>
          <label className="mt-3 inline-flex cursor-pointer rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800">
            Browse Files
            <input type="file" accept=".csv" className="hidden" onChange={onInputChange} />
          </label>

          {file && (
            <p className="mt-4 text-sm text-slate-600">
              Selected: <span className="font-medium text-slate-900">{file.name}</span>
            </p>
          )}
        </div>

        <button
          onClick={onUpload}
          disabled={isUploading}
          className="mt-5 rounded-lg bg-teal-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-teal-700 disabled:cursor-not-allowed disabled:bg-teal-300"
        >
          {isUploading ? "Uploading and scanning..." : "Upload and Run Scan"}
        </button>

        {error && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}
      </div>

      {uploadResult && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="font-display text-xl font-semibold text-slate-900">Preview (First 10 Rows)</h2>
          <p className="mt-1 text-sm text-slate-600">
            Columns: {uploadResult.columns.length} | Rows: {uploadResult.row_count}
          </p>

          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full border-collapse text-sm">
              <thead>
                <tr>
                  {previewColumns.map((column) => (
                    <th
                      key={column}
                      className="border-b border-slate-200 px-3 py-2 text-left font-semibold text-slate-700"
                    >
                      {prettyHeader(column)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {uploadResult.preview_rows.map((row, index) => (
                  <tr key={index} className="odd:bg-slate-50">
                    {previewColumns.map((column) => (
                      <td key={`${index}-${column}`} className="px-3 py-2 text-slate-600">
                        {String(row[column] ?? "")}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {scanResult && (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5 text-sm text-emerald-900">
          Scan complete. Fairness score: <strong>{scanResult.fairness_score}</strong> | Biased groups found:{" "}
          <strong>{scanResult.biased_groups_found}</strong>
        </div>
      )}
    </section>
  );
}
