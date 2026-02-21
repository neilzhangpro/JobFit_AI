/**
 * API endpoint constants.
 * All backend API paths defined in one place.
 */
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/api/auth/login',
    REGISTER: '/api/auth/register',
    REFRESH: '/api/auth/refresh',
    ME: '/api/auth/me',
  },
  RESUMES: {
    UPLOAD: '/api/resumes/upload',
    LIST: '/api/resumes',
  },
  OPTIMIZE: {
    RUN: '/api/optimize',
    SESSIONS: '/api/sessions',
  },
  INTERVIEW: {
    PREP: '/api/interview-prep',
    COVER_LETTER: '/api/cover-letter',
  },
  BILLING: {
    USAGE: '/api/billing/usage',
    SUBSCRIPTION: '/api/billing/subscription',
  },
} as const;
