/** OAuth provider flags — available on server and client. */
export const authDisabled =
  process.env.AUTH_DISABLED === "true" || process.env.NEXT_PUBLIC_AUTH_DISABLED === "true";

export const hasGithub =
  process.env.NEXT_PUBLIC_HAS_GITHUB === "1" || Boolean(process.env.GITHUB_ID && process.env.GITHUB_SECRET);

export const hasGoogle =
  process.env.NEXT_PUBLIC_HAS_GOOGLE === "1" ||
  Boolean(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET);

/** Read OAuth flags at request time on the server (uses runtime .env.local). */
export function getAuthProviderFlags() {
  return {
    authDisabled:
      process.env.AUTH_DISABLED === "true" || process.env.NEXT_PUBLIC_AUTH_DISABLED === "true",
    hasGithub:
      process.env.NEXT_PUBLIC_HAS_GITHUB === "1" ||
      Boolean(process.env.GITHUB_ID && process.env.GITHUB_SECRET),
    hasGoogle:
      process.env.NEXT_PUBLIC_HAS_GOOGLE === "1" ||
      Boolean(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET),
  };
}
