"use client";

import type { SessionItem } from "@/features/chat/types";

type Props = {
  sessions: SessionItem[];
  activeSessionId: string | null;
  onSelect: (session: SessionItem) => void;
};

export function SessionList({ sessions, activeSessionId, onSelect }: Props) {
  if (sessions.length === 0) {
    return <div className="muted" style={{ padding: "10px 2px", fontSize: "12px" }}>Chưa có phiên chat</div>;
  }

  return (
    <div className="session-list">
      {sessions.map((session) => {
        const active = session.id === activeSessionId;
        return (
          <button
            key={session.id}
            type="button"
            className={`item-card ${active ? "active" : ""}`}
            onClick={() => onSelect(session)}
          >
            <div className="session-title">{session.title || "Phiên chưa đặt tên"}</div>
            {session.last_message_at ? (
              <div className="meta" style={{ marginTop: 4 }}>
                Cập nhật gần nhất
              </div>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
