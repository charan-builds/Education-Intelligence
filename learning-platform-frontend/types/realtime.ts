import type { DiscussionReply, DiscussionThread } from "@/types/community";

export type RealtimeEvent =
  | {
      type: "presence.snapshot";
      tenant_id: number;
      active_users: number;
      sent_at: string;
    }
  | {
      type: "activity.created";
      scope: "tenant";
      event_type: string;
      user_id: number;
      topic_id?: number;
      community_id?: number;
      thread_id?: number;
      message: string;
    }
  | {
      type: "progress.updated";
      step_id: number;
      topic_id: number;
      progress_status: string;
    }
  | {
      type: "mentor.response.ready";
      request_id?: string | null;
      reply: string;
      used_ai: boolean;
      session_summary?: string;
    }
  | {
      type: "mentor.response.chunk";
      request_id?: string | null;
      content: string;
      done: boolean;
    }
  | {
      type: "community.thread.created";
      thread: DiscussionThread;
    }
  | {
      type: "community.reply.created";
      reply: DiscussionReply;
    }
  | {
      type: "community.typing";
      thread_id: number;
      user_id: number;
    }
  | {
      type: "pong";
    };
