import "@fontsource-variable/inter";
import "@fontsource-variable/plus-jakarta-sans";
import "./index.css";

import { MotionConfig } from "framer-motion";
import { lazy, StrictMode, Suspense } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { ToastProvider } from "./lib/hooks";
import Landing from "./pages/Landing";

const Auth = lazy(() => import("./pages/Auth"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Chat = lazy(() => import("./pages/Chat"));
const Check = lazy(() => import("./pages/Check"));
const Labs = lazy(() => import("./pages/Labs"));
const Meals = lazy(() => import("./pages/Meals"));
const Meds = lazy(() => import("./pages/Meds"));
const Ask = lazy(() => import("./pages/Ask"));
const Profile = lazy(() => import("./pages/Profile"));

function Fallback() {
  return (
    <div className="grid min-h-[60vh] place-items-center">
      <div className="h-10 w-10 animate-spin rounded-full border-2 border-white/10 border-t-brand-300" />
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <MotionConfig reducedMotion="user">
      <ToastProvider>
        <BrowserRouter>
          <Suspense fallback={<Fallback />}>
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={<Auth mode="login" />} />
              <Route path="/register" element={<Auth mode="register" />} />
              <Route path="/app" element={<AppShell />}>
                <Route index element={<Dashboard />} />
                <Route path="chat" element={<Chat />} />
                <Route path="check" element={<Check />} />
                <Route path="labs" element={<Labs />} />
                <Route path="meals" element={<Meals />} />
                <Route path="meds" element={<Meds />} />
                <Route path="ask" element={<Ask />} />
                <Route path="profile" element={<Profile />} />
              </Route>
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </ToastProvider>
    </MotionConfig>
  </StrictMode>,
);
