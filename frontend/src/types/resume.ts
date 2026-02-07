/**
 * TypeScript types for resume: Resume, ResumeSection, SectionType, UploadResumeResponse.
 */

export type SectionType = 'experience' | 'education' | 'skills' | 'summary' | 'other';

export interface ResumeSection {
  // TODO: Define resume section properties
  type: SectionType;
  content: string;
}

export interface Resume {
  // TODO: Define resume properties
  id: string;
  fileName: string;
  sections: ResumeSection[];
  uploadedAt: string;
}

export interface UploadResumeResponse {
  // TODO: Define upload response properties
  resumeId: string;
  fileName: string;
  parsed: boolean;
}
