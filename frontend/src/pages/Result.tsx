import { useLocation, useNavigate, useParams } from "react-router-dom";
import { getDownloadUrl } from "../api/api";

const REVIEWABLE_KEYS = [
  "operational_availability",
  "incident_notification_time",
  "data_residency",
  "security_certifications",
] as const;

type FieldData = {
  normalized?: {
    min?: string | number | null;
    max?: string | number | null;
    unit?: string | null;
  };
  source?: {
    text?: string | null;
    page?: number | null;
    file?: string | null;
  };
  lineage?: {
    source_text?: string | null;
    raw_text?: string | null;
    page?: number | null;
    file?: string | null;
    confidence?: number | null;
    extraction_rule?: string | null;
    mapped_field?: string | null;
    conflict?: unknown;
  };
  metadata?: {
    confidence?: number | null;
    priority?: string | null;
    review_required?: boolean | null;
    claim?: Record<string, unknown>;
  };
  trust?: {
    score?: number | null;
    verification_tier?: string | null;
    binding_strength?: string | null;
    source_type?: string | null;
    staleness_status?: string | null;
  };
  risk?: {
    flags?: string[];
    trace?: unknown[];
    severity?: string | null;
  };
  review?: {
    decision?: string | null;
    reviewer?: string | null;
    timestamp?: string | null;
    reason?: string | null;
  };
  status?: string;
};

type ConflictSummary = {
  field?: string;
  summary_type?: string;
  severity?: string;
  headline?: string;
  primary_value?: unknown;
  alternate_values?: unknown[];
  explanation?: string;
};

type ConflictItem = {
  field?: string;
  type?: string;
  details?: string | number | boolean | Record<string, unknown> | unknown[] | null;
};

type StatePanel = {
  completeness_percent?: number;
  missing_fields?: string[];
  conflicts?: ConflictItem[];
  conflict_summaries?: ConflictSummary[];
  review_progress?: {
    approved?: number;
    total?: number;
  };
};

type VendorProfile = {
  vendor_name?: string | null;
  service_type?: string | null;
  criticality?: string | null;
  risk_level?: string | null;
  dependency?: string | null;
  contract_status?: string | null;
};

type EvidencePayload = {
  operational_availability?: FieldData;
  incident_notification_time?: FieldData;
  data_residency?: FieldData;
  security_certifications?: FieldData;
  state?: StatePanel;
  vendor_profile?: VendorProfile;
};

type ValidationPayload = {
  status?: string;
  fields?: Record<string, { status?: string }>;
};

type DpmMappingValue = {
  unit?: string;
  value?: {
    min?: string | number | null;
    max?: string | number | null;
  };
  risk_flags?: string[];
  trust_score?: number | null;
  binding_strength?: string | null;
  verification_tier?: string | null;
  source?: {
    raw_text?: string | null;
    page?: number | null;
    file?: string | null;
    rule?: string | null;
  };
  claim?: Record<string, unknown>;
  status?: string;
};

type ResultPayload = {
  evidence?: EvidencePayload;
  validation?: ValidationPayload;
  exceptions?: Array<{
    field?: string;
    message?: string;
  }>;
  dpm_mapping?: Record<string, DpmMappingValue>;
  xbrl_csv?: {
    csv?: string;
    metadata?: string;
  };
  zip?: string;
};

function renderUnknown(value: unknown): string {
  if (value == null) return "";
  if (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return String(value);
  }
  return JSON.stringify(value);
}

export default function Result() {
  const location = useLocation();
  const { id } = useParams();
  const navigate = useNavigate();

  const data = location.state as ResultPayload | null;

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

  const filename = data.xbrl_csv?.csv?.split("/").pop();
  const metadataFile = data.xbrl_csv?.metadata?.split("/").pop();
  const zipFile = data.zip?.split("/").pop();

  const evidence = data.evidence || {};
  const state = evidence.state;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white">
      <div className="fixed top-0 left-0 w-full h-20 bg-black/40 backdrop-blur border-b border-white/10 flex items-center justify-between px-6 z-50">
        <img
          src="/BridgeX-logo.png"
          alt="BridgeX"
          className="h-12 object-contain"
        />

        <div className="absolute left-1/2 transform -translate-x-1/2 text-lg font-medium">
          Result Dashboard
        </div>

        <div className="text-sm text-gray-300">Record #{id}</div>
      </div>

      <div className="pt-28 px-6">
        <div className="max-w-5xl mx-auto space-y-8">
          <div className="bg-white/10 border border-white/10 rounded-xl p-5">
            <p className="text-gray-400 text-sm">Record ID</p>
            <p className="text-xl font-semibold">{id}</p>
          </div>

          <section>
            <h2 className="text-xl mb-4">State</h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white/10 border border-white/10 rounded-xl p-5">
                <p className="text-gray-400 text-sm">Completeness</p>
                <p className="text-xl font-semibold">
                  {state?.completeness_percent ?? 0}%
                </p>
              </div>

              <div className="bg-white/10 border border-white/10 rounded-xl p-5">
                <p className="text-gray-400 text-sm">Missing Fields</p>
                <p className="text-xl font-semibold">
                  {state?.missing_fields?.length ?? 0}
                </p>
              </div>

              <div className="bg-white/10 border border-white/10 rounded-xl p-5">
                <p className="text-gray-400 text-sm">Conflicts</p>
                <p className="text-xl font-semibold">
                  {state?.conflict_summaries?.length ??
                    state?.conflicts?.length ??
                    0}
                </p>
              </div>
            </div>

            {state?.missing_fields && state.missing_fields.length > 0 && (
              <div className="mt-4 bg-white/10 border border-white/10 rounded-xl p-5">
                <p className="font-medium mb-2">Missing Fields</p>
                <ul className="list-disc ml-5 space-y-1 text-yellow-300">
                  {state.missing_fields.map((field, idx) => (
                    <li key={idx}>{field}</li>
                  ))}
                </ul>
              </div>
            )}

            {state?.conflict_summaries && state.conflict_summaries.length > 0 && (
              <div className="mt-4 bg-white/10 border border-white/10 rounded-xl p-5">
                <p className="font-medium mb-3">Conflict Interpretations</p>
                <div className="space-y-3">
                  {state.conflict_summaries.map((item, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded bg-white/5 border border-white/10"
                    >
                      <p className="text-white font-medium">
                        {item.field || "unknown"} — {item.headline || "Interpretation"}
                      </p>

                      {item.primary_value != null && (
                        <p className="text-sm text-gray-300 mt-1">
                          Primary value: {renderUnknown(item.primary_value)}
                        </p>
                      )}

                      {item.alternate_values && item.alternate_values.length > 0 && (
                        <p className="text-sm text-gray-300 mt-1">
                          Alternate values:{" "}
                          {item.alternate_values.map((v) => renderUnknown(v)).join(", ")}
                        </p>
                      )}

                      {item.explanation && (
                        <p className="text-sm text-gray-400 mt-1">
                          {item.explanation}
                        </p>
                      )}

                      <p className="text-xs mt-2 text-gray-500">
                        Severity: {item.severity || "unknown"}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>

          <section>
            <h2 className="text-xl mb-4">Evidence</h2>

            <div className="space-y-4">
              {REVIEWABLE_KEYS.map((key) => {
                const field = evidence[key];

                return (
                  <div
                    key={key}
                    className="bg-white/10 p-5 rounded-xl border border-white/10"
                  >
                    <h3 className="text-lg font-semibold mb-2">{key}</h3>

                    <p>
                      <span className="font-medium">Value:</span>{" "}
                      {field?.normalized &&
                      (field.normalized.min !== null ||
                        field.normalized.max !== null)
                        ? `${field.normalized.min ?? "-"} - ${
                            field.normalized.max ?? "-"
                          } ${field.normalized.unit ?? ""}`.trim()
                        : "N/A"}
                    </p>

                    <p>
                      <span className="font-medium">Source:</span>{" "}
                      {field?.source?.text ||
                        field?.lineage?.source_text ||
                        "N/A"}
                    </p>

                    <p>
                      <span className="font-medium">Page:</span>{" "}
                      {field?.source?.page ?? field?.lineage?.page ?? "N/A"}
                    </p>

                    <p>
                      <span className="font-medium">Source File:</span>{" "}
                      {field?.source?.file || field?.lineage?.file || "N/A"}
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
                        {field?.status || "PENDING"}
                      </span>
                    </p>

                    <p className="text-sm text-gray-400 mt-2">
                      Confidence:{" "}
                      {field?.metadata?.confidence ??
                        field?.lineage?.confidence ??
                        "N/A"}{" "}
                      | Priority: {field?.metadata?.priority ?? "N/A"}
                    </p>

                    <p className="text-sm text-gray-400 mt-1">
                      Trust Score: {field?.trust?.score ?? "N/A"} | Verification
                      Tier: {field?.trust?.verification_tier ?? "N/A"}
                    </p>

                    <p className="text-sm text-gray-400 mt-1">
                      Binding Strength:{" "}
                      {field?.trust?.binding_strength ?? "N/A"} | Source Type:{" "}
                      {field?.trust?.source_type ?? "N/A"}
                    </p>

                    <p className="text-sm text-gray-400 mt-1">
                      Extraction Rule:{" "}
                      {field?.lineage?.extraction_rule ?? "N/A"} | Mapped Field:{" "}
                      {field?.lineage?.mapped_field ?? "N/A"}
                    </p>

                    {field?.risk?.flags && field.risk.flags.length > 0 && (
                      <div className="mt-3">
                        <p className="font-medium mb-1">Risk Flags</p>
                        <ul className="list-disc ml-5 text-red-300 space-y-1">
                          {field.risk.flags.map((flag, idx) => (
                            <li key={idx}>{flag}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {field?.review?.reason && (
                      <p className="text-sm text-gray-300 mt-2">
                        <span className="font-medium">Review Note:</span>{" "}
                        {field.review.reason}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          </section>

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
                  {data.validation?.status ?? "unknown"}
                </span>
              </p>

              <div className="mt-3 space-y-2">
                {Object.entries(data.validation?.fields || {}).map(([k, v]) => (
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
                ))}
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-xl mb-4">Exceptions</h2>

            <div className="bg-white/10 border border-white/10 rounded-xl p-5">
              {data.exceptions && data.exceptions.length > 0 ? (
                data.exceptions.map((ex, i) => (
                  <div
                    key={i}
                    className="mb-3 p-3 rounded bg-red-500/10 text-red-400 border border-red-500/20"
                  >
                    <b>{ex.field}</b> → {ex.message}
                  </div>
                ))
              ) : (
                <div className="text-green-400">No issues detected</div>
              )}
            </div>
          </section>

          <section>
            <h2 className="text-xl mb-4">DPM Mapping</h2>

            <div className="bg-white/10 p-5 rounded-xl border border-white/10 space-y-2">
              {Object.entries(data.dpm_mapping || {}).map(([k, v]) => (
                <div key={k}>
                  <span className="font-medium">{k}</span> → {v.unit} (
                  {v.value?.min ?? "-"} - {v.value?.max ?? "-"})
                </div>
              ))}
            </div>
          </section>

          <section>
            <h2 className="text-xl mb-4">Downloads</h2>

            <div className="flex gap-3 flex-wrap">
              {filename && (
                <a href={getDownloadUrl(filename)} download>
                  <button className="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700">
                    CSV Report
                  </button>
                </a>
              )}

              {metadataFile && (
                <a href={getDownloadUrl(metadataFile)} download>
                  <button className="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700">
                    Metadata
                  </button>
                </a>
              )}

              {zipFile && (
                <a href={getDownloadUrl(zipFile)} download>
                  <button className="px-4 py-2 bg-green-600 rounded hover:bg-green-700">
                    Full Package (ZIP)
                  </button>
                </a>
              )}
            </div>
          </section>

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