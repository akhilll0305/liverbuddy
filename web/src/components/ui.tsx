import { animate, motion, useInView, useMotionValue, useTransform, type HTMLMotionProps } from "framer-motion";
import { clsx } from "clsx";
import { Loader2 } from "lucide-react";
import { forwardRef, useEffect, useId, useRef, useState, type ButtonHTMLAttributes, type ReactNode } from "react";
import { RISK, type Tone } from "../lib/theme";

export const cx = clsx;

/* ---------------------------------------------------------------- Button */
type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost" | "outline" | "danger";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  icon?: ReactNode;
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "primary", size = "md", loading, icon, className, children, disabled, ...rest },
  ref,
) {
  const sizes = { sm: "h-8 px-3 text-xs gap-1.5", md: "h-10 px-4 text-sm gap-2", lg: "h-12 px-6 text-[15px] gap-2.5" };
  const variants = {
    primary:
      "relative overflow-hidden text-ink-950 font-semibold bg-gradient-to-r from-brand-300 via-brand-400 to-sky2-400 shadow-glow hover:brightness-110 " +
      "before:absolute before:inset-0 before:-translate-x-full before:bg-gradient-to-r before:from-transparent before:via-white/40 before:to-transparent hover:before:translate-x-full before:transition-transform before:duration-700",
    ghost: "text-slate-300 hover:text-white hover:bg-white/[0.06]",
    outline: "text-slate-200 border border-white/[0.12] bg-white/[0.03] hover:bg-white/[0.07] hover:border-white/20",
    danger: "text-rose-200 border border-rose-400/30 bg-rose-500/10 hover:bg-rose-500/20",
  };
  return (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cx(
        "inline-flex select-none items-center justify-center rounded-xl font-medium transition-all duration-200 active:scale-[.97] disabled:pointer-events-none disabled:opacity-50",
        sizes[size],
        variants[variant],
        className,
      )}
      {...rest}
    >
      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : icon}
      <span className="relative">{children}</span>
    </button>
  );
});

/* ---------------------------------------------------------------- Card */
export function Card({ className, children, hover, ...rest }: HTMLMotionProps<"div"> & { hover?: boolean }) {
  return (
    <motion.div className={cx("glass p-5", hover && "glass-hover", className)} {...rest}>
      {children}
    </motion.div>
  );
}

export function CardTitle({ icon, title, action, sub }: { icon?: ReactNode; title: string; sub?: string; action?: ReactNode }) {
  return (
    <div className="mb-4 flex items-start justify-between gap-3">
      <div className="flex items-center gap-3">
        {icon && <div className="grid h-9 w-9 place-items-center rounded-xl bg-white/[0.05] text-brand-300 ring-1 ring-white/10">{icon}</div>}
        <div>
          <h3 className="text-[15px] font-semibold">{title}</h3>
          {sub && <p className="text-xs text-slate-400">{sub}</p>}
        </div>
      </div>
      {action}
    </div>
  );
}

/* ---------------------------------------------------------------- Badge */
export function Badge({ tone = "none", children, className }: { tone?: Tone; children: ReactNode; className?: string }) {
  const t = RISK[tone];
  return (
    <span className={cx("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ring-1", t.bg, t.text, t.ring, className)}>
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: t.hex }} />
      {children}
    </span>
  );
}

/* ---------------------------------------------------------------- Animated number */
export function AnimatedNumber({ value, decimals = 0, suffix = "", className, duration = 1.2 }: {
  value: number; decimals?: number; suffix?: string; className?: string; duration?: number;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const mv = useMotionValue(0);
  const text = useTransform(mv, (v) => v.toFixed(decimals) + suffix);
  useEffect(() => {
    if (!inView) return;
    const controls = animate(mv, value, { duration, ease: [0.16, 1, 0.3, 1] });
    return () => controls.stop();
  }, [inView, value, mv, duration]);
  return <motion.span ref={ref} className={className}>{text}</motion.span>;
}

/* ---------------------------------------------------------------- Radial gauge */
export function Gauge({ value, min = 0, max, ticks = [], tone, size = 132, display }: {
  value: number | null; min?: number; max: number; ticks?: number[]; tone: Tone; size?: number; display?: string;
}) {
  const stroke = 10;
  const r = (size - stroke) / 2;
  const c = Math.PI * r; // half circle
  const frac = value === null ? 0 : Math.min(1, Math.max(0, (value - min) / (max - min)));
  const color = RISK[tone].hex;
  const id = `g${useId().replace(/:/g, "")}`;
  const point = (f: number, rr: number) => {
    const a = Math.PI * (1 - f);
    return [size / 2 + rr * Math.cos(a), size / 2 - rr * Math.sin(a)];
  };
  return (
    <div className="relative" style={{ width: size, height: size / 2 + 18 }}>
      <svg width={size} height={size / 2 + stroke} className="overflow-visible">
        <defs>
          <linearGradient id={id} x1="0" x2="1">
            <stop offset="0" stopColor={color} stopOpacity=".55" />
            <stop offset="1" stopColor={color} />
          </linearGradient>
        </defs>
        <path d={`M ${stroke / 2} ${size / 2} A ${r} ${r} 0 0 1 ${size - stroke / 2} ${size / 2}`} fill="none"
          stroke="rgba(255,255,255,.07)" strokeWidth={stroke} strokeLinecap="round" />
        <motion.path
          d={`M ${stroke / 2} ${size / 2} A ${r} ${r} 0 0 1 ${size - stroke / 2} ${size / 2}`}
          fill="none" stroke={`url(#${id})`} strokeWidth={stroke} strokeLinecap="round"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: c * (1 - frac) }}
          transition={{ duration: 1.4, ease: [0.16, 1, 0.3, 1], delay: 0.15 }}
          style={{ filter: `drop-shadow(0 0 8px ${color}66)` }}
        />
        {ticks.map((t) => {
          const f = (t - min) / (max - min);
          const [x1, y1] = point(f, r - stroke);
          const [x2, y2] = point(f, r + stroke * 0.9);
          return <line key={t} x1={x1} y1={y1} x2={x2} y2={y2} stroke="rgba(255,255,255,.35)" strokeWidth={1.5} />;
        })}
      </svg>
      <div className="absolute inset-x-0 bottom-0 text-center">
        <div className="font-display text-2xl font-bold text-white">
          {value === null ? <span className="text-slate-500">—</span> : display ?? <AnimatedNumber value={value} decimals={Math.abs(value) < 10 ? 2 : 1} />}
        </div>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- Ring (0..1) */
export function Ring({ value, size = 120, stroke = 10, color, children }: {
  value: number; size?: number; stroke?: number; color: string; children?: ReactNode;
}) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  return (
    <div className="relative grid place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,.07)" strokeWidth={stroke} />
        <motion.circle
          cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round"
          strokeDasharray={c} initial={{ strokeDashoffset: c }} animate={{ strokeDashoffset: c * (1 - value) }}
          transition={{ duration: 1.5, ease: [0.16, 1, 0.3, 1] }} style={{ filter: `drop-shadow(0 0 10px ${color}55)` }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center">{children}</div>
    </div>
  );
}

/* ---------------------------------------------------------------- Reveal (stagger children) */
export const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.07, delayChildren: 0.05 } } };
export const rise = {
  hidden: { opacity: 0, y: 18, filter: "blur(6px)" },
  show: { opacity: 1, y: 0, filter: "blur(0px)", transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] } },
};

export function Reveal({ children, className, delay = 0 }: { children: ReactNode; className?: string; delay?: number }) {
  return (
    <motion.div className={className} initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }} transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1], delay }}>
      {children}
    </motion.div>
  );
}

/* ---------------------------------------------------------------- Page header */
export function PageHeader({ eyebrow, title, sub, action }: { eyebrow?: string; title: ReactNode; sub?: ReactNode; action?: ReactNode }) {
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
      className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        {eyebrow && <div className="label mb-2 text-brand-300/80">{eyebrow}</div>}
        <h1 className="text-3xl font-bold md:text-4xl">{title}</h1>
        {sub && <p className="mt-2 max-w-2xl text-sm text-slate-400">{sub}</p>}
      </div>
      {action}
    </motion.div>
  );
}

/* ---------------------------------------------------------------- Field */
export function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 flex items-baseline justify-between text-xs font-medium text-slate-300">
        {label}
        {hint && <span className="text-[10px] font-normal text-slate-500">{hint}</span>}
      </span>
      {children}
    </label>
  );
}

export function NumberInput({ value, onChange, placeholder, step = "any" }: {
  value: number | null | undefined; onChange: (v: number | null) => void; placeholder?: string; step?: string;
}) {
  return (
    <input type="number" inputMode="decimal" step={step} className="input" placeholder={placeholder}
      value={value ?? ""} onChange={(e) => onChange(e.target.value === "" ? null : Number(e.target.value))} />
  );
}

export function Toggle({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button type="button" onClick={() => onChange(!checked)}
      className={cx("flex w-full items-center justify-between gap-3 rounded-xl border px-3.5 py-2.5 text-left text-sm transition",
        checked ? "border-brand-400/40 bg-brand-400/[0.07] text-white" : "border-white/10 bg-ink-900/60 text-slate-300 hover:border-white/20")}>
      {label}
      <span className={cx("relative h-5 w-9 shrink-0 rounded-full transition", checked ? "bg-brand-400" : "bg-white/15")}>
        <motion.span layout transition={{ type: "spring", stiffness: 500, damping: 32 }}
          className={cx("absolute top-0.5 h-4 w-4 rounded-full bg-white shadow", checked ? "right-0.5" : "left-0.5")} />
      </span>
    </button>
  );
}

export function Segmented<T extends string>({ value, options, onChange, id }: {
  value: T; options: { value: T; label: string; icon?: ReactNode }[]; onChange: (v: T) => void; id: string;
}) {
  return (
    <div className="inline-flex rounded-xl border border-white/10 bg-ink-900/70 p-1">
      {options.map((o) => (
        <button key={o.value} type="button" onClick={() => onChange(o.value)}
          className={cx("relative flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-sm transition", value === o.value ? "text-ink-950" : "text-slate-400 hover:text-white")}>
          {value === o.value && (
            <motion.span layoutId={`seg-${id}`} className="absolute inset-0 rounded-lg bg-gradient-to-r from-brand-300 to-sky2-400"
              transition={{ type: "spring", stiffness: 400, damping: 34 }} />
          )}
          <span className="relative flex items-center gap-1.5 font-medium">{o.icon}{o.label}</span>
        </button>
      ))}
    </div>
  );
}

/* ---------------------------------------------------------------- States */
export function EmptyState({ icon, title, text, action }: { icon: ReactNode; title: string; text: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-14 text-center">
      <div className="relative mb-5">
        <div className="absolute inset-0 animate-pulse-ring rounded-2xl bg-brand-400/20" />
        <div className="relative grid h-14 w-14 place-items-center rounded-2xl bg-white/[0.05] text-brand-300 ring-1 ring-white/10">{icon}</div>
      </div>
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="mt-1 max-w-sm text-sm text-slate-400">{text}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cx("skeleton", className)} />;
}

export function ErrorNote({ error }: { error: string | null }) {
  if (!error) return null;
  return (
    <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-rose-400/25 bg-rose-500/[0.08] px-4 py-3 text-sm text-rose-200">
      {error}
    </motion.div>
  );
}

export function Disclaimer() {
  return (
    <p className="mt-10 text-center text-[11px] text-slate-500">
      Educational tool, not a medical device. It does not diagnose or prescribe. Always discuss results with your doctor.
    </p>
  );
}

/* ---------------------------------------------------------------- Logo */
export function Logo({ size = 32, withText = true }: { size?: number; withText?: boolean }) {
  const gid = `logo${useId().replace(/:/g, "")}`;
  return (
    <div className="flex items-center gap-2.5">
      <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden>
        <defs>
          <linearGradient id={gid} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#6ff2c8" />
            <stop offset="1" stopColor="#2fb2f5" />
          </linearGradient>
        </defs>
        <rect width="64" height="64" rx="18" fill="rgba(255,255,255,.04)" stroke="rgba(255,255,255,.1)" />
        <path d="M14 30c0-9 8-15 19-15 9 0 17 4 17 11 0 9-9 19-20 23-7 2-16-6-16-19z" fill={`url(#${gid})`} />
        <path d="M30 26c4 3 9 4 14 3" stroke="#05070d" strokeWidth="3" fill="none" strokeLinecap="round" />
      </svg>
      {withText && <span className="font-display text-[17px] font-bold tracking-tight text-white">Liver<span className="text-gradient">Buddy</span></span>}
    </div>
  );
}

/* ---------------------------------------------------------------- Aurora background */
export function Aurora({ intensity = 1 }: { intensity?: number }) {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden" aria-hidden style={{ opacity: intensity }}>
      <div className="absolute -left-[20%] -top-[30%] h-[70vmax] w-[70vmax] animate-aurora rounded-full bg-[radial-gradient(circle,rgba(52,224,176,.18),transparent_60%)] blur-3xl" />
      <div className="absolute -right-[25%] top-[10%] h-[60vmax] w-[60vmax] animate-aurora-slow rounded-full bg-[radial-gradient(circle,rgba(47,178,245,.16),transparent_60%)] blur-3xl" />
      <div className="absolute bottom-[-35%] left-[20%] h-[60vmax] w-[60vmax] animate-aurora rounded-full bg-[radial-gradient(circle,rgba(139,92,246,.12),transparent_60%)] blur-3xl" />
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,.025)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.025)_1px,transparent_1px)] bg-[size:56px_56px] [mask-image:radial-gradient(ellipse_at_center,black_20%,transparent_75%)]" />
    </div>
  );
}

/* ---------------------------------------------------------------- Spotlight card (cursor-follow glow) */
export function Spotlight({ children, className }: { children: ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState({ x: -999, y: -999 });
  return (
    <div ref={ref} className={cx("group relative overflow-hidden", className)}
      onMouseMove={(e) => {
        const r = ref.current!.getBoundingClientRect();
        setPos({ x: e.clientX - r.left, y: e.clientY - r.top });
      }}
      onMouseLeave={() => setPos({ x: -999, y: -999 })}>
      <div className="pointer-events-none absolute -inset-px opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{ background: `radial-gradient(420px circle at ${pos.x}px ${pos.y}px, rgba(52,224,176,.10), transparent 45%)` }} />
      {children}
    </div>
  );
}
