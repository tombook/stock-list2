import { type ButtonHTMLAttributes, forwardRef } from "react";
import { cn } from "../../lib/cn";

type Variant = "primary" | "ghost";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

export const Button = forwardRef<HTMLButtonElement, Props>(function Button(
  { variant = "primary", className, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      className={cn(
        "rounded-md px-3 py-1.5 text-sm font-medium transition disabled:opacity-50",
        variant === "primary"
          ? "bg-brand text-white hover:bg-brand-dark"
          : "hover:bg-slate-100 dark:hover:bg-slate-800",
        className,
      )}
      {...rest}
    />
  );
});
