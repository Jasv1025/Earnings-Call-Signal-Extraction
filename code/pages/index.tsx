import { useEffect, useState } from "react";
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip } from "chart.js";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip);

type ResultStructured = {
  management_sentiment?: string[];
  qa_sentiment?: string[];
  strategic_focuses?: string[];
  summary?: string;
  transcript?: string;
};

type Analysis = {
  quarter: string;
  date: string;
  analysis: {
    company: string;
    model: string;
    provider: string;
    result: ResultStructured;
    signal: string;
  };
};

const BASE_URL =
  typeof window !== "undefined" && window.location.hostname === "localhost"
    ? "http://localhost:5000"
    : "http://backend:5000";

export default function IndexPage(){
  const [data, setData] = useState<Analysis[]>([]);
  const [toneShifts, setToneShifts] = useState<{ from: string; to: string; result: string }[]>([]);
  const [activeTab, setActiveTab] = useState("transcripts");
  const [transcriptsSubTab, setTranscriptsSubTab] = useState<"summary" | "full">("summary");

  useEffect(() => {
    fetch(`${BASE_URL}/analyze/last-four`)
      .then(res => res.json())
      .then(json => setData(json.results));

    fetch(`${BASE_URL}/analyze/tone-shift`)
      .then(res => res.json())
      .then(json => setToneShifts(json.comparisons));
    
    console.log("Active Tab:", activeTab);
    console.log("Sub Tab:", transcriptsSubTab);
  },[]);

  const renderContent = () => {
    console.log("Active Tab:", activeTab);
    console.log("Sub Tab:", transcriptsSubTab);
    
    if(activeTab === "transcripts"){
      return (
        <div id="summary-section">
          {data.map((item) => (
            <div key={item.quarter} className="mb-4 p-4 border rounded bg-white shadow">
              <h2 className="text-xl font-bold">{item.quarter} – {item.date}</h2>
              <pre className="whitespace-pre-wrap mt-2">
                {transcriptsSubTab === "summary"
                  ? item.analysis.result.summary
                  : item.analysis.result.transcript || "Full transcript not available."}
              </pre>
            </div>
          ))}
        </div>
      );
    }if(activeTab === "sentiment"){
      return data.map((item) => (
        <div key={item.quarter} className="mb-4 p-4 border rounded bg-white shadow">
          <h3 className="font-semibold">{item.quarter}</h3>
          <p className="mt-2 font-semibold">Management Sentiment:</p>
          <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-2 rounded">
            {item.analysis.result.management_sentiment || "N/A"}
          </pre>
          <p className="mt-2 font-semibold">Q&A Sentiment:</p>
          <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-2 rounded">
            {item.analysis.result.qa_sentiment || "N/A"}
          </pre>
        </div>
      ));
    }if(activeTab === "strategic"){
      return data.map((item) => (
        <div key={item.quarter} className="mb-4 p-4 border rounded bg-white shadow">
          <h3 className="font-semibold">{item.quarter}</h3>
          <p className="mt-2 font-semibold">Strategic Focus Summary:</p>
          <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-2 rounded">
            {item.analysis.result.strategic_focuses || "N/A"}
          </pre>
        </div>
      ));
    }if(activeTab === "tone"){
      return (
        <div id="tone-section">
          {toneShifts.map((shift, i) => (
            <div key={i} className="mb-4 p-4 border rounded bg-white shadow">
              <h3 className="font-semibold">From {shift.from} to {shift.to}</h3>
              <p>{shift.result}</p>
            </div>
          ))}
        </div>
      );
    }return null;
  };

  return(
    <div className="flex min-h-screen bg-gray-50" style={{ marginLeft: "16rem" }}>
      <aside className="fixed top-0 left-0 h-screen w-64 bg-white shadow-md p-4 overflow-y-auto">
        <h2 className="text-xl font-bold mb-6">Dashboard</h2>
        <nav className="space-y-2">
          <button
            className={navItemStyle(activeTab === "transcripts")}
            onClick={() => setActiveTab("transcripts")}
          >
            Transcripts
          </button>
          {activeTab === "transcripts" && (
            <div className="ml-4 space-y-1">
              <button
                className={navSubItemStyle(transcriptsSubTab === "summary")}
                onClick={() => setTranscriptsSubTab("summary")}
              >
                Summary
              </button>
              <button
                className={navSubItemStyle(transcriptsSubTab === "full")}
                onClick={() => setTranscriptsSubTab("full")}
              >
                Full Text
              </button>
            </div>
          )}
          <button
            className={navItemStyle(activeTab === "sentiment")}
            onClick={() => setActiveTab("sentiment")}
          >
            Sentiment
          </button>
          <button
            className={navItemStyle(activeTab === "strategic")}
            onClick={() => setActiveTab("strategic")}
          >
            Strategic Focuses
          </button>
          <button
            className={navItemStyle(activeTab === "tone")}
            onClick={() => setActiveTab("tone")}
          >
            Tone Change
          </button>
        </nav>
      </aside>

      <main className="flex-1 p-8 overflow-y-auto">
        <h1 className="text-3xl font-bold mb-6 text-gray-800">NVIDIA Earnings Call Analysis</h1>
        {renderContent()}
      </main>
    </div>
  );
}

function navItemStyle(active: boolean){
  return `w-full text-left px-3 py-2 rounded-md font-medium transition ${
    active ? "bg-green-600 text-white" : "text-gray-700 hover:bg-gray-100"
  }`;
}

function navSubItemStyle(active: boolean){
  return `w-full text-left px-3 py-1 rounded-md text-sm transition ${
    active ? "bg-green-100 text-green-800" : "text-gray-600 hover:bg-gray-100"
  }`;
}