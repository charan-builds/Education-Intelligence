type NextTopicCardProps = {
  topicLabel: string;
  difficulty: string;
  deadline?: string;
};

export default function NextTopicCard({ topicLabel, difficulty, deadline }: NextTopicCardProps) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Recommended Next Topic</h2>
      <p className="mt-4 text-2xl font-semibold text-slate-900">{topicLabel}</p>
      <p className="mt-1 text-sm text-slate-600 capitalize">Difficulty: {difficulty}</p>
      {deadline ? <p className="mt-1 text-sm text-slate-600">Target by: {deadline}</p> : null}
    </section>
  );
}
