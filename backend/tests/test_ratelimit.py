from app.ratelimit import RateLimiter


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def test_per_visitor_limit_resets_after_an_hour():
    clock = Clock()
    limiter = RateLimiter(per_visitor_per_hour=2, global_per_day=100, clock=clock)
    assert [limiter.check("a") for _ in range(3)] == [None, None, "visitor"]
    assert limiter.check("b") is None  # other visitors are unaffected
    clock.now += 3601
    assert limiter.check("a") is None


def test_daily_cap_applies_across_visitors():
    clock = Clock()
    limiter = RateLimiter(per_visitor_per_hour=10, global_per_day=3, clock=clock)
    assert [limiter.check(v) for v in "abcd"] == [None, None, None, "daily"]
    clock.now += 86401
    assert limiter.check("d") is None


def test_blocked_attempts_are_not_counted():
    clock = Clock()
    limiter = RateLimiter(per_visitor_per_hour=1, global_per_day=2, clock=clock)
    limiter.check("a")
    for _ in range(5):
        assert limiter.check("a") == "visitor"
    assert limiter.check("b") is None  # a's rejected attempts didn't use the daily budget
