"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Copy, RefreshCw, Send, Sparkles } from "lucide-react";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";

import MarkdownMessage from "@/components/chat/MarkdownMessage";
import RecommendationPanel from "@/components/dashboard/RecommendationPanel";
import PageHeader from "@/components/layouts/PageHeader";
import Button from "@/components/ui/Button";
import SmartLoadingState from "@/components/ui/SmartLoadingState";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { useToast } from "@/components/providers/ToastProvider";
import { useRealtime } from "@/components/providers/RealtimeProvider";
import { useAuth } from "@/hooks/useAuth";
import { useMentorWorkspace } from "@/hooks/useDashboard";
import { ackMentorChat, getMentorChatStatus, recoverMentorChat } from "@/services/mentorService";

type ChatMessage = {
  id: number;
  role: "mentor" | "learner";
  text: string;
  metadata?: string;
  provider?: string | null;
  whyRecommended?: string[];
};

export default function MentorChatPage() {
  const { user } = useAuth();
  const workspace = useMentorWorkspace();
  const { toast } = useToast();
  const { lastMentorChunk, lastMentorReply, sendMentorMessage } = useRealtime();
  const searchParams = useSearchParams();
  const [input, setInput] = useState("");
  const [streamingId, setStreamingId] = useState<number | null>(null);
  const [draftResponse, setDraftResponse] = useState("");
  const [lastPrompt, setLastPrompt] = useState("");
  const [pendingRequestId, setPendingRequestId] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 1,
      role: "mentor",
      text: "Ask for study guidance, a roadmap nudge, or support on weak topics.\n- I can help prioritize what to learn next.\n- I can turn weak signals into a simple action plan.\n- I can explain why a step matters before you commit to it.",
    },
  ]);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const statusPollTimerRef = useRef<number | null>(null);
  const pendingRequestIdRef = useRef<string | null>(null);

  const canSend = useMemo(() => Boolean(input.trim() && user?.user_id && user?.tenant_id), [input, user?.tenant_id, user?.user_id]);

  useEffect(() => {
    const prompt = searchParams.get("prompt");
    if (!prompt) {
      return;
    }
    setInput(prompt);
  }, [searchParams]);

  useEffect(() => {
    if (!streamingId || !lastMentorChunk || !messages.length) {
      return;
    }
    const currentStreamingMessage = messages.find((message) => message.id === streamingId);
    if (!currentStreamingMessage || currentStreamingMessage.metadata !== lastMentorChunk.requestId) {
      return;
    }
    setDraftResponse(lastMentorChunk.content);
  }, [lastMentorChunk, messages, streamingId]);

  useEffect(() => {
    if (!lastMentorReply || !pendingRequestId || !streamingId) {
      return;
    }
    if (lastMentorReply.requestId !== pendingRequestId) {
      return;
    }
    setMessages((current) =>
      current.map((message) =>
        message.id === streamingId
          ? {
              ...message,
              text: lastMentorReply.reply,
              metadata: lastMentorReply.usedAi
                ? `AI-backed mentor reply • ${lastMentorReply.requestId}`
                : `Rule-based fallback reply • ${lastMentorReply.requestId}`,
              provider: lastMentorReply.provider ?? null,
              whyRecommended: lastMentorReply.whyRecommended ?? [],
            }
          : message,
      ),
    );
    setStreamingId(null);
    setDraftResponse("");
    setPendingRequestId(null);
    pendingRequestIdRef.current = null;
    setIsSending(false);
    setInput("");
    if (statusPollTimerRef.current) {
      window.clearTimeout(statusPollTimerRef.current);
      statusPollTimerRef.current = null;
    }
    void ackMentorChat(lastMentorReply.requestId).catch(() => undefined);
  }, [lastMentorReply, pendingRequestId, streamingId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [draftResponse, messages]);

  useEffect(() => {
    return () => {
      if (statusPollTimerRef.current) {
        window.clearTimeout(statusPollTimerRef.current);
      }
    };
  }, []);

  async function pollMentorStatus(payload: { prompt: string; requestId: string; responseMessageId: number; attempt: number }) {
    if (!user?.user_id || !user?.tenant_id || pendingRequestIdRef.current !== payload.requestId) {
      return;
    }
    try {
      const status = await getMentorChatStatus(payload.requestId);
      if (status.reply) {
        setMessages((current) =>
          current.map((message) =>
            message.id === payload.responseMessageId
              ? {
                  ...message,
                  text: status.reply ?? "",
                  metadata: `Recovered async reply • ${payload.requestId}`,
                }
              : message,
          ),
        );
        setStreamingId(null);
        setDraftResponse("");
        setPendingRequestId(null);
        pendingRequestIdRef.current = null;
        setIsSending(false);
        setInput("");
        await ackMentorChat(payload.requestId);
        toast({
          title: "Mentor response recovered",
          description: "Realtime delivery lagged, so the queued reply was recovered from chat status.",
          variant: "info",
        });
        return;
      }
    } catch {
      if (payload.attempt >= 5) {
        try {
          const response = await recoverMentorChat({
            message: payload.prompt,
            user_id: user.user_id,
            tenant_id: user.tenant_id,
            request_id: payload.requestId,
            chat_history: messages.slice(-6).map((message) => ({
              role: message.role === "learner" ? "user" : "assistant",
              content: message.text,
            })),
          });
          if (response.reply) {
            setMessages((current) =>
              current.map((message) =>
                message.id === payload.responseMessageId
                  ? {
                      ...message,
                      text: response.reply,
                      metadata: `Recovered async reply • ${payload.requestId}`,
                      provider: response.provider ?? null,
                      whyRecommended: response.why_recommended ?? [],
                    }
                  : message,
              ),
            );
            setStreamingId(null);
            setDraftResponse("");
            setPendingRequestId(null);
            pendingRequestIdRef.current = null;
            setIsSending(false);
            setInput("");
            await ackMentorChat(payload.requestId);
            return;
          }
        } catch {
          // Keep polling below.
        }
      }
    }

    if (payload.attempt >= 10) {
      setIsSending(false);
      toast({
        title: "Mentor reply delayed",
        description: "The queued response is still processing. Please retry in a moment.",
        variant: "error",
      });
      return;
    }

    statusPollTimerRef.current = window.setTimeout(() => {
      void pollMentorStatus({
        ...payload,
        attempt: payload.attempt + 1,
      });
    }, 1500);
  }

  function submitPrompt(prompt: string) {
    if (!prompt.trim() || !user?.user_id || !user?.tenant_id || isSending) {
      return;
    }
    const learnerMessage = prompt.trim();
    const requestId = `mentor-${Date.now()}`;
    const baseId = messages.length + 1;
    setMessages((current) => [
      ...current,
      { id: baseId, role: "learner", text: learnerMessage },
      {
        id: baseId + 1,
        role: "mentor",
        text: "",
        metadata: requestId,
      },
    ]);
    setStreamingId(baseId + 1);
    setDraftResponse("");
    setPendingRequestId(requestId);
    pendingRequestIdRef.current = requestId;
    setIsSending(true);
    setLastPrompt(learnerMessage);
    sendMentorMessage({
      message: learnerMessage,
      userId: user.user_id,
      tenantId: user.tenant_id,
      requestId,
      chatHistory: messages.slice(-6).map((message) => ({
        role: message.role === "learner" ? "user" : "assistant",
        content: message.text,
      })),
    });
    if (statusPollTimerRef.current) {
      window.clearTimeout(statusPollTimerRef.current);
    }
    statusPollTimerRef.current = window.setTimeout(() => {
      void pollMentorStatus({
        prompt: learnerMessage,
        requestId,
        responseMessageId: baseId + 1,
        attempt: 1,
      });
    }, 4000);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSend) {
      return;
    }
    submitPrompt(input);
  }

  async function handleCopy(text: string) {
    await navigator.clipboard.writeText(text);
    toast({ title: "Copied response", description: "Mentor reply copied to your clipboard.", variant: "success" });
  }

  async function handleRegenerate() {
    if (!lastPrompt || !user?.user_id || !user?.tenant_id || isSending) {
      return;
    }
    submitPrompt(lastPrompt);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Mentor chat"
        title="Conversation workspace"
        description="This workspace now streams mentor replies over the authenticated realtime channel, using learner context and AI assistance when the tenant feature flag allows it."
      />

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <SurfaceCard
          title="Mentor conversation"
          description="Mentor replies are AI-backed when enabled and fall back to deterministic guidance if the AI path is unavailable."
          actions={
            <div className="flex flex-wrap gap-2">
              <Button variant="secondary" onClick={handleRegenerate} disabled={!lastPrompt || isSending}>
                <RefreshCw className="h-4 w-4" />
                Regenerate
              </Button>
            </div>
          }
        >
          <div
            ref={scrollRef}
            className="h-[560px] space-y-3 overflow-y-auto rounded-[28px] border border-slate-200 bg-white/70 p-4 dark:border-slate-700 dark:bg-slate-900/70"
          >
            <AnimatePresence initial={false}>
              {messages.map((message) => {
                const visibleText = streamingId === message.id ? draftResponse : message.text;
                return (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 12, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -8 }}
                    className={[
                      "max-w-[88%] rounded-[24px] px-4 py-3 text-sm leading-7 shadow-sm",
                      message.role === "learner"
                        ? "ml-auto bg-[linear-gradient(135deg,#0f766e,#14b8a6,#f97316)] text-white"
                        : "mr-auto border border-slate-200 bg-white text-slate-800 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100",
                    ].join(" ")}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-xs font-semibold uppercase tracking-[0.22em] opacity-70">{message.role}</p>
                      {message.role === "mentor" && visibleText ? (
                        <div className="flex items-center gap-2">
                          <button type="button" onClick={() => handleCopy(visibleText)} className="opacity-70 transition hover:opacity-100">
                            <Copy className="h-4 w-4" />
                          </button>
                        </div>
                      ) : null}
                    </div>
                    {message.metadata ? (
                      <p className="mt-2 text-[11px] uppercase tracking-[0.18em] opacity-60">
                        {message.metadata}
                        {message.provider ? ` • ${message.provider}` : ""}
                      </p>
                    ) : null}
                    <div className="mt-2">
                      <MarkdownMessage content={visibleText} />
                    </div>
                    {streamingId === message.id ? (
                      <div className="mt-3 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-teal-600 dark:text-teal-300">
                        <span className="h-2 w-2 animate-pulse rounded-full bg-current" />
                        Typing
                      </div>
                    ) : null}
                    {message.whyRecommended?.length ? (
                      <div className="mt-4 rounded-2xl bg-slate-100/80 p-3 text-xs text-slate-600 dark:bg-slate-900/80 dark:text-slate-300">
                        <p className="font-semibold uppercase tracking-[0.2em]">Why this response</p>
                        <div className="mt-2 space-y-1">
                          {message.whyRecommended.map((reason) => (
                            <p key={reason}>- {reason}</p>
                          ))}
                        </div>
                      </div>
                    ) : null}
                  </motion.div>
                );
              })}
            </AnimatePresence>

            {isSending ? (
              <div className="mr-auto max-w-[88%]">
                <SmartLoadingState
                  compact
                  title="Mentor is thinking"
                  description="Synthesizing roadmap signals, weak topics, and the best next step."
                />
              </div>
            ) : null}
          </div>

          <form className="mt-4 space-y-3" onSubmit={handleSubmit}>
            <div className="rounded-[28px] border border-slate-200 bg-white/80 p-2 dark:border-slate-700 dark:bg-slate-900/80">
              <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              rows={4}
              placeholder="Ask for guidance on a roadmap step or weak topic"
                className="min-h-[120px] w-full resize-none rounded-[22px] border-0 bg-transparent px-4 py-4 text-sm text-slate-900 outline-none placeholder:text-slate-400 dark:text-slate-100 dark:placeholder:text-slate-500"
              />
              <div className="flex flex-col gap-3 border-t border-slate-200/80 px-3 pb-2 pt-3 dark:border-slate-700/70 sm:flex-row sm:items-center sm:justify-between">
                <div className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">
                  <Sparkles className="h-3.5 w-3.5 text-teal-600 dark:text-teal-300" />
                  Context-aware mentor chat
                </div>
                <Button type="submit" disabled={!canSend || isSending}>
                  {isSending ? "Sending..." : "Send"}
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </form>
        </SurfaceCard>

        <RecommendationPanel
          title="Suggested guidance"
          description="Use these quick prompts as a starting point in the conversation."
          items={workspace.suggestions.length > 0 ? workspace.suggestions : workspace.recommendedFocus}
        />
      </div>
    </div>
  );
}
