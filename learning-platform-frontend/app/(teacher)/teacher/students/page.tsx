"use client";

import { useMemo, useState } from "react";

import PageHeader from "@/components/layouts/PageHeader";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import SurfaceCard from "@/components/ui/SurfaceCard";
import { useTeacherDashboard } from "@/hooks/useDashboard";

export default function TeacherStudentsPage() {
  const dashboard = useTeacherDashboard();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");

  const learners = useMemo(() => {
    return dashboard.learners.filter((learner) => {
      const matchesSearch = learner.email.toLowerCase().includes(search.toLowerCase());
      if (filter === "all") {
        return matchesSearch;
      }
      if (filter === "at_risk") {
        return matchesSearch && learner.mastery_percent < 50;
      }
      if (filter === "strong") {
        return matchesSearch && learner.mastery_percent >= 70;
      }
      return matchesSearch;
    });
  }, [dashboard.learners, filter, search]);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Teacher workspace"
        title="Student performance roster"
        description="Filter learners by search and support need using the tenant-scoped roadmap progress analytics."
      />

      <SurfaceCard title="Filters" description="Refine the learner list without leaving the dashboard.">
        <div className="grid gap-4 md:grid-cols-[1fr_240px]">
          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search by learner email"
          />
          <Select value={filter} onChange={(event) => setFilter(event.target.value)}>
            <option value="all">All learners</option>
            <option value="at_risk">At risk</option>
            <option value="strong">Strong mastery</option>
          </Select>
        </div>
      </SurfaceCard>

      <SurfaceCard title="Roster" description="Current student list derived from `/analytics/roadmap-progress`.">
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="text-slate-500 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3 font-medium">Learner</th>
                <th className="px-4 py-3 font-medium">Completion</th>
                <th className="px-4 py-3 font-medium">Mastery</th>
                <th className="px-4 py-3 font-medium">Status mix</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {learners.map((learner) => (
                <tr key={learner.user_id}>
                  <td className="px-4 py-3 text-slate-900 dark:text-slate-100">{learner.email}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{learner.completion_percent}%</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{learner.mastery_percent}%</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-400">
                    {learner.completed_steps} done / {learner.in_progress_steps} active / {learner.pending_steps} pending
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SurfaceCard>
    </div>
  );
}
