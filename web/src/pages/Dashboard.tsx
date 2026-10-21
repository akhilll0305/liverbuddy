import { motion } from "framer-motion";
import { ArrowDownRight, ArrowUpRight, FlaskConical, LineChart, Pill, Salad, Scale, Sparkles, UtensilsCrossed } from "lucide-react";
import { useMemo, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAsync, useAuth } from "../lib/hooks";
import { likelihoodTone } from "../lib/theme";
import { NextStep, RiskCard, ScoreGauges, TrendChart } from "../components/clinical";
import { AnimatedNumber, Badge, Button, Card, CardTitle, Disclaimer, EmptyState, ErrorNote, PageHeader, Segmented, Skeleton, cx, rise, stagger } from "../components/ui";

function greeting() {
  const h = new Date().getHours();
  return h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening";
}

function Kpi({ icon, label, value, decimals = 0, suffix = "", delta, goodWhenDown = true, sub }: {
  icon: ReactNode; label: string; value: number | null; decimals?: number; suffix?: string; delta?: number | null; goodWhenDown?: boolean; sub?: string;
}) {
  const good = delta == null ? null : goodWhenDown ? delta < 0 : delta > 0;
  return (
    <motion.div variants={rise} className="glass glass-hover p-4">
      <div className="mb-3 flex items-center justify-between">
        <span className="label">{label}</span>
        <span className="text-slate-500 [&>svg]:h-4 [&>svg]:w-4">{icon}</span>
      </div>
      <div className="flex items-end justify-between gap-2">
        <div className="font-display text-3xl font-bold text-white">
          {value === null ? <span className="text-slate-500">—</span> : <AnimatedNumber value={value} decimals={decimals} suffix={suffix} />}
        </div>
        {delta != null && delta !== 0 && (
          <span className={cx("mb-1 inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-[11px] font-semibold",
            good ? "bg-emerald-400/10 text-emerald-300" : "bg-rose-400/10 text-rose-300")}>
            {delta < 0 ? <ArrowDownRight className="h-3.5 w-3.5" /> : <ArrowUpRight className="h-3.5 w-3.5" />}
            {Math.abs(delta).toFixed(decimals)}{suffix}
          </span>
        )}
      </div>
      {sub && <div className="mt-1 text-[11px] text-slate-500">{sub}</div>}
    </motion.div>
  );
}

export default function Dashboard() {
  const { signedIn } = useAuth();
  const summary = useAsync(api.summary, [], signedIn);
  const labs = useAsync(api.labs, [], signedIn);
  const body = useAsync(api.measurements, [], signedIn);
  const meals = useAsync(api.meals, [], signedIn);
  const meds = useAsync(api.meds, [], signedIn);
  const profile = useAsync(api.profile, [], signedIn);
  const [series, setSeries] = useState<"fib4" | "alt" | "triglycerides" | "hba1c" | "weight_kg">("fib4");

  const first = labs.data?.[0];
  const last = labs.data?.[labs.data.length - 1];
  const delta = (k: string) => (first && last && labs.data!.length > 1 && typeof first[k] === "number" && typeof last[k] === "number"
    ? (last[k] as number) - (first[k] as number) : null);
  const weights = body.data?.filter((m) => m.weight_kg != null) ?? [];
  const avgMeal = meals.data?.length ? meals.data.slice(0, 7).reduce((s, m) => s + m.score, 0) / Math.min(7, meals.data.length) : null;
  const chartData = useMemo(
    () => (series === "weight_kg" ? weights.map((w) => ({ taken_on: w.taken_on, weight_kg: w.weight_kg })) : labs.data ?? []),
    [series, weights, labs.data],
  );

  if (!signedIn) {
    return (
      <Card className="mt-10">
        <EmptyState icon={<LineChart className="h-6 w-6" />} title="Your dashboard lives here"
          text="Sign in to track FIB-4, labs, weight, meals and medicines over time, or explore a demo patient."
          action={<div className="flex gap-2"><Link to="/login"><Button>Sign in</Button></Link><Link to="/"><Button variant="outline">Back home</Button></Link></div>} />
      </Card>
    );
  }

  const name = profile.data?.display_name?.split(" ")[0];
  return (
    <>
      <PageHeader eyebrow={new Date().toLocaleDateString(undefined, { weekday: "long", day: "numeric", month: "long" })}
        title={<>{greeting()}{name ? <>, <span className="text-gradient">{name}</span></> : ""}</>}
        sub="Your liver health at a glance: validated scores, an explainable risk estimate and your trends."
        action={<div className="flex gap-2">
          <Link to="/app/labs"><Button variant="outline" size="sm" icon={<FlaskConical className="h-4 w-4" />}>Add labs</Button></Link>
          <Link to="/app/chat"><Button size="sm" icon={<Sparkles className="h-4 w-4" />}>Ask Liver Buddy</Button></Link>
        </div>} />

      <ErrorNote error={summary.error} />

      <motion.div variants={stagger} initial="hidden" animate="show" className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Kpi icon={<LineChart />} label="FIB-4" value={(last?.fib4 as number) ?? null} decimals={2} delta={delta("fib4")} sub="since first test" />
        <Kpi icon={<FlaskConical />} label="ALT (U/L)" value={(last?.alt as number) ?? null} delta={delta("alt")} sub="normal ≤ 30 (AASLD)" />
        <Kpi icon={<Scale />} label="Weight (kg)" value={weights.at(-1)?.weight_kg ?? null} decimals={1}
          delta={weights.length > 1 ? weights.at(-1)!.weight_kg! - weights[0].weight_kg! : null}
          sub={weights.length > 1 ? `${(((weights[0].weight_kg! - weights.at(-1)!.weight_kg!) / weights[0].weight_kg!) * 100).toFixed(1)}% lost · goal 7–10%` : undefined} />
        <Kpi icon={<UtensilsCrossed />} label="Meal score" value={avgMeal} goodWhenDown={false} sub="average of recent meals" />
      </motion.div>

      {summary.loading && !summary.data ? (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-5">{[...Array(5)].map((_, i) => <Skeleton key={i} className="h-52" />)}</div>
      ) : summary.data && (
        <div className="space-y-6">
          <ScoreGauges panel={summary.data.panel} />
          <NextStep panel={summary.data.panel} />
          <div className="grid gap-4 lg:grid-cols-2">
            {summary.data.steatosis && <RiskCard pred={summary.data.steatosis} title="Liver fat" />}
            {summary.data.fibrosis && <RiskCard pred={summary.data.fibrosis} title="Liver stiffness" />}
          </div>
        </div>
      )}

      <Card className="mt-6" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
        <CardTitle icon={<LineChart className="h-4 w-4" />} title="Trends" sub="Dashed line shows the guideline threshold"
          action={<Segmented id="series" value={series} onChange={setSeries} options={[
            { value: "fib4", label: "FIB-4" }, { value: "alt", label: "ALT" }, { value: "triglycerides", label: "TG" },
            { value: "hba1c", label: "HbA1c" }, { value: "weight_kg", label: "Weight" },
          ]} />} />
        {chartData.length ? <TrendChart key={series} data={chartData as Record<string, unknown>[]} series={series} height={260} />
          : <EmptyState icon={<FlaskConical className="h-6 w-6" />} title="No results yet" text="Upload a lab report to start your trend lines."
              action={<Link to="/app/labs"><Button size="sm">Upload labs</Button></Link>} />}
      </Card>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card>
          <CardTitle icon={<Salad className="h-4 w-4" />} title="Recent meals" action={<Link to="/app/meals" className="text-xs text-brand-300 hover:underline">Analyse a meal →</Link>} />
          {meals.data?.length ? (
            <ul className="space-y-2">
              {meals.data.slice(0, 5).map((m, i) => (
                <motion.li key={m.id} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}
                  className="flex items-center gap-3 rounded-xl bg-white/[0.025] px-3 py-2.5 ring-1 ring-white/[0.04]">
                  <span className={cx("grid h-9 w-9 shrink-0 place-items-center rounded-lg font-display text-sm font-bold",
                    m.score >= 80 ? "bg-emerald-400/15 text-emerald-300" : m.score >= 50 ? "bg-amber-400/15 text-amber-300" : "bg-rose-400/15 text-rose-300")}>{m.score}</span>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm text-slate-200">{m.description}</div>
                    <div className="text-[11px] text-slate-500">{new Date(m.eaten_at).toLocaleString(undefined, { weekday: "short", hour: "numeric", minute: "2-digit" })} · {Math.round(m.kcal)} kcal</div>
                  </div>
                </motion.li>
              ))}
            </ul>
          ) : <p className="py-6 text-center text-sm text-slate-500">No meals logged yet.</p>}
        </Card>
        <Card>
          <CardTitle icon={<Pill className="h-4 w-4" />} title="Medicines · liver safety" action={<Link to="/app/meds" className="text-xs text-brand-300 hover:underline">Manage →</Link>} />
          {meds.data?.length ? (
            <ul className="space-y-2">
              {meds.data.map((m, i) => (
                <motion.li key={m.id} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}
                  className="flex items-center justify-between gap-3 rounded-xl bg-white/[0.025] px-3 py-2.5 ring-1 ring-white/[0.04]">
                  <div className="min-w-0">
                    <div className="truncate text-sm text-slate-200">{m.name} {m.dose_text && <span className="text-slate-500">· {m.dose_text}</span>}</div>
                    <div className="text-[11px] text-slate-500">{m.livertox_name ?? "Not in LiverTox"}</div>
                  </div>
                  <Badge tone={likelihoodTone(m.likelihood)}>LiverTox {m.likelihood ?? "–"}</Badge>
                </motion.li>
              ))}
            </ul>
          ) : <p className="py-6 text-center text-sm text-slate-500">No medicines added.</p>}
        </Card>
      </div>
      <Disclaimer />
    </>
  );
}
