"use client";

import React from "react";
import { useLocale } from "@/contexts/locale-context";
import { cn } from "@/lib/utils";

interface LocaleOption {
  code: string;
  label: string;
  emoji?: string;
}

const DEFAULT_LABELS: Record<string, LocaleOption> = {
  en: { code: "en", label: "English", emoji: "🇺🇸" },
  ru: { code: "ru", label: "Русский", emoji: "🇷🇺" },
};

export function LocaleSelector({
  className,
  labels = DEFAULT_LABELS,
}: {
  className?: string;
  labels?: Record<string, LocaleOption>;
}) {
  const { locale, setLocale, supportedLocales, loading } = useLocale();

  if (loading) {
    return (
      <div
        className={cn(
          "inline-flex h-9 items-center rounded-md border border-dashed border-border px-3 text-xs text-muted-foreground",
          className,
        )}
      >
        …
      </div>
    );
  }

  const handleChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setLocale(event.target.value);
  };

  return (
    <label className={cn("inline-flex items-center gap-2 text-xs font-medium text-foreground", className)}>
      <span className="text-muted-foreground">Locale</span>
      <div className="relative">
        <select
          value={locale}
          onChange={handleChange}
          className="appearance-none rounded-md border border-border bg-background py-1 pl-3 pr-6 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
        >
          {supportedLocales.map((localeCode) => {
            const option = labels[localeCode] ?? { code: localeCode, label: localeCode.toUpperCase() };
            return (
              <option key={localeCode} value={localeCode}>
                {option.emoji ? `${option.emoji} ${option.label}` : option.label}
              </option>
            );
          })}
        </select>
        <span className="pointer-events-none absolute inset-y-0 right-2 flex items-center text-xs text-muted-foreground">
          ▾
        </span>
      </div>
    </label>
  );
}
