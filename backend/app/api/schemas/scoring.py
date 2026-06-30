from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class JobFitScoreResponse(BaseModel):
    id: UUID
    score: int
    label: str
    signals: dict
    matched_skills: list[str]
    missing_skills: list[str]
    risk_flags: list[str]
    recommended_action: str
    explanation: str
    recommended_category: str | None
    category_confidence: int | None
    scored_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserScoringPrefsUpdate(BaseModel):
    work_authorization: str = Field(default="work_permit", max_length=50)
    target_provinces: list[str] = Field(default_factory=lambda: ["AB", "BC", "ON", "SK"])
    relocation_open: bool = True
    threshold_overrides: dict[str, int] | None = None

    @model_validator(mode="after")
    def validate_thresholds(self):
        if self.threshold_overrides is None:
            return self
        allowed = {"low_max", "stretch_max", "reviewed_max", "recommended_max"}
        unknown = set(self.threshold_overrides) - allowed
        if unknown:
            raise ValueError(f"Unsupported threshold keys: {', '.join(sorted(unknown))}")
        values = {
            "low_max": 39,
            "stretch_max": 59,
            "reviewed_max": 74,
            "recommended_max": 84,
            **self.threshold_overrides,
        }
        ordered = [values[key] for key in ("low_max", "stretch_max", "reviewed_max", "recommended_max")]
        if not (0 <= ordered[0] < ordered[1] < ordered[2] < ordered[3] < 100):
            raise ValueError("Fit thresholds must be ordered between 0 and 99")
        return self


class UserScoringPrefsResponse(UserScoringPrefsUpdate):
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
