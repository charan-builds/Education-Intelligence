"use client";

export const dynamic = "force-dynamic";

import { FormEvent, useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import MentorNotifications from "@/components/MentorNotifications";
import MentorSuggestions from "@/components/MentorSuggestions";
import MentorProgressAnalysis from "@/components/MentorProgressAnalysis";
import { useAuth } from "@/hooks/useAuth";
import { chatWithMentor } from "@/services/mentorService";

type ChatMessage = {
  id: number;
  role: "student" | "mentor";
  text: string;
  ts: string;
};

export default function MentorPage() {
  const { user, isAuthenticated } = useAuth();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 1,
      role: "mentor",
      text: "Hi, I am your AI mentor. Ask me about roadmap steps, weak topics, or study strategy.",
      ts: new Date().toISOString(),
    },
  ]);

  const chatMutation = useMutation({
    mutationFn: chatWithMentor,
    onSuccess: (data, variables) => {
      setMessages((prev) => [
        ...prev,
        {
          id: prev.length + 1,
          role: "student",
          text: variables.message,
          ts: new Date().toISOString(),
        },
        {
          id: prev.length + 2,
          role: "mentor",
          text: data.reply,
          ts: new Date().toISOString(),
        },
      ]);
      setInput("");
    },
  });

  const canSend = useMemo(
    () => isAuthenticated && Boolean(user?.user_id && user?.tenant_id) && input.trim().length > 0,
    [isAuthenticated, user?.tenant_id, user?.user_id, input],
  );

  async function onSend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSend || !user?.user_id || !user?.tenant_id) {
      return;
    }

    await chatMutation.mutateAsync({
      message: input.trim(),
      user_id: user.user_id,
      tenant_id: user.tenant_id,
    });
  }

  if (!isAuthenticated) {
    return (
      <main className="mx-auto min-h-screen max-w-4xl px-6 py-10">
        <h1 className="text-3xl font-semibold tracking-tight">AI Mentor</h1>
        <p className="mt-3 text-slate-600">Please login to use mentor chat.</p>
      </main>
    );
  }

  return (
    <main className="mx-auto min-h-screen max-w-7xl px-6 py-10">
      <h1 className="text-3xl font-semibold tracking-tight">AI Mentor Chat</h1>
      <p className="mt-2 text-slate-600">Discuss roadmap reminders, weak topics, and next learning actions.</p>

      <div className="mt-6 grid gap-4 xl:grid-cols-[2fr_1fr]">
        <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="h-[460px] space-y-3 overflow-y-auto rounded-lg bg-slate-50 p-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={[
                  "max-w-[85%] rounded-2xl px-4 py-2 text-sm",
                  message.role === "student"
                    ? "ml-auto bg-brand-600 text-white"
                    : "mr-auto border border-slate-200 bg-white text-slate-800",
                ].join(" ")}
              >
                <p className="font-medium capitalize opacity-80">{message.role}</p>
                <p className="mt-1">{message.text}</p>
              </div>
            ))}
          </div>

          <form className="mt-4 flex gap-3" onSubmit={onSend}>
            <input
              type="text"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask your mentor..."
              className="flex-1 rounded-lg border border-slate-300 px-3 py-2 outline-none ring-brand-600 focus:ring-2"
            />
            <button
              type="submit"
              disabled={!canSend || chatMutation.isPending}
              className="rounded-lg bg-brand-600 px-4 py-2 text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {chatMutation.isPending ? "Sending..." : "Send"}
            </button>
          </form>

          {chatMutation.isError && <p className="mt-3 text-sm text-red-600">Failed to get mentor response.</p>}
        </section>

        <div className="space-y-4">
          <MentorSuggestions />
          <MentorNotifications />
          <MentorProgressAnalysis />
        </div>
      </div>
    </main>
  );
}
