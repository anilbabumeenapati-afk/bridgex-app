import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import type { AxiosProgressEvent } from "axios";
import { uploadFile } from "../api/api";

export default function Upload() {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a file");
      return;
    }

    setLoading(true);
    setError("");
    setProgress(0);

    try {
      const res = await uploadFile(file, (progressEvent: AxiosProgressEvent) => {
        if (progressEvent.total) {
          const percent = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setProgress(percent);
        }
      });

      console.log("UPLOAD RESPONSE:", res.data);

      if (res.data?.error) {
        setError(`Upload failed: ${res.data.error}`);
        return;
      }

      if (res.data?.reason && !res.data?.record_id) {
        setError(`Upload failed: ${res.data.reason}`);
        return;
      }

      const recordId =
        res.data?.record_id ??
        (typeof res.data?.message === "string"
          ? res.data.message.match(/\d+/)?.[0]
          : undefined);

      if (!recordId) {
        setError(
          `Upload returned no record ID. Response: ${JSON.stringify(res.data)}`
        );
        return;
      }

      setTimeout(() => navigate(`/review/${recordId}`), 500);
    } catch (err: unknown) {
      console.error(err);
      setError("Upload failed. Check backend logs and browser console.");
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) setFile(droppedFile);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800 text-white">
      <div className="w-full max-w-lg p-8 rounded-2xl backdrop-blur-lg bg-white/10 shadow-xl border border-white/20">
        <h2 className="text-2xl font-semibold mb-2">Upload Document</h2>
        <p className="text-sm text-gray-300 mb-6">
          Drag & drop your file or click to browse
        </p>

        <div
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          className={`cursor-pointer border-2 border-dashed rounded-xl p-10 text-center transition ${
            dragging
              ? "border-blue-400 bg-blue-400/10"
              : "border-gray-500 hover:border-gray-300"
          }`}
        >
          <p className="text-gray-300">
            {file ? file.name : "Click or drag file here"}
          </p>
        </div>

        <input
          ref={inputRef}
          type="file"
          className="hidden"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />

        {file && (
          <div className="mt-4 text-sm text-gray-300">
            Selected: <span className="font-medium">{file.name}</span>
          </div>
        )}

        {loading && (
          <div className="mt-4">
            <div className="h-2 bg-gray-700 rounded">
              <div
                className="h-2 bg-blue-500 rounded transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-xs mt-1 text-gray-400">
              Uploading... {progress}%
            </p>
          </div>
        )}

        {error && <div className="mt-4 text-red-400 text-sm break-words">{error}</div>}

        <button
          onClick={handleUpload}
          disabled={loading}
          className="mt-6 w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-700 transition disabled:opacity-50"
        >
          {loading ? "Uploading..." : "Upload"}
        </button>
      </div>
    </div>
  );
}