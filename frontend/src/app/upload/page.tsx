"use client";

import { ChangeEvent, DragEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { getReport, scanBias, uploadCsv } from "@/lib/api";
import { ScanResponse, UploadResponse } from "@/lib/types";

const MAX_FILE_SIZE_MB = 50;
const ALLOWED_FILE_TYPES = [".csv", "text/csv"];

function prettyHeader(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (m) => m.toUpperCase());
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
}

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const previewColumns = useMemo(() => uploadResult?.columns ?? [], [uploadResult]);

  const validateFile = (selected: File): { valid: boolean; error?: string } => {
    if (!selected) {
      return { valid: false };
    }

    // Check file extension
    if (!selected.name.toLowerCase().endsWith(".csv")) {
      return { valid: false, error: "Only .csv files are supported." };
    }

    // Check file size
    if (selected.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      return {
        valid: false,
        error: `File size (${formatFileSize(selected.size)}) exceeds ${MAX_FILE_SIZE_MB}MB limit.`,
      };
    }

    // Check file type
    if (selected.type && !ALLOWED_FILE_TYPES.includes(selected.type)) {
      return { valid: false, error: "Invalid file type. Please upload a CSV file." };
    }

    return { valid: true };
  };

  const onFileSelect = (selected: File | null) => {
    if (!selected) {
      setFile(null);
      setError(null);
      return;
    }

    const validation = validateFile(selected);
    if (!validation.valid) {
      setError(validation.error || "Invalid file.");
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
    const selected = event.dataTransfer.files?.[0] ?? null;
    onFileSelect(selected);
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
      setUploadProgress("Uploading file...");

      // Reset stale client-side state before replacing dataset/report.
      localStorage.removeItem("biasxray_scan_report");

      const uploaded = await uploadCsv(file);
      setUploadResult(uploaded);
      localStorage.setItem("biasxray_dataset_path", uploaded.temp_path);
      setUploadProgress("Running bias scan...");

      await scanBias({ dataset_path: uploaded.temp_path });

      // Fetch latest persisted report so dashboard opens with fresh backend state.
      setUploadProgress("Fetching results...");
      const latestReport = await getReport();
      setScanResult(latestReport as ScanResponse);
      localStorage.setItem("biasxray_scan_report", JSON.stringify(latestReport));

      setUploadProgress(null);
      router.push(`/dashboard?refresh=${Date.now()}`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An unexpected error occurred during upload.";
      setError(errorMessage);
      setUploadProgress(null);
      console.error("Upload error:", err);
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
            <div className="mt-4 space-y-2">
              <p className="text-sm text-slate-600">
                Selected: <span className="font-medium text-slate-900">{file.name}</span>
              </p>
              <p className="text-xs text-slate-500">
                Size: {formatFileSize(file.size)} (Max: {MAX_FILE_SIZE_MB}MB)
              </p>
            </div>
          )}
        </div>

        <div className="mt-4 space-y-3">
          <button
            onClick={onUpload}
            disabled={!file || isUploading}
            className="w-full rounded-lg bg-teal-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-teal-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {isUploading ? "Processing..." : file ? "Upload and Run Scan" : "Select a file to continue"}
          </button>

          {uploadProgress && (
            <div className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-700">
              <div className="flex items-center gap-2">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-300 border-t-blue-700"></div>
                {uploadProgress}
              </div>
            </div>
          )}

          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              <p className="font-medium">Error:</p>
              <p className="mt-1">{error}</p>
            </div>
          )}
        </div>

        <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
          <p className="text-xs font-semibold uppercase text-slate-600">Requirements:</p>
          <ul className="mt-2 space-y-1 text-xs text-slate-600">
            <li>✓ CSV format with headers</li>
            <li>✓ Maximum file size: {MAX_FILE_SIZE_MB}MB</li>
            <li>✓ At least 2 columns (features + target)</li>
          </ul>
        </div>
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
