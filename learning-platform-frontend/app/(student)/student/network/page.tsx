"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, Trophy, Users } from "lucide-react";

import PageHeader from "@/components/layouts/PageHeader";
import Button from "@/components/ui/Button";
import MetricCard from "@/components/ui/MetricCard";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { followUser, getSocialNetwork, unfollowUser } from "@/services/socialService";

export default function StudentNetworkPage() {
  const queryClient = useQueryClient();
  const networkQuery = useQuery({
    queryKey: ["social", "network"],
    queryFn: getSocialNetwork,
  });

  const followMutation = useMutation({
    mutationFn: followUser,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["social", "network"] });
    },
  });

  const unfollowMutation = useMutation({
    mutationFn: unfollowUser,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["social", "network"] });
    },
  });

  const network = networkQuery.data;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Learning network"
        title="Global learning social layer"
        description="Profiles, live progress updates, and peer groups turn the platform into a learning social network instead of a solo dashboard."
      />

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard title="Followers" value={network?.me.follower_count ?? 0} icon={<Users className="h-5 w-5" />} tone="info" />
        <MetricCard title="Following" value={network?.me.following_count ?? 0} icon={<Users className="h-5 w-5" />} tone="success" />
        <MetricCard title="XP" value={network?.me.xp ?? 0} icon={<Trophy className="h-5 w-5" />} tone="warning" />
        <MetricCard title="Feed updates" value={network?.feed.length ?? 0} icon={<Activity className="h-5 w-5" />} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <SurfaceCard title="My profile" description="Your social learning card exposes progress, skills, and momentum to the network.">
          {network?.me ? (
            <div className="space-y-4">
              <div className="rounded-[28px] border border-slate-200 bg-white/70 p-5 dark:border-slate-700 dark:bg-slate-900/70">
                <p className="text-lg font-semibold text-slate-950 dark:text-slate-100">{network.me.display_name}</p>
                <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">{network.me.role}</p>
                <p className="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-400">{network.me.tagline}</p>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl bg-emerald-50/80 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700">Top skills</p>
                  <div className="mt-2 space-y-1 text-sm text-emerald-950">
                    {(network.me.top_skills.length ? network.me.top_skills : ["Skills still building"]).map((item) => (
                      <p key={item}>- {item}</p>
                    ))}
                  </div>
                </div>
                <div className="rounded-2xl bg-amber-50/80 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-700">Weak topics</p>
                  <div className="mt-2 space-y-1 text-sm text-amber-950">
                    {(network.me.weak_topics.length ? network.me.weak_topics : ["No urgent weakness signal"]).map((item) => (
                      <p key={item}>- {item}</p>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-600">Loading profile...</p>
          )}
        </SurfaceCard>

        <SurfaceCard title="Social feed" description="A learner-centric feed of progress, badges, and activity from your network.">
          <div className="space-y-4">
            {(network?.feed ?? []).map((item) => (
              <div key={`${item.actor_user_id}-${item.event_type}-${item.created_at}`} className="rounded-[24px] border border-slate-200 bg-white/70 p-4 dark:border-slate-700 dark:bg-slate-900/70">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-slate-950 dark:text-slate-100">{item.title}</p>
                    <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                      {item.actor_name} • {new Date(item.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <p className="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-400">{item.description}</p>
              </div>
            ))}
            {network && network.feed.length === 0 ? <p className="text-sm text-slate-600">No feed activity yet.</p> : null}
          </div>
        </SurfaceCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <SurfaceCard title="People to follow" description="Suggested learners and mentors based on platform momentum and learning visibility.">
          <div className="space-y-4">
            {(network?.suggested_people ?? []).map((person) => (
              <div key={person.user_id} className="rounded-[28px] border border-slate-200 bg-white/75 p-5 dark:border-slate-700 dark:bg-slate-900/75">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-base font-semibold text-slate-950 dark:text-slate-100">{person.display_name}</p>
                    <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                      {person.role} • {person.completion_percent.toFixed(0)}% complete • {person.xp} XP
                    </p>
                  </div>
                  <Button onClick={() => followMutation.mutate(person.user_id)} disabled={followMutation.isPending}>
                    Follow
                  </Button>
                </div>
                <p className="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-400">{person.tagline}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {person.top_skills.slice(0, 3).map((skill) => (
                    <span key={skill} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </SurfaceCard>

        <SurfaceCard title="Following and peer groups" description="Track your learning circle and join topic-driven group learning clusters.">
          <div className="space-y-5">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Following</p>
              <div className="mt-3 space-y-3">
                {(network?.following ?? []).map((person) => (
                  <div key={person.user_id} className="rounded-2xl border border-slate-200 bg-white/70 p-4 dark:border-slate-700 dark:bg-slate-900/70">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-sm font-semibold text-slate-950 dark:text-slate-100">{person.display_name}</p>
                        <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                          {person.role} • {person.streak_days} day streak
                        </p>
                      </div>
                      <Button variant="secondary" onClick={() => unfollowMutation.mutate(person.user_id)} disabled={unfollowMutation.isPending}>
                        Unfollow
                      </Button>
                    </div>
                  </div>
                ))}
                {network && network.following.length === 0 ? <p className="text-sm text-slate-600">You are not following anyone yet.</p> : null}
              </div>
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Group learning</p>
              <div className="mt-3 space-y-4">
                {(network?.peer_groups ?? []).map((group) => (
                  <div key={group.title} className="rounded-[24px] border border-indigo-200 bg-indigo-50/70 p-4">
                    <p className="text-sm font-semibold text-indigo-950">{group.title}</p>
                    <p className="mt-2 text-sm leading-7 text-indigo-900/80">{group.description}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {group.members.map((member) => (
                        <span key={`${group.title}-${member.user_id}`} className="rounded-full bg-white/80 px-3 py-1 text-xs font-semibold text-indigo-800">
                          {member.display_name}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </SurfaceCard>
      </div>
    </div>
  );
}
