/** Pure evidence for a fresh, single-run Chat acceptance scenario; no I/O. */
import { createHash } from "node:crypto"

const digest = value => createHash("sha256").update(value).digest("hex")

export class ChatSnapshotEvidenceError extends Error {
  constructor(code, evidence = {}) {
    super(code)
    this.code = code
    this.evidence = evidence
  }
}

function requireEvidence(condition, code, evidence) {
  if (!condition) throw new ChatSnapshotEvidenceError(code, evidence)
}

function safeObservation(body, runId) {
  const messages = Array.isArray(body?.messages) ? body.messages : []
  return {
    count: messages.length,
    messages: messages.slice(0, 2).map(m => ({
      role: ["user", "assistant"].includes(m?.role) ? m.role : "invalid",
      status: ["pending", "streaming", "completed", "failed"].includes(m?.status) ? m.status : "invalid",
      valid_id: typeof m?.message_id === "string" && m.message_id.length > 0,
      content_length: typeof m?.content === "string" ? m.content.length : null,
      content_sha256: typeof m?.content === "string" ? digest(m.content) : null,
      run_matches: m?.run_id === runId,
    })),
  }
}

export function terminalChatSnapshot(body, runId) {
  const messages = body?.messages
  const observation = safeObservation(body, runId)
  requireEvidence(Array.isArray(messages) && messages.length === 2, "CHAT_SNAPSHOT_COUNT", observation)
  requireEvidence(messages[0]?.role === "user" && messages[1]?.role === "assistant", "CHAT_SNAPSHOT_ORDER", observation)
  requireEvidence(messages.every(m => typeof m.message_id === "string" && m.message_id.length > 0) &&
    messages[0].message_id !== messages[1].message_id, "CHAT_SNAPSHOT_ID", observation)
  requireEvidence(messages.every(m => m.status === "completed"), "CHAT_SNAPSHOT_STATUS", observation)
  requireEvidence(messages.every(m => typeof m.content === "string" && m.content.length > 0), "CHAT_SNAPSHOT_CONTENT", observation)
  requireEvidence(typeof runId === "string" && runId.length > 0 && messages[1].run_id === runId, "CHAT_SNAPSHOT_RUN", observation)
  requireEvidence(typeof body.event_watermark === "string" && body.event_watermark.length > 0, "CHAT_SNAPSHOT_WATERMARK", observation)
  const frozen = messages.map(m => Object.freeze({
    message_id: m.message_id, role: m.role, status: m.status, content: m.content,
    ...(m.run_id === undefined ? {} : { run_id: m.run_id }),
  }))
  return Object.freeze({
    messages: Object.freeze(frozen),
    event_watermark: body.event_watermark,
    run_id: runId,
    assistant_content_sha256: digest(frozen[1].content),
    user_content_sha256: digest(frozen[0].content),
    message_ids_sha256: digest(JSON.stringify(frozen.map(m => m.message_id))),
  })
}

function safeSnapshot(value) {
  return {
    assistant_content_sha256: value.assistant_content_sha256,
    user_content_sha256: value.user_content_sha256,
    message_ids_sha256: value.message_ids_sha256,
    watermark_sha256: digest(value.event_watermark),
  }
}

export function assertChatSnapshotUnchanged(before, after) {
  const evidence = { before: safeSnapshot(before), after: safeSnapshot(after) }
  for (const [key, code] of [
    ["message_id", "CHAT_SNAPSHOT_ID_CHANGED"],
    ["run_id", "CHAT_SNAPSHOT_RUN_CHANGED"],
    ["role", "CHAT_SNAPSHOT_ORDER_CHANGED"],
    ["status", "CHAT_SNAPSHOT_STATUS_CHANGED"],
    ["content", "CHAT_SNAPSHOT_CONTENT_CHANGED"],
  ]) {
    if (before.messages.some((m, i) => m[key] !== after.messages[i][key])) {
      throw new ChatSnapshotEvidenceError(code, evidence)
    }
  }
  if (before.event_watermark !== after.event_watermark) {
    throw new ChatSnapshotEvidenceError("CHAT_SNAPSHOT_WATERMARK_CHANGED", evidence)
  }
}
