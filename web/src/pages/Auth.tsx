import { AnimatePresence, motion } from "framer-motion";
import { ArrowLeft, Lock, Mail, Sparkles, UserRound } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { errorText, useAuth, useToast } from "../lib/hooks";
import { Aurora, Button, ErrorNote, Logo } from "../components/ui";

export default function AuthPage({ mode: initial }: { mode: "login" | "register" }) {
  const [mode, setMode] = useState(initial);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<"form" | "demo" | null>(null);
  const { signIn } = useAuth();
  const nav = useNavigate();
  const toast = useToast();

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading("form");
    try {
      const r = mode === "login" ? await api.login(email, password) : await api.register(email, password, name);
      signIn(r.access_token);
      toast("ok", mode === "login" ? "Welcome back!" : "Account created. Add your profile to personalise your scores.");
      nav(mode === "login" ? "/app" : "/app/profile");
    } catch (err) {
      setError(errorText(err));
    } finally {
      setLoading(null);
    }
  };

  const demo = async () => {
    setLoading("demo");
    try {
      signIn((await api.demo()).access_token);
      nav("/app");
    } catch (err) {
      setError(errorText(err));
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="grain relative grid min-h-screen lg:grid-cols-2">
      <Aurora />
      <div className="relative hidden flex-col justify-between overflow-hidden border-r border-white/[0.05] p-12 lg:flex">
        <Link to="/"><Logo /></Link>
        <div>
          <motion.blockquote initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2, duration: 0.8 }}
            className="font-display text-3xl font-semibold leading-snug text-white">
            "Compute what can be computed, cite what you claim, and refuse what you shouldn't answer."
          </motion.blockquote>
          <p className="mt-4 text-sm text-slate-400">The design principle behind Liver Buddy.</p>
        </div>
        <div className="grid grid-cols-3 gap-3 text-center">
          {[["0.839", "risk AUROC"], ["1,175", "drugs checked"], ["7,788", "USDA foods"]].map(([v, l], i) => (
            <motion.div key={l} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 + i * 0.1 }} className="glass p-4">
              <div className="font-display text-2xl font-bold text-gradient">{v}</div>
              <div className="text-[11px] text-slate-400">{l}</div>
            </motion.div>
          ))}
        </div>
      </div>

      <div className="flex flex-col justify-center px-6 py-12 sm:px-12">
        <Link to="/" className="mb-10 flex items-center gap-2 text-sm text-slate-400 hover:text-white lg:hidden"><ArrowLeft className="h-4 w-4" />Back</Link>
        <div className="mx-auto w-full max-w-sm">
          <AnimatePresence mode="wait">
            <motion.div key={mode} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.3 }}>
              <h1 className="text-3xl font-bold">{mode === "login" ? "Welcome back" : "Create your account"}</h1>
              <p className="mt-2 text-sm text-slate-400">
                {mode === "login" ? "Sign in to see your liver health over time." : "Track your labs, meals and medicines in one place."}
              </p>
            </motion.div>
          </AnimatePresence>

          <form onSubmit={submit} className="mt-8 space-y-3.5">
            <AnimatePresence>
              {mode === "register" && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }}>
                  <div className="relative">
                    <UserRound className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                    <input className="input pl-10" placeholder="Your name" value={name} onChange={(e) => setName(e.target.value)} />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            <div className="relative">
              <Mail className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
              <input className="input pl-10" type="email" required placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
            </div>
            <div className="relative">
              <Lock className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
              <input className="input pl-10" type="password" required minLength={8} placeholder="Password (8+ characters)" value={password}
                onChange={(e) => setPassword(e.target.value)} autoComplete={mode === "login" ? "current-password" : "new-password"} />
            </div>
            <ErrorNote error={error} />
            <Button type="submit" size="lg" className="w-full" loading={loading === "form"}>
              {mode === "login" ? "Sign in" : "Create account"}
            </Button>
          </form>

          <div className="my-6 flex items-center gap-3 text-xs text-slate-500">
            <div className="h-px flex-1 bg-white/10" />or<div className="h-px flex-1 bg-white/10" />
          </div>
          <Button variant="outline" size="lg" className="w-full" onClick={demo} loading={loading === "demo"} icon={<Sparkles className="h-4 w-4 text-brand-300" />}>
            Continue with a demo patient
          </Button>

          <p className="mt-8 text-center text-sm text-slate-400">
            {mode === "login" ? "New here? " : "Already have an account? "}
            <button className="font-medium text-brand-300 hover:text-brand-200" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(null); }}>
              {mode === "login" ? "Create an account" : "Sign in"}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
