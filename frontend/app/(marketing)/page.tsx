import { MarketingHero } from "@/components/marketing/MarketingHero";
import { MarketingFeatureGrid } from "@/components/marketing/MarketingFeatureGrid";
import { MarketingHowItWorks } from "@/components/marketing/MarketingHowItWorks";

export default function LandingPage() {
  return (
    <>
      <MarketingHero />
      <MarketingFeatureGrid />
      <MarketingHowItWorks />
    </>
  );
}
