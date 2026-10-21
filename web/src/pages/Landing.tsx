import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import {
  ArrowRight, BookOpenCheck, BrainCircuit, Calculator, FlaskConical, Github, Pill, Salad, ShieldCheck, Sparkles, Stethoscope,
} from "lucide-react";
import { useState, type ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { errorText, useAuth, useToast } from "../lib/hooks";
import { AnimatedNumber, Aurora, Badge, Button, Gauge, Logo, Reveal, Ring, Spotlight, cx } from "../components/ui";

function useDemo() {
  const nav = useNavigate();
  const toast = useToast();
  const { signIn } = useAuth();
  const [loading, setLoading] = useState(false);
  return {
    loading,
    start: async () => {
      setLoading(true);
      try {
        signIn((await api.demo()).access_token);
        toast("ok", "Welcome! You're exploring a demo patient with 9 months of history.");
        nav("/app");
      } catch (e) {
        toast("warn", errorText(e));
      } finally {
        setLoading(false);
      }
    },
  };
}

/* ---------------------------------------------------------------- hero preview (parallax) */
function HeroPreview() {
  const mx = useMotionValue(0);
  const my = useMotionValue(0);
  const rx = useSpring(useTransform(my, [-0.5, 0.5], [8, -8]), { stiffness: 120, damping: 18 });
  const ry = useSpring(useTransform(mx, [-0.5, 0.5], [-10, 10]), { stiffness: 120, damping: 18 });
  const layer = (depth: number) => ({
    x: useSpring(useTransform(mx, [-0.5, 0.5], [-depth, depth]), { stiffness: 120, damping: 18 }),
    y: useSpring(useTransform(my, [-0.5, 0.5], [-depth, depth]), { stiffness: 120, damping: 18 }),
  });
  const l1 = layer(12), l2 = layer(26), l3 = layer(40);
  return (
    <div className="relative h-[460px] w-full [perspective:1200px]"
      onMouseMove={(e) => {
        const r = e.currentTarget.getBoundingClientRect();
        mx.set((e.clientX - r.left) / r.width - 0.5);
        my.set((e.clientY - r.top) / r.height - 0.5);
      }}
      onMouseLeave={() => { mx.set(0); my.set(0); }}>
      <motion.div style={{ rotateX: rx, rotateY: ry }} className="relative h-full w-full [transform-style:preserve-3d]">
        {/* main dashboard card */}
        <motion.div style={l1} initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3, duration: 0.8 }}
          className="glass absolute left-[6%] top-[8%] w-[78%] p-5">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <div className="label">Liver health · Sep 2026</div>
              <div className="mt-1 font-display text-lg font-semibold text-white">Arjun's dashboard</div>
            </div>
            <Badge tone="low">Improving</Badge>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-xl bg-white/[0.03] p-3 text-center ring-1 ring-white/[0.06]">
              <div className="mb-1 text-xs font-semibold text-slate-300">FIB-4</div>
              <div className="flex justify-center"><Gauge value={1.18} max={4} ticks={[1.3, 2.67]} tone="low" size={120} /></div>
            </div>
            <div className="rounded-xl bg-white/[0.03] p-3 text-center ring-1 ring-white/[0.06]">
              <div className="mb-1 text-xs font-semibold text-slate-300">Fatty Liver Index</div>
              <div className="flex justify-center"><Gauge value={71.4} max={100} ticks={[30, 60]} tone="high" size={120} /></div>
            </div>
          </div>
          <svg viewBox="0 0 300 70" className="mt-4 h-16 w-full">
            <defs>
              <linearGradient id="hero-line" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stopColor="#34e0b0" stopOpacity=".35" />
                <stop offset="1" stopColor="#34e0b0" stopOpacity="0" />
              </linearGradient>
            </defs>
            <motion.path d="M0,14 C40,18 70,22 100,30 S170,42 200,48 S260,56 300,58" fill="none" stroke="#34e0b0" strokeWidth="2.5"
              initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 2, delay: 0.8, ease: "easeInOut" }} />
            <path d="M0,14 C40,18 70,22 100,30 S170,42 200,48 S260,56 300,58 L300,70 L0,70Z" fill="url(#hero-line)" />
          </svg>
          <div className="flex justify-between text-[10px] text-slate-500"><span>ALT 82 U/L</span><span>ALT 46 U/L ↓ 44%</span></div>
        </motion.div>

        {/* chat bubble */}
        <motion.div style={l3} initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.7, duration: 0.8 }}
          className="glass absolute right-0 top-[60%] w-[60%] animate-float p-4 [animation-delay:-2s]">
          <div className="mb-2 flex items-center gap-2 text-xs text-slate-400">
            <div className="grid h-6 w-6 place-items-center rounded-lg bg-gradient-to-br from-brand-300 to-sky2-400"><Sparkles className="h-3.5 w-3.5 text-ink-950" /></div>
            Liver Buddy
          </div>
          <p className="text-[13px] leading-relaxed text-slate-200">
            A sustained weight loss of <b className="text-white">7–10%</b> improves liver inflammation; <b className="text-white">≥10%</b> can improve fibrosis
            <span className="ml-1 rounded bg-brand-400/15 px-1.5 py-0.5 text-[10px] font-semibold text-brand-300">EASL 2024</span>
          </p>
          <div className="mt-3 flex gap-1.5">
            <span className="chip !py-0.5 !text-[10px]">search_guidelines · 41 ms</span>
            <span className="chip !py-0.5 !text-[10px]">compute_liver_scores</span>
          </div>
        </motion.div>

        {/* meal score */}
        <motion.div style={l2} initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.55, duration: 0.8 }}
          className="glass absolute -bottom-[4%] left-0 flex w-[44%] animate-float items-center gap-3 p-4">
          <Ring value={0.92} size={64} stroke={7} color="#34d399"><span className="font-display text-sm font-bold text-white">92</span></Ring>
          <div>
            <div className="text-xs font-semibold text-white">Dal, roti & salad</div>
            <div className="text-[11px] text-emerald-300">Excellent · +8 vegetables</div>
          </div>
        </motion.div>

        {/* drug badge */}
        <motion.div style={l3} initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.9, duration: 0.8 }}
          className="glass absolute right-[2%] top-0 flex animate-float items-center gap-2.5 px-3.5 py-2.5 [animation-delay:-4s]">
          <Pill className="h-4 w-4 text-amber-300" />
          <div className="text-[11px]"><span className="font-semibold text-white">Crocin</span> <span className="text-slate-400">→ Acetaminophen</span></div>
          <Badge tone="high">LiverTox A</Badge>
        </motion.div>
      </motion.div>
    </div>
  );
}

/* ---------------------------------------------------------------- sections */
const FEATURES: { icon: ReactNode; title: string; text: string; tag: string }[] = [
  { icon: <Calculator />, title: "Validated liver scores", text: "FIB-4, NAFLD Fibrosis Score, FLI, HSI and APRI, computed with published formulas and placed on the EASL 2024 care pathway.", tag: "Deterministic" },
  { icon: <BrainCircuit />, title: "Explainable ML risk", text: "XGBoost trained on 7,094 NHANES adults with FibroScan. TreeSHAP shows exactly what raises or lowers your estimate.", tag: "AUROC 0.839" },
  { icon: <Sparkles />, title: "Tool-using AI copilot", text: "Ask anything. The agent calls calculators, the risk model, LiverTox and the guidelines, and shows every step it took.", tag: "Agentic" },
  { icon: <BookOpenCheck />, title: "Cited guideline answers", text: "Hybrid search over AASLD 2023 and EASL 2024. Every claim is cited, and it says so when the guidelines don't cover a question.", tag: "Grounded RAG" },
  { icon: <FlaskConical />, title: "Lab report reader", text: "Drop in a PDF. Indian and SI formats (lakh/cumm, mmol/L) are normalised and scored automatically.", tag: "PDF → scores" },
  { icon: <Salad />, title: "Meal analyser", text: "Describe or photograph a meal. Nutrients come from USDA data, and the liver-diet score explains every point.", tag: "USDA grounded" },
];

const STATS = [
  { value: 0.839, decimals: 3, suffix: "", label: "AUROC for liver-fat risk", sub: "beats the Fatty Liver Index (0.821)" },
  { value: 93.8, decimals: 1, suffix: "%", label: "Gold passage in top-3", sub: "hybrid retrieval vs 84.4% single-method" },
  { value: 62, decimals: 0, suffix: "%", label: "Less calorie error", sub: "with LLM re-ranking (Nutrition5k)" },
  { value: 99.4, decimals: 1, suffix: "%", label: "Medicine lookup accuracy", sub: "909 brand, generic and misspelt queries" },
];

const SOURCES = ["AASLD 2023 Guidance", "EASL–EASD–EASO 2024", "NIH LiverTox", "USDA FoodData Central", "CDC NHANES"];

export default function Landing() {
  const demo = useDemo();
  const { signedIn } = useAuth();
  return (
    <div className="grain relative min-h-screen overflow-x-hidden">
      <Aurora />
      {/* nav */}
      <header className="sticky top-0 z-40 border-b border-white/[0.05] bg-ink-950/50 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-3.5">
          <Logo />
          <nav className="hidden items-center gap-8 text-sm text-slate-400 md:flex">
            <a href="#features" className="transition hover:text-white">Features</a>
            <a href="#results" className="transition hover:text-white">Results</a>
            <a href="#how" className="transition hover:text-white">How it works</a>
            <a href="#safety" className="transition hover:text-white">Safety</a>
          </nav>
          <div className="flex items-center gap-2">
            {signedIn ? (
              <Link to="/app"><Button size="sm" icon={<ArrowRight className="h-4 w-4" />}>Open app</Button></Link>
            ) : (
              <>
                <Link to="/login" className="hidden sm:block"><Button variant="ghost" size="sm">Sign in</Button></Link>
                <Button size="sm" onClick={demo.start} loading={demo.loading}>Try the demo</Button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* hero */}
      <section className="relative mx-auto grid max-w-7xl items-center gap-12 px-5 pb-20 pt-16 lg:grid-cols-[1.15fr_1fr] lg:pt-24">
        <div>
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            className="spin-border mb-6 inline-flex items-center gap-2 rounded-full px-3.5 py-1.5 text-xs text-slate-300">
            <span className="relative flex h-2 w-2"><span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-400 opacity-60" /><span className="relative inline-flex h-2 w-2 rounded-full bg-brand-400" /></span>
            Grounded · Evaluated · Runs fully offline
          </motion.div>
          <motion.h1 initial={{ opacity: 0, y: 20, filter: "blur(8px)" }} animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
            className="text-[2.6rem] font-extrabold leading-[1.05] sm:text-6xl lg:text-[3.5rem] xl:text-[4rem]">
            Understand your liver<br /><span className="text-gradient">before it's too late.</span>
          </motion.h1>
          <motion.p initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2, duration: 0.8 }}
            className="mt-6 max-w-xl text-lg leading-relaxed text-slate-400">
            Fatty liver disease affects 1 in 3 adults and usually has no symptoms. Liver Buddy turns your checkup numbers,
            lab reports, meals and medicines into clear guidance, with <span className="text-slate-200">every number computed, every claim cited.</span>
          </motion.p>
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35, duration: 0.8 }}
            className="mt-9 flex flex-wrap items-center gap-3">
            <Button size="lg" onClick={demo.start} loading={demo.loading} icon={<Sparkles className="h-4 w-4" />}>Explore the live demo</Button>
            <Link to="/app/check"><Button size="lg" variant="outline" icon={<Calculator className="h-4 w-4" />}>Check my scores</Button></Link>
          </motion.div>
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }} className="mt-8 flex items-center gap-5 text-xs text-slate-500">
            <span className="flex items-center gap-1.5"><ShieldCheck className="h-4 w-4 text-brand-400" />Safety rules run before the AI</span>
            <span className="hidden items-center gap-1.5 sm:flex"><Stethoscope className="h-4 w-4 text-brand-400" />Built on clinical guidelines</span>
          </motion.div>
        </div>
        <HeroPreview />
      </section>

      {/* sources strip */}
      <section className="border-y border-white/[0.05] bg-white/[0.015] py-6">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-center gap-x-10 gap-y-3 px-5">
          <span className="label">Grounded in</span>
          {SOURCES.map((s, i) => (
            <motion.span key={s} initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} transition={{ delay: i * 0.08 }}
              className="font-display text-sm font-semibold text-slate-400">{s}</motion.span>
          ))}
        </div>
      </section>

      {/* features */}
      <section id="features" className="mx-auto max-w-7xl px-5 py-24">
        <Reveal className="mx-auto mb-14 max-w-2xl text-center">
          <div className="label mb-3 text-brand-300/80">Everything in one place</div>
          <h2 className="text-3xl font-bold sm:text-5xl">An AI that knows what it <span className="text-gradient">shouldn't</span> guess</h2>
          <p className="mt-4 text-slate-400">The language model routes, extracts and explains. Scores, probabilities, nutrients and drug-risk grades come from code and curated data.</p>
        </Reveal>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => (
            <Reveal key={f.title} delay={i * 0.06}>
              <Spotlight className="glass glass-hover h-full p-6">
                <div className="relative">
                  <div className="mb-5 flex items-center justify-between">
                    <div className="grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-brand-400/20 to-sky2-400/10 text-brand-300 ring-1 ring-brand-300/20 [&>svg]:h-5 [&>svg]:w-5">{f.icon}</div>
                    <span className="chip !text-[10px]">{f.tag}</span>
                  </div>
                  <h3 className="mb-2 text-lg font-semibold">{f.title}</h3>
                  <p className="text-sm leading-relaxed text-slate-400">{f.text}</p>
                </div>
              </Spotlight>
            </Reveal>
          ))}
        </div>
      </section>

      {/* results */}
      <section id="results" className="relative py-24">
        <div className="absolute inset-0 -z-10 bg-gradient-to-b from-transparent via-brand-400/[0.04] to-transparent" />
        <div className="mx-auto max-w-7xl px-5">
          <Reveal className="mb-14 text-center">
            <div className="label mb-3 text-brand-300/80">Measured, not promised</div>
            <h2 className="text-3xl font-bold sm:text-5xl">Every claim has a number behind it</h2>
            <p className="mx-auto mt-4 max-w-xl text-slate-400">From the project's evaluation suite: held-out test sets, gold-labelled questions and public benchmarks.</p>
          </Reveal>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {STATS.map((s, i) => (
              <Reveal key={s.label} delay={i * 0.08}>
                <div className="glass glass-hover p-6">
                  <div className="font-display text-5xl font-extrabold text-gradient">
                    <AnimatedNumber value={s.value} decimals={s.decimals} suffix={s.suffix} duration={1.8} />
                  </div>
                  <div className="mt-3 text-sm font-semibold text-white">{s.label}</div>
                  <div className="mt-1 text-xs text-slate-400">{s.sub}</div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* how it works */}
      <section id="how" className="mx-auto max-w-7xl px-5 py-24">
        <Reveal className="mb-14 text-center">
          <div className="label mb-3 text-brand-300/80">How it works</div>
          <h2 className="text-3xl font-bold sm:text-5xl">From a blood test to a plan in seconds</h2>
        </Reveal>
        <div className="relative grid gap-6 md:grid-cols-3">
          <motion.div className="absolute left-[16%] right-[16%] top-9 hidden h-px origin-left bg-gradient-to-r from-brand-300 via-sky2-400 to-violet-400 md:block"
            initial={{ scaleX: 0 }} whileInView={{ scaleX: 1 }} viewport={{ once: true }} transition={{ duration: 1.6, ease: "easeInOut" }} />
          {[
            { n: "01", icon: <FlaskConical />, t: "Add your numbers", d: "Upload a lab report or type in your ALT, AST, platelets, weight and waist." },
            { n: "02", icon: <Calculator />, t: "Get validated scores", d: "FIB-4 and four other scores, the MASLD criteria, and an ML risk estimate with its reasons." },
            { n: "03", icon: <BookOpenCheck />, t: "Know what to do next", d: "Guideline-backed next steps, meal feedback and medicine checks to take to your doctor." },
          ].map((s, i) => (
            <Reveal key={s.n} delay={0.2 + i * 0.25} className="relative text-center">
              <div className="relative mx-auto mb-6 grid h-[72px] w-[72px] place-items-center rounded-2xl bg-ink-900 text-brand-300 ring-1 ring-white/10 [&>svg]:h-7 [&>svg]:w-7">
                {s.icon}
                <span className="absolute -right-2 -top-2 rounded-full bg-gradient-to-r from-brand-300 to-sky2-400 px-2 py-0.5 font-display text-[10px] font-bold text-ink-950">{s.n}</span>
              </div>
              <h3 className="mb-2 text-lg font-semibold">{s.t}</h3>
              <p className="mx-auto max-w-xs text-sm text-slate-400">{s.d}</p>
            </Reveal>
          ))}
        </div>
      </section>

      {/* safety */}
      <section id="safety" className="mx-auto max-w-7xl px-5 py-20">
        <Reveal>
          <div className="glass relative overflow-hidden p-8 md:p-12">
            <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-brand-400/10 blur-3xl" />
            <div className="relative grid gap-10 md:grid-cols-2">
              <div>
                <ShieldCheck className="mb-4 h-10 w-10 text-brand-300" />
                <h2 className="text-3xl font-bold">Safety is code, not a prompt</h2>
                <p className="mt-4 text-slate-400">Emergencies, crisis messages and dose questions are caught by fixed, tested rules before any AI model runs. CI fails if a single emergency is missed.</p>
              </div>
              <ul className="space-y-3 text-sm">
                {[
                  ["Vomiting blood, confusion, overdose", "Directed to emergency care immediately"],
                  ["Thoughts of self-harm", "Crisis support (Tele-MANAS 14416)"],
                  ["\"How much should I take?\"", "Never answers dosing questions"],
                  ["Answers without evidence", "Withheld. Invented citations are stripped"],
                ].map(([a, b]) => (
                  <li key={a} className="flex items-start gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] p-3.5">
                    <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-brand-400" />
                    <div><div className="font-medium text-white">{a}</div><div className="text-slate-400">{b}</div></div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </Reveal>
      </section>

      {/* cta */}
      <section className="mx-auto max-w-4xl px-5 py-24 text-center">
        <Reveal>
          <h2 className="text-4xl font-bold sm:text-5xl">See it with a real patient journey</h2>
          <p className="mx-auto mt-4 max-w-xl text-slate-400">One click creates a demo patient with nine months of labs, weights, medicines and meals. No sign-up needed.</p>
          <div className="mt-9 flex justify-center gap-3">
            <Button size="lg" onClick={demo.start} loading={demo.loading} icon={<Sparkles className="h-4 w-4" />}>Launch demo</Button>
            <Link to="/register"><Button size="lg" variant="outline">Create my account</Button></Link>
          </div>
        </Reveal>
      </section>

      <footer className="border-t border-white/[0.05] py-10">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-5 text-xs text-slate-500 md:flex-row">
          <Logo size={26} />
          <p className={cx("max-w-xl text-center")}>Educational project, not a medical device. It does not diagnose or prescribe. Always consult a qualified clinician.</p>
          <span className="flex items-center gap-1.5"><Github className="h-4 w-4" /> Built by Akhil Reddy</span>
        </div>
      </footer>
    </div>
  );
}
