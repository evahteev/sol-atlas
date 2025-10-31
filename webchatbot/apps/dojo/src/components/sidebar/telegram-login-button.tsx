"use client";

import { useEffect, useMemo, useRef } from "react";

import { cn } from "@/lib/utils";
import type { TelegramAuthPayload } from "@/types/auth";

interface TelegramLoginButtonProps {
  botUsername: string;
  onAuth: (initData: string, payload?: TelegramAuthPayload) => void;
  disabled?: boolean;
  className?: string;
}

function createInitDataFromPayload(payload: TelegramAuthPayload): string {
  const params = new URLSearchParams();

  const userPayload = {
    id: payload.id,
    first_name: payload.first_name,
    last_name: payload.last_name,
    username: payload.username,
    photo_url: payload.photo_url,
    language_code: payload.language_code,
  };

  params.set("user", JSON.stringify(userPayload));
  params.set("auth_date", String(payload.auth_date));
  params.set("hash", payload.hash);
  params.set("id", String(payload.id));

  if (payload.username) {
    params.set("username", payload.username);
  }
  if (payload.first_name) {
    params.set("first_name", payload.first_name);
  }
  if (payload.last_name) {
    params.set("last_name", payload.last_name);
  }
  if (payload.photo_url) {
    params.set("photo_url", payload.photo_url);
  }
  if (payload.language_code) {
    params.set("language_code", payload.language_code);
  }

  if (payload.query_id) {
    params.set("query_id", payload.query_id);
  }

  return params.toString();
}

export function TelegramLoginButton({
  botUsername,
  onAuth,
  disabled,
  className,
}: TelegramLoginButtonProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  const handlerName = useMemo(
    () => `__telegramLoginHandler_${Math.random().toString(36).slice(2)}`,
    [],
  );

  useEffect(() => {
    if (disabled || !botUsername || !containerRef.current) {
      return;
    }

    const container = containerRef.current;
    container.innerHTML = "";

    (window as typeof window & Record<string, unknown>)[handlerName] = (payload: TelegramAuthPayload) => {
      const initData = createInitDataFromPayload(payload);
      onAuth(initData, payload);
    };

    const script = document.createElement("script");
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.async = true;
    script.setAttribute("data-telegram-login", botUsername);
    script.setAttribute("data-size", "large");
    script.setAttribute("data-radius", "6");
    script.setAttribute("data-request-access", "write");
    script.setAttribute("data-userpic", "true");
    script.setAttribute("data-onauth", handlerName);
    script.setAttribute("data-lang", "en");

    container.appendChild(script);

    return () => {
      delete (window as typeof window & Record<string, unknown>)[handlerName];
      container.innerHTML = "";
    };
  }, [botUsername, disabled, handlerName, onAuth]);

  const classNames = cn("flex flex-col items-center justify-center gap-2", className);

  return <div ref={containerRef} className={classNames} />;
}
