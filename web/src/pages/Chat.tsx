import { AnimatePresence, motion } from "framer-motion";
import {
  AlertOctagon, ArrowUp, BookOpenCheck, Calculator, ChevronDown, FlaskConical, HeartHandshake, Pill, RotateCcw, Salad, ShieldAlert, Sparkles, UserRound, Wrench,
} from "lucide-react";
import { useEffect, useRef, useState, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import { api, type Citation, type CopilotReply } from "../lib/api";
import { errorText } from "../lib/hooks";
import { cx } from "../components/ui";

type Msg = { role: "user" | "assistant"; content: string; reply?: CopilotReply; error?: boolean };

const SUGGESTIONS = [
  { icon: <Calculator />, text: "I'm 48, AST 40, ALT 65, platelets 210. What's my FIB-4 and what next?" },
  { icon: <Pill />, text: "I take Lipitor and Crocin. Are they safe for my liver?" },
  { icon: <Salad />, text: "I had 2 parathas with butter and a mango lassi. Is that liver friendly?" },
  { icon: <BookOpenCheck />, text: "How much weight do I need to lose to improve fatty liver?" },
];

const TOOL_META: Record<string, { label: string; icon: ReactNode }> = {
  compute_liver_scores: { label: "Computed liver scores", icon: <Calculator className="h-3.5 w-3.5" /> },
  predict_liver_risk: { label: "Ran the ML risk model", icon: <Sparkles className="h-3.5 w-3.5" /> },
  check_medication: { label: "Checked NIH LiverTox", icon: <Pill className="h-3.5 w-3.5" /> },
  search_guidelines: { label: "Searched the guidelines", icon: <BookOpenCheck className="h-3.5 w-3.5" /> },
  analyze_meal: { label: "Analysed the meal (USDA)", icon: <Salad className="h-3.5 w-3.5" /> },
  get_my_health_summary: { label: "Read your health record", icon: <UserRound className="h-3.5 w-3.5" /> },
  get_lab_trend: { label: "Looked at your lab trend", icon: <FlaskConical className="h-3.5 w-3.5" /> },
};

const THINKING = ["Reading your question", "Choosing the right tools", "Checking clinical guidelines", "Verifying citations", "Writing a clear answer"];

function Thinking() {
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((x) => (x + 1) % THINKING.length), 1600);
    return () => clearInterval(t);
  }, []);
  return (
    <div className="flex items-center gap-3">
      <div className="flex gap-1">
        {[0, 1, 2].map((d) => (
          <motion.span key={d} className="h-2 w-2 rounded-full bg-brand-300" animate={{ y: [0, -5, 0], opacity: [0.4, 1, 0.4] }}
            transition={{ duration: 0.9, repeat: Infinity, delay: d * 0.15 }} />
        ))}
      </div>
      <AnimatePresence mode="wait">
        <motion.span key={i} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} className="text-sm text-slate-400">
          {THINKING[i]}…
        </motion.span>
      </AnimatePresence>
    </div>
  );
}

function CiteChip({ n, cite }: { n: string; cite?: Citation }) {
  const [open, setOpen] = useState(false);
  return (
    <span className="relative inline-block" onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}>
      <a href={cite?.url ?? "#"} target="_blank" rel="noreferrer"
        className="mx-0.5 inline-grid h-[18px] min-w-[18px] place-items-center rounded-md bg-brand-400/15 px-1 align-[2px] text-[10px] font-bold text-brand-300 no-underline ring-1 ring-brand-300/30 transition hover:bg-brand-400/30">
        {n}
      </a>
      <AnimatePresence>
        {open && cite && (
          <motion.span initial={{ opacity: 0, y: 6, scale: 0.97 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 4 }}
            className="absolute bottom-6 left-1/2 z-30 block w-80 -translate-x-1/2 rounded-xl border border-white/10 bg-ink-850/95 p-3.5 text-left shadow-2xl backdrop-blur-xl">
            <span className="block text-xs font-semibold text-white">{cite.title}</span>
            <span className="mb-2 block text-[11px] text-brand-300/80">{cite.section}</span>
            <span className="block text-[12px] leading-relaxed text-slate-300">"{cite.excerpt.slice(0, 260)}…"</span>
          </motion.span>
        )}
      </AnimatePresence>
    </span>
  );
}

function AssistantBody({ msg }: { msg: Msg }) {
  const r = msg.reply;
  const [showTools, setShowTools] = useState(false);
  const cites = new Map((r?.citations ?? []).map((c) => [String(c.n), c]));
  const text = msg.content.replace(/\[(\d+)\]/g, (_, n) => `[${n}](#cite-${n})`);
  const danger = r && (r.guardrail === "emergency" || r.guardrail === "crisis" || r.guardrail === "urgent");
  return (
    <div className="min-w-0 flex-1">
      {danger && (
        <div className={cx("mb-3 flex items-center gap-2 rounded-xl px-3.5 py-2.5 text-sm font-medium ring-1",
          r!.guardrail === "crisis" ? "bg-violet-500/10 text-violet-200 ring-violet-400/30" : "bg-rose-500/10 text-rose-200 ring-rose-400/30")}>
          {r!.guardrail === "crisis" ? <HeartHandshake className="h-4 w-4" /> : <AlertOctagon className="h-4 w-4" />}
          {r!.guardrail === "crisis" ? "You're not alone. Support is available right now." : "Safety rule triggered. This was not generated by AI."}
        </div>
      )}
      {r?.guardrail === "refuse_dosing" && (
        <div className="mb-3 flex items-center gap-2 rounded-xl bg-amber-500/10 px-3.5 py-2.5 text-sm text-amber-200 ring-1 ring-amber-400/30">
          <ShieldAlert className="h-4 w-4" /> Dosing questions are always referred to your prescriber.
        </div>
      )}
      <div className={cx("markdown text-[14.5px] leading-relaxed", msg.error ? "text-rose-200" : "text-slate-200")}>
        <ReactMarkdown components={{
          a: ({ href, children }) => href?.startsWith("#cite-")
            ? <CiteChip n={String(children)} cite={cites.get(String(children))} />
            : <a href={href} target="_blank" rel="noreferrer">{children}</a>,
        }}>{text}</ReactMarkdown>
      </div>
      {r && r.tools.length > 0 && (
        <div className="mt-3">
          <button onClick={() => setShowTools((s) => !s)} className="chip transition hover:border-brand-300/40 hover:text-white">
            <Wrench className="h-3.5 w-3.5 text-brand-300" />
            {r.tools.length} tool call{r.tools.length > 1 ? "s" : ""} · {r.citations.length} source{r.citations.length === 1 ? "" : "s"}
            {r.removed_invalid_citations.length > 0 && <span className="text-amber-300">· {r.removed_invalid_citations.length} bad citation removed</span>}
            <ChevronDown className={cx("h-3.5 w-3.5 transition", showTools && "rotate-180")} />
          </button>
          <AnimatePresence>
            {showTools && (
              <motion.ol initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }}
                className="relative ml-3 mt-3 space-y-3 overflow-hidden border-l border-white/10 pl-5">
                {r.tools.map((t, i) => (
                  <motion.li key={i} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.08 }} className="relative">
                    <span className="absolute -left-[29px] top-0.5 grid h-[18px] w-[18px] place-items-center rounded-full bg-ink-800 text-brand-300 ring-1 ring-white/15">
                      {TOOL_META[t.name]?.icon ?? <Wrench className="h-3 w-3" />}
                    </span>
                    <div className="text-[13px] text-slate-200">{TOOL_META[t.name]?.label ?? t.name}
                      <span className="ml-2 text-[11px] text-slate-500">{t.latency_ms.toFixed(0)} ms</span>
                      {t.error && <span className="ml-2 text-[11px] text-rose-300">{t.error}</span>}
                    </div>
                    <code className="mt-1 block truncate text-[11px] text-slate-500">{t.name}({JSON.stringify(t.arguments)})</code>
                  </motion.li>
                ))}
              </motion.ol>
            )}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}

export default function Chat() {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [msgs, busy]);
  useEffect(() => {
    const ta = taRef.current;
    if (ta) { ta.style.height = "0px"; ta.style.height = Math.min(ta.scrollHeight, 180) + "px"; }
  }, [input]);

  const send = async (q: string) => {
    const question = q.trim();
    if (!question || busy) return;
    const history = msgs.filter((m) => !m.error).map((m) => ({ role: m.role, content: m.content }));
    setMsgs((m) => [...m, { role: "user", content: question }]);
    setInput("");
    setBusy(true);
    try {
      const reply = await api.copilot(question, history);
      setMsgs((m) => [...m, { role: "assistant", content: reply.answer, reply }]);
    } catch (e) {
      setMsgs((m) => [...m, { role: "assistant", content: errorText(e), error: true }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-8rem)] flex-col">
      <div className="mb-6 flex items-end justify-between">
        <div>
          <div className="label mb-2 text-brand-300/80">AI copilot · tool-using agent</div>
          <h1 className="text-3xl font-bold md:text-4xl">Ask <span className="text-gradient">Liver Buddy</span></h1>
        </div>
        {msgs.length > 0 && (
          <button onClick={() => setMsgs([])} className="chip transition hover:text-white"><RotateCcw className="h-3.5 w-3.5" />New chat</button>
        )}
      </div>

      <div className="flex-1 space-y-6 pb-6">
        {msgs.length === 0 && (
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="pt-6 text-center">
            <motion.div className="mx-auto mb-6 grid h-16 w-16 place-items-center rounded-2xl bg-gradient-to-br from-brand-300 to-sky2-400 shadow-glow"
              animate={{ rotate: [0, 6, -6, 0] }} transition={{ duration: 6, repeat: Infinity }}>
              <Sparkles className="h-7 w-7 text-ink-950" />
            </motion.div>
            <h2 className="text-2xl font-semibold">How can I help with your liver health?</h2>
            <p className="mx-auto mt-2 max-w-md text-sm text-slate-400">I calculate with validated scores, check medicines in NIH LiverTox and cite the AASLD and EASL guidelines. I never guess numbers.</p>
            <div className="mx-auto mt-8 grid max-w-3xl gap-3 sm:grid-cols-2">
              {SUGGESTIONS.map((s, i) => (
                <motion.button key={s.text} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 + i * 0.07 }}
                  onClick={() => send(s.text)} className="glass glass-hover flex items-start gap-3 p-4 text-left text-sm text-slate-300">
                  <span className="mt-0.5 text-brand-300 [&>svg]:h-4 [&>svg]:w-4">{s.icon}</span>{s.text}
                </motion.button>
              ))}
            </div>
          </motion.div>
        )}

        <AnimatePresence initial={false}>
          {msgs.map((m, i) => (
            <motion.div key={i} layout initial={{ opacity: 0, y: 14, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ type: "spring", stiffness: 260, damping: 26 }} className={cx("flex gap-3", m.role === "user" && "justify-end")}>
              {m.role === "assistant" && (
                <div className="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-brand-300 to-sky2-400">
                  <Sparkles className="h-4 w-4 text-ink-950" />
                </div>
              )}
              {m.role === "user" ? (
                <div className="max-w-[80%] rounded-2xl rounded-tr-md bg-gradient-to-br from-brand-400/25 to-sky2-400/15 px-4 py-3 text-[14.5px] text-white ring-1 ring-brand-300/20">
                  {m.content}
                </div>
              ) : (
                <div className="glass max-w-[88%] flex-1 !rounded-2xl !rounded-tl-md px-4 py-3.5"><AssistantBody msg={m} /></div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
        {busy && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
            <div className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-brand-300 to-sky2-400"><Sparkles className="h-4 w-4 text-ink-950" /></div>
            <div className="glass !rounded-2xl !rounded-tl-md px-4 py-3.5"><Thinking /></div>
          </motion.div>
        )}
        <div ref={endRef} />
      </div>

      <div className="sticky bottom-4 z-20">
        <form onSubmit={(e) => { e.preventDefault(); send(input); }}
          className="glass flex items-end gap-2 !rounded-2xl !bg-ink-900/85 p-2 pl-4 shadow-2xl focus-within:border-brand-300/40">
          <textarea ref={taRef} rows={1} value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask about your scores, medicines, diet or the guidelines…"
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input); } }}
            className="max-h-44 flex-1 resize-none bg-transparent py-2.5 text-[14.5px] text-white outline-none placeholder:text-slate-500" />
          <motion.button whileTap={{ scale: 0.9 }} type="submit" disabled={!input.trim() || busy}
            className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-gradient-to-r from-brand-300 to-sky2-400 text-ink-950 shadow-glow transition disabled:opacity-30">
            <ArrowUp className="h-5 w-5" />
          </motion.button>
        </form>
        <p className="mt-2 text-center text-[11px] text-slate-500">Not medical advice. Emergencies are handled by fixed safety rules. Call 112 if you are unwell.</p>
      </div>
    </div>
  );
}
