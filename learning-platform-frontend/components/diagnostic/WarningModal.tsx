"use client";

import Button from "@/components/ui/Button";

type Props = {
  open: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  onConfirm: () => void;
  secondaryLabel?: string;
  onSecondary?: () => void;
  blocking?: boolean;
};

export default function WarningModal({
  open,
  title,
  description,
  confirmLabel = "Continue",
  onConfirm,
  secondaryLabel,
  onSecondary,
  blocking = false,
}: Props) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-[28px] border border-amber-400/20 bg-[#111827] p-6 shadow-[0_24px_80px_-20px_rgba(15,23,42,0.85)]">
        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-amber-300">Diagnostic Warning</p>
          <h3 className="text-2xl font-semibold text-slate-50">{title}</h3>
          <p className="text-sm leading-7 text-slate-300">{description}</p>
        </div>
        <div className="mt-6 flex flex-wrap justify-end gap-3">
          {secondaryLabel && onSecondary && !blocking ? (
            <Button variant="secondary" onClick={onSecondary}>
              {secondaryLabel}
            </Button>
          ) : null}
          <Button className="bg-violet-600 hover:bg-violet-500" onClick={onConfirm}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}

