"use client";

import type { SourceItem } from "@/features/chat/types";

type Props = {
  sources: SourceItem[];
};

export function SourceList({ sources }: Props) {
  if (sources.length === 0) {
    return <div className="muted" style={{ padding: "10px 2px", fontSize: "12px" }}>Chưa có nguồn</div>;
  }

  const uniqueSources = sources.filter(
    (source, index, self) => self.findIndex((item) => item.chunk_id === source.chunk_id) === index,
  );

  return (
    <div className="source-list">
      {uniqueSources.map((source) => (
        <div key={source.chunk_id} className="source-card">
          <div className="source-header">
            <h4>{source.filename}</h4>
            {typeof source.score === "number" ? (
              <span className="source-score">{source.score.toFixed(2)}</span>
            ) : null}
          </div>
          <div className="meta" style={{ marginTop: 6 }}>
            {source.section_title || source.procedure_title || "Section"}
            {source.page_number ? ` · p.${source.page_number}` : ""}
          </div>
        </div>
      ))}
    </div>
  );
}
