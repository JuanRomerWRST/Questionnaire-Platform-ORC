"use client";

import {
  Activity,
  FileUp,
  LayoutDashboard,
  Rows3,
  Settings,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { Logo } from "@/components/brand/Logo";
import { cn } from "@/lib/utils";

const LINKS = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/extract", label: "Extracción", icon: FileUp },
  { href: "/results", label: "Resultados", icon: Rows3 },
  { href: "/performance", label: "Rendimiento", icon: Activity },
  { href: "/settings", label: "Ajustes", icon: Settings },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex min-h-screen max-w-[1440px]">
        <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-border bg-card px-4 py-6 lg:flex">
          <Link href="/" className="mb-8 flex items-center gap-3 rounded-xl px-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
            <Logo className="h-9 w-9 shrink-0" />
            <span>
              <span className="block text-sm font-semibold tracking-tight">Questionnaire</span>
              <span className="block text-xs text-muted-foreground">Intelligence</span>
            </span>
          </Link>
          <nav className="flex flex-1 flex-col gap-1" aria-label="Principal">
            {LINKS.map((link) => {
              const active = pathname === link.href;
              const Icon = link.icon;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "flex min-h-11 items-center gap-3 rounded-xl px-3 text-sm transition duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                    active ? "bg-muted font-medium text-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground",
                  )}
                >
                  <Icon size={18} aria-hidden="true" />
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </aside>
        <div className="flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-10 max-w-full border-b border-border bg-card/95 backdrop-blur lg:hidden">
            <Link href="/" className="flex items-center gap-2 px-4 pt-3">
              <Logo className="h-8 w-8 shrink-0" />
              <span className="text-sm font-semibold tracking-tight">Questionnaire</span>
            </Link>
            <div className="flex max-w-full gap-1 overflow-x-auto px-3 py-2">
              {LINKS.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    "min-h-11 shrink-0 rounded-full px-3 py-2 text-sm",
                    pathname === link.href ? "bg-accent text-white" : "text-muted-foreground",
                  )}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </header>
          <main className="min-w-0 flex-1 px-4 py-6 sm:px-8 sm:py-8 lg:px-12">{children}</main>
        </div>
      </div>
    </div>
  );
}
