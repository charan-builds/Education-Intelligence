"use client";

import * as React from "react";

import { X } from "lucide-react";

import { cn } from "@/utils/cn";

import Button from "@/components/ui/Button";

type ModalProps = {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
};

export function Modal({ open, onClose, title, description, children, footer }: ModalProps) {
  React.useEffect(() => {
    if (!open) {
      return;
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-slate-950/55 backdrop-blur-sm"
        aria-label="Close modal"
        onClick={onClose}
      />
      <div
        className={cn(
          "relative z-10 w-full max-w-lg rounded-[28px] border border-white/70 bg-white/95 p-6 shadow-2xl dark:border-slate-700 dark:bg-slate-900/95",
        )}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-xl font-semibold text-slate-950 dark:text-slate-50">{title}</h3>
            {description ? <p className="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-400">{description}</p> : null}
          </div>
          <Button variant="ghost" className="h-9 rounded-xl px-3 text-xs" onClick={onClose} aria-label="Close">
            <X className="h-4 w-4" />
          </Button>
        </div>
        <div className="mt-5">{children}</div>
        {footer ? <div className="mt-6 flex items-center justify-end gap-3">{footer}</div> : null}
      </div>
    </div>
  );
}
