// Runnable without a test framework: `node lib/authRecovery.test.mjs`
// Guards the fix for "Not authenticated" on already-created accounts.
import assert from "node:assert";
import { authFailureAction, isAuthFailureDetail, needsBackendExchange } from "./authRecovery.ts";

let pass = 0;
const check = (name, fn) => { fn(); pass++; console.log("ok -", name); };

// A missing token yields "Not authenticated"; the old code only reacted to
// "Invalid token", so accounts whose session never got a backend token stayed stuck.
check("Not authenticated is an auth failure", () =>
  assert.strictEqual(isAuthFailureDetail("Not authenticated"), true));
check("Invalid token is an auth failure", () =>
  assert.strictEqual(isAuthFailureDetail("Invalid token"), true));
check("User not found is an auth failure", () =>
  assert.strictEqual(isAuthFailureDetail("User not found"), true));
check("case/whitespace insensitive", () =>
  assert.strictEqual(isAuthFailureDetail("  not authenticated  "), true));
check("unrelated errors are not auth failures", () =>
  assert.strictEqual(isAuthFailureDetail("Job not found"), false));
check("empty detail is not an auth failure", () =>
  assert.strictEqual(isAuthFailureDetail(""), false));

check("exchange needed when accessToken missing but identity present", () =>
  assert.strictEqual(needsBackendExchange({ oauthProvider: "github", oauthId: "42" }), true));
check("no exchange when accessToken already present", () =>
  assert.strictEqual(needsBackendExchange({ accessToken: "x", oauthProvider: "github", oauthId: "42" }), false));
check("no exchange when identity missing", () =>
  assert.strictEqual(needsBackendExchange({}), false));

// authFailureAction — guards the fix for the GitHub sign-in redirect loop.
// A rejected token (token WAS sent) must clear the NextAuth session too, or the
// still-authenticated /login page bounces the user back and re-401s forever.
check("rejected token forces reauthenticate (breaks the loop)", () =>
  assert.strictEqual(authFailureAction(401, "Invalid token", true), "reauthenticate"));
check("deleted user forces reauthenticate", () =>
  assert.strictEqual(authFailureAction(401, "User not found", true), "reauthenticate"));
// No Bearer sent = startup race; recover via self-heal, do NOT sign out.
check("no token sent only clears token, never signs out", () =>
  assert.strictEqual(authFailureAction(401, "Not authenticated", false), "clear-token"));
check("even a token-bearing 'Not authenticated' reauthenticates", () =>
  assert.strictEqual(authFailureAction(401, "Not authenticated", true), "reauthenticate"));
// Non-auth failures must never disturb the session.
check("403 is ignored", () =>
  assert.strictEqual(authFailureAction(403, "Invalid token", true), "ignore"));
check("401 with unrelated detail is ignored", () =>
  assert.strictEqual(authFailureAction(401, "Job not found", true), "ignore"));
check("500 is ignored", () =>
  assert.strictEqual(authFailureAction(500, "Not authenticated", false), "ignore"));

console.log(`\n${pass} passed`);
