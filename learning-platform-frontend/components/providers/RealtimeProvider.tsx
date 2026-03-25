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
import { useAuth } from "@/hooks/useAuth";
import type { PlatformNotification } from "@/types/notification";
import type { RealtimeEvent } from "@/types/realtime";

type RealtimeContextValue = {
  connectionStatus: "connecting" | "live" | "reconnecting" | "offline";
  activeUsers: number;
  liveEvents: Array<{ id: number; message: string; eventType: string }>;
  typingByThread: Record<number, number[]>;
  lastMentorChunk: { requestId: string; content: string; done: boolean } | null;
  lastMentorReply: {
    requestId: string;
    reply: string;
    usedAi: boolean;
    sessionSummary?: string;
    provider?: string | null;
    whyRecommended?: string[];
  } | null;
  liveNotifications: PlatformNotification[];
  subscribeCommunity: (communityId: number) => void;
  subscribeThread: (threadId: number) => void;
  sendTyping: (threadId: number) => void;
  sendMentorMessage: (payload: {
    message: string;
    userId: number;
    tenantId: number;
    requestId: string;
    chatHistory: Array<{ role: string; content: string }>;
  }) => void;
};

const RealtimeContext = createContext<RealtimeContextValue | null>(null);

function applyEventInvalidations(queryClient: QueryClient, event: RealtimeEvent): void {
  if (event.type === "progress.updated" || event.type === "activity.created") {
    void queryClient.invalidateQueries({ queryKey: ["dashboard", "student", "intelligence"] });
    void queryClient.invalidateQueries({ queryKey: ["dashboard", "student", "roadmap"] });
  }
  if (event.type === "notification.created") {
    void queryClient.invalidateQueries({ queryKey: ["notifications"] });
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
  const { isAuthenticated } = useAuth();
  const socketRef = useRef<WebSocket | null>(null);
  const typingTimersRef = useRef<Record<number, number>>({});
  const reconnectTimerRef = useRef<number | null>(null);
  const reconnectAttemptRef = useRef(0);
  const mountedRef = useRef(true);
  const [connectionStatus, setConnectionStatus] = useState<"connecting" | "live" | "reconnecting" | "offline">("connecting");
  const [activeUsers, setActiveUsers] = useState(0);
  const [liveEvents, setLiveEvents] = useState<Array<{ id: number; message: string; eventType: string }>>([]);
  const [typingByThread, setTypingByThread] = useState<Record<number, number[]>>({});
  const [lastMentorChunk, setLastMentorChunk] = useState<{ requestId: string; content: string; done: boolean } | null>(null);
  const [lastMentorReply, setLastMentorReply] = useState<{
    requestId: string;
    reply: string;
    usedAi: boolean;
    sessionSummary?: string;
    provider?: string | null;
    whyRecommended?: string[];
  } | null>(null);
  const [liveNotifications, setLiveNotifications] = useState<PlatformNotification[]>([]);

  function send(payload: Record<string, unknown>) {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(payload));
    }
  }

  useEffect(() => {
    mountedRef.current = true;
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    if (!apiUrl || !isAuthenticated) {
      setConnectionStatus("offline");
      return;
    }

    const wsUrl = apiUrl.replace(/^http/, "ws").replace(/\/$/, "") + `/realtime/ws`;

    const connect = () => {
      setConnectionStatus(reconnectAttemptRef.current > 0 ? "reconnecting" : "connecting");
      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        reconnectAttemptRef.current = 0;
        setConnectionStatus("live");
      };

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
        if (event.request_id) {
          setLastMentorReply({
            requestId: event.request_id,
            reply: event.reply,
            usedAi: event.used_ai,
            sessionSummary: event.session_summary,
            provider: "provider" in event ? (event.provider ?? null) : null,
            whyRecommended: "why_recommended" in event ? (event.why_recommended ?? []) : [],
          });
        }
        toast({
          title: "Mentor updated",
          description: event.session_summary,
          variant: "info",
        });
      }

      if (event.type === "notification.created") {
        setLiveNotifications((current) => [event.notification, ...current].slice(0, 20));
        toast({
          title: event.notification.title,
          description: event.notification.message,
          variant: event.notification.severity === "high" ? "error" : "info",
        });
      }

        if (event.type === "error") {
          toast({
            title: "Realtime error",
            description: event.detail,
            variant: "error",
          });
        }
      };

      socket.onclose = () => {
        if (!mountedRef.current) {
          return;
        }
        setConnectionStatus("reconnecting");
        const delay = Math.min(5000, 800 * (reconnectAttemptRef.current + 1));
        reconnectAttemptRef.current += 1;
        reconnectTimerRef.current = window.setTimeout(connect, delay);
      };
    };

    connect();

    return () => {
      mountedRef.current = false;
      if (reconnectTimerRef.current) {
        window.clearTimeout(reconnectTimerRef.current);
      }
      socketRef.current?.close();
      socketRef.current = null;
      setConnectionStatus("offline");
    };
  }, [isAuthenticated, queryClient, toast]);

  const value = useMemo<RealtimeContextValue>(
    () => ({
      connectionStatus,
      activeUsers,
      liveEvents,
      typingByThread,
      lastMentorChunk,
      lastMentorReply,
      liveNotifications,
      subscribeCommunity: (communityId: number) => {
        send({ action: "subscribe.community", community_id: communityId });
      },
      subscribeThread: (threadId: number) => {
        send({ action: "subscribe.thread", thread_id: threadId });
      },
      sendTyping: (threadId: number) => {
        send({ action: "community.typing", thread_id: threadId });
      },
      sendMentorMessage: ({ message, userId, tenantId, requestId, chatHistory }) => {
        send({
          action: "mentor.chat",
          message,
          user_id: userId,
          tenant_id: tenantId,
          request_id: requestId,
          chat_history: chatHistory,
        });
      },
    }),
    [activeUsers, connectionStatus, lastMentorChunk, lastMentorReply, liveEvents, liveNotifications, typingByThread],
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
