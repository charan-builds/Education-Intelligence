"use client";

import { motion } from "framer-motion";
import { Crown, Flame, Map, ShieldCheck, Swords, Trophy } from "lucide-react";

import SurfaceCard from "@/components/ui/SurfaceCard";

type Quest = {
  id: string;
  title: string;
  description: string;
  reward: string;
  status: "active" | "locked" | "completed";
};

type ImmersiveQuestBoardProps = {
  level: number;
  xp: number;
  streakDays: number;
  quests: Quest[];
};

const statusStyles = {
  active: "border-amber-200 bg-amber-50/85 text-amber-950",
  locked: "border-slate-200 bg-slate-100/90 text-slate-500",
  completed: "border-emerald-200 bg-emerald-50/85 text-emerald-950",
} as const;

export default function ImmersiveQuestBoard({
  level,
  xp,
  streakDays,
  quests,
}: ImmersiveQuestBoardProps) {
  return (
    <SurfaceCard
      title="Quest board"
      description="Learning is framed as missions, unlocks, and visible rewards instead of a plain checklist."
      className="mesh-panel"
      actions={
        <div className="inline-flex items-center gap-2 rounded-full bg-slate-950 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-white">
          <Crown className="h-3.5 w-3.5 text-amber-300" />
          Chapter progression
        </div>
      }
    >
      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="rounded-[30px] border border-white/70 bg-[linear-gradient(135deg,rgba(15,23,42,0.96),rgba(37,99,235,0.88),rgba(20,184,166,0.72))] p-6 text-white shadow-panel">
          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/60">Current level</p>
              <p className="mt-3 text-4xl font-semibold tracking-tight">Lv. {level}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/60">Experience</p>
              <p className="mt-3 text-4xl font-semibold tracking-tight">{xp}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/60">Streak power</p>
              <p className="mt-3 text-4xl font-semibold tracking-tight">{streakDays}</p>
            </div>
          </div>

          <div className="mt-6 rounded-[24px] border border-white/10 bg-white/10 p-4 backdrop-blur">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <Flame className="h-4 w-4 text-orange-200" />
                <p className="text-sm font-semibold">Journey energy</p>
              </div>
              <p className="text-xs uppercase tracking-[0.22em] text-white/60">
                {Math.max(0, 250 - (xp % 250 || 250))} XP to next level
              </p>
            </div>
            <div className="mt-4 h-3 overflow-hidden rounded-full bg-white/10">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(100, ((xp % 250 || 250) / 250) * 100)}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="h-full rounded-full bg-[linear-gradient(90deg,#f59e0b,#fb7185,#22d3ee)]"
              />
            </div>
          </div>
        </div>

        <div className="grid gap-3">
          {quests.map((quest, index) => (
            <motion.div
              key={quest.id}
              initial={{ opacity: 0, y: 14 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.25 }}
              transition={{ duration: 0.35, delay: index * 0.06 }}
              className={`rounded-[26px] border px-4 py-4 ${statusStyles[quest.status]}`}
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.22em] opacity-60">
                    {quest.status === "active" ? "Active quest" : quest.status === "completed" ? "Achievement unlocked" : "Locked mission"}
                  </p>
                  <p className="mt-2 text-lg font-semibold">{quest.title}</p>
                  <p className="mt-2 text-sm leading-6 opacity-80">{quest.description}</p>
                </div>
                <div className="rounded-[18px] bg-white/60 p-3">
                  {quest.status === "completed" ? (
                    <ShieldCheck className="h-5 w-5" />
                  ) : quest.status === "active" ? (
                    <Swords className="h-5 w-5" />
                  ) : (
                    <Map className="h-5 w-5" />
                  )}
                </div>
              </div>
              <div className="mt-4 inline-flex items-center gap-2 rounded-full bg-white/55 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em]">
                <Trophy className="h-3.5 w-3.5" />
                {quest.reward}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </SurfaceCard>
  );
}
