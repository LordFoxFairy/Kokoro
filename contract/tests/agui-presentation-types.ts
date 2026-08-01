import { EventType, type AGUIEvent } from "@ag-ui/core";

// Compile-time proof that Kokoro's closed presentation subset remains a valid
// subset of the exact official SDK types pinned by the contract package.
const presentationEvents = [
  {
    type: EventType.RUN_STARTED,
    timestamp: 1,
    threadId: "thread.1",
    runId: "run.1",
  },
  {
    type: EventType.RUN_FINISHED,
    timestamp: 2,
    threadId: "thread.1",
    runId: "run.1",
  },
  {
    type: EventType.RUN_ERROR,
    timestamp: 3,
    message: "The run failed.",
    code: "RUN_FAILED",
  },
  {
    type: EventType.TEXT_MESSAGE_START,
    timestamp: 4,
    messageId: "message.1",
    role: "assistant",
  },
  {
    type: EventType.TEXT_MESSAGE_CONTENT,
    timestamp: 5,
    messageId: "message.1",
    delta: "Hello",
  },
  {
    type: EventType.TEXT_MESSAGE_END,
    timestamp: 6,
    messageId: "message.1",
  },
  {
    type: EventType.ACTIVITY_SNAPSHOT,
    timestamp: 7,
    messageId: "message.1",
    activityType: "kokoro.safe-summary.v1",
    content: { partRef: "part.1", summary: "Safe", status: "complete" },
    replace: true,
  },
  {
    type: EventType.CUSTOM,
    timestamp: 8,
    name: "kokoro.session.replace.v1",
    value: { sessionId: "session.1", profileRevision: "kokoro-agui-presentation.v1" },
  },
] satisfies readonly AGUIEvent[];

void presentationEvents;

// Agent candidate RUN_FINISHED is intentionally narrower than the browser
// presentation variant: upstream success outcome is required at Agent ingress
// and Session strips it only after validation and binding projection.
const agentRunFinishedCandidate = {
  type: EventType.RUN_FINISHED,
  timestamp: 9,
  threadId: "internal.thread.1",
  runId: "internal.run.1",
  outcome: { type: "success" },
} satisfies AGUIEvent;

void agentRunFinishedCandidate;
