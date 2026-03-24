"use client";

import { Fragment } from "react";

function renderInline(text: string) {
  const parts = text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g).filter(Boolean);
  return parts.map((part, index) => {
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={`${part}-${index}`} className="rounded bg-slate-900/10 px-1.5 py-0.5 text-[0.92em] dark:bg-white/10">
          {part.slice(1, -1)}
        </code>
      );
    }
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={`${part}-${index}`}>{part.slice(2, -2)}</strong>;
    }
    return <Fragment key={`${part}-${index}`}>{part}</Fragment>;
  });
}

export default function MarkdownMessage({ content }: { content: string }) {
  const lines = content.split("\n").filter((line, index, all) => line.trim() || (index < all.length - 1 && all[index + 1].trim()));

  return (
    <div className="space-y-3 text-sm leading-7">
      {lines.map((line, index) => {
        const trimmed = line.trim();
        if (trimmed.startsWith("- ")) {
          return (
            <div key={`${trimmed}-${index}`} className="flex gap-2">
              <span className="mt-2 h-1.5 w-1.5 rounded-full bg-current opacity-60" />
              <p>{renderInline(trimmed.slice(2))}</p>
            </div>
          );
        }
        return <p key={`${trimmed}-${index}`}>{renderInline(trimmed)}</p>;
      })}
    </div>
  );
}
