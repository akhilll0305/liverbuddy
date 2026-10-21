import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, CheckCircle2, Info, X } from "lucide-react";
import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { ApiError, auth } from "./api";

/* ---------------------------------------------------------------- auth */
export function useAuth() {
  const [token, setToken] = useState<string | null>(auth.token);
  useEffect(() => {
    const on = () => setToken(auth.token);
    window.addEventListener("lb-auth", on);
    window.addEventListener("storage", on);
    return () => {
      window.removeEventListener("lb-auth", on);
      window.removeEventListener("storage", on);
    };
  }, []);
  return { token, signedIn: !!token, signIn: (t: string) => auth.set(t), signOut: () => auth.set(null) };
}

/* ---------------------------------------------------------------- data loading */
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[] = [], enabled = true) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(enabled);
  const run = useRef(0);
  const reload = useCallback(() => {
    if (!enabled) return;
    const id = ++run.current;
    setLoading(true);
    fn()
      .then((d) => id === run.current && (setData(d), setError(null)))
      .catch((e: unknown) => id === run.current && setError(errorText(e)))
      .finally(() => id === run.current && setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, ...deps]);
  useEffect(reload, [reload]);
  return { data, error, loading, reload, setData };
}

export function errorText(e: unknown): string {
  if (e instanceof ApiError) return e.message;
  if (e instanceof Error) return e.message;
  return "Something went wrong.";
}

/* ---------------------------------------------------------------- toasts */
type Toast = { id: number; kind: "ok" | "info" | "warn"; text: string };
const ToastCtx = createContext<(kind: Toast["kind"], text: string) => void>(() => {});

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const push = useCallback((kind: Toast["kind"], text: string) => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, kind, text }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4200);
  }, []);
  const icon = { ok: <CheckCircle2 className="h-4 w-4 text-emerald-300" />, info: <Info className="h-4 w-4 text-sky-300" />,
    warn: <AlertTriangle className="h-4 w-4 text-amber-300" /> };
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div className="pointer-events-none fixed bottom-5 right-5 z-[100] flex w-[min(380px,calc(100vw-2.5rem))] flex-col gap-2">
        <AnimatePresence>
          {toasts.map((t) => (
            <motion.div key={t.id} layout initial={{ opacity: 0, y: 16, scale: 0.96 }} animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, x: 40 }} transition={{ type: "spring", stiffness: 380, damping: 30 }}
              className="glass pointer-events-auto flex items-start gap-3 !rounded-xl !bg-ink-850/90 px-4 py-3 text-sm text-slate-200">
              <span className="mt-0.5">{icon[t.kind]}</span>
              <span className="flex-1">{t.text}</span>
              <button onClick={() => setToasts((x) => x.filter((y) => y.id !== t.id))} className="text-slate-500 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastCtx.Provider>
  );
}

export const useToast = () => useContext(ToastCtx);
