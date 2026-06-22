import { MarketingNavbar } from "@/components/marketing/MarketingNavbar";

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <MarketingNavbar />
      {children}
      <footer className="border-t border-zinc-800/80 py-8 text-center text-sm text-zinc-600">
        <p>
          Built by{" "}
          <a href="https://github.com/NevilPatel01" className="text-zinc-400 hover:text-white">
            Nevil Patel
          </a>
          {" · "}
          <a href="https://github.com/NevilPatel01/JobPilot" className="text-zinc-400 hover:text-white">
            MIT License
          </a>
        </p>
      </footer>
    </div>
  );
}
