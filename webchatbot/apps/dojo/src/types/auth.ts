export interface TelegramUser {
  id: number | string;
  first_name?: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  language_code?: string;
}

export interface BotApiSession {
  token: string;
  refreshToken?: string;
  expiresAt?: number;
  issuedAt?: number;
  user?: TelegramUser;
}

export interface SessionResponseBody {
  authenticated: boolean;
  user?: TelegramUser;
  expiresAt?: number;
  issuedAt?: number;
}

export interface TelegramAuthPayload {
  id: number;
  first_name?: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  auth_date: number;
  hash: string;
  language_code?: string;
  query_id?: string;
}
