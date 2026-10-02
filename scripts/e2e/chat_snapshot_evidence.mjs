/** Pure evidence for completed Chat turns bound to ordered POST receipts; no I/O. */
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

function safeObservation(body, orderedReceipts) {
  const messages = Array.isArray(body?.messages) ? body.messages : []
  return {
    count: messages.length,
    messages: Array.from(messages, (m, index) => ({
      role: ["user", "assistant"].includes(m?.role) ? m.role : "invalid",
      status: ["pending", "streaming", "completed", "failed"].includes(m?.status) ? m.status : "invalid",
      valid_id: typeof m?.message_id === "string" && m.message_id.length > 0,
      content_length: typeof m?.content === "string" ? m.content.length : null,
      content_sha256: typeof m?.content === "string" ? digest(m.content) : null,
      run_matches: Array.isArray(orderedReceipts) &&
        m?.run_id === orderedReceipts[Math.floor(index / 2)]?.run_id,
    })),
  }
}

export function terminalChatSnapshot(body, orderedReceipts) {
  const messages = body?.messages
  const observation = safeObservation(body, orderedReceipts)
  const receiptKeys = ["run_id", "user_message_id", "assistant_message_id"]
  requireEvidence(Array.isArray(orderedReceipts) && orderedReceipts.length > 0 &&
    Array.from(orderedReceipts).every(receipt => receipt !== null &&
      typeof receipt === "object" && !Array.isArray(receipt) &&
      Object.keys(receipt).length === receiptKeys.length &&
      receiptKeys.every(key => Object.hasOwn(receipt, key) &&
        typeof receipt[key] === "string" && receipt[key].length > 0)),
    "CHAT_SNAPSHOT_RECEIPT", observation)
  requireEvidence(new Set(orderedReceipts.map(receipt => receipt.run_id)).size === orderedReceipts.length,
    "CHAT_SNAPSHOT_RUN", observation)
  const expectedIds = orderedReceipts.flatMap(receipt => [receipt.user_message_id, receipt.assistant_message_id])
  requireEvidence(new Set(expectedIds).size === expectedIds.length, "CHAT_SNAPSHOT_ID", observation)
  requireEvidence(Array.isArray(messages) && messages.length === expectedIds.length, "CHAT_SNAPSHOT_COUNT", observation)
  requireEvidence(Array.from(messages).every((m, index) => m?.role === (index % 2 === 0 ? "user" : "assistant")),
    "CHAT_SNAPSHOT_ORDER", observation)
  requireEvidence(messages.every((m, index) => typeof m.message_id === "string" &&
    m.message_id === expectedIds[index]) &&
    new Set(messages.map(m => m.message_id)).size === messages.length, "CHAT_SNAPSHOT_ID", observation)
  requireEvidence(messages.every(m => m.status === "completed"), "CHAT_SNAPSHOT_STATUS", observation)
  requireEvidence(messages.every(m => typeof m.content === "string" && m.content.length > 0), "CHAT_SNAPSHOT_CONTENT", observation)
  requireEvidence(messages.every((m, index) => (index % 2 === 0 && m.run_id === undefined) ||
    m.run_id === orderedReceipts[Math.floor(index / 2)].run_id), "CHAT_SNAPSHOT_RUN", observation)
  requireEvidence(typeof body.event_watermark === "string" && body.event_watermark.length > 0, "CHAT_SNAPSHOT_WATERMARK", observation)
  const frozen = messages.map(m => Object.freeze({
    message_id: m.message_id, role: m.role, status: m.status, content: m.content,
    ...(m.run_id === undefined ? {} : { run_id: m.run_id }),
  }))
  return Object.freeze({
    messages: Object.freeze(frozen),
    event_watermark: body.event_watermark,
    run_id: orderedReceipts.at(-1).run_id,
    assistant_content_sha256: digest(frozen.at(-1).content),
    user_content_sha256: digest(frozen.at(-2).content),
    message_ids_sha256: digest(JSON.stringify(frozen.map(m => m.message_id))),
    message_contents_sha256: digest(JSON.stringify(frozen.map(m => m.content))),
  })
}

function safeSnapshot(value) {
  return {
    assistant_content_sha256: value.assistant_content_sha256,
    user_content_sha256: value.user_content_sha256,
    message_ids_sha256: value.message_ids_sha256,
    message_contents_sha256: value.message_contents_sha256,
    watermark_sha256: digest(value.event_watermark),
  }
}

export function assertChatSnapshotUnchanged(before, after) {
  const evidence = { before: safeSnapshot(before), after: safeSnapshot(after) }
  requireEvidence(Array.isArray(before.messages) && Array.isArray(after.messages) &&
    before.messages.length === after.messages.length, "CHAT_SNAPSHOT_COUNT", evidence)
  for (const [key, code] of [
    ["message_id", "CHAT_SNAPSHOT_ID_CHANGED"],
    ["run_id", "CHAT_SNAPSHOT_RUN_CHANGED"],
    ["role", "CHAT_SNAPSHOT_ORDER_CHANGED"],
    ["status", "CHAT_SNAPSHOT_STATUS_CHANGED"],
    ["content", "CHAT_SNAPSHOT_CONTENT_CHANGED"],
  ]) {
    if (before.messages.some((m, i) => m[key] !== after.messages[i]?.[key])) {
      throw new ChatSnapshotEvidenceError(code, evidence)
    }
  }
  if (before.event_watermark !== after.event_watermark) {
    throw new ChatSnapshotEvidenceError("CHAT_SNAPSHOT_WATERMARK_CHANGED", evidence)
  }
}
