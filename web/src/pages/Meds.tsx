import { AnimatePresence, motion } from "framer-motion";
import { ExternalLink, Loader2, Pill, Plus, Search, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { api, type DrugLookup } from "../lib/api";
import { errorText, useAsync, useAuth, useToast } from "../lib/hooks";
import { LIKELIHOOD_TEXT, RISK, likelihoodTone } from "../lib/theme";
import { Badge, Button, Card, CardTitle, Disclaimer, EmptyState, PageHeader, cx } from "../components/ui";

const QUICK = ["Crocin", "Lipitor", "Glycomet", "Ashwagandha", "Augmentin", "Green tea"];
const SCALE = ["A", "B", "C", "D", "E"];

function LikelihoodScale({ grade }: { grade: string }) {
  const idx = SCALE.indexOf(grade[0]);
  return (
    <div>
      <div className="flex gap-1.5">
        {SCALE.map((g, i) => {
          const tone = likelihoodTone(g);
          const active = i === idx;
          return (
            <motion.div key={g} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
              className={cx("relative flex h-11 flex-1 items-center justify-center rounded-lg font-display text-sm font-bold transition",
                active ? "text-ink-950" : "bg-white/[0.04] text-slate-500")}
              style={active ? { background: RISK[tone].hex, boxShadow: `0 0 24px ${RISK[tone].hex}66` } : undefined}>
              {g}
              {active && <motion.span layoutId="lt-ring" className="absolute -inset-1 rounded-xl ring-2" style={{ ["--tw-ring-color" as string]: RISK[tone].hex + "88" }} />}
            </motion.div>
          );
        })}
      </div>
      <div className="mt-1.5 flex justify-between text-[10px] uppercase tracking-wider text-slate-500"><span>known cause</span><span>unlikely cause</span></div>
    </div>
  );
}

export default function Meds() {
  const { signedIn } = useAuth();
  const toast = useToast();
  const [q, setQ] = useState("");
  const [res, setRes] = useState<DrugLookup | null>(null);
  const [searching, setSearching] = useState(false);
  const meds = useAsync(api.meds, [], signedIn);

  useEffect(() => {
    if (q.trim().length < 3) return setRes(null);
    setSearching(true);
    const t = setTimeout(() => {
      api.drug(q).then(setRes).catch(() => setRes(null)).finally(() => setSearching(false));
    }, 350);
    return () => clearTimeout(t);
  }, [q]);

  const add = async () => {
    try {
      await api.addMed(q);
      toast("ok", `${res?.record?.name ?? q} added to your list.`);
      meds.reload();
    } catch (e) {
      toast("warn", errorText(e));
    }
  };

  const rec = res?.record;
  return (
    <>
      <PageHeader eyebrow="NIH LiverTox · 1,175 drugs and supplements" title={<>Is it safe for <span className="text-gradient">my liver?</span></>}
        sub="Brand, generic, misspelt or Indian brand names all work. The grade is LiverTox's expert likelihood score, not an AI guess. Never stop a prescribed medicine without your doctor." />

      <div className="relative mb-4">
        <Search className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500" />
        <input autoFocus className="input !rounded-2xl !py-4 pl-12 text-base" placeholder="Search a medicine or supplement…" value={q} onChange={(e) => setQ(e.target.value)} />
        {searching && <Loader2 className="absolute right-4 top-1/2 h-5 w-5 -translate-y-1/2 animate-spin text-brand-300" />}
      </div>
      <div className="mb-8 flex flex-wrap gap-2">
        {QUICK.map((x) => <button key={x} onClick={() => setQ(x)} className="chip transition hover:border-brand-300/40 hover:text-white">{x}</button>)}
      </div>

      <AnimatePresence mode="wait">
        {rec && res?.matched ? (
          <motion.div key={rec.id} initial={{ opacity: 0, y: 16, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -10 }}>
            <Card className="relative overflow-hidden">
              <div className="absolute -right-20 -top-20 h-60 w-60 rounded-full blur-3xl" style={{ background: RISK[likelihoodTone(rec.likelihood)].hex + "22" }} />
              <div className="relative grid gap-6 md:grid-cols-[1.2fr_1fr]">
                <div>
                  {q.toLowerCase() !== rec.name.toLowerCase() && <div className="mb-1 text-xs text-slate-400">"{q}" →</div>}
                  <h2 className="text-3xl font-bold">{rec.name}</h2>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {rec.drug_class && <span className="chip">{rec.drug_class}</span>}
                    {rec.trade_names.slice(0, 5).map((t) => <span key={t} className="chip !text-[10px]">{t}</span>)}
                  </div>
                  <p className="mt-4 text-sm leading-relaxed text-slate-300">{rec.summary}</p>
                  <div className="mt-5 flex flex-wrap gap-2">
                    <a href={rec.url} target="_blank" rel="noreferrer"><Button variant="outline" size="sm" icon={<ExternalLink className="h-4 w-4" />}>LiverTox monograph</Button></a>
                    {signedIn && <Button size="sm" onClick={add} icon={<Plus className="h-4 w-4" />}>Add to my list</Button>}
                  </div>
                </div>
                <div>
                  <div className="label mb-2">LiverTox likelihood score</div>
                  <div className="mb-4 flex items-baseline gap-3">
                    <span className="font-display text-6xl font-extrabold" style={{ color: RISK[likelihoodTone(rec.likelihood)].hex }}>{rec.likelihood}</span>
                    <span className="text-sm text-slate-300">{LIKELIHOOD_TEXT[rec.likelihood] ?? res.category_meaning}</span>
                  </div>
                  <LikelihoodScale grade={rec.likelihood} />
                  <p className="mt-4 rounded-xl bg-white/[0.03] p-3 text-xs leading-relaxed text-slate-400 ring-1 ring-white/[0.06]">{res.note.replace(/Source: NIH LiverTox ([^)]*).s*/, "")}</p>
                </div>
              </div>
            </Card>
          </motion.div>
        ) : res && !res.matched ? (
          <motion.div key="nomatch" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass p-5 text-sm text-slate-300">
            {res.note} {res.alternatives.length > 0 && <>Did you mean{" "}
              {res.alternatives.map((a, i) => <button key={a} onClick={() => setQ(a)} className="font-medium text-brand-300 hover:underline">{a}{i < res.alternatives.length - 1 ? ", " : ""}</button>)}?</>}
          </motion.div>
        ) : null}
      </AnimatePresence>

      {signedIn && (
        <Card className="mt-8">
          <CardTitle icon={<Pill className="h-4 w-4" />} title="My medicines" sub="Checked against LiverTox when added" />
          {meds.data?.length ? (
            <ul className="space-y-2">
              <AnimatePresence>
                {meds.data.map((m) => (
                  <motion.li key={m.id} layout initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, x: 30 }}
                    className="group flex items-center justify-between gap-3 rounded-xl bg-white/[0.025] px-3.5 py-3 ring-1 ring-white/[0.05]">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-medium text-white">{m.name} {m.dose_text && <span className="font-normal text-slate-500">· {m.dose_text}</span>}</div>
                      <div className="text-[11px] text-slate-500">{m.livertox_name ?? "Not found in LiverTox"}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge tone={likelihoodTone(m.likelihood)}>{m.likelihood ?? "–"}</Badge>
                      <button onClick={async () => { await api.removeMed(m.id); meds.reload(); }}
                        className="rounded-lg p-1.5 text-slate-500 opacity-0 transition hover:bg-rose-500/10 hover:text-rose-300 group-hover:opacity-100" aria-label="Remove">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </motion.li>
                ))}
              </AnimatePresence>
            </ul>
          ) : <EmptyState icon={<Pill className="h-6 w-6" />} title="No medicines yet" text="Search above and add the medicines and supplements you take." />}
        </Card>
      )}
      <Disclaimer />
    </>
  );
}
