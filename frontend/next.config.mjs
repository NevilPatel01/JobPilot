/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  env: {
    NEXT_PUBLIC_HAS_GITHUB: process.env.GITHUB_ID ? "1" : process.env.NEXT_PUBLIC_HAS_GITHUB || "",
    NEXT_PUBLIC_HAS_GOOGLE: process.env.GOOGLE_CLIENT_ID ? "1" : process.env.NEXT_PUBLIC_HAS_GOOGLE || "",
  },
};

export default nextConfig;
