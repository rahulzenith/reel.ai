interface Props {
  runId: string;
  videoPath: string | null;
  youtubeUrl: string | null;
  dryRun: boolean;
}

export default function VideoBanner({ runId, videoPath, youtubeUrl, dryRun }: Props) {
  if (!videoPath) return null;
  const src = `/outputs/${runId}/short.mp4`;

  return (
    <div className="bg-slate-900/50 border border-emerald-400/20 rounded-2xl p-5 backdrop-blur animate-fade-up">
      <div className="flex items-center justify-between mb-4">
        <p className="text-[11px] font-semibold text-emerald-400 uppercase tracking-[0.15em]">
          ✦ Video ready
        </p>
        <div className="flex items-center gap-3 text-xs">
          {youtubeUrl ? (
            <a href={youtubeUrl} target="_blank" rel="noreferrer" className="text-emerald-400 hover:underline">
              Watch on YouTube ↗
            </a>
          ) : (
            dryRun && (
              <span className="px-2 py-0.5 rounded-full bg-amber-400/10 text-amber-400 border border-amber-400/20">
                dry run — not uploaded
              </span>
            )
          )}
          <a href={src} download className="text-slate-400 hover:text-slate-200">
            download ↓
          </a>
        </div>
      </div>
      <div className="flex justify-center">
        <video
          src={src}
          controls
          className="rounded-xl max-h-[420px] aspect-[9/16] bg-black shadow-2xl shadow-emerald-500/10"
        />
      </div>
    </div>
  );
}
