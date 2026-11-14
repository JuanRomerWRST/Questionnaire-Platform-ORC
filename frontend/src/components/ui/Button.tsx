import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost";
};

export function Button({ variant = "primary", className, ...props }: Props) {
  return (
    <button
      className={cn(
        "inline-flex min-h-11 items-center justify-center rounded-full px-5 text-sm font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary" && "bg-[var(--accent)] text-white hover:bg-[var(--accent-strong)]",
        variant === "ghost" && "border border-[var(--line)] bg-white text-[var(--ink)] hover:bg-[var(--paper-2)]",
        className,
      )}
      {...props}
    />
  );
}
