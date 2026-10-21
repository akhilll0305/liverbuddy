import { AnimatePresence, motion } from "framer-motion";
import { BookOpenCheck, ChevronDown, ExternalLink, Search, ShieldAlert, Sparkles } from "lucide-react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { api, type GroundedAnswer, type Guardrail } from "../lib/api";
import { errorText } from "../lib/hooks";
import { Button, Card, Disclaimer, ErrorNote, PageHeader, cx } from "../components/ui";

const QUESTIONS = [
  "Is coffee good for fatty liver?", "What FIB-4 value means advanced fibrosis is unlikely?", "Are statins safe with fatty liver?",
  "How much exercise is recommended for MASLD?", "Can you get fatty liver if you're not overweight?", "What is resmetirom used for?",
];

export default function Ask() {
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [out, setOut] = useState<{ guardrail: Guardrail; answer: GroundedAnswer | null } | null>(null);
  const [openCite, setOpenCite] = useState<number | null>(null);

  const ask = async (question = q) => {
    if (!question.trim()) return;
    setQ(question);
    setBusy(true);
    setError(null);
    setOut(null);
    try {
      setOut(await api.ask(question));
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  };

  const a = out?.answer;
  return (
    <>
      <PageHeader eyebrow="Grounded Q&A · hybrid retrieval" title={<>Ask the <span className="text-gradient">guidelines</span></>}
        sub="Answers come only from the AASLD 2023 guidance, the EASL-EASD-EASO 2024 guideline and NIH LiverTox. Every claim is cited, and when the sources don't cover a question it says so instead of guessing." />

      <form onSubmit={(e) => { e.preventDefault(); ask(); }} className="relative">
        <Search className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500" />
        <input className="input !rounded-2xl !py-4 pl-12 pr-32 text-base" placeholder="Ask a question about fatty liver…" value={q} onChange={(e) => setQ(e.target.value)} />
        <Button type="submit" className="absolute right-2 top-1/2 -translate-y-1/2" loading={busy} disabled={!q.trim()}>Ask</Button>
      </form>
      <div className="mt-4 flex flex-wrap gap-2">
        {QUESTIONS.map((x) => <button key={x} onClick={() => ask(x)} className="chip transition hover:border-brand-300/40 hover:text-white">{x}</button>)}
      </div>

      <div className="mt-8"><ErrorNote error={error} /></div>
      {busy && (
        <Card className="mt-2 space-y-3">
          <div className="flex items-center gap-2 text-sm text-slate-400"><Sparkles className="h-4 w-4 animate-pulse text-brand-300" />Searching 150 guideline passages and 7,272 LiverTox passages…</div>
          <div className="skeleton h-4 w-full" /><div className="skeleton h-4 w-11/12" /><div className="skeleton h-4 w-3/4" />
        </Card>
      )}

      <AnimatePresence>
        {out && !a && out.guardrail.message && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex gap-3 rounded-2xl border border-rose-400/30 bg-rose-500/10 p-5 text-rose-100">
            <ShieldAlert className="h-5 w-5 shrink-0" />{out.guardrail.message}
          </motion.div>
        )}
        {a && (
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
            {out?.guardrail.action === "caution_medication" && (
              <div className="rounded-xl border border-amber-400/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">{out.guardrail.message}</div>
            )}
            <Card className={cx(a.abstained && "!border-amber-400/20")}>
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="grid h-8 w-8 place-items-center rounded-xl bg-gradient-to-br from-brand-300 to-sky2-400"><BookOpenCheck className="h-4 w-4 text-ink-950" /></div>
                  <span className="font-semibold text-white">{a.abstained ? "Not covered by the guidelines" : "Answer"}</span>
                </div>
                <span className="chip !text-[10px]">retrieval similarity {a.top_similarity.toFixed(2)}</span>
              </div>
              <div className="markdown text-[15px] leading-relaxed text-slate-200">
                <ReactMarkdown>{a.answer.replace(/\[(\d+)\]/g, "**[$1]**")}</ReactMarkdown>
              </div>
            </Card>
            {a.citations.length > 0 && (
              <div className="space-y-2">
                <div className="label">Sources</div>
                {a.citations.map((c, i) => (
                  <motion.div key={c.n} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 + i * 0.07 }} className="glass overflow-hidden">
                    <button onClick={() => setOpenCite(openCite === c.n ? null : c.n)} className="flex w-full items-center gap-3 px-4 py-3 text-left">
                      <span className="grid h-6 w-6 shrink-0 place-items-center rounded-md bg-brand-400/15 text-xs font-bold text-brand-300 ring-1 ring-brand-300/30">{c.n}</span>
                      <div className="min-w-0 flex-1">
                        <div className="text-sm font-medium text-white">{c.title}</div>
                        <div className="truncate text-xs text-slate-400">{c.section}</div>
                      </div>
                      <ChevronDown className={cx("h-4 w-4 text-slate-500 transition", openCite === c.n && "rotate-180")} />
                    </button>
                    <AnimatePresence>
                      {openCite === c.n && (
                        <motion.div initial={{ height: 0 }} animate={{ height: "auto" }} exit={{ height: 0 }} className="overflow-hidden">
                          <div className="border-t border-white/[0.06] px-4 py-3 text-sm leading-relaxed text-slate-300">
                            "{c.excerpt}…"
                            <a href={c.url} target="_blank" rel="noreferrer" className="mt-2 flex items-center gap-1 text-xs text-brand-300 hover:underline">Open source <ExternalLink className="h-3 w-3" /></a>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
      <Disclaimer />
    </>
  );
}
