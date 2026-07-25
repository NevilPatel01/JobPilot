/** Pure decision helpers for recovering from a missing/rejected backend token.
 *
 * Background: the backend raises 401 with detail "Not authenticated" when a
 * request carries no Bearer token, "Invalid token" when the JWT is unreadable,
 * and "User not found" when it decodes to a deleted account. Any of these means
 * the stored token is unusable and the user must be re-authenticated — the old
 * code only reacted to "Invalid token", so already-signed-in accounts whose
 * session never received a backend token were stuck on "Not authenticated".
 */

const AUTH_FAILURE_DETAILS = new Set([
  "not authenticated",
  "invalid token",
  "user not found",
]);

export function isAuthFailureDetail(detail: string): boolean {
  return AUTH_FAILURE_DETAILS.has((detail || "").trim().toLowerCase());
}

/** A NextAuth token that may or may not have completed the backend exchange. */
export interface ExchangeableToken {
  accessToken?: string;
  oauthProvider?: string;
  oauthId?: string;
}

/** True when we know who the user is but have no backend token yet — i.e. the
 * sign-in exchange never ran or failed transiently, and should be retried. */
export function needsBackendExchange(token: ExchangeableToken): boolean {
  return Boolean(!token.accessToken && token.oauthProvider && token.oauthId);
}

/** What the API client should do when a request comes back unauthorized.
 *  - "ignore":          not an auth problem — surface the error, touch nothing.
 *  - "clear-token":     no Bearer was sent (AuthInit hasn't populated it yet, a
 *                       startup race). Drop any stale stored token and let the
 *                       self-heal + a retry recover; do NOT tear down the session.
 *  - "reauthenticate":  a token WAS sent and the backend rejected it (rotated
 *                       SECRET_KEY, deleted user). The NextAuth session has
 *                       drifted out of sync and can't self-heal, so the session
 *                       must be cleared and the user sent through sign-in again.
 *                       Redirecting to /login WITHOUT clearing the session is the
 *                       infinite-loop bug this replaces. */
export type AuthFailureAction = "ignore" | "clear-token" | "reauthenticate";

export function authFailureAction(
  status: number,
  detail: string,
  hadToken: boolean,
): AuthFailureAction {
  if (status !== 401 || !isAuthFailureDetail(detail)) return "ignore";
  return hadToken ? "reauthenticate" : "clear-token";
}
