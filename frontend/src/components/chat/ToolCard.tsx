import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import type { ToolMessage } from "../../types/analyze";
import { Card } from "../ui/Card";
import { cn } from "../../lib/cn";

const RESULT_PREVIEW = 200;

export function ToolCard({ msg }: { msg: ToolMessage }) {
  const [open, setOpen] = useState(false);
  const resultJson = msg.result !== undefined ? JSON.stringify(msg.result, null, 2) : "";
  const long = resultJson.length > RESULT_PREVIEW;
  const body = open || !long ? resultJson : resultJson.slice(0, RESULT_PREVIEW) + "…";

  return (
    <Card className="space-y-2 text-sm">
      <div className="flex items-center gap-2">
        <span
          className={cn(
            "rounded px-1.5 py-0.5 text-xs font-mono",
            msg.ok === false
              ? "bg-red-100 text-red-700"
              : msg.ok === true
                ? "bg-emerald-100 text-emerald-700"
                : "bg-slate-100 text-slate-600",
          )}
        >
          {msg.name}
        </span>
        <span className="text-xs text-slate-400">tool</span>
      </div>
      <pre className="overflow-auto rounded bg-slate-50 p-2 text-xs dark:bg-slate-800">
        {JSON.stringify(msg.args, null, 2)}
      </pre>
      {resultJson && (
        <div>
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700"
          >
            {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
            result
          </button>
          <pre className="mt-1 overflow-auto rounded bg-slate-50 p-2 text-xs dark:bg-slate-800">
            {body}
          </pre>
        </div>
      )}
    </Card>
  );
}
