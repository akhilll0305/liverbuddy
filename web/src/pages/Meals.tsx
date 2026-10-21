import { AnimatePresence, motion } from "framer-motion";
import { Camera, ImagePlus, Minus, Plus, Salad, Sparkles, Type, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { api, type MealAnalysis } from "../lib/api";
import { errorText, useAuth, useToast } from "../lib/hooks";
import { AnimatedNumber, Button, Card, CardTitle, Disclaimer, ErrorNote, PageHeader, Ring, Segmented, Toggle, cx } from "../components/ui";

const EXAMPLES = ["2 rotis, a bowl of dal and cucumber salad", "Chicken biryani with raita and a cola", "Grilled salmon, steamed broccoli and brown rice"];
// per-meal reference amounts (about one third of daily guidance)
const NUTRIENTS: { key: keyof MealAnalysis["totals"]; label: string; unit: string; ref: number; goodHigh?: boolean }[] = [
  { key: "kcal", label: "Energy", unit: "kcal", ref: 700 },
  { key: "protein_g", label: "Protein", unit: "g", ref: 30, goodHigh: true },
  { key: "fiber_g", label: "Fibre", unit: "g", ref: 10, goodHigh: true },
  { key: "sugars_g", label: "Sugars", unit: "g", ref: 25 },
  { key: "sat_fat_g", label: "Saturated fat", unit: "g", ref: 7 },
  { key: "sodium_mg", label: "Sodium", unit: "mg", ref: 800 },
];
const VERDICT_COLOR = { Excellent: "#34d399", Good: "#5cc8ff", Fair: "#fbbf24", Poor: "#fb7185" };

export default function Meals() {
  const { signedIn } = useAuth();
  const toast = useToast();
  const [mode, setMode] = useState<"text" | "photo">("text");
  const [text, setText] = useState("");
  const [photo, setPhoto] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [portion, setPortion] = useState<"small" | "medium" | "large">("medium");
  const [save, setSave] = useState(signedIn);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [res, setRes] = useState<MealAnalysis | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!photo) return setPreview(null);
    const url = URL.createObjectURL(photo);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [photo]);

  const analyse = async () => {
    setBusy(true);
    setError(null);
    const fd = new FormData();
    if (mode === "text") fd.append("description", text);
    if (mode === "photo" && photo) fd.append("image", photo);
    fd.append("portion", portion);
    fd.append("save", String(signedIn && save));
    try {
      const r = await api.analyzeMeal(fd);
      setRes(r);
      if (signedIn && save) toast("ok", "Meal saved to your log.");
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  };

  const ready = mode === "text" ? text.trim().length > 2 : !!photo;
  const color = res ? VERDICT_COLOR[res.diet.verdict] : "#34d399";
  return (
    <>
      <PageHeader eyebrow="Meal analyser" title={<>Is this meal <span className="text-gradient">liver-friendly?</span></>}
        sub="The AI identifies the foods and estimates portions. Every nutrient comes from USDA FoodData Central, and the score follows explicit rules drawn from the EASL and AASLD diet advice." />

      <div className="grid gap-6 lg:grid-cols-[1fr_1.1fr]">
        <Card initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} className="h-fit">
          <div className="mb-5"><Segmented id="mealmode" value={mode} onChange={setMode}
            options={[{ value: "text", label: "Describe", icon: <Type className="h-4 w-4" /> }, { value: "photo", label: "Photo", icon: <Camera className="h-4 w-4" /> }]} /></div>
          <AnimatePresence mode="wait">
            {mode === "text" ? (
              <motion.div key="t" initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 10 }}>
                <textarea className="input min-h-[120px]" value={text} onChange={(e) => setText(e.target.value)} placeholder="What did you eat? e.g. 2 rotis, dal, salad…" />
                <div className="mt-3 flex flex-wrap gap-2">
                  {EXAMPLES.map((e) => <button key={e} onClick={() => setText(e)} className="chip transition hover:border-brand-300/40 hover:text-white">{e}</button>)}
                </div>
              </motion.div>
            ) : (
              <motion.div key="p" initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 10 }}>
                <input ref={fileRef} type="file" accept="image/*" hidden onChange={(e) => setPhoto(e.target.files?.[0] ?? null)} />
                {preview ? (
                  <div className="relative overflow-hidden rounded-2xl ring-1 ring-white/10">
                    <img src={preview} alt="Meal" className="h-64 w-full object-cover" />
                    <button onClick={() => setPhoto(null)} className="absolute right-3 top-3 rounded-full bg-black/60 p-1.5 text-white backdrop-blur hover:bg-black/80"><X className="h-4 w-4" /></button>
                  </div>
                ) : (
                  <button onClick={() => fileRef.current?.click()}
                    className="grid h-64 w-full place-items-center rounded-2xl border-2 border-dashed border-white/10 text-slate-400 transition hover:border-brand-300/40 hover:text-white">
                    <div className="text-center"><ImagePlus className="mx-auto mb-3 h-8 w-8 text-brand-300" />Add a photo of your plate</div>
                  </button>
                )}
                <p className="mt-2 text-[11px] text-slate-500">Photos need a vision model (local qwen2.5-VL or Gemini).</p>
              </motion.div>
            )}
          </AnimatePresence>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <div><div className="label mb-2">Portion</div>
              <Segmented id="portion" value={portion} onChange={setPortion}
                options={[{ value: "small", label: "Small" }, { value: "medium", label: "Medium" }, { value: "large", label: "Large" }]} /></div>
            {signedIn && <div className="self-end"><Toggle label="Save to my log" checked={save} onChange={setSave} /></div>}
          </div>
          <div className="mt-4"><ErrorNote error={error} /></div>
          <Button size="lg" className="mt-5 w-full" onClick={analyse} loading={busy} disabled={!ready} icon={<Sparkles className="h-4 w-4" />}>
            {busy ? "Analysing with USDA data…" : "Analyse meal"}
          </Button>
        </Card>

        <AnimatePresence mode="wait">
          {res ? (
            <motion.div key="res" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }} className="space-y-4">
              <Card>
                <div className="flex flex-wrap items-center gap-6">
                  <Ring value={res.diet.score / 100} size={140} stroke={12} color={color}>
                    <div className="text-center">
                      <div className="font-display text-4xl font-extrabold text-white"><AnimatedNumber value={res.diet.score} /></div>
                      <div className="text-[10px] uppercase tracking-wider text-slate-400">of 100</div>
                    </div>
                  </Ring>
                  <div className="flex-1">
                    <div className="label">Liver-diet score</div>
                    <div className="font-display text-3xl font-bold" style={{ color }}>{res.diet.verdict}</div>
                    <div className="mt-1 text-sm text-slate-400">{Math.round(res.totals.kcal)} kcal · {res.items.length} items identified</div>
                  </div>
                </div>
                <ul className="mt-5 space-y-2">
                  {res.diet.adjustments.map((a, i) => (
                    <motion.li key={i} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 + i * 0.06 }}
                      className="flex items-start gap-3 text-sm">
                      <span className={cx("mt-0.5 inline-flex shrink-0 items-center gap-0.5 rounded-md px-1.5 py-0.5 font-display text-xs font-bold",
                        a.points > 0 ? "bg-emerald-400/15 text-emerald-300" : "bg-rose-400/15 text-rose-300")}>
                        {a.points > 0 ? <Plus className="h-3 w-3" /> : <Minus className="h-3 w-3" />}{Math.abs(a.points)}
                      </span>
                      <span className="text-slate-300">{a.reason}</span>
                    </motion.li>
                  ))}
                </ul>
              </Card>
              <Card>
                <CardTitle title="Nutrients" sub="Bars compare this meal with roughly one third of daily guidance" />
                <div className="space-y-3">
                  {NUTRIENTS.map((n, i) => {
                    const v = res.totals[n.key];
                    const pct = Math.min(100, (v / n.ref) * 100);
                    const over = !n.goodHigh && v > n.ref;
                    return (
                      <div key={n.key}>
                        <div className="mb-1 flex justify-between text-xs"><span className="text-slate-300">{n.label}</span>
                          <span className={cx("font-medium", over ? "text-rose-300" : "text-slate-300")}>{Math.round(v)} {n.unit}</span></div>
                        <div className="h-2 overflow-hidden rounded-full bg-white/[0.06]">
                          <motion.div className="h-full rounded-full" initial={{ width: 0 }} animate={{ width: `${pct}%` }} transition={{ duration: 1, delay: 0.2 + i * 0.07 }}
                            style={{ background: over ? "linear-gradient(90deg,#fb718588,#fb7185)" : n.goodHigh ? "linear-gradient(90deg,#34d39988,#34d399)" : "linear-gradient(90deg,#5cc8ff88,#5cc8ff)" }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </Card>
              <Card>
                <CardTitle icon={<Salad className="h-4 w-4" />} title="What we found" sub={res.source} />
                {res.unmatched.length > 0 && (
                  <div className="mb-3 rounded-xl border border-amber-400/25 bg-amber-500/[0.08] px-3.5 py-2.5 text-xs text-amber-100">
                    No USDA match for {res.unmatched.join(", ")}, so calories are underestimated. Try describing the main ingredients.
                  </div>
                )}
                <div className="divide-y divide-white/[0.05]">
                  {res.items.map((it) => (
                    <div key={it.name} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                      <div className="min-w-0">
                        <div className="font-medium text-white"><span className="capitalize">{it.name}</span> <span className="font-normal text-slate-500">· ~{Math.round(it.grams)} g</span></div>
                        <div className="truncate text-[11px] text-slate-500">USDA: {it.usda_match?.description ?? "no match"}</div>
                      </div>
                      <span className="shrink-0 font-display font-semibold text-slate-200">{Math.round(it.nutrients.kcal)} kcal</span>
                    </div>
                  ))}
                </div>
              </Card>
            </motion.div>
          ) : (
            <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              className="glass hidden min-h-[420px] flex-col items-center justify-center p-10 text-center lg:flex">
              <motion.div animate={{ y: [0, -8, 0] }} transition={{ duration: 4, repeat: Infinity }}
                className="mb-5 grid h-20 w-20 place-items-center rounded-3xl bg-gradient-to-br from-brand-400/20 to-sky2-400/10 ring-1 ring-white/10">
                <Salad className="h-9 w-9 text-brand-300" />
              </motion.div>
              <h3 className="text-lg font-semibold">Your meal breakdown appears here</h3>
              <p className="mt-2 max-w-xs text-sm text-slate-400">Score, reasons, USDA nutrients and what to swap next time.</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      <Disclaimer />
    </>
  );
}
