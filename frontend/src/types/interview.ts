/**
 * TypeScript types for interview: InterviewPrep, InterviewQuestion, CoverLetter.
 */

export interface InterviewQuestion {
  // TODO: Define interview question properties
  question: string;
  answer: string;
  category: string;
}

export interface InterviewPrep {
  // TODO: Define interview prep properties
  id: string;
  sessionId: string;
  questions: InterviewQuestion[];
  tips: string[];
}

export interface CoverLetter {
  // TODO: Define cover letter properties
  id: string;
  sessionId: string;
  content: string;
  generatedAt: string;
}
