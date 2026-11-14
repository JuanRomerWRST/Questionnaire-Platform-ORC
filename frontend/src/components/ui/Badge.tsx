import { cn } from "@/lib/utils";

export function Badge({ children, tone = "neutral" }: { children: string; tone?: "neutral" | "good" | "warn" }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium",
        tone === "neutral" && "bg-[var(--paper-2)] text-[var(--ink-soft)]",
        tone === "good" && "bg-[#e5f3f1] text-[#0c4f4c]",
        tone === "warn" && "bg-[#f8edd9] text-[#6d4710]",
      )}
    >
      {children}
    </span>
  );
}
