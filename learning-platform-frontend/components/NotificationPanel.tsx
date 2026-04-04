"use client";

type NotificationPanelProps = {
  roadmapReminders: string[];
  topicSuggestions: string[];
};

export default function NotificationPanel({ roadmapReminders, topicSuggestions }: NotificationPanelProps) {
  return (
    <section className="rounded-[28px] border border-violet-200/80 bg-white/88 p-5 shadow-[0_20px_60px_-36px_rgba(109,40,217,0.28)] backdrop-blur">
      <h2 className="text-lg font-semibold text-violet-950">Notifications</h2>

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <article className="rounded-[22px] border border-violet-200/70 bg-violet-50/55 p-4">
          <h3 className="text-sm font-semibold text-violet-900">Roadmap Reminders</h3>
          {roadmapReminders.length === 0 ? (
            <p className="mt-2 text-sm text-violet-700/78">No reminders right now.</p>
          ) : (
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-violet-800/84">
              {roadmapReminders.map((item, idx) => (
                <li key={`${idx}-${item}`}>{item}</li>
              ))}
            </ul>
          )}
        </article>

        <article className="rounded-[22px] border border-violet-200/70 bg-violet-50/55 p-4">
          <h3 className="text-sm font-semibold text-violet-900">Topic Suggestions</h3>
          {topicSuggestions.length === 0 ? (
            <p className="mt-2 text-sm text-violet-700/78">No suggestions available.</p>
          ) : (
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-violet-800/84">
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
