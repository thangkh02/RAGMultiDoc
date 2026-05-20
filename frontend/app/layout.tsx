import "./globals.css";
import type { ReactNode } from "react";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { AppShell } from "@/components/layout/AppShell";

export const metadata = {
  title: "RAG Chatbot",
  description: "Giao diện chat RAG tối giản cho tài liệu hệ thống và tài liệu người dùng tải lên.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="vi">
      <body>
        <AuthProvider>
          <AppShell>{children}</AppShell>
        </AuthProvider>
      </body>
    </html>
  );
}
