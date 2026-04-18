"use client";

import { ChangeEvent, Dispatch, FormEvent, SetStateAction, useEffect, useMemo, useState } from "react";

import { getSimulateSchema, simulate } from "@/lib/api";
import { SimulateField, SimulateResponse, SimulateSchemaResponse } from "@/lib/types";

type ProfileForm = Record<string, string>;

const defaultProfile: ProfileForm = {
  gender: "female",
  region: "rural",
  income: "38000",
  education: "high_school",
  age: "29",
};

const FALLBACK_FIELDS: SimulateField[] = [
  { name: "gender", label: "Gender", type: "categorical", options: ["female", "male"], default: "female" },
  { name: "region", label: "Region", type: "categorical", options: ["rural", "urban", "suburban"], default: "rural" },
  { name: "income", label: "Income", type: "numeric", default: 38000 },
  { name: "education", label: "Education", type: "categorical", options: ["high_school", "bachelors", "masters"], default: "high_school" },
  { name: "age", label: "Age", type: "numeric", default: 29 },
];

function profileFromFields(fields: SimulateField[], overrides?: Record<string, string>): ProfileForm {
  const profile: ProfileForm = {};
  for (const field of fields) {
    const defaultValue = overrides?.[field.name] ?? String(field.default ?? "");
    profile[field.name] = defaultValue;
  }
  return profile;
}

function toPayload(profile: ProfileForm, fields: SimulateField[]): Record<string, string | number> {
  const payload: Record<string, string | number> = {};
  for (const field of fields) {
    const rawValue = profile[field.name] ?? "";
    if (field.type === "numeric") {
      const numericValue = Number(rawValue);
      payload[field.name] = Number.isNaN(numericValue) ? 0 : numericValue;
    } else {
      payload[field.name] = rawValue;
    }
  }
  return payload;
}

export default function SimulatorPage() {
  const [fields, setFields] = useState<SimulateField[]>(FALLBACK_FIELDS);
  const [baseline, setBaseline] = useState<ProfileForm>(defaultProfile);
  const [scenario, setScenario] = useState<ProfileForm>({ ...defaultProfile, gender: "male" });
  const [schemaInfo, setSchemaInfo] = useState<SimulateSchemaResponse | null>(null);
  const [schemaLoading, setSchemaLoading] = useState(true);
  const [result, setResult] = useState<SimulateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const datasetPath = useMemo(
    () => (typeof window === "undefined" ? "" : localStorage.getItem("biasxray_dataset_path") ?? ""),
    [],
  );

  useEffect(() => {
    let mounted = true;

    const loadSchema = async () => {
      try {
        setSchemaLoading(true);
        const schema = await getSimulateSchema(datasetPath ? { dataset_path: datasetPath } : undefined);
        if (!mounted) {
          return;
        }

        const dynamicFields = schema.fields.length > 0 ? schema.fields : FALLBACK_FIELDS;
        setFields(dynamicFields);
        setBaseline(profileFromFields(dynamicFields));

        const scenarioOverrides: Record<string, string> = {};
        if (dynamicFields.some((field) => field.name === "gender")) {
          scenarioOverrides.gender = "male";
        }
        setScenario(profileFromFields(dynamicFields, scenarioOverrides));
        setSchemaInfo(schema);
      } catch {
        if (!mounted) {
          return;
        }
        setFields(FALLBACK_FIELDS);
        setBaseline({ ...defaultProfile });
        setScenario({ ...defaultProfile, gender: "male" });
        setSchemaInfo(null);
      } finally {
        if (mounted) {
          setSchemaLoading(false);
        }
      }
    };

    void loadSchema();
    return () => {
      mounted = false;
    };
  }, [datasetPath]);

  const update =
    (stateSetter: Dispatch<SetStateAction<ProfileForm>>) =>
    (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      const { name, value } = event.target;
      stateSetter((prev) => ({ ...prev, [name]: value }));
    };

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();

    try {
      setLoading(true);
      setError(null);

      const response = await simulate({
        dataset_path: schemaInfo?.dataset_path ?? datasetPath,
        target_column: schemaInfo?.target_column,
        baseline_features: toPayload(baseline, fields),
        scenario_features: toPayload(scenario, fields),
      });
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Simulation failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="space-y-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="font-display text-3xl font-semibold text-slate-900">What-If Simulator</h1>
        <p className="mt-2 text-sm text-slate-600">
          Compare a baseline profile against a changed profile to test fairness sensitivity.
        </p>
        {schemaInfo ? (
          <p className="mt-2 text-xs text-slate-500">
            Active target: <strong>{schemaInfo.target_column}</strong>
          </p>
        ) : (
          <p className="mt-2 text-xs text-slate-500">Using fallback demo form until a dataset is uploaded.</p>
        )}
      </div>

      {schemaLoading && <div className="rounded-lg bg-slate-100 px-4 py-3 text-sm text-slate-600">Loading latest dataset schema...</div>}

      <form onSubmit={onSubmit} className="grid gap-4 lg:grid-cols-2">
        {[{ title: "Baseline Profile", state: baseline, set: setBaseline }, { title: "Scenario Profile", state: scenario, set: setScenario }].map((pane) => (
          <div key={pane.title} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="font-display text-lg font-semibold text-slate-900">{pane.title}</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {fields.map((field) => (
                <label key={`${pane.title}-${field.name}`} className="text-sm text-slate-600">
                  {field.label}
                  {field.type === "categorical" ? (
                    <select
                      name={field.name}
                      value={pane.state[field.name] ?? ""}
                      onChange={update(pane.set)}
                      className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
                    >
                      {(field.options ?? []).map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      name={field.name}
                      value={pane.state[field.name] ?? ""}
                      onChange={update(pane.set)}
                      type="number"
                      className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
                    />
                  )}
                </label>
              ))}
            </div>
          </div>
        ))}

        <div className="lg:col-span-2">
          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-teal-600 px-5 py-3 text-sm font-semibold text-white hover:bg-teal-700 disabled:cursor-not-allowed disabled:bg-teal-300"
          >
            {loading ? "Simulating..." : "Run Simulation"}
          </button>
        </div>
      </form>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      )}

      {result && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="font-display text-xl font-semibold text-slate-900">Simulation Result</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl bg-slate-100 p-4">
              <p className="text-xs uppercase tracking-wide text-slate-500">Baseline</p>
              <p className="mt-1 text-lg font-semibold text-slate-900">Prediction: {result.baseline.prediction}</p>
              <p className="text-sm text-slate-600">Probability: {result.baseline.probability}</p>
            </div>
            <div className="rounded-xl bg-slate-100 p-4">
              <p className="text-xs uppercase tracking-wide text-slate-500">Scenario</p>
              <p className="mt-1 text-lg font-semibold text-slate-900">Prediction: {result.scenario.prediction}</p>
              <p className="text-sm text-slate-600">Probability: {result.scenario.probability}</p>
            </div>
          </div>
          <p className="mt-4 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800">{result.message}</p>
        </div>
      )}
    </section>
  );
}
