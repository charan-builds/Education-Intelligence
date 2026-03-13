"use client";

type NotificationPanelProps = {
  roadmapReminders: string[];
  topicSuggestions: string[];
};

export default function NotificationPanel({ roadmapReminders, topicSuggestions }: NotificationPanelProps) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Notifications</h2>

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <article className="rounded-lg border border-slate-200 p-4">
          <h3 className="text-sm font-semibold text-slate-800">Roadmap Reminders</h3>
          {roadmapReminders.length === 0 ? (
            <p className="mt-2 text-sm text-slate-600">No reminders right now.</p>
          ) : (
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
              {roadmapReminders.map((item, idx) => (
                <li key={`${idx}-${item}`}>{item}</li>
              ))}
            </ul>
          )}
        </article>

        <article className="rounded-lg border border-slate-200 p-4">
          <h3 className="text-sm font-semibold text-slate-800">Topic Suggestions</h3>
          {topicSuggestions.length === 0 ? (
            <p className="mt-2 text-sm text-slate-600">No suggestions available.</p>
          ) : (
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
              {topicSuggestions.map((item, idx) => (
                <li key={`${idx}-${item}`}>{item}</li>
              ))}
            </ul>
          )}
        </article>
      </div>
    </section>
  );
}
