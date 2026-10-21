import { motion } from "framer-motion";
import { ArrowRight, BrainCircuit, CheckCircle2, CircleDashed, XCircle } from "lucide-react";
import { Area, AreaChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { RiskPrediction, ScorePanel } from "../lib/api";
import { CATEGORY_LABEL, GAUGE, RISK, SHORT_NAME, toneOf } from "../lib/theme";
import { AnimatedNumber, Badge, Card, Gauge, Ring, rise, stagger } from "./ui";

/* ---------------------------------------------------------------- score gauges */
export function ScoreGauges({ panel }: { panel: ScorePanel }) {
  return (
    <motion.div variants={stagger} initial="hidden" animate="show" className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
      {panel.scores.map((s) => {
        const g = GAUGE[s.name] ?? { max: Math.max(1, (s.value ?? 1) * 2), ticks: [] };
        const tone = toneOf(s.category);
        return (
          <motion.div key={s.name} variants={rise} className="glass glass-hover group flex flex-col items-center p-4 text-center">
            <div className="mb-2 flex w-full items-center justify-between">
              <span className="font-display text-sm font-semibold text-white">{SHORT_NAME[s.name] ?? s.name}</span>
              <Badge tone={tone}>{CATEGORY_LABEL[s.category]}</Badge>
            </div>
            <Gauge value={s.value} min={g.min} max={g.max} ticks={g.ticks} tone={tone} size={128} />
            <p className="mt-2 line-clamp-3 min-h-[3.2em] text-[11.5px] leading-snug text-slate-400">
              {s.value === null ? `Needs ${s.missing_inputs.join(", ")}` : s.interpretation}
            </p>
          </motion.div>
        );
      })}
    </motion.div>
  );
}

export function NextStep({ panel }: { panel: ScorePanel }) {
  const c = panel.criteria;
  const crit: [string, boolean | null][] = [
    ["Weight / waist", c.overweight_or_central_obesity], ["Blood sugar", c.dysglycaemia], ["Blood pressure", c.hypertension],
    ["Triglycerides", c.hypertriglyceridaemia], ["HDL cholesterol", c.low_hdl],
  ];
  return (
    <Card className="flex flex-col gap-5 md:flex-row md:items-center" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="flex-1">
        <div className="label mb-2">Recommended next step · EASL 2024 pathway</div>
        <p className="flex gap-2 text-[15px] leading-relaxed text-slate-100">
          <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-brand-300" />
          {panel.next_step}
        </p>
      </div>
      <div className="md:w-[360px]">
        <div className="label mb-2">MASLD cardiometabolic criteria · {c.met_count}/5 met</div>
        <div className="flex flex-wrap gap-1.5">
          {crit.map(([name, v]) => (
            <span key={name} className={`chip ${v ? "!border-amber-400/30 !text-amber-200" : ""}`}>
              {v === true ? <CheckCircle2 className="h-3.5 w-3.5 text-amber-300" /> : v === false ? <XCircle className="h-3.5 w-3.5 text-emerald-300" /> : <CircleDashed className="h-3.5 w-3.5 text-slate-500" />}
              {name}
            </span>
          ))}
        </div>
      </div>
    </Card>
  );
}

/* ---------------------------------------------------------------- ML risk */
export function RiskCard({ pred, title }: { pred: RiskPrediction; title: string }) {
  const tone = toneOf(pred.band);
  const color = RISK[tone].hex;
  const maxAbs = Math.max(0.01, ...pred.drivers.map((d) => Math.abs(d.contribution)));
  return (
    <Card hover className="h-full" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
      <div className="flex items-start gap-5">
        <Ring value={pred.probability} color={color} size={112}>
          <div className="text-center">
            <div className="font-display text-2xl font-bold text-white"><AnimatedNumber value={pred.probability * 100} suffix="%" /></div>
            <div className="text-[10px] uppercase tracking-wider text-slate-400">probability</div>
          </div>
        </Ring>
        <div className="min-w-0 flex-1">
          <div className="mb-1 flex items-center gap-2">
            <h3 className="text-base font-semibold">{title}</h3>
            <Badge tone={tone}>{pred.band}</Badge>
          </div>
          <p className="text-xs text-slate-400">Chance of {pred.outcome}</p>
          <div className="mt-3 flex flex-wrap gap-1.5">
            <span className="chip"><BrainCircuit className="h-3.5 w-3.5 text-brand-300" />XGBoost · {pred.model_variant === "full" ? "with labs" : "no-labs model"}</span>
            <span className="chip">AUROC {pred.test_auroc}</span>
          </div>
        </div>
      </div>
      {pred.drivers.length > 0 && (
        <div className="mt-5">
          <div className="label mb-2.5">What drives this estimate · TreeSHAP</div>
          <div className="space-y-2">
            {pred.drivers.map((d, i) => {
              const up = d.contribution > 0;
              const w = (Math.abs(d.contribution) / maxAbs) * 50;
              return (
                <div key={d.feature} className="grid grid-cols-[120px_1fr] items-center gap-3 text-xs">
                  <span className="truncate text-slate-300">{d.label}{d.value !== null && <span className="text-slate-500"> · {d.value}</span>}</span>
                  <div className="relative h-5">
                    <div className="absolute left-1/2 top-0 h-full w-px bg-white/15" />
                    <motion.div className="absolute top-1 h-3 rounded-full"
                      style={{ background: up ? "linear-gradient(90deg,#fb718599,#fb7185)" : "linear-gradient(270deg,#34d39999,#34d399)",
                        [up ? "left" : "right"]: "50%" }}
                      initial={{ width: 0 }} animate={{ width: `${w}%` }}
                      transition={{ duration: 0.9, delay: 0.2 + i * 0.08, ease: [0.16, 1, 0.3, 1] }} />
                  </div>
                </div>
              );
            })}
          </div>
          <div className="mt-2 flex justify-between text-[10px] uppercase tracking-wider text-slate-500">
            <span className="text-emerald-400/80">lowers risk</span><span className="text-rose-400/80">raises risk</span>
          </div>
        </div>
      )}
      <p className="mt-4 text-[11px] leading-relaxed text-slate-500">{pred.note}</p>
    </Card>
  );
}

/* ---------------------------------------------------------------- trend chart */
const SERIES: Record<string, { label: string; color: string; ref?: number }> = {
  fib4: { label: "FIB-4", color: "#34e0b0", ref: 1.3 },
  alt: { label: "ALT", color: "#5cc8ff", ref: 30 },
  ast: { label: "AST", color: "#a78bfa" },
  ggt: { label: "GGT", color: "#f472b6" },
  triglycerides: { label: "Triglycerides", color: "#fbbf24", ref: 150 },
  hba1c: { label: "HbA1c", color: "#fb7185", ref: 5.7 },
  weight_kg: { label: "Weight", color: "#34e0b0" },
  waist_cm: { label: "Waist", color: "#5cc8ff" },
};

export function TrendChart({ data, series, height = 220 }: { data: Record<string, unknown>[]; series: string; height?: number }) {
  const s = SERIES[series];
  const gid = `trend-${series}`;
  const fmt = (d: string) => new Date(d).toLocaleDateString(undefined, { month: "short", year: "2-digit" });
  return (
    <motion.div initial={{ opacity: 0, clipPath: "inset(0 100% 0 0)" }} animate={{ opacity: 1, clipPath: "inset(0 0% 0 0)" }}
      transition={{ duration: 1.4, ease: [0.16, 1, 0.3, 1] }}>
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 10, right: 12, left: -18, bottom: 0 }}>
        <defs>
          <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={s.color} stopOpacity={0.35} />
            <stop offset="100%" stopColor={s.color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="rgba(255,255,255,.05)" vertical={false} />
        <XAxis dataKey="taken_on" tickFormatter={fmt} tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} domain={["auto", "auto"]} />
        <Tooltip
          cursor={{ stroke: "rgba(255,255,255,.15)" }}
          contentStyle={{ background: "rgba(14,20,36,.95)", border: "1px solid rgba(255,255,255,.1)", borderRadius: 12, fontSize: 12 }}
          labelFormatter={(l) => new Date(String(l)).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })}
          formatter={(v) => [v as number, s.label]}
        />
        {s.ref !== undefined && (
          <ReferenceLine y={s.ref} stroke="rgba(255,255,255,.3)" strokeDasharray="4 4"
            label={{ value: `${s.ref}`, fill: "#94a3b8", fontSize: 10, position: "insideTopRight" }} />
        )}
        <Area type="monotone" dataKey={series} stroke={s.color} strokeWidth={2.5} fill={`url(#${gid})`} connectNulls
          dot={{ r: 3.5, fill: s.color, strokeWidth: 0 }} activeDot={{ r: 6, strokeWidth: 2, stroke: "#05070d" }}
          isAnimationActive={false} />
      </AreaChart>
    </ResponsiveContainer>
    </motion.div>
  );
}

export const TREND_SERIES = SERIES;
