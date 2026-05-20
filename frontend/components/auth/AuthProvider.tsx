"use client";

import { createContext, useContext, useEffect, useMemo, useState, type PropsWithChildren } from "react";

import type { AuthCredentials, AuthUser } from "@/features/auth/types";

type StoredUser = AuthUser & { password: string };

type AuthContextValue = {
  user: AuthUser | null;
  ready: boolean;
  login: (credentials: AuthCredentials) => Promise<void>;
  register: (credentials: AuthCredentials) => Promise<void>;
  logout: () => void;
};

const USERS_KEY = "rag_chatbot_users";
const CURRENT_KEY = "rag_chatbot_current_user";

const AuthContext = createContext<AuthContextValue | null>(null);

function readUsers(): StoredUser[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(USERS_KEY);
    return raw ? (JSON.parse(raw) as StoredUser[]) : [];
  } catch {
    return [];
  }
}

function readCurrentUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(CURRENT_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

function persistUsers(users: StoredUser[]) {
  window.localStorage.setItem(USERS_KEY, JSON.stringify(users));
}

function persistCurrentUser(user: AuthUser | null) {
  if (user) {
    window.localStorage.setItem(CURRENT_KEY, JSON.stringify(user));
  } else {
    window.localStorage.removeItem(CURRENT_KEY);
  }
}

function toUser(input: StoredUser): AuthUser {
  return {
    id: input.id,
    name: input.name,
    email: input.email,
  };
}

function userIdFromEmail(email: string) {
  return `user_${email.trim().toLowerCase().replace(/[^a-z0-9]+/g, "_")}`;
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setUser(readCurrentUser());
    setReady(true);
  }, []);

  const value = useMemo<AuthContextValue>(() => {
    const login = async ({ email, password }: AuthCredentials) => {
      const users = readUsers();
      const found = users.find((item) => item.email.toLowerCase() === email.trim().toLowerCase());
      if (!found || found.password !== password) {
        throw new Error("Email hoặc mật khẩu không đúng");
      }
      const nextUser = toUser(found);
      setUser(nextUser);
      persistCurrentUser(nextUser);
    };

    const register = async ({ name, email, password }: AuthCredentials) => {
      const normalizedEmail = email.trim().toLowerCase();
      const normalizedName = (name || "").trim();
      if (!normalizedName) {
        throw new Error("Vui lòng nhập tên");
      }
      if (!normalizedEmail || !password) {
        throw new Error("Thiếu email hoặc mật khẩu");
      }
      const users = readUsers();
      if (users.some((item) => item.email.toLowerCase() === normalizedEmail)) {
        throw new Error("Email này đã được sử dụng");
      }
      const created: StoredUser = {
        id: userIdFromEmail(normalizedEmail),
        name: normalizedName,
        email: normalizedEmail,
        password,
      };
      persistUsers([...users, created]);
      const nextUser = toUser(created);
      setUser(nextUser);
      persistCurrentUser(nextUser);
    };

    const logout = () => {
      setUser(null);
      persistCurrentUser(null);
    };

    return { user, ready, login, register, logout };
  }, [ready, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
