"""Pytest plugin implementation for SQLAlchemy async greenlet context."""

from __future__ import annotations

import inspect
from typing import Any

import pytest

# Try to import MissingGreenlet for error detection
try:
    from sqlalchemy.exc import MissingGreenlet
except ImportError:
    MissingGreenlet = None  # type: ignore[assignment]

try:
    from sqlalchemy.util._concurrency_py3k import greenlet_spawn
except ImportError:
    # Fallback for different SQLAlchemy versions
    try:
        from sqlalchemy.util import greenlet_spawn
    except ImportError:
        greenlet_spawn = None  # type: ignore[assignment]


async def _establish_greenlet_context_async(debug: bool = False) -> None:
    """
    Establish greenlet context from within an async context.

    This is more reliable because it ensures we're in the right async context
    when establishing the greenlet context.

    Args:
        debug: If True, log debug information
    """
    if greenlet_spawn is None:
        if debug:
            import warnings

            warnings.warn(
                "greenlet_spawn not available. Greenlet context cannot be established.",
                UserWarning,
                stacklevel=2,
            )
        return

    try:

        def _noop() -> None:
            pass

        # greenlet_spawn is a coroutine - we must await it!
        await greenlet_spawn(_noop)
        if debug:
            import warnings

            warnings.warn(
                "Greenlet context established successfully.",
                UserWarning,
                stacklevel=2,
            )
    except Exception as e:
        if debug:
            import warnings

            warnings.warn(
                f"Failed to establish greenlet context: {e}",
                UserWarning,
                stacklevel=2,
            )
        pass


def _should_establish_context(config: pytest.Config) -> bool:
    """
    Check if greenlet context should be established automatically.

    Args:
        config: Pytest configuration

    Returns:
        True if context should be established, False otherwise
    """
    # Check if autouse is disabled via config
    return config.getoption("green_light_autouse", default=True)


@pytest.fixture(scope="function", autouse=True)
async def ensure_greenlet_context(request: pytest.FixtureRequest) -> Any:
    """
    Auto-use async fixture that ensures greenlet context is established.

    Note: For async tests, the pytest_pyfunc_call hook is the primary method
    for establishing greenlet context, as it ensures context is established
    in the exact same async context where the test runs. This fixture provides
    additional coverage for edge cases and non-async tests that may need
    greenlet context.

    Can be disabled with --green-light-no-autouse flag.

    Args:
        request: Pytest fixture request

    Yields:
        None - context is active during fixture lifetime
    """
    config = request.config
    autouse = _should_establish_context(config)
    debug = config.getoption("green_light_debug", default=False)

    # Only establish if autouse is enabled
    if autouse:
        await _establish_greenlet_context_async(debug=debug)

    yield
    # Cleanup if needed (currently no cleanup required)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options for the plugin."""
    group = parser.getgroup("green-light", "pytest-green-light options")

    group.addoption(
        "--green-light-autouse",
        action="store_true",
        default=True,
        help="Automatically establish greenlet context for all tests (default: True)",
    )

    group.addoption(
        "--green-light-no-autouse",
        action="store_false",
        dest="green_light_autouse",
        help="Disable automatic greenlet context establishment",
    )

    group.addoption(
        "--green-light-debug",
        action="store_true",
        default=False,
        help="Enable debug logging for greenlet context establishment",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "async_sqlalchemy: marks tests that use SQLAlchemy async",
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> Any:
    """
    Establish greenlet context before async test execution.

    This hook wraps test function execution and establishes greenlet context
    in the same async context where the test will run, ensuring
    SQLAlchemy async engines work correctly.

    Args:
        pyfuncitem: The pytest function item being executed
    """
    # Check if autouse is enabled
    config = pyfuncitem.config
    autouse = _should_establish_context(config)
    debug = config.getoption("green_light_debug", default=False)

    # Only proceed if autouse is enabled
    if not autouse:
        yield
        return

    # Check if test function is async
    test_function = pyfuncitem.function
    is_async = inspect.iscoroutinefunction(test_function)

    if is_async and greenlet_spawn is not None:
        # For async tests, we need to establish greenlet context
        # in the async context where the test will run.
        # We wrap the test function to establish context first.
        original_function = test_function

        async def wrapped_test_function(*args: Any, **kwargs: Any) -> Any:
            """Wrapper that establishes greenlet context then runs the test."""
            # Establish greenlet context in the same async context as the test
            await _establish_greenlet_context_async(debug=debug)
            # Run the original test function
            return await original_function(*args, **kwargs)

        # Replace the test function with our wrapper
        pyfuncitem.function = wrapped_test_function

    # Execute the test (hookwrapper pattern)
    yield


def _get_diagnostic_info() -> str:
    """
    Get diagnostic information about the current environment.

    Returns:
        Diagnostic string with helpful information
    """
    diagnostics = []

    # Check SQLAlchemy version
    try:
        import sqlalchemy

        diagnostics.append(f"SQLAlchemy version: {sqlalchemy.__version__}")
    except ImportError:
        diagnostics.append("SQLAlchemy: Not installed")

    # Check greenlet availability
    try:
        import greenlet

        diagnostics.append(f"greenlet version: {greenlet.__version__}")
    except ImportError:
        diagnostics.append("greenlet: Not installed")

    # Check greenlet_spawn availability
    if greenlet_spawn is None:
        diagnostics.append("greenlet_spawn: Not available")
    else:
        diagnostics.append("greenlet_spawn: Available")

    # Check pytest-asyncio
    try:
        import pytest_asyncio  # noqa: F401  # type: ignore[import-untyped]

        diagnostics.append("pytest-asyncio: Installed")
    except ImportError:
        diagnostics.append("pytest-asyncio: Not installed")

    return "\n".join(diagnostics)


def pytest_exception_interact(
    node: pytest.Item | pytest.Collector,
    call: pytest.CallInfo,
    report: pytest.CollectReport | pytest.TestReport,
) -> None:
    """
    Intercept exceptions and provide helpful diagnostics for MissingGreenlet errors.

    Args:
        node: The pytest item/node
        call: The call information
        report: The test report
    """
    if MissingGreenlet is None:
        return

    excinfo = call.excinfo
    if excinfo is None:
        return

    exception = excinfo.value
    if not isinstance(exception, MissingGreenlet):
        return

    # Add helpful diagnostics to the error
    diagnostics = _get_diagnostic_info()

    # Create a more helpful error message
    error_msg = (
        f"\n\n{'=' * 70}\n"
        f"MissingGreenlet Error Detected\n"
        f"{'=' * 70}\n"
        f"\nThe plugin attempted to establish greenlet context, but it seems\n"
        f"the context was not properly established or was lost.\n"
        f"\nDiagnostic Information:\n{diagnostics}\n"
        f"\nTroubleshooting Steps:\n"
        f"1. Ensure pytest-green-light is installed: pip install pytest-green-light\n"
        f"2. Verify the plugin is loaded: pytest --version should show 'green-light'\n"
        f"3. Try running with --green-light-debug to see detailed logs\n"
        f"4. Ensure you're using async fixtures and async test functions\n"
        f"5. Check that pytest-asyncio is installed if you're using async tests\n"
        f"6. Verify SQLAlchemy >= 2.0 is installed\n"
        f"\nIf the problem persists, please file an issue at:\n"
        f"https://github.com/eddiethedean/pytest-green-light/issues\n"
        f"{'=' * 70}\n"
    )

    # Add the diagnostic message to the exception
    if hasattr(exception, "args") and len(exception.args) > 0:
        original_msg = str(exception.args[0])
        exception.args = (original_msg + error_msg,) + exception.args[1:]
    else:
        exception.args = (error_msg,)
