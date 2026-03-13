type WeakTopic = {
  topicId: number;
  difficulty: string;
  status: string;
};

type WeakTopicsCardProps = {
  weakTopics: WeakTopic[];
};

export default function WeakTopicsCard({ weakTopics }: WeakTopicsCardProps) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Weak Topics</h2>

      {weakTopics.length === 0 ? (
        <p className="mt-4 text-sm text-emerald-700">No weak topics detected. Great progress.</p>
      ) : (
        <ul className="mt-4 space-y-2">
          {weakTopics.map((topic) => (
            <li key={topic.topicId} className="rounded-lg border border-rose-100 bg-rose-50 px-3 py-2 text-sm">
              <span className="font-medium text-rose-800">Topic #{topic.topicId}</span>
              <span className="ml-2 text-rose-700">
                ({topic.difficulty}, {topic.status.replace("_", " ")})
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
