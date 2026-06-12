interface Props {
  topic: string | null;
  source: string | null;
}

const SOURCE_STYLES: Record<string, string> = {
  tavily: "bg-blue-100 text-blue-700",
  "google-trends": "bg-purple-100 text-purple-700",
  curated: "bg-gray-100 text-gray-600",
};

export default function TopicCard({ topic, source }: Props) {
  return (
    <div className="bg-white border border-gray-100 rounded-xl p-4">
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">Today's topic</p>
      {topic ? (
        <>
          <p className="text-sm font-medium text-gray-900 leading-snug">{topic}</p>
          {source && (
            <span
              className={`inline-block mt-2 text-xs px-2 py-0.5 rounded-full ${SOURCE_STYLES[source] ?? "bg-gray-100 text-gray-600"}`}
            >
              {source}
            </span>
          )}
        </>
      ) : (
        <p className="text-sm text-gray-300">Waiting for trend scout...</p>
      )}
    </div>
  );
}
