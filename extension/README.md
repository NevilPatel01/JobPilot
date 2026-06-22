# JobPilot Capture

Manifest V3 Chrome extension for manually capturing job listings into JobPilot.

## Install for local development

1. Open `chrome://extensions`.
2. Enable **Developer mode**.
3. Click **Load unpacked** and choose this `extension/` directory.
4. In JobPilot Settings, create a Public API Token.
5. Open the extension, enter the JobPilot API URL, app URL, and token.

## Fast capture

- Press **Ctrl+Shift+Y** on Windows/Linux or **Command+Shift+Y** on macOS to open capture for the active tab.
- Click the toolbar icon to extract the job in the current tab automatically.
- Paste a job URL into the popup and click **Load URL** when the listing is not already open.
- Review the extracted details, then choose **Save to Inbox** or **Save + Applied**.

Chrome shortcut assignments can be changed at `chrome://extensions/shortcuts`.

The extension stores only the JobPilot server URL, app URL, and API token. It does not store profile or resume content.

Supported extraction paths: LinkedIn, Indeed, Job Bank, Greenhouse, Lever, Workday, schema.org `JobPosting` JSON-LD, generic job pages, and selected-text fallback.
