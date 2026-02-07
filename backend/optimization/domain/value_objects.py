"""JDAnalysis (hard_skills, soft_skills, responsibilities, qualifications), ATSScore (overall + breakdown), GapReport (missing_skills, recommendations), SessionStatus enum (pending/processing/completed/failed)."""

# TODO: Implement JDAnalysis value object
#   - Fields: hard_skills, soft_skills, responsibilities, qualifications
#   - Validation: ensure all fields are non-empty lists
# TODO: Implement ATSScore value object
#   - Fields: overall (float), breakdown (dict of category -> score)
#   - Validation: overall score between 0-100, breakdown values between 0-100
# TODO: Implement GapReport value object
#   - Fields: missing_skills (list), recommendations (list)
#   - Validation: ensure recommendations provided for missing skills
# TODO: Implement SessionStatus enum
#   - Values: PENDING, PROCESSING, COMPLETED, FAILED
#   - Add transition validation methods
