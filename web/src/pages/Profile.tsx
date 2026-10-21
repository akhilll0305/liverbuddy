import { motion } from "framer-motion";
import { HeartPulse, Ruler, Save, Scale, UserRound } from "lucide-react";
import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { api, type Measurement, type Profile } from "../lib/api";
import { errorText, useAsync, useAuth, useToast } from "../lib/hooks";
import { TrendChart } from "../components/clinical";
import { Button, Card, CardTitle, Field, NumberInput, PageHeader, Segmented, Skeleton, Toggle } from "../components/ui";

export default function ProfilePage() {
  const { signedIn } = useAuth();
  const toast = useToast();
  const prof = useAsync(api.profile, [], signedIn);
  const body = useAsync(api.measurements, [], signedIn);
  const [p, setP] = useState<Profile | null>(null);
  const [m, setM] = useState<Measurement>({ taken_on: new Date().toISOString().slice(0, 10), weight_kg: null, waist_cm: null, systolic_bp: null, diastolic_bp: null });
  const [saving, setSaving] = useState<"p" | "m" | null>(null);

  useEffect(() => { if (prof.data) setP(prof.data); }, [prof.data]);
  if (!signedIn) return <Navigate to="/login" replace />;

  const set = <K extends keyof Profile>(k: K) => (v: Profile[K]) => setP((x) => (x ? { ...x, [k]: v } : x));
  const saveProfile = async () => {
    if (!p) return;
    setSaving("p");
    try { await api.saveProfile(p); toast("ok", "Profile saved. Your scores now use it."); } catch (e) { toast("warn", errorText(e)); } finally { setSaving(null); }
  };
  const addMeasurement = async () => {
    setSaving("m");
    try { await api.addMeasurement(m); toast("ok", "Measurement added."); body.reload(); } catch (e) { toast("warn", errorText(e)); } finally { setSaving(null); }
  };

  return (
    <>
      <PageHeader eyebrow="Your profile" title={<>Personalise <span className="text-gradient">your scores</span></>}
        sub="Age, sex, height and risk factors feed the score formulas and the risk model. Nothing is shared." />
      <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
        <Card initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}>
          <CardTitle icon={<UserRound className="h-4 w-4" />} title="About you" />
          {!p ? <Skeleton className="h-72" /> : (
            <div className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-2">
                <Field label="Display name"><input className="input" value={p.display_name} onChange={(e) => set("display_name")(e.target.value)} /></Field>
                <Field label="Sex"><Segmented id="psex" value={(p.sex ?? "male") as "male" | "female"} onChange={(v) => set("sex")(v)}
                  options={[{ value: "male", label: "Male" }, { value: "female", label: "Female" }]} /></Field>
                <Field label="Birth year"><NumberInput value={p.birth_year} onChange={(v) => set("birth_year")(v)} placeholder="1980" /></Field>
                <Field label="Height" hint="cm"><NumberInput value={p.height_cm} onChange={(v) => set("height_cm")(v)} placeholder="170" /></Field>
                <Field label="Alcohol" hint="grams / week (1 drink ≈ 10–14 g)"><NumberInput value={p.alcohol_g_per_week} onChange={(v) => set("alcohol_g_per_week")(v)} placeholder="0" /></Field>
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                <Toggle label="Type 2 diabetes" checked={p.type2_diabetes} onChange={set("type2_diabetes")} />
                <Toggle label="Blood-pressure medicine" checked={p.on_antihypertensives} onChange={set("on_antihypertensives")} />
                <Toggle label="Cholesterol medicine" checked={p.on_lipid_lowering} onChange={set("on_lipid_lowering")} />
                <Toggle label="Asian ethnicity (BMI cut-off 23)" checked={p.asian_ethnicity} onChange={set("asian_ethnicity")} />
              </div>
              <div className="flex justify-end"><Button onClick={saveProfile} loading={saving === "p"} icon={<Save className="h-4 w-4" />}>Save profile</Button></div>
            </div>
          )}
        </Card>
        <div className="space-y-6">
          <Card initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.08 }}>
            <CardTitle icon={<Scale className="h-4 w-4" />} title="Log a measurement" />
            <div className="grid grid-cols-2 gap-3">
              <Field label="Date"><input type="date" className="input" value={m.taken_on} onChange={(e) => setM({ ...m, taken_on: e.target.value })} /></Field>
              <Field label="Weight" hint="kg"><NumberInput value={m.weight_kg} onChange={(v) => setM({ ...m, weight_kg: v })} /></Field>
              <Field label="Waist" hint="cm"><NumberInput value={m.waist_cm} onChange={(v) => setM({ ...m, waist_cm: v })} /></Field>
              <Field label="Blood pressure" hint="sys / dia">
                <div className="flex gap-2"><NumberInput value={m.systolic_bp} onChange={(v) => setM({ ...m, systolic_bp: v })} placeholder="120" />
                  <NumberInput value={m.diastolic_bp} onChange={(v) => setM({ ...m, diastolic_bp: v })} placeholder="80" /></div>
              </Field>
            </div>
            <Button className="mt-4 w-full" variant="outline" onClick={addMeasurement} loading={saving === "m"} icon={<Ruler className="h-4 w-4" />}>Add measurement</Button>
          </Card>
          {(body.data?.filter((x) => x.weight_kg).length ?? 0) > 1 && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <Card>
                <CardTitle icon={<HeartPulse className="h-4 w-4" />} title="Weight trend" />
                <TrendChart data={body.data!.filter((x) => x.weight_kg) as unknown as Record<string, unknown>[]} series="weight_kg" height={180} />
              </Card>
            </motion.div>
          )}
        </div>
      </div>
    </>
  );
}
