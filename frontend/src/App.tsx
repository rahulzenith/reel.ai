import { useState } from "react";
import Topbar from "./components/layout/Topbar";
import AgentPipeline from "./components/pipeline/AgentPipeline";
import TopicCard from "./components/topic/TopicCard";
import ScriptCard from "./components/script/ScriptCard";
import ScorePanel from "./components/scores/ScorePanel";
import LiveLog from "./components/logs/LiveLog";
import VideoBanner from "./components/video/VideoBanner";
import HistoryTable from "./components/history/HistoryTable";
import { useRunState } from "./hooks/useRunState";
import { useHistory } from "./hooks/useHistory";
import { triggerRun } from "./api/client";

export default function App() {
  const state = useRunState();
  const history = useHistory(state.runStatus);
  const [topic, setTopic] = useState("");
  const [content, setContent] = useState("");
  const [showContent, setShowContent] = useState(false);
  const [language, setLanguage] = useState("en");

  const handleRun = () => {
    triggerRun(topic, content, language)
      .then(() => {
        setTopic("");
        setContent("");
        setShowContent(false);
      })
      .catch((e) => alert(e.message));
  };

  return (
    <div className="min-h-screen text-slate-200 px-6 pb-10 font-sans">
      <Topbar
        connected={state.connected}
        runStatus={state.runStatus}
        publishMode={state.publishMode}
        nextScheduledRun={state.nextScheduledRun}
        topic={topic}
        content={content}
        showContent={showContent}
        language={language}
        onTopicChange={setTopic}
        onContentChange={setContent}
        onToggleContent={() => setShowContent((v) => !v)}
        onLanguageChange={setLanguage}
        onRun={handleRun}
      />

      <div className="max-w-6xl mx-auto flex flex-col gap-4">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Left: the live pipeline */}
          <div className="lg:col-span-4">
            <AgentPipeline nodes={state.nodes} />
          </div>

          {/* Right: what the agents are producing */}
          <div className="lg:col-span-8 flex flex-col gap-4">
            <TopicCard topic={state.topic} source={state.topicSource} />
            <ScriptCard script={state.script} />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <ScorePanel scores={state.scores} retryCount={state.retryCount} feedback={state.evalFeedback} />
          <LiveLog logs={state.logs} />
        </div>

        {state.runStatus === "completed" && state.runId && (
          <VideoBanner
            runId={state.runId}
            videoPath={state.videoPath}
            youtubeUrl={state.youtubeUrl}
            dryRun={state.dryRun}
          />
        )}

        <HistoryTable runs={history} />
      </div>
    </div>
  );
}
