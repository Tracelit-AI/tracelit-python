from __future__ import annotations

from opentelemetry.sdk.trace.sampling import Decision, SamplingResult, Sampler


class ErrorAlwaysOnSampler(Sampler):
    def __init__(self, inner: Sampler) -> None:
        self._inner = inner

    def should_sample(self, *args, **kwargs) -> SamplingResult:
        result = self._inner.should_sample(*args, **kwargs)
        if result.decision in (Decision.RECORD_AND_SAMPLE, Decision.RECORD_ONLY):
            return result
        return SamplingResult(decision=Decision.RECORD_ONLY, attributes=result.attributes, trace_state=result.trace_state)

    def get_description(self) -> str:
        return f"ErrorAlwaysOnSampler({self._inner.get_description()})"
