"use client";

import { QueryClient, useQueryClient } from "@tanstack/react-query";
import {
  createContext,
  PropsWithChildren,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { useToast } from "@/components/providers/ToastProvider";
import type { RealtimeEvent } from "@/types/realtime";

type RealtimeContextValue = {
  activeUsers: number;
  liveEvents: Array<{ id: number; message: string; eventType: string }>;
  typingByThread: Record<number, number[]>;
  lastMentorChunk: { requestId: string; content: string; done: boolean } | null;
  subscribeCommunity: (communityId: number) => void;
  subscribeThread: (threadId: number) => void;
  sendTyping: (threadId: number) => void;
};

const RealtimeContext = createContext<RealtimeContextValue | null>(null);

function applyEventInvalidations(queryClient: QueryClient, event: RealtimeEvent): void {
  if (event.type === "progress.updated" || event.type === "activity.created") {
    void queryClient.invalidateQueries({ queryKey: ["dashboard", "student", "intelligence"] });
    void queryClient.invalidateQueries({ queryKey: ["dashboard", "student", "roadmap"] });
  }
  if (event.type === "community.thread.created") {
    void queryClient.invalidateQueries({ queryKey: ["community-threads"] });
    void queryClient.invalidateQueries({ queryKey: ["community-communities"] });
  }
  if (event.type === "community.reply.created") {
    void queryClient.invalidateQueries({ queryKey: ["community-replies", event.reply.thread_id] });
  }
}

export function RealtimeProvider({ children }: PropsWithChildren) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const socketRef = useRef<WebSocket | null>(null);
  const typingTimersRef = useRef<Record<number, number>>({});
  const [activeUsers, setActiveUsers] = useState(0);
  const [liveEvents, setLiveEvents] = useState<Array<{ id: number; message: string; eventType: string }>>([]);
  const [typingByThread, setTypingByThread] = useState<Record<number, number[]>>({});
  const [lastMentorChunk, setLastMentorChunk] = useState<{ requestId: string; content: string; done: boolean } | null>(null);

  function send(payload: Record<string, unknown>) {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(payload));
    }
  }

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    if (!apiUrl || !token) {
      return;
    }

    const wsUrl = apiUrl.replace(/^http/, "ws").replace(/\/$/, "") + `/realtime/ws?token=${encodeURIComponent(token)}`;
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onmessage = (message) => {
      const event = JSON.parse(message.data) as RealtimeEvent;
      applyEventInvalidations(queryClient, event);

      if (event.type === "presence.snapshot") {
        setActiveUsers(event.active_users);
      }

      if (event.type === "activity.created") {
        setLiveEvents((current) => [
          { id: Date.now() + Math.random(), message: event.message, eventType: event.event_type },
          ...current,
        ].slice(0, 12));
      }

      if (event.type === "community.typing") {
        setTypingByThread((current) => {
          const next = new Set(current[event.thread_id] ?? []);
          next.add(event.user_id);
          return { ...current, [event.thread_id]: Array.from(next) };
        });
        if (typingTimersRef.current[event.thread_id]) {
          window.clearTimeout(typingTimersRef.current[event.thread_id]);
        }
        typingTimersRef.current[event.thread_id] = window.setTimeout(() => {
          setTypingByThread((current) => ({ ...current, [event.thread_id]: [] }));
        }, 1800);
      }

      if (event.type === "mentor.response.chunk" && event.request_id) {
        setLastMentorChunk({ requestId: event.request_id, content: event.content, done: event.done });
      }

      if (event.type === "mentor.response.ready" && event.session_summary) {
        toast({
          title: "Mentor updated",
          description: event.session_summary,
          variant: "info",
        });
      }
    };

    return () => {
      socket.close();
      socketRef.current = null;
    };
  }, [queryClient, toast]);

  const value = useMemo<RealtimeContextValue>(
    () => ({
      activeUsers,
      liveEvents,
      typingByThread,
      lastMentorChunk,
      subscribeCommunity: (communityId: number) => {
        send({ action: "subscribe.community", community_id: communityId });
      },
      subscribeThread: (threadId: number) => {
        send({ action: "subscribe.thread", thread_id: threadId });
      },
      sendTyping: (threadId: number) => {
        send({ action: "community.typing", thread_id: threadId });
      },
    }),
    [activeUsers, lastMentorChunk, liveEvents, typingByThread],
  );

  return <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>;
}

export function useRealtime() {
  const context = useContext(RealtimeContext);
  if (!context) {
    throw new Error("useRealtime must be used within RealtimeProvider");
  }
  return context;
}
