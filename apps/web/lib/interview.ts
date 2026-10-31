// Metin tabanlı mülakat istemci durumu. Protokol: services/api/app/ws.py

export type InterviewType = "technical" | "behavioral" | "mixed";
export type Language = "tr" | "en";
export type EndReason = "completed" | "timeout" | "user_ended";
export type UtteranceKind =
  | "question"
  | "follow_up"
  | "redirect"
  | "candidate_invite"
  | "candidate_answer"
  | "closing";

export interface CVSummary {
  skills: string[];
  projects: { name: string; description: string; technologies: string[] }[];
  experience: string[];
  education: string[];
}

export interface StartPayload {
  type: "start";
  job_text: string;
  cv_summary: CVSummary | null;
  interview_type: InterviewType;
  language: Language;
  duration_min: number;
}

export type ServerMessage =
  | { type: "status"; status: "preparing" }
  | { type: "ready"; total_questions: number; duration_s: number }
  | {
      type: "interviewer";
      text: string;
      kind: UtteranceKind;
      question_index: number | null;
      remaining_s: number;
    }
  | { type: "ended"; reason: EndReason | null }
  | { type: "error"; code: string; message: string };

export interface ChatMessage {
  role: "interviewer" | "candidate";
  text: string;
  kind: UtteranceKind | "answer";
}

export type Phase = "setup" | "connecting" | "preparing" | "running" | "ended" | "error";

export interface InterviewState {
  phase: Phase;
  messages: ChatMessage[];
  totalQuestions: number;
  questionNumber: number; // 1'den başlar; 0 = henüz soru yok
  candidateStage: boolean; // "bize sorunuz var mı" aşaması
  remainingS: number | null;
  awaitingReply: boolean;
  rejectedAnswer: string | null; // sunucunun reddettiği cevap, giriş kutusuna geri konur
  endReason: EndReason | null;
  error: string | null;
}

export type Action =
  | { type: "connect" }
  | { type: "server"; message: ServerMessage }
  | { type: "answer_sent"; text: string }
  | { type: "tick" }
  | { type: "connection_lost" }
  | { type: "reset" };

export const initialState: InterviewState = {
  phase: "setup",
  messages: [],
  totalQuestions: 0,
  questionNumber: 0,
  candidateStage: false,
  remainingS: null,
  awaitingReply: false,
  rejectedAnswer: null,
  endReason: null,
  error: null,
};

// Bağlantıyı sonlandırmayan, kullanıcıya gösterilip devam edilen hatalar.
const RECOVERABLE_ERRORS = new Set(["rate_limited", "invalid_message", "too_large"]);

function onServer(state: InterviewState, msg: ServerMessage): InterviewState {
  switch (msg.type) {
    case "status":
      return { ...state, phase: "preparing" };
    case "ready":
      return {
        ...state,
        phase: "running",
        totalQuestions: msg.total_questions,
        remainingS: msg.duration_s,
      };
    case "interviewer":
      return {
        ...state,
        phase: state.phase === "ended" ? "ended" : "running",
        awaitingReply: false,
        remainingS: msg.remaining_s,
        questionNumber:
          msg.question_index === null ? state.questionNumber : msg.question_index + 1,
        candidateStage: state.candidateStage || msg.kind === "candidate_invite",
        messages: [
          ...state.messages,
          { role: "interviewer", text: msg.text, kind: msg.kind },
        ],
      };
    case "ended":
      return { ...state, phase: "ended", awaitingReply: false, endReason: msg.reason };
    case "error":
      if (RECOVERABLE_ERRORS.has(msg.code)) {
        // Reddedilen cevap işlenmedi: transkriptten çıkarılır, kullanıcı tekrar gönderebilir.
        const last = state.messages.at(-1);
        const rejected = state.awaitingReply && last?.role === "candidate";
        return {
          ...state,
          awaitingReply: false,
          error: msg.message,
          messages: rejected ? state.messages.slice(0, -1) : state.messages,
          rejectedAnswer: rejected ? last.text : null,
        };
      }
      return { ...state, phase: "error", awaitingReply: false, error: msg.message };
  }
}

export function interviewReducer(state: InterviewState, action: Action): InterviewState {
  switch (action.type) {
    case "connect":
      return { ...initialState, phase: "connecting" };
    case "server":
      return onServer(state, action.message);
    case "answer_sent":
      return {
        ...state,
        awaitingReply: true,
        rejectedAnswer: null,
        error: null,
        messages: [...state.messages, { role: "candidate", text: action.text, kind: "answer" }],
      };
    case "tick":
      if (state.phase !== "running" || state.remainingS === null) return state;
      return { ...state, remainingS: Math.max(0, state.remainingS - 1) };
    case "connection_lost":
      if (state.phase === "ended" || state.phase === "error") return state;
      return { ...state, phase: "error", awaitingReply: false, error: "Bağlantı koptu." };
    case "reset":
      return initialState;
  }
}

export function formatRemaining(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}
