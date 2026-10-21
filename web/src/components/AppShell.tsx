import { AnimatePresence, motion } from "framer-motion";
import {
  Activity, Calculator, FlaskConical, LayoutDashboard, LogOut, Menu, MessageCircleHeart, Pill, Salad, ScrollText, UserRound, X,
} from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/hooks";
import { Aurora, Logo, cx } from "./ui";

const NAV = [
  { to: "/app", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/app/chat", label: "Ask Liver Buddy", icon: MessageCircleHeart },
  { to: "/app/check", label: "Scores & risk", icon: Calculator },
  { to: "/app/labs", label: "Lab report", icon: FlaskConical },
  { to: "/app/meals", label: "Meals", icon: Salad },
  { to: "/app/meds", label: "Medicines", icon: Pill },
  { to: "/app/ask", label: "Guidelines Q&A", icon: ScrollText },
];

function NavItems({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="flex flex-col gap-1">
      {NAV.map(({ to, label, icon: Icon, end }) => (
        <NavLink key={to} to={to} end={end} onClick={onNavigate}
          className={({ isActive }) => cx("group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition",
            isActive ? "text-white" : "text-slate-400 hover:bg-white/[0.04] hover:text-slate-100")}>
          {({ isActive }) => (
            <>
              {isActive && (
                <motion.span layoutId="nav-pill" transition={{ type: "spring", stiffness: 420, damping: 36 }}
                  className="absolute inset-0 rounded-xl border border-white/10 bg-gradient-to-r from-brand-400/[0.14] to-sky2-400/[0.06]" />
              )}
              {isActive && <motion.span layoutId="nav-bar" className="absolute -left-3 top-2 bottom-2 w-1 rounded-r-full bg-gradient-to-b from-brand-300 to-sky2-400" />}
              <Icon className={cx("relative h-[18px] w-[18px] transition", isActive ? "text-brand-300" : "group-hover:text-brand-300/80")} />
              <span className="relative font-medium">{label}</span>
            </>
          )}
        </NavLink>
      ))}
    </nav>
  );
}

function SidebarFooter({ onNavigate }: { onNavigate?: () => void }) {
  const { signedIn, signOut } = useAuth();
  const nav = useNavigate();
  return (
    <div className="mt-auto space-y-1 border-t border-white/[0.06] pt-4">
      {signedIn ? (
        <>
          <NavLink to="/app/profile" onClick={onNavigate}
            className={({ isActive }) => cx("flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition",
              isActive ? "bg-white/[0.06] text-white" : "text-slate-400 hover:bg-white/[0.04] hover:text-white")}>
            <UserRound className="h-[18px] w-[18px]" /> Profile
          </NavLink>
          <button onClick={() => { signOut(); nav("/"); }}
            className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-400 transition hover:bg-white/[0.04] hover:text-rose-300">
            <LogOut className="h-[18px] w-[18px]" /> Sign out
          </button>
        </>
      ) : (
        <NavLink to="/login" className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-brand-300 hover:bg-white/[0.04]">
          <UserRound className="h-[18px] w-[18px]" /> Sign in to save history
        </NavLink>
      )}
      <div className="flex items-center gap-2 px-3 pt-3 text-[11px] text-slate-500">
        <Activity className="h-3.5 w-3.5 text-brand-400" /> Not a medical device
      </div>
    </div>
  );
}

export function AppShell() {
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  return (
    <div className="grain min-h-screen">
      <Aurora intensity={0.7} />
      {/* desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-white/[0.06] bg-ink-950/60 px-5 py-6 backdrop-blur-2xl lg:flex">
        <NavLink to="/" className="mb-8 px-1"><Logo /></NavLink>
        <NavItems />
        <SidebarFooter />
      </aside>
      {/* mobile top bar + drawer */}
      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-white/[0.06] bg-ink-950/70 px-4 py-3 backdrop-blur-xl lg:hidden">
        <NavLink to="/"><Logo size={28} /></NavLink>
        <button onClick={() => setOpen(true)} className="rounded-lg p-2 text-slate-300 hover:bg-white/[0.06]" aria-label="Open menu">
          <Menu className="h-5 w-5" />
        </button>
      </header>
      <AnimatePresence>
        {open && (
          <>
            <motion.div className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden" initial={{ opacity: 0 }}
              animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setOpen(false)} />
            <motion.aside className="fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-white/10 bg-ink-900 px-5 py-6 lg:hidden"
              initial={{ x: -300 }} animate={{ x: 0 }} exit={{ x: -300 }} transition={{ type: "spring", stiffness: 380, damping: 38 }}>
              <div className="mb-8 flex items-center justify-between">
                <Logo />
                <button onClick={() => setOpen(false)} className="rounded-lg p-1.5 text-slate-400 hover:text-white" aria-label="Close menu">
                  <X className="h-5 w-5" />
                </button>
              </div>
              <NavItems onNavigate={() => setOpen(false)} />
              <SidebarFooter onNavigate={() => setOpen(false)} />
            </motion.aside>
          </>
        )}
      </AnimatePresence>
      <main className="relative z-10 lg:pl-64">
        <AnimatePresence mode="wait">
          <motion.div key={loc.pathname} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }} className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-10 lg:py-10">
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
