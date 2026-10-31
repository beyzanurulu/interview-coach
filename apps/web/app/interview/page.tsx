"use client";

import { useCallback, useEffect, useReducer, useRef } from "react";

import { InterviewChat } from "@/components/InterviewChat";
import { SetupForm } from "@/components/SetupForm";
import { getWsUrl } from "@/lib/config";
import {
  initialState,
  interviewReducer,
  type ServerMessage,
  type StartPayload,
} from "@/lib/interview";

export default function InterviewPage() {
  const [state, dispatch] = useReducer(interviewReducer, initialState);
  const wsRef = useRef<WebSocket | null>(null);

  const start = useCallback((payload: StartPayload) => {
    dispatch({ type: "connect" });
    const ws = new WebSocket(getWsUrl("/ws/interview"));
    wsRef.current = ws;
    ws.onopen = () => ws.send(JSON.stringify(payload));
    ws.onmessage = (event) => {
      dispatch({ type: "server", message: JSON.parse(event.data) as ServerMessage });
    };
    ws.onclose = () => dispatch({ type: "connection_lost" });
  }, []);

  const send = useCallback((message: object) => {
    wsRef.current?.send(JSON.stringify(message));
  }, []);

  // Sayaç sadece gösterim içindir; süreyi sunucu uygular.
  useEffect(() => {
    if (state.phase !== "running") return;
    const id = setInterval(() => dispatch({ type: "tick" }), 1000);
    return () => clearInterval(id);
  }, [state.phase]);

  useEffect(() => () => wsRef.current?.close(), []);

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-4 py-10">
      <h1 className="text-2xl font-semibold">Mülakat (metin)</h1>
      {state.phase === "setup" ? (
        <SetupForm onStart={start} />
      ) : (
        <InterviewChat
          state={state}
          onAnswer={(text) => {
            dispatch({ type: "answer_sent", text });
            send({ type: "answer", text });
          }}
          onEnd={() => send({ type: "end" })}
          onRestart={() => {
            wsRef.current?.close();
            wsRef.current = null;
            dispatch({ type: "reset" });
          }}
        />
      )}
    </main>
  );
}
