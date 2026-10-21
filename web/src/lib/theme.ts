import type { Category } from "./api";

export const RISK = {
  low: { hex: "#34d399", text: "text-emerald-300", bg: "bg-emerald-400/10", ring: "ring-emerald-400/30", label: "Low" },
  mid: { hex: "#fbbf24", text: "text-amber-300", bg: "bg-amber-400/10", ring: "ring-amber-400/30", label: "Indeterminate" },
  high: { hex: "#fb7185", text: "text-rose-300", bg: "bg-rose-400/10", ring: "ring-rose-400/30", label: "High" },
  none: { hex: "#64748b", text: "text-slate-400", bg: "bg-slate-400/10", ring: "ring-slate-400/20", label: "Unknown" },
} as const;

export type Tone = keyof typeof RISK;

export function toneOf(c: Category | "moderate"): Tone {
  if (c === "low" || c === "rule_out") return "low";
  if (c === "high" || c === "rule_in") return "high";
  if (c === "indeterminate" || c === "moderate") return "mid";
  return "none";
}

export const CATEGORY_LABEL: Record<Category, string> = {
  low: "Low risk",
  rule_out: "Ruled out",
  indeterminate: "Indeterminate",
  high: "High risk",
  rule_in: "Likely",
  unknown: "Needs data",
};

/** LiverTox likelihood grade -> tone; A is the strongest evidence of liver injury. */
export function likelihoodTone(g: string | null | undefined): Tone {
  if (!g) return "none";
  if (g.startsWith("A") || g.startsWith("B")) return "high";
  if (g.startsWith("C") || g.startsWith("D")) return "mid";
  if (g.startsWith("E")) return "low";
  return "none";
}

export const LIKELIHOOD_TEXT: Record<string, string> = {
  A: "Well-established cause of liver injury",
  B: "Highly likely cause",
  C: "Probable cause",
  D: "Possible rare cause",
  "D*": "Possible rare cause",
  E: "Unlikely cause",
  "E*": "Unproven, suspected rare cause",
  X: "Unknown",
};

/** Upper bounds used to place each score on its gauge (cut-offs drawn as ticks). */
export const GAUGE: Record<string, { max: number; ticks: number[]; min?: number }> = {
  "FIB-4": { max: 4, ticks: [1.3, 2.67] },
  "NAFLD Fibrosis Score": { min: -4, max: 2, ticks: [-1.455, 0.676] },
  "Fatty Liver Index": { max: 100, ticks: [30, 60] },
  "Hepatic Steatosis Index": { min: 20, max: 50, ticks: [30, 36] },
  APRI: { max: 2, ticks: [0.5, 1.5] },
};

export const SHORT_NAME: Record<string, string> = {
  "FIB-4": "FIB-4",
  "NAFLD Fibrosis Score": "NFS",
  "Fatty Liver Index": "FLI",
  "Hepatic Steatosis Index": "HSI",
  APRI: "APRI",
};
