from sqlalchemy import ColumnElement
from sqlalchemy.sql import Select

from app.models.job import Job
from app.services.location import TARGET_COUNTRY


def canada_job_clause() -> ColumnElement[bool]:
    return Job.country == TARGET_COUNTRY


def apply_canada_filter(query: Select) -> Select:
    return query.where(canada_job_clause())
