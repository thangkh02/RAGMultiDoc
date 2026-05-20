"use client";

import { useState } from "react";

import type { AuthCredentials } from "@/features/auth/types";
import { useAuth } from "./AuthProvider";

type Mode = "login" | "register";

export function AuthModal() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const submit = async () => {
    const payload: AuthCredentials = { name, email, password };
    setBusy(true);
    setError("");
    try {
      if (mode === "login") {
        await login(payload);
      } else {
        await register(payload);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Có lỗi xảy ra");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-overlay">
      <div className="auth-card panel">
        <div className="auth-brand">
          <div className="brand-mark">RAG</div>
          <div>
            <div className="brand">Chatbot Studio</div>
            <div className="muted" style={{ fontSize: 12 }}>Đăng nhập để tiếp tục</div>
          </div>
        </div>

        <div className="auth-tabs">
          <button className={`auth-tab ${mode === "login" ? "active" : ""}`} type="button" onClick={() => setMode("login")}>
            Đăng nhập
          </button>
          <button className={`auth-tab ${mode === "register" ? "active" : ""}`} type="button" onClick={() => setMode("register")}>
            Đăng ký
          </button>
        </div>

        <form className="stack" onSubmit={(e) => {
          e.preventDefault();
          void submit();
        }}>
          {mode === "register" ? (
            <input
              className="input auth-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Tên hiển thị"
            />
          ) : null}
          <input
            className="input auth-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            type="email"
          />
          <input
            className="input auth-input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Mật khẩu"
            type="password"
          />
          {error ? <div className="auth-error">{error}</div> : null}
          <button className="button auth-submit" type="submit" disabled={busy}>
            {busy ? "Đang xử lý..." : mode === "login" ? "Đăng nhập" : "Tạo tài khoản"}
          </button>
        </form>

        <div className="auth-footnote">
          Dữ liệu auth đang lưu cục bộ trên trình duyệt. Nếu bạn muốn auth thật, tôi có thể nối backend sau.
        </div>
      </div>
    </div>
  );
}
