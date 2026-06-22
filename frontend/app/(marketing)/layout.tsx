import { MarketingNavbar } from "@/components/marketing/MarketingNavbar";
import type { Metadata } from "next";
import { siteConfig } from "@/lib/site";

export const metadata: Metadata = {
  title: siteConfig.title,
  description: siteConfig.description,
  openGraph: {
    title: siteConfig.title,
    description: siteConfig.description,
    url: siteConfig.url,
  },
};

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <MarketingNavbar />
      {children}
      <footer className="border-t border-border py-8 text-center text-sm text-muted-foreground">
        <p>
          Built by{" "}
          <a href="https://github.com/NevilPatel01" className="text-muted-foreground hover:text-foreground">
            Nevil Patel
          </a>
          {" · "}
          <a href="https://github.com/NevilPatel01/JobPilot" className="text-muted-foreground hover:text-foreground">
            MIT License
          </a>
        </p>
      </footer>
    </div>
  );
}
