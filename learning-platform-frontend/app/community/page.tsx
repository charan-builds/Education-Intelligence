"use client";

export const dynamic = "force-dynamic";

import { useMemo, useState } from "react";

type Thread = {
  id: number;
  title: string;
  topic: string;
  author: string;
  replies: number;
  lastActivity: string;
};

type Question = {
  id: number;
  question: string;
  topic: string;
  askedBy: string;
  answered: boolean;
};

type MentorBadge = {
  id: number;
  mentor: string;
  badge: string;
  reason: string;
};

const THREADS: Thread[] = [
  {
    id: 1,
    title: "How to approach gradient descent intuition?",
    topic: "Machine Learning",
    author: "Akhil",
    replies: 14,
    lastActivity: "2h ago",
  },
  {
    id: 2,
    title: "Best way to clean messy CSV datasets",
    topic: "Data Cleaning",
    author: "Neha",
    replies: 8,
    lastActivity: "5h ago",
  },
  {
    id: 3,
    title: "Pandas groupby performance tips",
    topic: "Pandas",
    author: "Rahul",
    replies: 5,
    lastActivity: "1d ago",
  },
];

const QUESTIONS: Question[] = [
  {
    id: 1,
    question: "Why does overfitting increase when model complexity grows?",
    topic: "Statistics",
    askedBy: "Sneha",
    answered: true,
  },
  {
    id: 2,
    question: "Any practical way to revise linear algebra for ML quickly?",
    topic: "Linear Algebra",
    askedBy: "Kiran",
    answered: false,
  },
  {
    id: 3,
    question: "What is the difference between loc and iloc in pandas?",
    topic: "Pandas",
    askedBy: "Priya",
    answered: true,
  },
];

const BADGES: MentorBadge[] = [
  {
    id: 1,
    mentor: "Dr. Meera",
    badge: "Top Mentor",
    reason: "Resolved 120+ learner questions",
  },
  {
    id: 2,
    mentor: "Arjun",
    badge: "Community Guide",
    reason: "Consistent high-quality roadmap feedback",
  },
  {
    id: 3,
    mentor: "Sara",
    badge: "Concept Clarifier",
    reason: "Most upvoted explanations this month",
  },
];

export default function CommunityPage() {
  const [search, setSearch] = useState("");

  const filteredThreads = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) {
      return THREADS;
    }
    return THREADS.filter(
      (thread) =>
        thread.title.toLowerCase().includes(q) ||
        thread.topic.toLowerCase().includes(q) ||
        thread.author.toLowerCase().includes(q),
    );
  }, [search]);

  return (
    <main className="mx-auto min-h-screen max-w-7xl px-6 py-10">
      <h1 className="text-3xl font-semibold tracking-tight">Community Learning</h1>
      <p className="mt-2 text-slate-600">Collaborate through discussion threads, questions, and mentor recognition.</p>

      <section className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-slate-900">Discussion Threads</h2>
          <input
            type="text"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search topic, title, or author"
            className="w-full max-w-sm rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none ring-brand-600 focus:ring-2"
          />
        </div>

        {filteredThreads.length === 0 ? (
          <p className="mt-4 text-sm text-slate-600">No threads found for this query.</p>
        ) : (
          <ul className="mt-4 space-y-3">
            {filteredThreads.map((thread) => (
              <li key={thread.id} className="rounded-lg border border-slate-200 p-4">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <h3 className="font-semibold text-slate-900">{thread.title}</h3>
                    <p className="mt-1 text-sm text-slate-600">
                      {thread.topic} • by {thread.author}
                    </p>
                  </div>
                  <div className="text-right text-sm text-slate-600">
                    <p>{thread.replies} replies</p>
                    <p>{thread.lastActivity}</p>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="mt-6 grid gap-4 lg:grid-cols-2">
        <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Learner Questions</h2>
          <ul className="mt-4 space-y-3">
            {QUESTIONS.map((item) => (
              <li key={item.id} className="rounded-lg border border-slate-200 p-4">
                <p className="font-medium text-slate-900">{item.question}</p>
                <p className="mt-1 text-sm text-slate-600">
                  {item.topic} • asked by {item.askedBy}
                </p>
                <span
                  className={[
                    "mt-3 inline-flex rounded-full px-2.5 py-1 text-xs font-medium",
                    item.answered ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700",
                  ].join(" ")}
                >
                  {item.answered ? "Answered" : "Open"}
                </span>
              </li>
            ))}
          </ul>
        </article>

        <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Mentor Badges</h2>
          <ul className="mt-4 space-y-3">
            {BADGES.map((badge) => (
              <li key={badge.id} className="rounded-lg border border-slate-200 p-4">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="font-semibold text-slate-900">{badge.mentor}</p>
                    <p className="text-sm text-slate-600">{badge.reason}</p>
                  </div>
                  <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700">
                    {badge.badge}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </article>
      </section>
    </main>
  );
}
