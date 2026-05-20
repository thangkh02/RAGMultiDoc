import Link from "next/link";

export default function HomePage() {
  return (
    <main className="workspace">
      <section className="panel stack" style={{ padding: "28px" }}>
        <div>
          <div className="eyebrow">RAG CHATBOT</div>
          <h1 className="hero-title">Tìm câu trả lời từ tài liệu</h1>
          <p className="hero-copy">
           
          </p>
        </div>

        <div className="toolbar">
          <Link href="/chat" className="button">
            Vào chat
          </Link>
          <Link href="/documents" className="button secondary">
            Quản lý tài liệu
          </Link>
        </div>
      </section>

      <section className="grid" style={{ gridTemplateColumns: "repeat(3, minmax(0, 1fr))" }}>
        {[
          {
            title: "Chat tập trung",
            text: "Tối ưu cho trao đổi ngắn, rõ và có trích dẫn.",
          },
          {
            title: "RAG scope",
            text: "Chọn nguồn hệ thống, tài liệu cá nhân hoặc chế độ tự động.",
          },
          {
            title: "Upload nhanh",
            text: "Kéo thả PDF, DOC, DOCX và dùng ngay trong luồng chat.",
          },
        ].map((item) => (
          <article key={item.title} className="panel stack" style={{ minHeight: "150px" }}>
            <h2 style={{ fontFamily: "var(--font-display)", fontSize: "16px", fontWeight: 800 }}>
              {item.title}
            </h2>
            <p className="hero-copy" style={{ marginTop: 0 }}>
              {item.text}
            </p>
          </article>
        ))}
      </section>
    </main>
  );
}
