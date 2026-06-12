import Topbar from "./components/layout/Topbar";
import AgentPipeline from "./components/pipeline/AgentPipeline";
import TopicCard from "./components/topic/TopicCard";
import ScorePanel from "./components/scores/ScorePanel";
import LiveLog from "./components/logs/LiveLog";
import HistoryTable from "./components/history/HistoryTable";
import { useRunState } from "./hooks/useRunState";
import { useHistory } from "./hooks/useHistory";
import { triggerRun } from "./api/client";

export default function App() {
  const state = useRunState();
  const history = useHistory(state.runStatus);

  const handleRun = () => {
    triggerRun().catch((e) => alert(e.message));
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6 font-sans">
      <div className="max-w-5xl mx-auto">
        <Topbar
          connected={state.connected}
          runStatus={state.runStatus}
          publishMode={state.publishMode}
          nextScheduledRun={state.nextScheduledRun}
          onRun={handleRun}
        />

        <div className="grid grid-cols-3 gap-4">
          <div className="col-span-2">
            <AgentPipeline nodes={state.nodes} />
          </div>
          <div className="flex flex-col gap-4">
            <TopicCard topic={state.topic} source={state.topicSource} />
            <ScorePanel scores={state.scores} retryCount={state.retryCount} feedback={state.evalFeedback} />
            <LiveLog logs={state.logs} />
          </div>
        </div>

        {state.runStatus === "completed" && state.videoPath && state.runId && (
          <div className="mt-4 bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-sm text-emerald-800">
            Video ready:{" "}
            <a
              href={state.youtubeUrl ?? `/outputs/${state.runId}/short.mp4`}
              target="_blank"
              rel="noreferrer"
              className="font-medium underline"
            >
              {state.youtubeUrl ?? "preview local render"}
            </a>
            {state.dryRun && <span className="ml-2 text-emerald-600">(dry run — not uploaded)</span>}
          </div>
        )}

        <HistoryTable runs={history} />
      </div>
    </div>
  );
}
