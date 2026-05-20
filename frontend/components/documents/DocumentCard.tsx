"use client";

import { useState, type MouseEvent } from "react";

import { apiClient } from "@/lib/api-client";
import type { DocumentItem } from "@/features/documents/types";

type Props = {
  document: DocumentItem;
  onDelete?: () => Promise<void>;
};

export function DocumentCard({ document, onDelete }: Props) {
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async (e: MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    if (deleting || !confirm("Xóa tài liệu này?")) return;

    setDeleting(true);
    try {
      await apiClient.delete(`/documents/${encodeURIComponent(document.id)}`);
      if (onDelete) {
        await onDelete();
      }
    } catch (err) {
      console.error("Delete failed", err);
      alert("Không thể xóa tài liệu này");
    } finally {
      setDeleting(false);
    }
  };

  const statusClass =
    document.status === "ready"
      ? ""
      : document.status === "processing"
        ? "warn"
        : "danger";

  return (
    <div className="item-card document-card" style={{ opacity: deleting ? 0.55 : 1 }}>
      <button type="button" className="delete-btn" onClick={handleDelete} disabled={deleting}>
        ×
      </button>

      <div style={{ fontSize: 13, fontWeight: 700, paddingRight: 24 }}>
        {document.title || document.filename}
      </div>

      <div className="status">
        <span className={`status-dot ${statusClass}`} />
        <span>{document.status}</span>
        {document.chunk_count ? <span>· {document.chunk_count} chunks</span> : null}
      </div>
    </div>
  );
}
