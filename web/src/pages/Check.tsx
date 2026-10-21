import { AnimatePresence, motion } from "framer-motion";
import { Calculator, Droplets, Ruler, Sparkles, UserRound, Wand2 } from "lucide-react";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { api, type Measures, type RiskPrediction, type ScorePanel } from "../lib/api";
import { errorText, useAuth } from "../lib/hooks";
import { NextStep, RiskCard, ScoreGauges } from "../components/clinical";
import { Button, Card, CardTitle, Disclaimer, ErrorNote, Field, NumberInput, PageHeader, Segmented, Toggle } from "../components/ui";

const EXAMPLE: Measures = {
  age: 52, sex: "male", height_cm: 170, weight_kg: 88, waist_cm: 104, alt: 61, ast: 48, ggt: 72, platelets: 190, albumin: 4.2,
  triglycerides: 210, hdl: 38, fasting_glucose: 112, hba1c: 6.1, type2_diabetes: false, on_antihypertensives: true, asian_ethnicity: true,
};

const LABS: [keyof Measures, string, string][] = [
  ["alt", "ALT / SGPT", "U/L"], ["ast", "AST / SGOT", "U/L"], ["ggt", "GGT", "U/L"], ["platelets", "Platelets", "×10⁹/L"],
  ["albumin", "Albumin", "g/dL"], ["triglycerides", "Triglycerides", "mg/dL"], ["hdl", "HDL", "mg/dL"],
  ["fasting_glucose", "Fasting glucose", "mg/dL"], ["hba1c", "HbA1c", "%"],
];

function Section({ icon, title, children }: { icon: ReactNode; title: string; children: ReactNode }) {
  return (
    <div>
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-white"><span className="text-brand-300 [&>svg]:h-4 [&>svg]:w-4">{icon}</span>{title}</div>
      {children}
    </div>
  );
}

export default function Check() {
  const { signedIn } = useAuth();
  const [m, setM] = useState<Measures>({ sex: "male" });
  const [result, setResult] = useState<{ panel: ScorePanel; st: RiskPrediction; fb: RiskPrediction } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const resultRef = useRef<HTMLDivElement>(null);
  const set = (k: keyof Measures) => (v: unknown) => setM((p) => ({ ...p, [k]: v }));

  useEffect(() => {
    if (!signedIn) return;
    api.summary().then((s) => setM((p) => ({ ...p, ...Object.fromEntries(Object.entries(s.measures).filter(([, v]) => v !== null)) }))).catch(() => {});
  }, [signedIn]);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const [panel, st, fb] = await Promise.all([api.scores(m), api.risk(m, "steatosis"), api.risk(m, "fibrosis")]);
      setResult({ panel, st, fb });
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
    } catch (e) {
      setError(errorText(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <PageHeader eyebrow="Calculator" title={<>Liver scores <span className="text-gradient">& risk</span></>}
        sub="Five validated scores from published formulas, plus a machine-learning estimate trained on 7,094 adults with FibroScan results. Leave unknown values empty."
        action={<Button variant="outline" size="sm" icon={<Wand2 className="h-4 w-4" />} onClick={() => setM(EXAMPLE)}>Load an example</Button>} />

      <Card className="space-y-8" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}>
        <div className="grid gap-8 lg:grid-cols-2">
          <Section icon={<UserRound />} title="About you">
            <div className="grid grid-cols-2 gap-3">
              <Field label="Age" hint="years"><NumberInput value={m.age} onChange={set("age")} placeholder="45" /></Field>
              <Field label="Sex">
                <Segmented id="sex" value={(m.sex ?? "male") as "male" | "female"} onChange={set("sex")}
                  options={[{ value: "male", label: "Male" }, { value: "female", label: "Female" }]} />
              </Field>
              <div className="col-span-2 grid gap-2 sm:grid-cols-3">
                <Toggle label="Type 2 diabetes" checked={!!m.type2_diabetes} onChange={set("type2_diabetes")} />
                <Toggle label="BP medicines" checked={!!m.on_antihypertensives} onChange={set("on_antihypertensives")} />
                <Toggle label="Asian ethnicity" checked={!!m.asian_ethnicity} onChange={set("asian_ethnicity")} />
              </div>
            </div>
          </Section>
          <Section icon={<Ruler />} title="Body measurements">
            <div className="grid grid-cols-3 gap-3">
              <Field label="Height" hint="cm"><NumberInput value={m.height_cm} onChange={set("height_cm")} placeholder="170" /></Field>
              <Field label="Weight" hint="kg"><NumberInput value={m.weight_kg} onChange={set("weight_kg")} placeholder="80" /></Field>
              <Field label="Waist" hint="cm"><NumberInput value={m.waist_cm} onChange={set("waist_cm")} placeholder="95" /></Field>
            </div>
            {m.height_cm && m.weight_kg ? (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-3 text-xs text-slate-400">
                BMI <span className="font-semibold text-white">{(m.weight_kg / (m.height_cm / 100) ** 2).toFixed(1)}</span> kg/m²
              </motion.div>
            ) : null}
          </Section>
        </div>
        <Section icon={<Droplets />} title="Blood tests">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            {LABS.map(([k, label, unit]) => (
              <Field key={k} label={label} hint={unit}><NumberInput value={m[k] as number | null} onChange={set(k)} /></Field>
            ))}
          </div>
        </Section>
        <ErrorNote error={error} />
        <div className="flex justify-end">
          <Button size="lg" onClick={run} loading={loading} icon={<Calculator className="h-4 w-4" />}>Calculate</Button>
        </div>
      </Card>

      <AnimatePresence>
        {result && (
          <motion.div ref={resultRef} initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }} className="mt-8 space-y-6 scroll-mt-6">
            <CardTitle icon={<Sparkles className="h-4 w-4" />} title="Your results" sub="Validated scores first, then the ML estimate" />
            <ScoreGauges panel={result.panel} />
            <NextStep panel={result.panel} />
            <div className="grid gap-4 lg:grid-cols-2">
              <RiskCard pred={result.st} title="Liver fat" />
              <RiskCard pred={result.fb} title="Liver stiffness" />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      <Disclaimer />
    </>
  );
}
