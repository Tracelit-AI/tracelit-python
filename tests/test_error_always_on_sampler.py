from opentelemetry.sdk.trace.sampling import Decision, SamplingResult

from tracelit.error_always_on_sampler import ErrorAlwaysOnSampler


class DropSampler:
    def should_sample(self, *args, **kwargs):
        return SamplingResult(decision=Decision.DROP)

    def get_description(self):
        return "drop"


def test_error_always_on_promotes_drop():
    sampler = ErrorAlwaysOnSampler(DropSampler())
    result = sampler.should_sample(None, 0, "name")
    assert result.decision == Decision.RECORD_ONLY
