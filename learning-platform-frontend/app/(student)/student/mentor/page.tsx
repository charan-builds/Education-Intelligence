"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import MarkdownMessage from "@/components/chat/MarkdownMessage";
import PageHeader from "@/components/layouts/PageHeader";
import SurfaceCard from "@/components/ui/SurfaceCard";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import SmartLoadingState from "@/components/ui/SmartLoadingState";
import { useToast } from "@/components/providers/ToastProvider";
import { getAIChatHistory, sendAIChatMessage } from "@/services/aiService";

type ConversationItem = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

export default function StudentMentorPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [message, setMessage] = useState("");

  const historyQuery = useQuery({
    queryKey: ["student", "ai-chat", "history"],
    queryFn: getAIChatHistory,
  });

  const conversation = useMemo(() => {
    return (historyQuery.data ?? []).flatMap((item) => {
      const base: ConversationItem[] = [
        { id: `${item.request_id}-user`, role: "user" as const, content: item.message },
      ];
      if (item.response) {
        base.push({ id: `${item.request_id}-assistant`, role: "assistant" as const, content: item.response });
      }
      return base;
    });
  }, [historyQuery.data]);

  const sendMutation = useMutation({
    mutationFn: () =>
      sendAIChatMessage({
        message,
        chat_history: conversation.slice(-8).map((item) => ({
          role: item.role,
          content: item.content,
        })),
      }),
    onSuccess: async () => {
      setMessage("");
      await queryClient.invalidateQueries({ queryKey: ["student", "ai-chat", "history"] });
      toast({
        title: "AI mentor replied",
        description: "Your roadmap-aware mentor response is ready.",
        variant: "success",
      });
    },
  });

  useEffect(() => {
    if (!message && conversation.length === 0) {
      setMessage("Explain my next roadmap topic and tell me why it matters.");
    }
  }, [conversation.length, message]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!message.trim() || sendMutation.isPending) {
      return;
    }
    sendMutation.mutate();
  }

  if (historyQuery.isLoading) {
    return <SmartLoadingState title="Loading AI mentor" description="Pulling your recent learner conversation and context." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="AI Mentor"
        title="Chat with your roadmap-aware study mentor"
        description="Ask for topic explanations, next-step guidance, and study plans grounded in your diagnostic and roadmap."
      />

      <SurfaceCard
        title="Conversation"
        description="The mentor explains topics clearly and recommends next topics using your current roadmap and weak-topic signals."
      >
        <div className="space-y-4">
          {conversation.length === 0 ? (
            <p className="text-sm text-slate-600">No messages yet. Ask the mentor to explain a topic or suggest your best next step.</p>
          ) : (
            conversation.map((item) => (
              <div
                key={item.id}
                className={`rounded-2xl px-4 py-3 ${item.role === "assistant" ? "bg-slate-100 text-slate-900" : "bg-sky-50 text-sky-950"}`}
              >
                <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] opacity-70">
                  {item.role === "assistant" ? "AI mentor" : "You"}
                </p>
                <MarkdownMessage content={item.content} />
              </div>
            ))
          )}
        </div>
      </SurfaceCard>

      <SurfaceCard
        title="Ask the Mentor"
        description="Example prompt structure: learning goal, topic/question, what feels confusing, and the kind of help you want."
      >
        <form className="space-y-4" onSubmit={handleSubmit}>
          <Input
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Example: My goal is backend development. Explain joins simply, then suggest the best next roadmap topic."
          />
          <div className="flex justify-end">
            <Button type="submit" disabled={sendMutation.isPending || !message.trim()}>
              {sendMutation.isPending ? "Thinking..." : "Send"}
            </Button>
          </div>
        </form>
      </SurfaceCard>
    </div>
  );
}
