import { describe, expect, it } from "vitest";

import {
  formatRemaining,
  initialState,
  interviewReducer,
  type Action,
  type InterviewState,
} from "@/lib/interview";

function run(actions: Action[], state: InterviewState = initialState): InterviewState {
  return actions.reduce(interviewReducer, state);
}

const started: Action[] = [
  { type: "connect" },
  { type: "server", message: { type: "status", status: "preparing" } },
  { type: "server", message: { type: "ready", total_questions: 5, duration_s: 600 } },
  {
    type: "server",
    message: {
      type: "interviewer",
      text: "Merhaba! Soru 1?",
      kind: "question",
      question_index: 0,
      remaining_s: 598,
    },
  },
];

describe("interviewReducer", () => {
  it("moves through connect → preparing → running", () => {
    const state = run(started);
    expect(state.phase).toBe("running");
    expect(state.totalQuestions).toBe(5);
    expect(state.questionNumber).toBe(1);
    expect(state.remainingS).toBe(598);
    expect(state.messages).toHaveLength(1);
  });

  it("marks follow-ups and keeps the question number", () => {
    const state = run([
      ...started,
      { type: "answer_sent", text: "kısa" },
      {
        type: "server",
        message: {
          type: "interviewer",
          text: "Örnek?",
          kind: "follow_up",
          question_index: null,
          remaining_s: 550,
        },
      },
    ]);
    expect(state.questionNumber).toBe(1);
    expect(state.messages.at(-1)).toEqual({ role: "interviewer", text: "Örnek?", kind: "follow_up" });
    expect(state.awaitingReply).toBe(false);
  });

  it("waits for reply after sending an answer", () => {
    const state = run([...started, { type: "answer_sent", text: "cevap" }]);
    expect(state.awaitingReply).toBe(true);
    expect(state.messages.at(-1)?.role).toBe("candidate");
  });

  it("ends with reason and ignores connection loss afterwards", () => {
    const state = run([
      ...started,
      { type: "server", message: { type: "ended", reason: "timeout" } },
      { type: "connection_lost" },
    ]);
    expect(state.phase).toBe("ended");
    expect(state.endReason).toBe("timeout");
  });

  it("keeps running on recoverable errors but stops on fatal ones", () => {
    const soft = run([
      ...started,
      { type: "server", message: { type: "error", code: "rate_limited", message: "yavaş" } },
    ]);
    expect(soft.phase).toBe("running");
    expect(soft.error).toBe("yavaş");

    const hard = run([
      { type: "connect" },
      { type: "server", message: { type: "error", code: "llm_unavailable", message: "yok" } },
    ]);
    expect(hard.phase).toBe("error");
  });

  it("removes a rejected answer from the transcript and keeps its text", () => {
    const state = run([
      ...started,
      { type: "answer_sent", text: "çok hızlı cevap" },
      { type: "server", message: { type: "error", code: "rate_limited", message: "yavaş" } },
    ]);
    expect(state.messages.at(-1)?.role).toBe("interviewer");
    expect(state.rejectedAnswer).toBe("çok hızlı cevap");
    expect(state.awaitingReply).toBe(false);
  });

  it("ticks the countdown only while running", () => {
    expect(run([...started, { type: "tick" }]).remainingS).toBe(597);
    expect(run([{ type: "tick" }]).remainingS).toBeNull();
  });
});

describe("formatRemaining", () => {
  it("formats minutes and seconds", () => {
    expect(formatRemaining(605)).toBe("10:05");
    expect(formatRemaining(9)).toBe("0:09");
  });
});
