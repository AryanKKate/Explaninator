"use client";

import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function Upload() {
  const [status, setStatus] = useState("");
  const [isUploading, setIsUploading] = useState(false);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setStatus("Uploading and indexing notes...");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail ?? "Upload failed.");
      }

      setStatus(`Indexed ✅ ${data.chunks_indexed} chunks from ${data.file}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unexpected upload error";
      setStatus(`Upload failed: ${message}`);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="bg-slate-900 p-4 rounded-lg">
      <h2 className="text-lg font-semibold mb-2">Upload Notes</h2>

      <input
        type="file"
        onChange={handleUpload}
        className="mb-2"
        accept=".pdf,.png,.jpg,.jpeg,.bmp,.tiff,.webp"
        disabled={isUploading}
      />

      <p className="text-sm text-muted">{status}</p>
    </div>
  );
}
