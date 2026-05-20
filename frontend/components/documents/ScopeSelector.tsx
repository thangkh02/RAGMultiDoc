"use client";

import { retrievalScopes, RetrievalScope } from "@/lib/constants";

type Props = {
  value: RetrievalScope;
  onChange: (value: RetrievalScope) => void;
};

const labels: Record<RetrievalScope, string> = {
  auto: "Auto",
  current_upload: "Current",
  all_user_uploads: "My uploads",
  system_docs: "System",
  mixed: "Mixed",
};

export function ScopeSelector({ value, onChange }: Props) {
  return (
    <div className="field">
      <label>Retrieval scope</label>
      <select className="select" value={value} onChange={(event) => onChange(event.target.value as RetrievalScope)}>
        {retrievalScopes.map((scope) => (
          <option key={scope} value={scope}>
            {labels[scope]}
          </option>
        ))}
      </select>
    </div>
  );
}
