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

export function assertCompletedMessagePrefixUnchanged(before, after) {
  requireEvidence(Array.isArray(before) && before.length > 0 && Array.isArray(after) &&
    after.length >= before.length, "CHAT_SNAPSHOT_COUNT")
  const keys = ["message_id", "run_id", "role", "status", "content"]
  requireEvidence(before.every((message, index) => message.status === "completed" &&
    keys.every(key => message[key] === after[index]?.[key])), "CHAT_SNAPSHOT_CONTENT_CHANGED")
}

export function uniqueRunFrames(frames, runId) {
  requireEvidence(Array.isArray(frames) && frames.length <= 10000 &&
    typeof runId === "string" && /^[A-Za-z0-9_.:-]{1,191}$/u.test(runId), "CHAT_STREAM_BOUND")
  const unique = new Map()
  let bytes = 0
  for (const frame of frames) {
    requireEvidence(typeof frame?.id === "string" && frame.id.trim().length > 0 &&
      frame.id.length <= 4096 && frame.event !== null && typeof frame.event === "object" &&
      !Array.isArray(frame.event), "CHAT_STREAM_FRAME")
    const wire = JSON.stringify(frame.event)
    bytes += Buffer.byteLength(wire)
    requireEvidence(bytes <= 33554432, "CHAT_STREAM_BOUND")
    const previous = unique.get(frame.id)
    requireEvidence(previous === undefined || previous.wire === wire, "CHAT_STREAM_CURSOR_CONFLICT")
    if (previous === undefined) unique.set(frame.id, { frame, wire })
  }
  return [...unique.values()].map(value => value.frame).filter(frame =>
    (frame.event.runId ?? frame.event.metadata?.kokoro?.run_id) === runId)
}

function frameText(frames) {
  const deltas = frames.filter(frame => frame.event.type === "TEXT_MESSAGE_CONTENT")
    .map(frame => frame.event.delta)
  requireEvidence(deltas.every(delta => typeof delta === "string"), "CHAT_STREAM_TEXT")
  const content = deltas.join("")
  requireEvidence(Buffer.byteLength(content) <= 8388608, "CHAT_STREAM_BOUND")
  return content
}

export function runTextEvidence(frames, runId) {
  const unique = uniqueRunFrames(frames, runId)
  const count = type => unique.filter(frame => frame.event.type === type).length
  const startCount = count("RUN_STARTED"), finishCount = count("RUN_FINISHED"), errorCount = count("RUN_ERROR")
  requireEvidence(startCount === 1 && finishCount === 1 && errorCount === 0, "CHAT_STREAM_TERMINAL")
  const startIndex = unique.findIndex(frame => frame.event.type === "RUN_STARTED")
  const finishIndex = unique.findIndex(frame => frame.event.type === "RUN_FINISHED")
  requireEvidence(startIndex < finishIndex && unique.every((frame, index) =>
    !["TEXT_MESSAGE_START", "TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_END"].includes(frame.event.type) || (index > startIndex && index < finishIndex)), "CHAT_STREAM_ORDER")
  const content = frameText(unique)
  requireEvidence(content.length > 0, "CHAT_STREAM_TEXT")
  return { content, sha256: digest(content), start_count: startCount, finish_count: finishCount, error_count: errorCount }
}

export function hydratedRunText(hydration, tailFrames, receipt, lastEventId) {
  requireEvidence(typeof hydration?.event_watermark === "string" &&
    hydration.event_watermark.trim().length > 0 && hydration.event_watermark.length <= 4096 &&
    hydration.event_watermark === lastEventId, "CHAT_REPLAY_WATERMARK")
  requireEvidence(hydration.execution_head?.run_id === receipt?.run_id &&
    hydration.execution_head.state === "active" && Array.isArray(hydration.messages), "CHAT_REPLAY_ACTIVE")
  const messages = hydration.messages.filter(message => message.message_id === receipt.assistant_message_id)
  requireEvidence(messages.length === 1 && messages[0].run_id === receipt.run_id &&
    messages[0].role === "assistant" && messages[0].status === "streaming" &&
    typeof messages[0].content === "string" && messages[0].content.length > 0, "CHAT_REPLAY_PARTIAL")
  const unique = uniqueRunFrames(tailFrames, receipt.run_id)
  requireEvidence(!unique.some(frame => frame.id === lastEventId), "CHAT_REPLAY_INCLUSIVE_CURSOR")
  requireEvidence(unique.filter(frame => frame.event.type === "RUN_FINISHED").length === 1 &&
    !unique.some(frame => frame.event.type === "RUN_ERROR"), "CHAT_REPLAY_TERMINAL")
  const finishIndex = unique.findIndex(frame => frame.event.type === "RUN_FINISHED")
  requireEvidence(unique.every((frame, index) => frame.event.type !== "RUN_STARTED" &&
    (!["TEXT_MESSAGE_START", "TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_END"].includes(frame.event.type) || index < finishIndex)), "CHAT_STREAM_ORDER")
  const content = messages[0].content + frameText(unique)
  requireEvidence(Buffer.byteLength(content) <= 8388608, "CHAT_STREAM_BOUND")
  return { content, sha256: digest(content) }
}


// This fixture admits plain Markdown paragraphs only: no escaped syntax, inline
// markup, lists or HTML. Markdown strips outer whitespace and separates plain
// paragraphs by one newline; user bodies retain their exact literal text.
export function renderedChatEvidence(rows, messages, allowedAnchors = []) {
  requireEvidence(Array.isArray(rows) && Array.isArray(messages) && rows.length === messages.length &&
    messages.length > 0 && messages.length <= 4, "CHAT_RENDER_COUNT")
  const rendered = rows.map((row, index) => {
    const message = messages[index]
    const anchor = message.role === "user" ? message.message_id : `assistant:${message.run_id}:message:${message.message_id}`
    const allowed = allowedAnchors[index] ?? [anchor]
    requireEvidence(Array.isArray(allowed) && allowed.length > 0 && allowed.length <= 1000 &&
      allowed.every(value => typeof value === "string" && value.length <= 1024) && allowed.includes(row?.anchor) && row.role === message.role &&
      (message.role === "user" ? row.anchor === anchor : row.anchor.startsWith(`assistant:${message.run_id}:message:`)), "CHAT_RENDER_IDENTITY")
    requireEvidence(row.visible === true && row.plain === true && typeof row.body === "string", "CHAT_RENDER_PRESENTATION")
    requireEvidence(typeof message.content === "string" && Buffer.byteLength(message.content) <= 8388608, "CHAT_RENDER_BOUND")
    let expected = message.content
    if (message.role === "assistant") {
      expected = expected.trim()
      requireEvidence(/^[A-Za-z][A-Za-z0-9_ .,:/()!?\n-]*$/u.test(expected) &&
        expected.split("\n").every(line => !/^[-]|^\d+[.)] /u.test(line.trim())) && !/  \n/u.test(expected), "CHAT_RENDER_FIXTURE")
      expected = expected.replace(/\n[ \t]*\n+/gu, "\n")
    }
    requireEvidence(row.body === expected, "CHAT_RENDER_CONTENT")
    // Live UI uses native text segment IDs; reload uses the owner Message ID.
    // Normalize only after binding that actual anchor to this Run's real frames.
    return Object.freeze({anchor, role:message.role, body:row.body})
  })
  return Object.freeze(rendered)
}

export function assertRenderedChatUnchanged(before, after) {
  requireEvidence(JSON.stringify(before) === JSON.stringify(after), "CHAT_RENDER_CHANGED")
}
