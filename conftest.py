"""
pytest configuration shared by the package's suites (pyproject.toml makes this directory the
rootdir, so pytest picks this file up from any of them).

The `timed` marker measures one case on its own and fails it when it runs over its budget:

    pytest.param(..., marks=pytest.mark.timed(max_ms=200))

It is for cases that exist to pin a performance fix, where the output alone would still pass
if the fix were undone. Only the test function's own call is timed, not its setup or its
fixtures, so anything the case should not be charged for - a process brought up on first use,
a cache to fill - belongs in a fixture the case requests. The time is recorded in the case's
`user_properties` (so it reaches a junit report) and listed at the end of the run under
"timed cases". A case without the marker is not timed.

The hook is a new-style wrapper, which needs pytest 8; pyproject.toml says so in `minversion`.
"""

import time

import pytest

# pytest only exports TerminalReporter under its own name from 8.4; on 8.0 to 8.3, which
# minversion allows, the attribute lookup fails while this file is being loaded and takes
# every suite down with it. The class has always lived in this module.
from _pytest.terminal import TerminalReporter

TIMED_MARKER = "timed"
ELAPSED_PROPERTY = "elapsed_ms"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        f"{TIMED_MARKER}(max_ms): time the case's own call and fail it when it takes longer"
        " than max_ms milliseconds; the time is listed at the end of the run",
    )


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item: pytest.Item):
    marker = item.get_closest_marker(TIMED_MARKER)
    if marker is None:
        return (yield)
    max_ms = marker.kwargs.get("max_ms", marker.args[0] if marker.args else None)
    if max_ms is None:
        raise pytest.UsageError(f"{item.nodeid}: the {TIMED_MARKER} marker needs max_ms")
    start = time.perf_counter()
    try:
        result = yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        item.user_properties.append((ELAPSED_PROPERTY, elapsed_ms))
    # Only a call that passed is judged on its time: one that failed keeps its own exception,
    # and with it the expected/got diff, which a budget failure raised over it would replace.
    if elapsed_ms > max_ms:
        pytest.fail(
            f"took {elapsed_ms:.1f} ms, over the {max_ms} ms the case allows", pytrace=False
        )
    return result


def pytest_terminal_summary(terminalreporter: TerminalReporter) -> None:
    timed = [
        (report, elapsed_ms)
        for outcome in ("passed", "failed")
        for report in terminalreporter.stats.get(outcome, [])
        if getattr(report, "when", None) == "call"
        for name, elapsed_ms in report.user_properties
        if name == ELAPSED_PROPERTY
    ]
    if not timed:
        return
    terminalreporter.write_sep("-", "timed cases")
    for report, elapsed_ms in timed:
        terminalreporter.write_line(f"{elapsed_ms:8.1f} ms  {report.nodeid}")
