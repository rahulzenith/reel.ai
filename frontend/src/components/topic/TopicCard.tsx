interface Props {
  topic: string | null;
  source: string | null;
}

const SOURCE_STYLES: Record<string, string> = {
  tavily: "bg-sky-400/10 text-sky-300 border-sky-400/20",
  "google-trends": "bg-purple-400/10 text-purple-300 border-purple-400/20",
  curated: "bg-slate-400/10 text-slate-400 border-slate-400/20",
  user: "bg-emerald-400/10 text-emerald-300 border-emerald-400/20",
};

export default function TopicCard({ topic, source }: Props) {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5 backdrop-blur animate-fade-up">
      <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-[0.15em] mb-2">Today's topic</p>
      {topic ? (
        <div className="animate-fade-in">
          <p className="text-base font-medium text-white leading-snug">{topic}</p>
          {source && (
            <span
              className={`inline-block mt-2 text-[11px] px-2 py-0.5 rounded-full border ${SOURCE_STYLES[source] ?? SOURCE_STYLES.curated}`}
            >
              {source}
            </span>
          )}
        </div>
      ) : (
        <p className="text-sm text-slate-600">Waiting for trend scout…</p>
      )}
    </div>
  );
}
