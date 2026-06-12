import type { Scores } from "../../state/types";
import ScoreBar from "./ScoreBar";

interface Props {
  scores: Scores | null;
  retryCount: number;
  feedback: string | null;
}

const HOOK_THRESHOLD = 0.7;

export default function ScorePanel({ scores, retryCount, feedback }: Props) {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5 backdrop-blur animate-fade-up">
      <div className="flex justify-between items-center mb-4">
        <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-[0.15em]">Judge scores</p>
        {retryCount > 1 && (
          <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-400/10 text-amber-400 border border-amber-400/20 animate-fade-in">
            attempt {retryCount}
          </span>
        )}
      </div>
      <ScoreBar label="Hook strength" value={scores?.hook_score ?? null} threshold={HOOK_THRESHOLD} />
      <ScoreBar label="Retention" value={scores?.retention_score ?? null} />
      <ScoreBar label="Clarity" value={scores?.clarity_score ?? null} />
      {feedback && (
        <p className="text-xs text-slate-500 mt-3 pt-3 border-t border-slate-800 italic animate-fade-in">
          “{feedback}”
        </p>
      )}
    </div>
  );
}
