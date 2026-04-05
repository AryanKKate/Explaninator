"use client";

import { useState } from "react";

export default function Upload() {
  const [status, setStatus] = useState("");

  const handleUpload = async (e: any) => {
    const file = e.target.files[0];
    if (!file) return;

    setStatus("Uploading...");

    const formData = new FormData();
    formData.append("file", file);

    await fetch("http://localhost:8000/upload", {
      method: "POST",
      body: formData,
    });

    setStatus("Indexed ✅");
  };

  return (
    <div className="bg-slate-900 p-4 rounded-lg">
      <h2 className="text-lg font-semibold mb-2">Upload Notes</h2>

      <input
        type="file"
        onChange={handleUpload}
        className="mb-2"
      />

      <p className="text-sm text-muted">{status}</p>
    </div>
  );
}