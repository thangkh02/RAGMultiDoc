"use client";

import type { ChatMessage } from "@/features/chat/types";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`message ${isUser ? "user" : "assistant"}`}>
      <div className="message-head">
        <span>{isUser ? "Bạn" : "Trợ lý"}</span>
        {!isUser && message.sources?.length ? <span>{message.sources.length} nguồn</span> : null}
      </div>

      <div className="message-content">{message.content}</div>

      {!isUser && message.sources?.length ? (
        <div className="message-sources">
          {message.sources.slice(0, 3).map((source, index) => (
            <div key={`${source.chunk_id}-${index}`} className="source-pill">
              <strong>{source.filename}</strong>
              {source.page_number ? <div className="meta">Trang {source.page_number}</div> : null}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
