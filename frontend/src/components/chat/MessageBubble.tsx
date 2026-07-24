import ReactMarkdown from "react-markdown";
import type { ChatMessage } from "../../types/analyze";
import { ToolCard } from "./ToolCard";
import { cn } from "../../lib/cn";

export function MessageBubble({ msg }: { msg: ChatMessage }) {
  if (msg.kind === "tool") return <ToolCard msg={msg} />;

  const isUser = msg.kind === "user";
  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[80%] rounded-lg px-4 py-2 text-sm",
          isUser
            ? "bg-brand text-white"
            : msg.error
              ? "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300"
              : "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-100",
        )}
      >
        {isUser ? (
          msg.text
        ) : (
          <div className="prose prose-sm max-w-none dark:prose-invert">
            <ReactMarkdown>{msg.text}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
