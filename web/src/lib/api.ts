// Typed client for the Liver Buddy API (served under /api).

export type Category = "low" | "indeterminate" | "high" | "rule_out" | "rule_in" | "unknown";

export interface ScoreResult {
  name: string;
  value: number | null;
  category: Category;
  interpretation: string;
  missing_inputs: string[];
  reference: string;
}
export interface Criteria {
  met_count: number;
  summary: string;
  alcohol_category: string;
  overweight_or_central_obesity: boolean | null;
  dysglycaemia: boolean | null;
  hypertension: boolean | null;
  hypertriglyceridaemia: boolean | null;
  low_hdl: boolean | null;
}
export interface ScorePanel {
  bmi: number | null;
  scores: ScoreResult[];
  criteria: Criteria;
  next_step: string;
}
export interface Driver {
  feature: string;
  label: string;
  value: number | null;
  contribution: number;
}
export interface RiskPrediction {
  task: "steatosis" | "fibrosis";
  probability: number;
  band: "low" | "moderate" | "high";
  model_variant: "full" | "basic";
  outcome: string;
  drivers: Driver[];
  test_auroc: number;
  note: string;
}
export interface Measures {
  age?: number | null;
  sex?: "male" | "female" | null;
  height_cm?: number | null;
  weight_kg?: number | null;
  waist_cm?: number | null;
  alt?: number | null;
  ast?: number | null;
  ggt?: number | null;
  platelets?: number | null;
  albumin?: number | null;
  triglycerides?: number | null;
  hdl?: number | null;
  fasting_glucose?: number | null;
  hba1c?: number | null;
  type2_diabetes?: boolean;
  on_antihypertensives?: boolean;
  asian_ethnicity?: boolean;
}
export interface Summary {
  measures: Measures & { bmi?: number };
  panel: ScorePanel;
  steatosis: RiskPrediction | null;
  fibrosis: RiskPrediction | null;
}
export interface Profile {
  display_name: string;
  sex: "male" | "female" | null;
  birth_year: number | null;
  height_cm: number | null;
  asian_ethnicity: boolean;
  type2_diabetes: boolean;
  on_antihypertensives: boolean;
  on_lipid_lowering: boolean;
  alcohol_g_per_week: number | null;
}
export type LabRow = { taken_on: string; fib4: number | null } & Record<string, number | string | null>;
export interface Measurement {
  taken_on: string;
  weight_kg: number | null;
  waist_cm: number | null;
  systolic_bp: number | null;
  diastolic_bp: number | null;
}
export interface MealLog {
  id: number;
  eaten_at: string;
  description: string;
  score: number;
  kcal: number;
}
export interface Nutrients {
  kcal: number;
  protein_g: number;
  fat_g: number;
  carbs_g: number;
  fiber_g: number;
  sugars_g: number;
  sat_fat_g: number;
  sodium_mg: number;
}
export interface MealAnalysis {
  items: {
    name: string;
    grams: number;
    food_group: string;
    cooking: string;
    ultra_processed: boolean;
    usda_match: { description: string; fdc_id: number; confidence: number } | null;
    nutrients: Nutrients;
  }[];
  totals: Nutrients;
  diet: { score: number; verdict: "Excellent" | "Good" | "Fair" | "Poor"; adjustments: { points: number; reason: string }[]; basis: string };
  unmatched: string[];
  source: string;
}
export interface DrugRecord {
  id: string;
  name: string;
  trade_names: string[];
  drug_class: string;
  likelihood: string;
  summary: string;
  url: string;
}
export interface DrugLookup {
  query: string;
  matched: boolean;
  match_score: number;
  record: DrugRecord | null;
  category_meaning: string | null;
  alternatives: string[];
  note: string;
}
export interface Medication {
  id: number;
  name: string;
  dose_text: string;
  livertox_name: string | null;
  likelihood: string | null;
}
export interface Citation {
  n: number;
  chunk_id: string;
  title: string;
  section: string;
  url: string;
  excerpt: string;
}
export interface ToolTrace {
  name: string;
  arguments: Record<string, unknown>;
  result_preview: string;
  latency_ms: number;
  error: string | null;
}
export interface CopilotReply {
  answer: string;
  guardrail: "allow" | "caution_medication" | "emergency" | "urgent" | "crisis" | "refuse_dosing";
  tools: ToolTrace[];
  citations: Citation[];
  removed_invalid_citations: number[];
  output_filtered: boolean;
  steps: number;
}
export interface GroundedAnswer {
  question: string;
  answer: string;
  citations: Citation[];
  abstained: boolean;
  reason: string | null;
  top_similarity: number;
}
export interface Guardrail {
  action: CopilotReply["guardrail"];
  message: string | null;
  matched: string[];
}
export interface LabValue {
  analyte: string;
  value: number;
  unit: string;
  raw: string;
  method: "rule" | "llm";
}
export interface LabExtract {
  extraction: { values: Record<string, LabValue>; missing: string[]; warnings: string[] };
  panel: ScorePanel | null;
}

const TOKEN_KEY = "lb_token";

export const auth = {
  get token(): string | null {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  set(token: string | null) {
    try {
      if (token) localStorage.setItem(TOKEN_KEY, token);
      else localStorage.removeItem(TOKEN_KEY);
    } catch {
      /* storage unavailable: session-only */
    }
    window.dispatchEvent(new Event("lb-auth"));
  },
};

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(method: string, path: string, body?: unknown, form?: FormData): Promise<T> {
  const headers: Record<string, string> = {};
  const token = auth.token;
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";
  let res: Response;
  try {
    res = await fetch(`/api${path}`, { method, headers, body: form ?? (body !== undefined ? JSON.stringify(body) : undefined) });
  } catch {
    throw new ApiError(0, "Can't reach the Liver Buddy server. Is `liverbuddy serve` running?");
  }
  if (res.status === 401 && token) auth.set(null);
  if (!res.ok) {
    let msg = res.statusText;
    try {
      const j = await res.json();
      msg = typeof j.detail === "string" ? j.detail : Array.isArray(j.detail) ? j.detail.map((d: { msg: string }) => d.msg).join("; ") : msg;
    } catch {
      /* non-JSON error */
    }
    throw new ApiError(res.status, msg);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; version: string; llm_provider: string; resources: Record<string, boolean> }>("GET", "/health"),
  login: (email: string, password: string) => request<{ access_token: string }>("POST", "/auth/login", { email, password }),
  register: (email: string, password: string, display_name: string) =>
    request<{ access_token: string }>("POST", "/auth/register", { email, password, display_name }),
  demo: () => request<{ access_token: string }>("POST", "/auth/demo"),
  profile: () => request<Profile>("GET", "/me/profile"),
  saveProfile: (p: Profile) => request<Profile>("PUT", "/me/profile", p),
  summary: () => request<Summary>("GET", "/me/summary"),
  labs: () => request<LabRow[]>("GET", "/me/labs"),
  addLabs: (taken_on: string, values: Record<string, number>, source = "manual") =>
    request("POST", "/me/labs", { taken_on, values, source }),
  measurements: () => request<Measurement[]>("GET", "/me/measurements"),
  addMeasurement: (m: Measurement) => request("POST", "/me/measurements", m),
  meals: () => request<MealLog[]>("GET", "/me/meals"),
  meds: () => request<Medication[]>("GET", "/me/medications"),
  addMed: (name: string, dose_text = "") => request<{ id: number; lookup: DrugLookup }>("POST", "/me/medications", { name, dose_text }),
  removeMed: (id: number) => request("DELETE", `/me/medications/${id}`),
  drug: (q: string) => request<DrugLookup>("GET", `/drugs/lookup?q=${encodeURIComponent(q)}`),
  scores: (m: Measures) => request<ScorePanel>("POST", "/scores", m),
  risk: (measures: Measures, task: "steatosis" | "fibrosis") => request<RiskPrediction>("POST", "/risk", { measures, task }),
  ask: (question: string) => request<{ guardrail: Guardrail; answer: GroundedAnswer | null }>("POST", "/guidelines/ask", { question }),
  copilot: (question: string, history: { role: string; content: string }[]) =>
    request<CopilotReply>("POST", "/copilot", { question, history }),
  analyzeMeal: (fd: FormData) => request<MealAnalysis>("POST", "/meals/analyze", undefined, fd),
  extractLabs: (fd: FormData) => request<LabExtract>("POST", "/labs/extract", undefined, fd),
};
