"""
Tests for _run_async_in_sync_context helper function.
"""

import asyncio
import threading

import pytest

from novaeval.scorers.conversational import _run_async_in_sync_context


class TestRunAsyncInSyncContext:
    """Test cases for _run_async_in_sync_context function."""

    async def simple_coro(self, value: int) -> int:
        """Simple async coroutine for testing."""
        await asyncio.sleep(0.01)
        return value * 2

    async def failing_coro(self) -> None:
        """Async coroutine that raises an exception."""
        await asyncio.sleep(0.01)
        raise ValueError("Test error")

    async def system_exit_coro(self) -> None:
        """Async coroutine that raises SystemExit."""
        await asyncio.sleep(0.01)
        raise SystemExit("System exit test")

    def test_run_from_outside_event_loop(self):
        """Test when called from outside an event loop (RuntimeError path)."""
        result = _run_async_in_sync_context(self.simple_coro(5))
        assert result == 10

    def test_run_from_within_event_loop(self):
        """Test when called from within an existing event loop (thread path)."""

        async def run_in_loop():
            # We're inside an event loop, so this should use thread execution
            result = _run_async_in_sync_context(self.simple_coro(7))
            return result

        result = asyncio.run(run_in_loop())
        assert result == 14

    def test_exception_propagation_outside_loop(self):
        """Test exception propagation when called from outside event loop."""
        with pytest.raises(ValueError, match="Test error"):
            _run_async_in_sync_context(self.failing_coro())

    def test_exception_propagation_inside_loop(self):
        """Test exception propagation when called from inside event loop."""

        async def run_in_loop():
            with pytest.raises(ValueError, match="Test error"):
                _run_async_in_sync_context(self.failing_coro())

        asyncio.run(run_in_loop())

    def test_base_exception_catching(self):
        """Test that BaseException (including SystemExit) is caught."""
        with pytest.raises(SystemExit, match="System exit test"):
            _run_async_in_sync_context(self.system_exit_coro())

    def test_keyboard_interrupt_catching(self):
        """Test KeyboardInterrupt handling."""

        async def kb_interrupt_coro():
            await asyncio.sleep(0.01)
            raise KeyboardInterrupt("Keyboard interrupt test")

        with pytest.raises(KeyboardInterrupt, match="Keyboard interrupt test"):
            _run_async_in_sync_context(kb_interrupt_coro())

    def test_thread_completion_with_result(self):
        """Test successful thread completion with valid result."""

        async def complex_coro():
            await asyncio.sleep(0.01)
            return {"status": "success", "value": 42}

        async def run_in_loop():
            result = _run_async_in_sync_context(complex_coro())
            return result

        result = asyncio.run(run_in_loop())
        assert result == {"status": "success", "value": 42}

    def test_nested_async_calls(self):
        """Test nested async calls work correctly."""

        async def nested_coro():
            result1 = await self.simple_coro(3)
            result2 = await self.simple_coro(4)
            return result1 + result2

        async def run_in_loop():
            result = _run_async_in_sync_context(nested_coro())
            return result

        result = asyncio.run(run_in_loop())
        assert result == 14  # (3*2) + (4*2)

    def test_return_none(self):
        """Test coroutine that returns None."""

        async def none_coro():
            await asyncio.sleep(0.01)
            return None

        result = _run_async_in_sync_context(none_coro())
        assert result is None

    def test_return_string(self):
        """Test coroutine that returns a string."""

        async def string_coro():
            await asyncio.sleep(0.01)
            return "test result"

        result = _run_async_in_sync_context(string_coro())
        assert result == "test result"

    def test_thread_isolation(self):
        """Test that threads are properly isolated."""
        thread_results = []

        async def coro_with_thread_id():
            await asyncio.sleep(0.01)
            return threading.current_thread().ident

        async def run_in_loop():
            result = _run_async_in_sync_context(coro_with_thread_id())
            thread_results.append(result)
            main_thread_id = threading.current_thread().ident
            thread_results.append(main_thread_id)

        asyncio.run(run_in_loop())
        # The coro should run in a different thread than the main event loop thread
        assert len(thread_results) == 2
        assert thread_results[0] != thread_results[1]  # Different thread IDs
