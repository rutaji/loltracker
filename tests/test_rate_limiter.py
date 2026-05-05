from app.services.rate_limiter import TokenBucket


def test_token_bucket_respects_reserved_tokens():
    bucket = TokenBucket(capacity=100, refill_interval_seconds=120, reserved=10)

    assert bucket.try_acquire(90) is True
    assert bucket.try_acquire(1) is False


def test_token_bucket_reports_state():
    bucket = TokenBucket(capacity=10, refill_interval_seconds=120, reserved=2)
    state = bucket.get_state()

    assert state["capacity"] == 10.0
    assert state["reserved"] == 2
    assert state["tokens"] <= 10.0
