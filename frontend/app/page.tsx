"use client";
import { useState } from "react";
import Chat from "./components/Chat";
import Upload from "./components/Upload";
import Toggle from "./components/Toggle";

export default function Home() {
  const [webEnabled, setWebEnabled] = useState(false);

  return (
    <div className="flex flex-col h-screen p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6 border-b border-slate-800 pb-4">
        <h1 className="text-3xl font-bold text-primary">AI Tutor</h1>
        <Toggle onChange={setWebEnabled} />
      </div>

      <div className="flex gap-6 flex-1 min-h-0">
        <div className="w-1/3 flex flex-col gap-4">
          <Upload />
          <div className="bg-slate-900 p-4 rounded-lg flex-1">
            <h2 className="text-lg font-semibold mb-2">Instructions</h2>
            <p className="text-muted text-sm border-b border-slate-800 pb-2 mb-2">
              1. Upload your study material.<br/>
              2. Ask questions about it.<br/>
              3. Our AI Crew will find the answers and explain them.
            </p>
            {webEnabled && <p className="text-accent text-sm text-center">Web searching is enabled</p>}
          </div>
        </div>
        <div className="flex-1 bg-slate-900 rounded-lg overflow-hidden border border-slate-800">
          <Chat />
        </div>
      </div>
    </div>
  );
}