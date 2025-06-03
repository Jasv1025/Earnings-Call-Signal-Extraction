import { useEffect, useState } from "react";
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip } from "chart.js";

// Registering Chart.js components (for future use, though no charts used here yet)
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip);

// Type definition for the AI-generated analysis result structure
type ResultStructured = {
  management_sentiment?: string[];
  qa_sentiment?: string[];
  strategic_focuses?: string[];
  summary?: string;
  transcript?: string;
};

// Type definition for a single earnings analysis record
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

// Determine backend API base URL depending on client environment
const BASE_URL = process.env.NEXT_PUBLIC_API_URL!;

export default function IndexPage(){
  // Holds full response data for the last four quarters
  const [data, setData] = useState<Analysis[]>([]);
  // Holds tone comparison results between adjacent quarters
  const [toneShifts, setToneShifts] = useState<{ from: string; to: string; result: string }[]>([]);
  // Tracks which top-level section/tab is active
  const [activeTab, setActiveTab] = useState("transcripts");
  // Tracks which sub-tab of the transcript page is active
  const [transcriptsSubTab, setTranscriptsSubTab] = useState<"summary" | "full">("summary");

  useEffect(() => {
    // Fetch data for the last four quarters' earnings analysis
    fetch(`${BASE_URL}/analyze/last-four`)
      .then(res => res.json())
      .then(json => setData(json.results));

    // Fetch tone shift comparisons between quarters
    fetch(`${BASE_URL}/analyze/tone-shift`)
      .then(res => res.json())
      .then(json => setToneShifts(json.comparisons));
    
    // Debugging logs
    console.log("Active Tab:", activeTab);
    console.log("Sub Tab:", transcriptsSubTab);
  },[]);

  // Renders content based on the current active tab and sub-tab
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
    }

    if(activeTab === "sentiment"){
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
    }

    if(activeTab === "strategic"){
      return data.map((item) => (
        <div key={item.quarter} className="mb-4 p-4 border rounded bg-white shadow">
          <h3 className="font-semibold">{item.quarter}</h3>
          <p className="mt-2 font-semibold">Strategic Focus Summary:</p>
          <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-2 rounded">
            {item.analysis.result.strategic_focuses || "N/A"}
          </pre>
        </div>
      ));
    }

    if(activeTab === "tone"){
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
    }

    return null;
  };

  return(
    <div className="flex min-h-screen bg-gray-50" style={{ marginLeft: "16rem" }}>
      {/* Sidebar Navigation */}
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

      {/* Main Content Section */}
      <main className="flex-1 p-8 overflow-y-auto">
        <h1 className="text-3xl font-bold mb-6 text-gray-800">NVIDIA Earnings Call Analysis</h1>
        {renderContent()}
      </main>
    </div>
  );
}

// Styles the main nav items
function navItemStyle(active: boolean){
  return `w-full text-left px-3 py-2 rounded-md font-medium transition ${
    active ? "bg-green-600 text-white" : "text-gray-700 hover:bg-gray-100"
  }`;
}

// Styles the sub-nav items for transcript tabs
function navSubItemStyle(active: boolean){
  return `w-full text-left px-3 py-1 rounded-md text-sm transition ${
    active ? "bg-green-100 text-green-800" : "text-gray-600 hover:bg-gray-100"
  }`;
}