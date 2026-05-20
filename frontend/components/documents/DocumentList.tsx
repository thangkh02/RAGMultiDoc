"use client";

import type { ReactNode } from "react";

type Props<T> = {
  documents: T[];
  renderItem: (item: T) => ReactNode;
};

export function DocumentList<T>({ documents, renderItem }: Props<T>) {
  if (documents.length === 0) {
    return <div className="muted">Chưa có tài liệu nào.</div>;
  }

  return <div className="stack">{documents.map((item) => renderItem(item))}</div>;
}
