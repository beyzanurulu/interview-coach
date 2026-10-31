"use client";

import { useState } from "react";

import { getApiBaseUrl } from "@/lib/config";
import type { CVSummary, InterviewType, Language, StartPayload } from "@/lib/interview";

const DURATIONS = [5, 10, 15];
const MIN_JOB_CHARS = 40;

const TYPE_LABELS: Record<InterviewType, string> = {
  mixed: "Karışık",
  technical: "Teknik",
  behavioral: "Davranışsal",
};

export function SetupForm({ onStart }: { onStart: (payload: StartPayload) => void }) {
  const [jobText, setJobText] = useState("");
  const [interviewType, setInterviewType] = useState<InterviewType>("mixed");
  const [language, setLanguage] = useState<Language>("tr");
  const [duration, setDuration] = useState(10);
  const [cv, setCv] = useState<CVSummary | null>(null);
  const [cvStatus, setCvStatus] = useState<"idle" | "uploading" | "done" | "error">("idle");
  const [cvError, setCvError] = useState("");

  async function uploadCv(file: File) {
    setCvStatus("uploading");
    setCvError("");
    const body = new FormData();
    body.append("file", file);
    try {
      const resp = await fetch(`${getApiBaseUrl()}/api/cv`, { method: "POST", body });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail ?? "CV okunamadı.");
      setCv(data);
      setCvStatus("done");
    } catch (err) {
      setCv(null);
      setCvStatus("error");
      setCvError(err instanceof Error ? err.message : "CV okunamadı.");
    }
  }

  const canStart = jobText.trim().length >= MIN_JOB_CHARS && cvStatus !== "uploading";

  return (
    <form
      className="flex flex-col gap-5"
      onSubmit={(e) => {
        e.preventDefault();
        if (!canStart) return;
        onStart({
          type: "start",
          job_text: jobText,
          cv_summary: cv,
          interview_type: interviewType,
          language,
          duration_min: duration,
        });
      }}
    >
      <label className="flex flex-col gap-2">
        <span className="font-medium">İş ilanı metni</span>
        <textarea
          className="min-h-48 rounded-md border border-neutral-300 bg-transparent p-3 dark:border-neutral-700"
          placeholder="İlanın tamamını buraya yapıştırın: pozisyon, aranan beceriler, sorumluluklar…"
          value={jobText}
          maxLength={20000}
          onChange={(e) => setJobText(e.target.value)}
        />
      </label>

      <label className="flex flex-col gap-2">
        <span className="font-medium">CV (isteğe bağlı, PDF)</span>
        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void uploadCv(file);
          }}
        />
        {cvStatus === "uploading" && <span className="text-sm text-neutral-500">CV okunuyor…</span>}
        {cvStatus === "done" && (
          <span className="text-sm text-green-700 dark:text-green-400">
            CV okundu{cv?.skills.length ? `: ${cv.skills.slice(0, 5).join(", ")}…` : "."}
          </span>
        )}
        {cvStatus === "error" && <span className="text-sm text-red-600">{cvError}</span>}
      </label>

      <div className="grid gap-4 sm:grid-cols-3">
        <label className="flex flex-col gap-2">
          <span className="font-medium">Tür</span>
          <select
            className="rounded-md border border-neutral-300 bg-transparent p-2 dark:border-neutral-700"
            value={interviewType}
            onChange={(e) => setInterviewType(e.target.value as InterviewType)}
          >
            {Object.entries(TYPE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-2">
          <span className="font-medium">Dil</span>
          <select
            className="rounded-md border border-neutral-300 bg-transparent p-2 dark:border-neutral-700"
            value={language}
            onChange={(e) => setLanguage(e.target.value as Language)}
          >
            <option value="tr">Türkçe</option>
            <option value="en">English</option>
          </select>
        </label>
        <label className="flex flex-col gap-2">
          <span className="font-medium">Süre</span>
          <select
            className="rounded-md border border-neutral-300 bg-transparent p-2 dark:border-neutral-700"
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
          >
            {DURATIONS.map((d) => (
              <option key={d} value={d}>
                {d} dakika
              </option>
            ))}
          </select>
        </label>
      </div>

      <button
        type="submit"
        disabled={!canStart}
        className="rounded-md bg-neutral-900 px-4 py-3 font-medium text-white disabled:opacity-40 dark:bg-neutral-100 dark:text-neutral-900"
      >
        Mülakatı başlat
      </button>
      {!canStart && jobText.length > 0 && jobText.trim().length < MIN_JOB_CHARS && (
        <p className="text-sm text-neutral-500">İlan metni çok kısa.</p>
      )}
    </form>
  );
}
