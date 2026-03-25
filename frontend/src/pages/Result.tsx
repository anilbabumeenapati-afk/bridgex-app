import { useLocation, useParams, useNavigate } from "react-router-dom";

export default function Result() {
  const location = useLocation();
  const { id } = useParams();
  const navigate = useNavigate();

  const data = location.state;
  const filename = data.xbrl_csv?.csv?.split("/").pop();
  const metadataFile = data.xbrl_csv?.metadata?.split("/").pop();
  const zipFile = data.zip?.split("/").pop();

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900 text-white">
        <div>
          <h2 className="text-xl mb-4">No result data found</h2>
          <button
            onClick={() => navigate("/")}
            className="px-4 py-2 bg-blue-600 rounded"
          >
            Back to Upload
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white">

      {/* NAVBAR */}
      <div className="fixed top-0 left-0 w-full h-20 bg-black/40 backdrop-blur border-b border-white/10 flex items-center justify-between px-6 z-50">
        
        <img
          src="/BridgeX-logo.png"
          alt="BridgeX"
          className="h-12 object-contain"
        />

        <div className="absolute left-1/2 transform -translate-x-1/2 text-lg font-medium">
          Result Dashboard
        </div>

        <div className="text-sm text-gray-300">
          Record #{id}
        </div>
      </div>

      {/* CONTENT */}
      <div className="pt-28 px-6">
        <div className="max-w-5xl mx-auto space-y-8">

          {/* HEADER */}
          <div className="bg-white/10 border border-white/10 rounded-xl p-5">
            <p className="text-gray-400 text-sm">Record ID</p>
            <p className="text-xl font-semibold">{id}</p>
          </div>

          {/* ================= EVIDENCE ================= */}
          <section>
            <h2 className="text-xl mb-4">Evidence</h2>

            <div className="space-y-4">
              {Object.entries(data.evidence || {}).map(([key, field]: any) => (
                <div
                  key={key}
                  className="bg-white/10 p-5 rounded-xl border border-white/10"
                >
                  <h3 className="text-lg font-semibold mb-2">{key}</h3>

                  <p>
                    <span className="font-medium">Value:</span>{" "}
                    {field?.normalized &&
                    (field.normalized.min !== null || field.normalized.max !== null)
                      ? `${field.normalized.min ?? "-"} - ${field.normalized.max ?? "-"}`
                      : "N/A"}
                  </p>

                  <p>
                    <span className="font-medium">Source:</span>{" "}
                    {field?.lineage?.source_text || "N/A"}
                  </p>

                  <p>
                    <span className="font-medium">Page:</span>{" "}
                    {field?.lineage?.page ?? "N/A"}
                  </p>

                  <p className="mt-2">
                    <span
                      className={`px-2 py-1 text-xs rounded ${
                        field?.status === "APPROVED"
                          ? "bg-green-500/20 text-green-400"
                          : field?.status === "REJECTED"
                          ? "bg-red-500/20 text-red-400"
                          : "bg-gray-500/20 text-gray-300"
                      }`}
                    >
                      {field?.status}
                    </span>
                  </p>

                  <p className="text-sm text-gray-400 mt-2">
                    Confidence: {field?.metadata?.confidence ?? "N/A"} | Priority:{" "}
                    {field?.metadata?.priority ?? "N/A"}
                  </p>
                </div>
              ))}
            </div>
          </section>

          {/* ================= VALIDATION ================= */}
          <section>
            <h2 className="text-xl mb-4">Validation</h2>

            <div className="bg-white/10 p-5 rounded-xl border border-white/10">
              <p>
                Status:{" "}
                <span
                  className={`font-medium ${
                    data.validation?.status === "valid"
                      ? "text-green-400"
                      : "text-red-400"
                  }`}
                >
                  {data.validation?.status}
                </span>
              </p>

              <div className="mt-3 space-y-2">
                {Object.entries(data.validation?.fields || {}).map(
                  ([k, v]: any) => (
                    <div key={k} className="text-sm text-gray-300">
                      {k}:{" "}
                      <span
                        className={
                          v.status === "pass"
                            ? "text-green-400"
                            : v.status === "fail"
                            ? "text-red-400"
                            : "text-yellow-400"
                        }
                      >
                        {v.status}
                      </span>
                    </div>
                  )
                )}
              </div>
            </div>
          </section>

          {/* ================= EXCEPTIONS ================= */}
          <section>
            <h2 className="text-xl mb-4">Exceptions</h2>

            <div className="bg-white/10 border border-white/10 rounded-xl p-5">

              {data.exceptions && data.exceptions.length > 0 ? (
                data.exceptions.map((ex: any, i: number) => (
                  <div
                    key={i}
                    className="mb-3 p-3 rounded bg-red-500/10 text-red-400 border border-red-500/20"
                  >
                    <b>{ex.field}</b> → {ex.message}
                  </div>
                ))
              ) : (
                <div className="text-green-400">
                  No issues detected
                </div>
              )}

            </div>
          </section>

          {/* ================= DPM ================= */}
          <section>
            <h2 className="text-xl mb-4">DPM Mapping</h2>

            <div className="bg-white/10 p-5 rounded-xl border border-white/10 space-y-2">
              {Object.entries(data.dpm_mapping || {}).map(([k, v]: any) => (
                <div key={k}>
                  <span className="font-medium">{k}</span> → {v.unit} (
                  {v.value?.min ?? "-"} - {v.value?.max ?? "-"})
                </div>
              ))}
            </div>
          </section>

          {/* ================= DOWNLOADS ================= */}
          <section>
            <h2 className="text-xl mb-4">Downloads</h2>

            <div className="flex gap-3 flex-wrap">

              <a href={`https://bridgex-app.onrender.com/api/v1/download/${filename}`} download>
                <button className="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700">
                  CSV Report
                </button>
              </a>

              <a href={`https://bridgex-app.onrender.com/api/v1/download/${metadataFile}`} download>
                <button className="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700">
                  Metadata
                </button>
              </a>

              <a href={`https://bridgex-app.onrender.com/api/v1/download/${zipFile}`} download>
                <button className="px-4 py-2 bg-green-600 rounded hover:bg-green-700">
                  Full Package (ZIP)
                </button>
              </a>

            </div>
          </section>

          {/* BACK */}
          <button
            onClick={() => navigate("/")}
            className="text-gray-400 hover:text-white"
          >
            ← Back to Upload
          </button>

        </div>
      </div>
    </div>
  );
}