type RoadmapProgressProps = {
  totalTopics: number;
  completedTopics: number;
  currentTopic: string;
};

export default function RoadmapProgress({ totalTopics, completedTopics, currentTopic }: RoadmapProgressProps) {
  const percent = totalTopics > 0 ? Math.round((completedTopics / totalTopics) * 100) : 0;

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Roadmap Progress</h2>
      <div className="mt-4 flex items-end justify-between gap-3">
        <div>
          <p className="text-3xl font-semibold text-slate-900">{percent}%</p>
          <p className="text-sm text-slate-600">
            {completedTopics} of {totalTopics} topics completed
          </p>
        </div>
        <p className="text-sm text-slate-600">
          Current Topic: <span className="font-medium text-slate-900">{currentTopic}</span>
        </p>
      </div>

      <div className="mt-4 h-2 w-full rounded-full bg-slate-200">
        <div className="h-2 rounded-full bg-brand-600 transition-all" style={{ width: `${percent}%` }} />
      </div>
    </section>
  );
}
