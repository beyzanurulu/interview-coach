"use client";

import { useEffect, useRef, useState } from "react";

import { formatRemaining, type InterviewState } from "@/lib/interview";

const END_TEXT = {
  completed: "Mülakat tamamlandı.",
  timeout: "Süre doldu.",
  user_ended: "Mülakatı sonlandırdınız.",
};

export function InterviewChat({
  state,
  onAnswer,
  onEnd,
  onRestart,
}: {
  state: InterviewState;
  onAnswer: (text: string) => void;
  onEnd: () => void;
  onRestart: () => void;
}) {
  const [draft, setDraft] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const running = state.phase === "running";

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [state.messages.length, state.awaitingReply]);

  // Sunucu cevabı reddettiyse metni kaybetmemek için giriş kutusuna geri koy.
  useEffect(() => {
    if (state.rejectedAnswer) setDraft(state.rejectedAnswer);
  }, [state.rejectedAnswer]);

  function submit() {
    const text = draft.trim();
    if (!text || !running || state.awaitingReply) return;
    onAnswer(text);
    setDraft("");
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between text-sm text-neutral-600 dark:text-neutral-400">
        <span>
          {state.totalQuestions > 0
            ? `Soru ${state.questionNumber} / ${state.totalQuestions}`
            : "Hazırlanıyor…"}
        </span>
        <span className="font-mono">
          {state.remainingS !== null ? formatRemaining(state.remainingS) : "--:--"}
        </span>
        {running && (
          <button type="button" onClick={onEnd} className="underline">
            Bitir
          </button>
        )}
      </div>

      <div className="flex flex-col gap-3" aria-live="polite">
        {(state.phase === "connecting" || state.phase === "preparing") && (
          <p className="text-neutral-500">
            {state.phase === "connecting"
              ? "Sunucuya bağlanılıyor… (ilk bağlantı bir dakika sürebilir)"
              : "İlan inceleniyor ve sorular hazırlanıyor…"}
          </p>
        )}
        {state.messages.map((m, i) => (
          <div
            key={i}
            className={
              m.role === "interviewer"
                ? "max-w-[85%] self-start rounded-lg bg-neutral-100 p-3 dark:bg-neutral-800"
                : "max-w-[85%] self-end rounded-lg bg-blue-600 p-3 text-white"
            }
          >
            {m.kind === "follow_up" && (
              <span className="mb-1 block text-xs text-neutral-500 dark:text-neutral-400">
                Takip sorusu
              </span>
            )}
            <p className="whitespace-pre-wrap">{m.text}</p>
          </div>
        ))}
        {state.awaitingReply && <p className="text-sm text-neutral-500">Mülakatçı yazıyor…</p>}
        <div ref={bottomRef} />
      </div>

      {state.error && (
        <p role="alert" className="text-sm text-red-600">
          {state.error}
        </p>
      )}

      {running && (
        <div className="flex flex-col gap-2">
          <textarea
            className="min-h-24 rounded-md border border-neutral-300 bg-transparent p-3 dark:border-neutral-700"
            placeholder="Cevabınızı yazın… (Ctrl+Enter ile gönder)"
            value={draft}
            maxLength={4000}
            disabled={state.awaitingReply}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) submit();
            }}
          />
          <button
            type="button"
            onClick={submit}
            disabled={!draft.trim() || state.awaitingReply}
            className="self-end rounded-md bg-neutral-900 px-4 py-2 font-medium text-white disabled:opacity-40 dark:bg-neutral-100 dark:text-neutral-900"
          >
            Gönder
          </button>
        </div>
      )}

      {(state.phase === "ended" || state.phase === "error") && (
        <div className="flex flex-col gap-2 rounded-md border border-neutral-300 p-4 dark:border-neutral-700">
          <p className="font-medium">
            {state.phase === "ended" && state.endReason ? END_TEXT[state.endReason] : "Mülakat yarıda kaldı."}
          </p>
          <p className="text-sm text-neutral-500">
            Değerlendirme raporu henüz yok; yol haritasında bir sonraki adımlardan biri.
          </p>
          <button type="button" onClick={onRestart} className="self-start underline">
            Yeni mülakat
          </button>
        </div>
      )}
    </div>
  );
}
