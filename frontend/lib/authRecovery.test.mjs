// Runnable without a test framework: `node lib/authRecovery.test.mjs`
// Guards the fix for "Not authenticated" on already-created accounts.
import assert from "node:assert";
import { isAuthFailureDetail, needsBackendExchange } from "./authRecovery.ts";

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

console.log(`\n${pass} passed`);
