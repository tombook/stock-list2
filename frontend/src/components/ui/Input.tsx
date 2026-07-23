import { type InputHTMLAttributes, forwardRef } from "react";
import { cn } from "../../lib/cn";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  function Input({ className, ...rest }, ref) {
    return (
      <input
        ref={ref}
        className={cn(
          "rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm",
          "focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand",
          "dark:border-slate-700 dark:bg-slate-900",
          className,
        )}
        {...rest}
      />
    );
  },
);
