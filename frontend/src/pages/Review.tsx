import { useEffect, useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { approveField, getEvidence, rejectField } from "../api/api";

const REVIEWABLE_KEYS = [
  "operational_availability",
  "incident_notification_time",
  "data_residency",
  "security_certifications",
] as const;

type ReviewableKey = (typeof REVIEWABLE_KEYS)[number];

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
    source_file?: string | null;
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
  value?: unknown;
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

type StatePanel = {
  completeness_percent?: number;
  missing_fields?: string[];
  conflicts?: Array<{
    field?: string;
    type?: string;
    details?: unknown;
  }>;
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

export default function Review() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [evidence, setEvidence] = useState<EvidencePayload>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEvidence = async () => {
      try {
        if (!id) return;
        const res = await getEvidence(id);
        setEvidence(res.data.evidence || {});
      } catch (err) {
        console.error(err);
        alert("Failed to load evidence");
      } finally {
        setLoading(false);
      }
    };

    fetchEvidence();
  }, [id]);

  const approve = async (field: ReviewableKey) => {
    try {
      if (!id) return;
      const res = await approveField(id, field);

      if (res.data?.error) {
        alert(res.data.error);
        return;
      }

      setEvidence(res.data.evidence || {});

      if (res.data?.dpm_mapping) {
        navigate(`/result/${id}`, { state: res.data });
      }
    } catch (err) {
      console.error(err);
      alert("Failed to approve field");
    }
  };

  const reject = async (field: ReviewableKey) => {
    try {
      if (!id) return;
      const res = await rejectField(id, field);

      if (res.data?.error) {
        alert(res.data.error);
        return;
      }

      setEvidence(res.data.evidence || {});
    } catch (err) {
      console.error(err);
      alert("Failed to reject field");
    }
  };

  const reviewableEntries = useMemo(
    () =>
      REVIEWABLE_KEYS.map(
        (key): readonly [ReviewableKey, FieldData | undefined] => [
          key,
          evidence[key],
        ]
      ),
    [evidence]
  );

  const total = REVIEWABLE_KEYS.length;
  const approved = REVIEWABLE_KEYS.filter(
    (key) => evidence[key]?.status === "APPROVED"
  ).length;
  const progress = total ? (approved / total) * 100 : 0;

  const state = evidence.state;

  if (loading) {
    return <div className="text-white p-10">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white">
      <div className="fixed top-0 left-0 w-full h-20 bg-black/40 backdrop-blur border-b border-white/10 flex items-center justify-between px-6 z-50">
        <div className="flex items-center">
          <img
            src="/BridgeX-logo.png"
            alt="BridgeX"
            className="h-12 object-contain"
          />
        </div>

        <div className="absolute left-1/2 transform -translate-x-1/2 text-white font-medium text-lg">
          Review Evidence
        </div>

        <div className="text-sm text-gray-300">Record #{id}</div>
      </div>

      <div className="pt-28 px-6">
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="bg-white/10 border border-white/10 rounded-xl p-5">
            <div className="flex justify-between items-center mb-4">
              <div>
                <p className="text-gray-400 text-sm">Record</p>
                <p className="text-xl font-semibold">{id}</p>
              </div>

              <div>
                <p className="text-gray-400 text-sm">Progress</p>
                <p className="text-lg">
                  {approved} / {total}
                </p>
              </div>
            </div>

            <div className="w-full bg-gray-700 rounded h-3">
              <div
                className="bg-blue-500 h-3 rounded transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>

            {state && (
              <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                <div className="bg-white/5 rounded-lg p-3 border border-white/10">
                  <p className="text-gray-400">Completeness</p>
                  <p className="text-white font-medium">
                    {state.completeness_percent ?? 0}%
                  </p>
                </div>

                <div className="bg-white/5 rounded-lg p-3 border border-white/10">
                  <p className="text-gray-400">Missing Fields</p>
                  <p className="text-white font-medium">
                    {state.missing_fields?.length ?? 0}
                  </p>
                </div>

                <div className="bg-white/5 rounded-lg p-3 border border-white/10">
                  <p className="text-gray-400">Conflicts</p>
                  <p className="text-white font-medium">
                    {state.conflicts?.length ?? 0}
                  </p>
                </div>
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
                        <p className="text-sm text-gray-400 mt-1">{item.explanation}</p>
                      )}

                      <p className="text-xs mt-2 text-gray-500">
                        Severity: {item.severity || "unknown"}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="space-y-6">
            {reviewableEntries.map(([key, field]) => {
              const hasEvidence =
                !!field &&
                (
                  field.normalized?.min != null ||
                  field.normalized?.max != null ||
                  !!field.source?.text ||
                  !!field.lineage?.source_text
                );

              return (
                <div
                  key={key}
                  className="bg-white/10 backdrop-blur p-6 rounded-xl border border-white/10 shadow"
                >
                  <h2 className="text-xl font-semibold mb-4">{key}</h2>

                  <div className="space-y-2 text-sm text-gray-300">
                    <p>
                      <span className="font-medium text-white">Value:</span>{" "}
                      {field?.normalized &&
                      (field.normalized.min !== null ||
                        field.normalized.max !== null)
                        ? `${field.normalized.min ?? "-"} - ${
                            field.normalized.max ?? "-"
                          } ${field.normalized.unit ?? ""}`.trim()
                        : "N/A"}
                    </p>

                    <p>
                      <span className="font-medium text-white">Source:</span>{" "}
                      {field?.source?.text ||
                        field?.lineage?.source_text ||
                        "N/A"}
                    </p>

                    <p>
                      <span className="font-medium text-white">Page:</span>{" "}
                      {field?.source?.page ?? field?.lineage?.page ?? "N/A"}
                    </p>

                    <p>
                      <span className="font-medium text-white">Source File:</span>{" "}
                      {field?.source?.file || field?.lineage?.file || "N/A"}
                    </p>

                    <p>
                      <span className="font-medium text-white">Confidence:</span>{" "}
                      {field?.metadata?.confidence ??
                        field?.lineage?.confidence ??
                        "N/A"}
                    </p>

                    <p>
                      <span className="font-medium text-white">Priority:</span>{" "}
                      {field?.metadata?.priority ?? "N/A"}
                    </p>

                    <p>
                      <span className="font-medium text-white">Trust Score:</span>{" "}
                      {field?.trust?.score ?? "N/A"}
                    </p>

                    <p>
                      <span className="font-medium text-white">
                        Verification Tier:
                      </span>{" "}
                      {field?.trust?.verification_tier ?? "N/A"}
                    </p>

                    <p>
                      <span className="font-medium text-white">
                        Binding Strength:
                      </span>{" "}
                      {field?.trust?.binding_strength ?? "N/A"}
                    </p>

                    <p>
                      <span className="font-medium text-white">Source Type:</span>{" "}
                      {field?.trust?.source_type ?? "N/A"}
                    </p>

                    <p>
                      <span className="font-medium text-white">
                        Extraction Rule:
                      </span>{" "}
                      {field?.lineage?.extraction_rule ?? "N/A"}
                    </p>

                    <p>
                      <span className="font-medium text-white">Mapped Field:</span>{" "}
                      {field?.lineage?.mapped_field ?? "N/A"}
                    </p>

                    {field?.risk?.flags && field.risk.flags.length > 0 && (
                      <div className="mt-3">
                        <p className="font-medium text-white mb-1">Risk Flags:</p>
                        <ul className="list-disc ml-5 space-y-1 text-red-300">
                          {field.risk.flags.map((flag: string, idx: number) => (
                            <li key={idx}>{flag}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {field?.review?.reason && (
                      <p>
                        <span className="font-medium text-white">
                          Review Note:
                        </span>{" "}
                        {field.review.reason}
                      </p>
                    )}

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

                  {hasEvidence && field?.status !== "APPROVED" && (
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
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}