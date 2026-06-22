# JobPilot Capture

Manifest V3 Chrome extension for manually capturing job listings into JobPilot.

## Install for local development

1. Open `chrome://extensions`.
2. Enable **Developer mode**.
3. Click **Load unpacked** and choose this `extension/` directory.
4. In JobPilot Settings, create a Public API Token.
5. Open the extension, enter the JobPilot API URL, app URL, and token.

The extension stores only the JobPilot server URL, app URL, and API token. It does not store profile or resume content.

Supported extraction paths: LinkedIn, Indeed, Job Bank, Greenhouse, Lever, Workday, schema.org `JobPosting` JSON-LD, generic job pages, and selected-text fallback.
