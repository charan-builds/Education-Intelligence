"use client";

import { AnimatePresence, motion } from "framer-motion";
import {
  createContext,
  PropsWithChildren,
  useContext,
  useMemo,
  useState,
} from "react";
import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";

type ToastVariant = "success" | "error" | "info";

type ToastInput = {
  title: string;
  description?: string;
  variant?: ToastVariant;
};

type ToastRecord = ToastInput & {
  id: number;
  variant: ToastVariant;
};

type ToastContextValue = {
  toast: (input: ToastInput) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

function variantStyles(variant: ToastVariant) {
  if (variant === "success") {
    return {
      icon: CheckCircle2,
      className: "border-violet-200 bg-[linear-gradient(135deg,rgba(255,255,255,0.96),rgba(243,232,255,0.96))] text-violet-950 dark:border-violet-500/30 dark:bg-violet-500/12 dark:text-violet-100",
    };
  }

  if (variant === "error") {
    return {
      icon: AlertCircle,
      className: "border-violet-200 bg-[linear-gradient(135deg,rgba(255,255,255,0.96),rgba(250,245,255,0.96))] text-violet-950 dark:border-violet-500/30 dark:bg-violet-500/12 dark:text-violet-100",
    };
  }

  return {
    icon: Info,
    className: "border-violet-200 bg-[linear-gradient(135deg,rgba(255,255,255,0.96),rgba(237,233,254,0.96))] text-violet-950 dark:border-violet-500/30 dark:bg-violet-500/12 dark:text-violet-100",
  };
}

export function ToastProvider({ children }: PropsWithChildren) {
  const [toasts, setToasts] = useState<ToastRecord[]>([]);

  const toast = (input: ToastInput) => {
    const nextToast: ToastRecord = {
      id: Date.now() + Math.random(),
      title: input.title,
      description: input.description,
      variant: input.variant ?? "info",
    };

    setToasts((current) => [...current, nextToast]);

    window.setTimeout(() => {
      setToasts((current) => current.filter((item) => item.id !== nextToast.id));
    }, 4200);
  };

  const value = useMemo(() => ({ toast }), []);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed inset-x-0 top-4 z-[100] flex justify-center px-4">
        <div className="flex w-full max-w-md flex-col gap-3">
          <AnimatePresence>
            {toasts.map((item) => {
              const { icon: Icon, className } = variantStyles(item.variant);
              return (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: -18, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -14, scale: 0.98 }}
                  className={`pointer-events-auto rounded-2xl border px-4 py-3 shadow-panel ${className}`}
                >
                  <div className="flex items-start gap-3">
                    <Icon className="mt-0.5 h-5 w-5 flex-none" />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-semibold">{item.title}</p>
                      {item.description ? <p className="mt-1 text-sm opacity-85">{item.description}</p> : null}
                    </div>
                    <button
                      type="button"
                      onClick={() => setToasts((current) => current.filter((toastItem) => toastItem.id !== item.id))}
                      className="rounded-full p-1 opacity-70 transition hover:bg-black/5 hover:opacity-100 dark:hover:bg-white/5"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
}
