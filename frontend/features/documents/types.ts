export type DocumentItem = {
  id: string;
  filename: string;
  title: string;
  file_type: string;
  source_type: string;
  owner_user_id?: string | null;
  session_id?: string | null;
  procedure_title?: string | null;
  visibility: string;
  raw_storage_path: string;
  markdown_storage_path?: string | null;
  status: string;
  page_count?: number | null;
  page_source?: string | null;
  chunk_count?: number | null;
  file_size_bytes?: number | null;
  content_hash?: string | null;
  created_at: string;
  updated_at: string;
};

export type DocumentUploadResponse = {
  document_id: string;
  filename: string;
  status: string;
  message: string;
};
