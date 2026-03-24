import { useEffect, useState } from "react";
import axios from "axios";
import { useParams, useNavigate } from "react-router-dom";

export default function Review() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [evidence, setEvidence] = useState<any>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEvidence = async () => {
      try {
        const res = await axios.get(
          `https://bridgex-app.onrender.com/api/v1/evidence/${id}`
        );
        setEvidence(res.data.evidence);
      } catch (err) {
        console.error(err);
        alert("Failed to load evidence");
      } finally {
        setLoading(false);
      }
    };

    fetchEvidence();
  }, [id]);

  const approve = async (field: string) => {
    const res = await axios.post(
      `https://bridgex-app.onrender.com/api/v1/review/approve/${id}/${field}`
    );

    setEvidence(res.data.evidence);

    if (res.data?.dpm_mapping) {
      navigate(`/result/${id}`, { state: res.data });
    }
  };

  const reject = async (field: string) => {
    const res = await axios.post(
      `https://bridgex-app.onrender.com/api/v1/review/reject/${id}/${field}`
    );

    setEvidence(res.data.evidence);
  };

  if (loading)
    return <div className="text-white p-10">Loading...</div>;

  const total = Object.keys(evidence || {}).length;
  const approved = Object.values(evidence || {}).filter(
    (f: any) => f?.status === "APPROVED"
  ).length;

  const progress = total ? (approved / total) * 100 : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white">

      {/* ✅ NAVBAR (FIXED PROPERLY) */}
      <div className="fixed top-0 left-0 w-full h-20 bg-black/40 backdrop-blur border-b border-white/10 flex items-center justify-between px-6 z-50">

        {/* Left: Logo */}
        <div className="flex items-center">
          <img
            src="/BridgeX-logo.png"
            alt="BridgeX"
            className="h-12 object-contain"
          />
        </div>

        {/* Center: Title */}
        <div className="absolute left-1/2 transform -translate-x-1/2 text-white font-medium text-lg">
          Review Evidence
        </div>

        {/* Right: Record ID */}
        <div className="text-sm text-gray-300">
          Record #{id}
        </div>
      </div>

      {/* ✅ CONTENT (PUSHED BELOW NAVBAR) */}
      <div className="pt-28 px-6">

        <div className="max-w-4xl mx-auto space-y-8">

          {/* ✅ HEADER PANEL */}
          <div className="bg-white/10 border border-white/10 rounded-xl p-5">

            <div className="flex justify-between items-center mb-4">
              <div>
                <p className="text-gray-400 text-sm">Record</p>
                <p className="text-xl font-semibold">{id}</p>
              </div>

              <div>
                <p className="text-gray-400 text-sm">Progress</p>
                <p className="text-lg">{approved} / {total}</p>
              </div>
            </div>

            {/* ✅ Progress Bar (VISIBLE NOW) */}
            <div className="w-full bg-gray-700 rounded h-3">
              <div
                className="bg-blue-500 h-3 rounded transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* ✅ CARDS */}
          <div className="space-y-6">
            {Object.entries(evidence || {}).map(([key, field]: any) => (
              <div
                key={key}
                className="bg-white/10 backdrop-blur p-6 rounded-xl border border-white/10 shadow"
              >
                <h2 className="text-xl font-semibold mb-4">{key}</h2>

                <div className="space-y-2 text-sm text-gray-300">
                  <p>
                    <span className="font-medium text-white">Value:</span>{" "}
                    {field?.normalized
                      ? `${field.normalized.min} - ${field.normalized.max} ${field.normalized.unit}`
                      : "N/A"}
                  </p>

                  <p>
                    <span className="font-medium text-white">Source:</span>{" "}
                    {field?.lineage?.source_text || "N/A"}
                  </p>

                  <p>
                    <span className="font-medium text-white">Page:</span>{" "}
                    {field?.lineage?.page ?? "N/A"}
                  </p>

                  <p>
                    <span className="font-medium text-white">Confidence:</span>{" "}
                    {field?.metadata?.confidence ?? "N/A"}
                  </p>

                  <p>
                    <span className="font-medium text-white">Priority:</span>{" "}
                    {field?.metadata?.priority ?? "N/A"}
                  </p>

                  {/* Status */}
                  <div className="mt-3">
                    <span
                      className={`px-3 py-1 text-xs rounded-full ${
                        field?.status === "APPROVED"
                          ? "bg-green-500/20 text-green-400"
                          : field?.status === "REJECTED"
                          ? "bg-red-500/20 text-red-400"
                          : "bg-yellow-500/20 text-yellow-400"
                      }`}
                    >
                      {field?.status || "PENDING"}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                {field?.status !== "APPROVED" && (
                  <div className="mt-5 flex gap-3">
                    <button
                      onClick={() => approve(key)}
                      className="px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 transition"
                    >
                      Approve
                    </button>

                    <button
                      onClick={() => reject(key)}
                      className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 transition"
                    >
                      Reject
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>

        </div>
      </div>
    </div>
  );
}