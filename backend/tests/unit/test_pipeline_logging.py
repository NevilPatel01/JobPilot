import logging

from app.core.pipeline_logging import log_pipeline_event, log_pipeline_step


def test_log_pipeline_step_emits_structured_extra(caplog):
    logger = logging.getLogger("test.pipeline")
    with caplog.at_level(logging.INFO):
        log_pipeline_step(logger, resume_id="abc-123", step="tailor_resume", duration_ms=1500, status="completed")

    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.message == "pipeline_step tailor_resume"
    assert record.resume_id == "abc-123"
    assert record.step == "tailor_resume"
    assert record.duration_ms == 1500
    assert record.status == "completed"


def test_log_pipeline_event_emits_lifecycle_extra(caplog):
    logger = logging.getLogger("test.pipeline")
    with caplog.at_level(logging.INFO):
        log_pipeline_event(logger, resume_id="abc-123", event="complete", status="failed", error="timeout")

    record = caplog.records[0]
    assert record.message == "pipeline_complete"
    assert record.event == "complete"
    assert record.status == "failed"
    assert record.error == "timeout"
