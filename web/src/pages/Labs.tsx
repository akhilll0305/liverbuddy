import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, ClipboardPaste, FileText, FlaskConical, Save, ScanLine, TriangleAlert, UploadCloud } from "lucide-react";
import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, type LabExtract } from "../lib/api";
import { errorText, useAuth, useToast } from "../lib/hooks";
import { NextStep, ScoreGauges } from "../components/clinical";
import { Button, Card, CardTitle, Disclaimer, ErrorNote, PageHeader, Segmented, cx } from "../components/ui";

const NAMES: Record<string, string> = {
  alt: "ALT / SGPT", ast: "AST / SGOT", ggt: "GGT", platelets: "Platelets", albumin: "Albumin", triglycerides: "Triglycerides",
  hdl: "HDL cholesterol", fasting_glucose: "Fasting glucose", hba1c: "HbA1c",
};

export default function Labs() {
  const { signedIn } = useAuth();
  const toast = useToast();
  const [mode, setMode] = useState<"file" | "text">("file");
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState("");
  const [drag, setDrag] = useState(false);
  const [busy, setBusy] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [res, setRes] = useState<LabExtract | null>(null);
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const input = useRef<HTMLInputElement>(null);

  const extract = async (f: File | null = file) => {
    setBusy(true);
    setError(null);
    setRes(null);
    const fd = new FormData();
    if (mode === "file" && f) fd.append("file", f);
    else fd.append("text", text);
    try {
      setRes(await api.extractLabs(fd));
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  };

  const save = async () => {
    if (!res) return;
    setSaving(true);
    try {
      await api.addLabs(date, Object.fromEntries(Object.entries(res.extraction.values).map(([k, v]) => [k, v.value])), "report");
      toast("ok", "Saved to your results. Your dashboard trends are updated.");
    } catch (e) {
      toast("warn", errorText(e));
    } finally {
      setSaving(false);
    }
  };

  const values = res ? Object.values(res.extraction.values) : [];
  return (
    <>
      <PageHeader eyebrow="Lab report reader" title={<>Upload a <span className="text-gradient">lab report</span></>}
        sub="Reads ALT/SGPT, AST/SGOT, GGT, platelets, albumin, lipids, glucose and HbA1c. Handles Indian formats (lakh/cumm, 2,45,000) and SI units, then calculates your scores." />

      <Card initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}>
        <div className="mb-5"><Segmented id="labmode" value={mode} onChange={setMode}
          options={[{ value: "file", label: "Upload file", icon: <UploadCloud className="h-4 w-4" /> }, { value: "text", label: "Paste text", icon: <ClipboardPaste className="h-4 w-4" /> }]} /></div>
        {mode === "file" ? (
          <div onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)}
            onDrop={(e) => { e.preventDefault(); setDrag(false); const f = e.dataTransfer.files[0]; if (f) { setFile(f); extract(f); } }}
            onClick={() => input.current?.click()}
            className={cx("relative grid cursor-pointer place-items-center overflow-hidden rounded-2xl border-2 border-dashed px-6 py-14 text-center transition",
              drag ? "border-brand-300 bg-brand-400/[0.07]" : "border-white/10 hover:border-white/25 hover:bg-white/[0.02]")}>
            <input ref={input} type="file" accept=".pdf,.txt" hidden onChange={(e) => { const f = e.target.files?.[0] ?? null; setFile(f); if (f) extract(f); }} />
            {busy && <motion.div className="absolute inset-x-0 h-24 bg-gradient-to-b from-transparent via-brand-300/20 to-transparent"
              animate={{ top: ["-20%", "110%"] }} transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }} />}
            <motion.div animate={drag ? { scale: 1.1, rotate: -4 } : { scale: 1, rotate: 0 }}
              className="mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-white/[0.05] text-brand-300 ring-1 ring-white/10">
              {busy ? <ScanLine className="h-6 w-6" /> : file ? <FileText className="h-6 w-6" /> : <UploadCloud className="h-6 w-6" />}
            </motion.div>
            <div className="text-sm font-medium text-white">{busy ? "Reading your report…" : file ? file.name : "Drop your PDF here, or click to browse"}</div>
            <div className="mt-1 text-xs text-slate-500">PDF or text, up to 10 MB. Try <code className="text-slate-400">tests/fixtures/sample_lab_report.pdf</code></div>
          </div>
        ) : (
          <div className="space-y-3">
            <textarea className="input min-h-[180px] font-mono text-[13px]" value={text} onChange={(e) => setText(e.target.value)}
              placeholder={"SGPT (ALT)      68   U/L\nSGOT (AST)      45   U/L\nPlatelet Count  2.1  lakhs/cumm\n…"} />
            <div className="flex justify-end"><Button onClick={() => extract()} loading={busy} disabled={!text.trim()} icon={<ScanLine className="h-4 w-4" />}>Extract</Button></div>
          </div>
        )}
        <div className="mt-4"><ErrorNote error={error} /></div>
      </Card>

      <AnimatePresence>
        {res && (
          <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} className="mt-6 space-y-6">
            <Card>
              <CardTitle icon={<FlaskConical className="h-4 w-4" />} title={`Found ${values.length} of 9 tests`}
                sub={res.extraction.missing.length ? `Not found: ${res.extraction.missing.map((m) => NAMES[m]).join(", ")}` : "All key tests found"} />
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {values.map((v, i) => (
                  <motion.div key={v.analyte} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.05 }}
                    className="flex items-center justify-between rounded-xl bg-white/[0.03] px-3.5 py-3 ring-1 ring-white/[0.06]">
                    <div>
                      <div className="text-xs text-slate-400">{NAMES[v.analyte]}</div>
                      <div className="font-display text-lg font-semibold text-white">{v.value} <span className="text-xs font-normal text-slate-500">{v.unit}</span></div>
                    </div>
                    <span className={cx("chip !text-[10px]", v.method === "llm" && "!border-violet-400/30 !text-violet-200")}>
                      <CheckCircle2 className="h-3 w-3" />{v.method === "rule" ? "rule" : "AI"}
                    </span>
                  </motion.div>
                ))}
              </div>
              {res.extraction.warnings.length > 0 && (
                <div className="mt-4 space-y-1">{res.extraction.warnings.map((w) => (
                  <div key={w} className="flex items-center gap-2 text-xs text-amber-200/80"><TriangleAlert className="h-3.5 w-3.5" />{w}</div>))}
                </div>
              )}
              <div className="mt-5 flex flex-wrap items-center justify-end gap-3 border-t border-white/[0.06] pt-5">
                {signedIn ? (
                  <>
                    <input type="date" className="input !w-auto" value={date} onChange={(e) => setDate(e.target.value)} />
                    <Button onClick={save} loading={saving} icon={<Save className="h-4 w-4" />}>Save to my results</Button>
                  </>
                ) : <span className="text-sm text-slate-400"><Link to="/login" className="text-brand-300 hover:underline">Sign in</Link> to save results and see trends.</span>}
              </div>
            </Card>
            {res.panel && <><ScoreGauges panel={res.panel} /><NextStep panel={res.panel} /></>}
          </motion.div>
        )}
      </AnimatePresence>
      <Disclaimer />
    </>
  );
}
