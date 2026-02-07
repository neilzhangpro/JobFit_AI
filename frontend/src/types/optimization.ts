/**
 * TypeScript types for optimization: OptimizationSession, OptimizationResult, JDAnalysis, ATSScore, GapReport.
 */

export interface JDAnalysis {
  // TODO: Define JD analysis properties
  jobTitle: string;
  requiredSkills: string[];
}

export interface ATSScore {
  // TODO: Define ATS score properties
  score: number;
  maxScore: number;
}

export interface GapReport {
  // TODO: Define gap report properties
  missingSkills: string[];
  recommendations: string[];
}

export interface OptimizationResult {
  // TODO: Define optimization result properties
  id: string;
  atsScore: ATSScore;
  gapReport: GapReport;
  jdAnalysis: JDAnalysis;
}

export interface OptimizationSession {
  // TODO: Define optimization session properties
  id: string;
  resumeId: string;
  jobDescription: string;
  result: OptimizationResult | null;
  createdAt: string;
}
