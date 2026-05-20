"use client";

import { useEffect, useRef } from "react";

import type { ChatMessage } from "@/features/chat/types";
import { MessageBubble } from "./MessageBubble";

type Props = {
  messages: ChatMessage[];
  loading: boolean;
};

export function ChatWindow({ messages, loading }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <div className="chat-thread scroll-area">
      {messages.length === 0 ? (
        <div className="chat-empty">
          <div>
            <h2>Bắt đầu cuộc trò chuyện</h2>
            <div>Hỏi về tài liệu hệ thống hoặc file bạn đã tải lên.</div>
          </div>
        </div>
      ) : null}

      {messages.map((message, index) => (
        <MessageBubble key={index} message={message} />
      ))}

      {loading ? (
        <div style={{ alignSelf: "flex-start" }}>
          <div className="dots-loader">
            <span />
            <span />
            <span />
            <span style={{ marginLeft: 2 }}>Đang trả lời</span>
          </div>
        </div>
      ) : null}

      <div ref={bottomRef} style={{ height: 1 }} />
    </div>
  );
}
