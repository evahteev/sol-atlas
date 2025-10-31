"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import type { SessionResponseBody, TelegramUser } from "@/types/auth";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  status: AuthStatus;
  user: TelegramUser | null;
  isAuthenticating: boolean;
  isMiniApp: boolean;
  error: string | null;
  loginWithTelegramInitData: (initData: string) => Promise<TelegramUser | null>;
  refreshSession: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

interface TelegramWindow extends Window {
  Telegram?: {
    WebApp?: {
      initData?: string;
      ready?: () => void;
      expand?: () => void;
    };
  };
}

async function parseJson<T>(response: Response): Promise<T | null> {
  try {
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<TelegramUser | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [isMiniApp, setIsMiniApp] = useState(false);

  const autoLoginAttemptedRef = useRef(false);

  const refreshSession = useCallback(async () => {
    setError(null);
    setStatus((prev) => (prev === "authenticated" ? prev : "loading"));

    try {
      const response = await fetch("/api/auth/session", {
        method: "GET",
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error(`Session request failed with status ${response.status}`);
      }

      const body = (await parseJson<SessionResponseBody>(response)) ?? undefined;
      if (body?.authenticated) {
        setUser(body.user ?? null);
        setStatus("authenticated");
      } else {
        setUser(null);
        setStatus("unauthenticated");
      }
    } catch (sessionError) {
      console.error("Failed to refresh bot session", sessionError);
      setUser(null);
      setStatus("unauthenticated");
      setError("Unable to load session");
    }
  }, []);

  const loginWithTelegramInitData = useCallback(
    async (initData: string) => {
      if (!initData) {
        const errorMessage = "Missing Telegram authentication data";
        setError(errorMessage);
        setStatus("unauthenticated");
        return null;
      }

      setIsAuthenticating(true);
      setError(null);

      try {
        const response = await fetch("/api/auth/telegram", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({ initData }),
        });

        const payload =
          (await parseJson<SessionResponseBody & { error?: string }>(response)) ?? undefined;

        if (!response.ok) {
          const errorMessage = payload?.error ?? "Telegram login failed";
          throw new Error(errorMessage);
        }

        if (payload?.user) {
          setUser(payload.user);
          setStatus("authenticated");
          setError(null);
          return payload.user;
        }

        // Successful response but missing user info; refresh session as fallback
        await refreshSession();
        return payload?.user ?? null;
      } catch (authError) {
        const message =
          authError instanceof Error ? authError.message : "Telegram login failed";
        console.error("Telegram authentication failed", authError);
        setError(message);
        setUser(null);
        setStatus("unauthenticated");
        throw authError;
      } finally {
        setIsAuthenticating(false);
      }
    },
    [refreshSession],
  );

  const logout = useCallback(async () => {
    try {
      await fetch("/api/auth/session", {
        method: "DELETE",
        credentials: "include",
      });
    } catch (logoutError) {
      console.error("Failed to log out of bot API session", logoutError);
    } finally {
      setUser(null);
      setStatus("unauthenticated");
      setError(null);
    }
  }, []);

  // Initial session load
  useEffect(() => {
    void refreshSession();
  }, [refreshSession]);

  // Detect Telegram Mini App environment and attempt auto-login
  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const telegramWindow = window as TelegramWindow;
    const webApp = telegramWindow.Telegram?.WebApp;
    if (!webApp) {
      return;
    }

    setIsMiniApp(true);
    webApp.ready?.();
    webApp.expand?.();

    const initData = webApp.initData;
    if (!initData || initData.length === 0) {
      return;
    }

    if (status === "authenticated" || autoLoginAttemptedRef.current) {
      return;
    }
    autoLoginAttemptedRef.current = true;

    void loginWithTelegramInitData(initData).catch((error) => {
      console.error("Mini App auto-login failed", error);
    });
  }, [loginWithTelegramInitData, status]);

  const contextValue = useMemo<AuthContextValue>(
    () => ({
      status,
      user,
      isAuthenticating,
      isMiniApp,
      error,
      loginWithTelegramInitData,
      refreshSession,
      logout,
    }),
    [
      status,
      user,
      isAuthenticating,
      isMiniApp,
      error,
      loginWithTelegramInitData,
      refreshSession,
      logout,
    ],
  );

  return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
