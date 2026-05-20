"use client";

import type { PropsWithChildren } from "react";

import { AuthModal } from "@/components/auth/AuthModal";
import { useAuth } from "@/components/auth/AuthProvider";

export function AppShell({ children }: PropsWithChildren) {
  const { ready, user } = useAuth();

  return (
    <main className="app-frame">
      {children}
      {ready && !user ? <AuthModal /> : null}
    </main>
  );
}
