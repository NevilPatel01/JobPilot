from app.jobs.pipeline.dedup import description_similarity


def test_description_similarity_detects_near_duplicate_copy() -> None:
    original = "Provide technical support, resolve incidents, and document solutions for users."
    copied = "Provide technical support, resolve incidents, and document solutions for users!"

    assert description_similarity(original, copied) > 0.95


def test_description_similarity_rejects_unrelated_jobs() -> None:
    support = "Troubleshoot laptops, accounts, networks, and business applications."
    developer = "Design frontend interfaces with React and build GraphQL services."

    assert description_similarity(support, developer) < 0.5


def test_description_similarity_requires_both_descriptions() -> None:
    assert description_similarity(None, "Description") == 0
    assert description_similarity("", "Description") == 0
