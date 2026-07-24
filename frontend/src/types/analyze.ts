/** Discriminated union of chat messages the Analyze page renders. */
export interface UserMessage {
  kind: "user";
  id: string;
  text: string;
}

export interface AssistantMessage {
  kind: "assistant";
  id: string;
  text: string;
  error?: boolean;
}

export interface ToolMessage {
  kind: "tool";
  id: string; // tool_call id; tool_result updates the same card
  name: string;
  args: unknown;
  result?: unknown;
  ok?: boolean;
}

export type ChatMessage = UserMessage | AssistantMessage | ToolMessage;

/** Handlers dispatched by the SSE parser. All optional. */
export interface AnalyzeEventHandlers {
  onStep?(index: number): void;
  onToolCall?(id: string, name: string, args: unknown): void;
  onToolResult?(id: string, name: string, ok: boolean, result: unknown): void;
  onFinal?(answer: string): void;
  onError?(message: string): void;
  onDone?(): void;
}
