(() => {
  const text = (...selectors) => {
    for (const selector of selectors.flat()) {
      const element = document.querySelector(selector);
      const value = element?.textContent?.replace(/\s+/g, " ").trim();
      if (value) return value;
    }
    return "";
  };

  const attribute = (selector, name) => document.querySelector(selector)?.getAttribute(name)?.trim() || "";
  const stripHtml = (value) => {
    const node = document.createElement("div");
    node.innerHTML = value || "";
    return node.textContent?.replace(/\s+/g, " ").trim() || "";
  };

  const jobPostingJsonLd = () => {
    const scripts = [...document.querySelectorAll('script[type="application/ld+json"]')];
    for (const script of scripts) {
      try {
        const parsed = JSON.parse(script.textContent || "null");
        const candidates = Array.isArray(parsed) ? parsed : parsed?.["@graph"] || [parsed];
        const posting = candidates.find((item) => item?.["@type"] === "JobPosting");
        if (posting) return posting;
      } catch {
        // Ignore malformed third-party structured data.
      }
    }
    return null;
  };

  const sourceSite = (host) => {
    if (host.includes("linkedin.")) return "linkedin";
    if (host.includes("indeed.")) return "indeed";
    if (host.includes("jobbank.gc.ca")) return "job_bank";
    if (host.includes("greenhouse.io")) return "greenhouse";
    if (host.includes("lever.co")) return "lever";
    if (host.includes("myworkdayjobs.com")) return "workday";
    return "generic";
  };

  const selectors = {
    linkedin: {
      title: ["h1.job-details-jobs-unified-top-card__job-title", ".job-details-jobs-unified-top-card__job-title h1", "h1"],
      company: [".job-details-jobs-unified-top-card__company-name", ".job-details-jobs-unified-top-card__primary-description-container a"],
      location: [".job-details-jobs-unified-top-card__primary-description-container .tvm__text", ".job-details-jobs-unified-top-card__bullet"],
      description: [".jobs-description__content", ".jobs-description-content__text"]
    },
    indeed: {
      title: ["h1.jobsearch-JobInfoHeader-title", "h1[data-testid='jobsearch-JobInfoHeader-title']", "h1"],
      company: ["[data-testid='inlineHeader-companyName']", "[data-testid='jobsearch-JobInfoHeader-companyName']", "[data-company-name='true']"],
      location: ["[data-testid='job-location']", "[data-testid='inlineHeader-companyLocation']"],
      description: ["#jobDescriptionText"]
    },
    job_bank: {
      title: ["h1", "[property='title']"],
      company: ["[property='hiringOrganization']", "[property='name']"],
      location: ["[property='jobLocation']", ".location"] ,
      description: ["[property='description']", "#job-description", ".job-posting-detail"]
    },
    greenhouse: {
      title: ["h1.app-title", ".job__title h1", "h1"],
      company: [".company-name", ".logo-container img"],
      location: [".location", ".job__location"],
      description: ["#content", ".job__description"]
    },
    lever: {
      title: [".posting-headline h2", "h2.posting-title", "h1"],
      company: [".main-header-logo img", "meta[property='og:site_name']"],
      location: [".posting-categories .location", ".posting-category.location"],
      description: [".posting-page .content", ".section-wrapper"]
    },
    workday: {
      title: ["[data-automation-id='jobPostingHeader']", "h2[data-automation-id='jobPostingHeader']", "h1"],
      company: ["[data-automation-id='company']"],
      location: ["[data-automation-id='locations']", "[data-automation-id='jobPostingLocation']"],
      description: ["[data-automation-id='jobPostingDescription']"]
    },
    generic: {
      title: ["h1"],
      company: ["[data-company]", ".company", ".company-name"],
      location: ["[data-location]", ".location", ".job-location"],
      description: ["[data-job-description]", ".job-description", "article", "main"]
    }
  };

  const salary = (posting) => {
    const value = posting?.baseSalary?.value;
    if (!value) return {};
    return {
      salary_min: Number(value.minValue ?? value.value) || null,
      salary_max: Number(value.maxValue ?? value.value) || null,
      currency: posting.baseSalary.currency || "CAD"
    };
  };

  const extract = () => {
    const host = location.hostname.toLowerCase();
    const site = sourceSite(host);
    const config = selectors[site] || selectors.generic;
    const posting = jobPostingJsonLd();
    const selectedText = (window.getSelection()?.toString().replace(/\s+/g, " ").trim() || "").slice(0, 50000);
    const structuredLocation = posting?.jobLocation?.address;
    const jsonLocation = typeof structuredLocation === "string"
      ? structuredLocation
      : [structuredLocation?.addressLocality, structuredLocation?.addressRegion, structuredLocation?.addressCountry]
          .filter(Boolean)
          .join(", ");
    const companyImageAlt = document.querySelector(".main-header-logo img, .logo-container img")?.getAttribute("alt") || "";
    const pageTitle = document.title.split(/[|–—]/)[0].trim();

    const description = (text(config.description) || stripHtml(posting?.description) || selectedText).slice(0, 100000);
    return {
      title: text(config.title) || stripHtml(posting?.title) || pageTitle,
      company:
        text(config.company) ||
        companyImageAlt ||
        stripHtml(posting?.hiringOrganization?.name) ||
        attribute("meta[property='og:site_name']", "content"),
      location: text(config.location) || jsonLocation,
      description,
      selected_text: selectedText,
      url: location.href,
      source_site: site,
      job_type: Array.isArray(posting?.employmentType) ? posting.employmentType.join(", ") : posting?.employmentType || "",
      ...salary(posting)
    };
  };

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message?.type !== "JOBPILOT_EXTRACT") return false;
    try {
      sendResponse({ ok: true, data: extract() });
    } catch (error) {
      sendResponse({ ok: false, error: error instanceof Error ? error.message : "Could not read this page" });
    }
    return true;
  });
})();
