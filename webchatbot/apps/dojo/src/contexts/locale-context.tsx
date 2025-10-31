"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import getEnvVars from "@/env";

type Locale = string;

interface LocaleContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  supportedLocales: Locale[];
  loading: boolean;
}

const LocaleContext = createContext<LocaleContextValue | undefined>(undefined);

const STORAGE_KEY = "agui.locale";

function resolveInitialLocale(): { locale: Locale; fromStorage: boolean } {
  if (typeof window === "undefined") {
    const { defaultLocale } = getEnvVars();
    return { locale: defaultLocale, fromStorage: false };
  }

  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored) {
    return { locale: stored, fromStorage: true };
  }

  const browserLocale = window.navigator.language?.split("-")[0];
  return { locale: browserLocale || getEnvVars().defaultLocale, fromStorage: false };
}

export function LocaleProvider({ children }: { children: React.ReactNode }) {
  const { defaultLocale, supportedLocales } = getEnvVars();
  const [locale, setLocaleState] = useState<Locale>(defaultLocale);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const { locale: initialLocale } = resolveInitialLocale();
    if (supportedLocales.includes(initialLocale)) {
      setLocaleState(initialLocale);
    } else {
      setLocaleState(defaultLocale);
    }
    setLoading(false);
  }, [defaultLocale, supportedLocales]);

  const applyLocaleSideEffects = useCallback((nextLocale: Locale) => {
    if (typeof document !== "undefined") {
      document.documentElement.lang = nextLocale;
    }
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, nextLocale);
      const expires = new Date();
      expires.setFullYear(expires.getFullYear() + 1);
      document.cookie = `agui_locale=${nextLocale}; path=/; expires=${expires.toUTCString()}`;
    }
  }, []);

  const setLocale = useCallback(
    (newLocale: Locale) => {
      if (!supportedLocales.includes(newLocale)) {
        console.warn(`Unsupported locale attempted: ${newLocale}`);
        return;
      }
      setLocaleState(newLocale);
      applyLocaleSideEffects(newLocale);
    },
    [applyLocaleSideEffects, supportedLocales],
  );

  useEffect(() => {
    if (!loading) {
      applyLocaleSideEffects(locale);
    }
  }, [applyLocaleSideEffects, locale, loading]);

  const contextValue = useMemo(
    () => ({
      locale,
      setLocale,
      supportedLocales,
      loading,
    }),
    [locale, loading, setLocale, supportedLocales],
  );

  return <LocaleContext.Provider value={contextValue}>{children}</LocaleContext.Provider>;
}

export function useLocale() {
  const context = useContext(LocaleContext);
  if (!context) {
    throw new Error("useLocale must be used within a LocaleProvider");
  }
  return context;
}
