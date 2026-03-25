import { useState, useRef } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

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

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(
        "https://bridgex-app.onrender.com/api/v1/upload/",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percent = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
              );
              setProgress(percent);
            }
          }
        }
      );

      const recordId = res.data.message?.match(/\d+/)?.[0];

      if (!recordId) {
        setError("Upload succeeded but no record ID found");
        return;
      }

      // slight delay for UX polish
      setTimeout(() => navigate(`/review/${recordId}`), 800);

    } catch (err) {
      console.error(err);
      setError("Upload failed. Try again.");
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
        
        {/* Title */}
        <h2 className="text-2xl font-semibold mb-2">Upload Document</h2>
        <p className="text-sm text-gray-300 mb-6">
          Drag & drop your file or click to browse
        </p>

        {/* Drop Zone */}
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

        {/* File Info */}
        {file && (
          <div className="mt-4 text-sm text-gray-300">
            Selected: <span className="font-medium">{file.name}</span>
          </div>
        )}

        {/* Progress Bar */}
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

        {/* Error */}
        {error && (
          <div className="mt-4 text-red-400 text-sm">{error}</div>
        )}

        {/* Button */}
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