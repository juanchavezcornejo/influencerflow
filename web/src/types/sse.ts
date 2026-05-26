// SSE event payloads emitted by /api/v1/events/session/{id}
// Keep in sync with backend task emitters.

export type SseEventKind =
  | "sync.started"
  | "sync.progress"
  | "sync.completed"
  | "sync.failed"
  | "group.created"
  | "group.updated"
  | "asset.ready"
  | "edit.started"
  | "edit.completed"
  | "edit.failed"
  | "face.blended"
  | "export.started"
  | "export.progress"
  | "export.completed"
  | "export.failed";

interface SseBase {
  kind: SseEventKind;
  sessionId: string;
  ts: string;
}

export interface SyncProgressEvent extends SseBase {
  kind: "sync.progress";
  current: number;
  total: number;
  filename: string;
}

export interface SyncCompletedEvent extends SseBase {
  kind: "sync.completed";
  assetCount: number;
  groupCount: number;
}

export interface SyncFailedEvent extends SseBase {
  kind: "sync.failed";
  error: string;
}

export interface AssetReadyEvent extends SseBase {
  kind: "asset.ready";
  assetId: string;
  thumbnailUrl: string;
}

export interface EditCompletedEvent extends SseBase {
  kind: "edit.completed";
  assetId: string;
  editVersionId: string;
  previewUrl: string;
}

export interface EditFailedEvent extends SseBase {
  kind: "edit.failed";
  assetId: string;
  error: string;
}

export interface FaceBlendedEvent extends SseBase {
  kind: "face.blended";
  assetId: string;
  faceCropId: string;
  blendedOutputUrl: string;
}

export interface ExportProgressEvent extends SseBase {
  kind: "export.progress";
  groupId: string;
  current: number;
  total: number;
}

export interface ExportCompletedEvent extends SseBase {
  kind: "export.completed";
  groupId: string;
  downloadUrl: string;
}

export type SseEvent =
  | SyncProgressEvent
  | SyncCompletedEvent
  | SyncFailedEvent
  | AssetReadyEvent
  | EditCompletedEvent
  | EditFailedEvent
  | FaceBlendedEvent
  | ExportProgressEvent
  | ExportCompletedEvent
  | (SseBase & { kind: SseEventKind });
