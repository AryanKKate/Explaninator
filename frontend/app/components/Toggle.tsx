"use client";

import { useState } from "react";

export default function Toggle({ onChange }: any) {
  const [enabled, setEnabled] = useState(false);

  const toggle = () => {
    const newState = !enabled;
    setEnabled(newState);
    onChange(newState);
  };

  return (
    <div className="flex items-center gap-3">
      <span className="text-sm">Web Enhancement</span>

      <button
        onClick={toggle}
        className={`w-12 h-6 flex items-center rounded-full p-1 ${
          enabled ? "bg-accent" : "bg-gray-600"
        }`}
      >
        <div
          className={`bg-white w-4 h-4 rounded-full transform transition ${
            enabled ? "translate-x-6" : ""
          }`}
        />
      </button>
    </div>
  );
}