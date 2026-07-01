export { getAuthToken, setAuthToken } from "./_client";

import { analyticsApi, inboxApi, jobsApi, scraperApi } from "./jobs";
import { applicationsApi } from "./applications";
import { profileApi } from "./profile";
import { settingsApi } from "./settings";
import { resumesApi } from "./resumes";
import { coverLettersApi } from "./cover-letters";

export const api = {
  // Health + Auth
  health: jobsApi.health,
  authCallback: jobsApi.authCallback,

  // Jobs
  getJobs: jobsApi.getJobs,
  importJobUrl: jobsApi.importJobUrl,

  // Inbox
  getInbox: inboxApi.getInbox,
  addInboxJob: inboxApi.addInboxJob,
  saveJobToInbox: inboxApi.saveJobToInbox,
  importInboxUrl: inboxApi.importInboxUrl,
  updateInboxStatus: inboxApi.updateInboxStatus,
  rescoreInbox: inboxApi.rescoreInbox,
  rescoreInboxJob: inboxApi.rescoreInboxJob,
  updateInboxResumeCategory: inboxApi.updateInboxResumeCategory,
  generateInboxResume: inboxApi.generateInboxResume,
  getScoringPreferences: inboxApi.getScoringPreferences,
  updateScoringPreferences: inboxApi.updateScoringPreferences,

  // Scraper
  triggerScraper: scraperApi.triggerScraper,
  getScraperSources: scraperApi.getScraperSources,

  // Applications
  getApplications: applicationsApi.getApplications,
  createApplication: applicationsApi.createApplication,
  updateApplication: applicationsApi.updateApplication,
  deleteApplication: applicationsApi.deleteApplication,
  quickSaveJob: applicationsApi.quickSaveJob,

  // Profile
  getProfile: profileApi.getProfile,
  updateProfile: profileApi.updateProfile,
  getMatchScores: profileApi.getMatchScores,
  getScoringStatus: profileApi.getScoringStatus,
  getStructuredProfile: profileApi.getStructuredProfile,
  updateStructuredProfile: profileApi.updateStructuredProfile,
  uploadResumePdf: profileApi.uploadResumePdf,
  getProfilePreviewPdf: profileApi.getProfilePreviewPdf,

  // Settings / BYOK
  getApiKeys: settingsApi.getApiKeys,
  upsertApiKey: settingsApi.upsertApiKey,
  testApiKey: settingsApi.testApiKey,
  probeApiKeyModels: settingsApi.probeApiKeyModels,
  autoSelectApiKeyModels: settingsApi.autoSelectApiKeyModels,
  deleteApiKey: settingsApi.deleteApiKey,
  getApiTokens: settingsApi.getApiTokens,
  createApiToken: settingsApi.createApiToken,
  deleteApiToken: settingsApi.deleteApiToken,

  // Resumes
  getResumes: resumesApi.getResumes,
  getResume: resumesApi.getResume,
  getResumeStatus: resumesApi.getResumeStatus,
  createResume: resumesApi.createResume,
  updateResume: resumesApi.updateResume,
  deleteResume: resumesApi.deleteResume,
  regenerateResume: resumesApi.regenerateResume,
  regenerateTailoredResume: resumesApi.regenerateTailoredResume,
  getResumeLatex: resumesApi.getResumeLatex,
  regenerateResumeLatex: resumesApi.regenerateResumeLatex,
  downloadResumePdf: resumesApi.downloadResumePdf,
  getResumeMessages: resumesApi.getResumeMessages,
  sendResumeChat: resumesApi.sendResumeChat,
  atsFixResume: resumesApi.atsFixResume,
  handleResumeChange: resumesApi.handleResumeChange,
  handleResumeChangesBatch: resumesApi.handleResumeChangesBatch,
  runATSScore: resumesApi.runATSScore,
  getATSScore: resumesApi.getATSScore,
  getATSScoreHistory: resumesApi.getATSScoreHistory,

  // Cover letters
  getCoverLetters: coverLettersApi.getCoverLetters,
  getCoverLetter: coverLettersApi.getCoverLetter,
  updateCoverLetter: coverLettersApi.updateCoverLetter,
  createCoverLetter: coverLettersApi.createCoverLetter,
  regenerateCoverLetter: coverLettersApi.regenerateCoverLetter,
  getCoverLetterPreviewHtml: coverLettersApi.getCoverLetterPreviewHtml,
  getCoverLetterMessages: coverLettersApi.getCoverLetterMessages,
  sendCoverLetterChat: coverLettersApi.sendCoverLetterChat,
  handleCoverLetterChange: coverLettersApi.handleCoverLetterChange,
  downloadCoverLetterPdf: coverLettersApi.downloadCoverLetterPdf,

  // Analytics
  getAnalytics: analyticsApi.getAnalytics,
};
