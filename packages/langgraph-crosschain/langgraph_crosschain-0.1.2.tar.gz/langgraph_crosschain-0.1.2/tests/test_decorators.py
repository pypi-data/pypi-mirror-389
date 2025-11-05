"""Tests for utility decorators."""

import time

import pytest

from langgraph_crosschain.core.chain_registry import ChainRegistry
from langgraph_crosschain.exceptions import ChainNotFoundError
from langgraph_crosschain.utils.decorators import (
    log_call,
    measure_time,
    retry,
    thread_safe,
    validate_chain_registered,
)


class TestRetryDecorator:
    """Tests for retry decorator."""

    def test_retry_succeeds_on_first_attempt(self):
        """Test that successful functions work without retry."""
        call_count = 0

        @retry(max_attempts=3)
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_function()
        assert result == "success"
        assert call_count == 1

    def test_retry_succeeds_after_failures(self):
        """Test that function succeeds after retries."""
        call_count = 0

        @retry(max_attempts=3, delay=0.1, backoff=1.0)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = flaky_function()
        assert result == "success"
        assert call_count == 3

    def test_retry_exhausts_attempts(self):
        """Test that retry gives up after max attempts."""
        call_count = 0

        @retry(max_attempts=3, delay=0.1, backoff=1.0)
        def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent failure")

        with pytest.raises(ValueError, match="Permanent failure"):
            failing_function()

        assert call_count == 3

    def test_retry_with_specific_exceptions(self):
        """Test retrying only on specific exceptions."""
        call_count = 0

        @retry(max_attempts=3, delay=0.1, exceptions=(ValueError,))
        def function_with_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("Should not retry")

        with pytest.raises(TypeError, match="Should not retry"):
            function_with_type_error()

        assert call_count == 1  # No retry for TypeError


class TestLogCallDecorator:
    """Tests for log_call decorator."""

    def test_log_call_basic(self):
        """Test basic function call logging."""

        @log_call()
        def simple_function(x):
            return x * 2

        result = simple_function(5)
        assert result == 10

    def test_log_call_without_args(self):
        """Test logging without arguments."""

        @log_call(include_args=False)
        def simple_function(x):
            return x * 2

        result = simple_function(5)
        assert result == 10

    def test_log_call_without_result(self):
        """Test logging without result."""

        @log_call(include_result=False)
        def simple_function(x):
            return x * 2

        result = simple_function(5)
        assert result == 10


class TestMeasureTimeDecorator:
    """Tests for measure_time decorator."""

    def test_measure_time(self):
        """Test that execution time is measured."""

        @measure_time()
        def slow_function():
            time.sleep(0.1)
            return "done"

        result = slow_function()
        assert result == "done"
        assert slow_function.last_execution_time >= 0.1
        assert slow_function.last_execution_time < 0.2

    def test_measure_time_without_logging(self):
        """Test measuring time without logging."""

        @measure_time(log_result=False)
        def fast_function():
            return "done"

        result = fast_function()
        assert result == "done"
        assert hasattr(fast_function, "last_execution_time")
        assert fast_function.last_execution_time >= 0


class TestValidateChainRegisteredDecorator:
    """Tests for validate_chain_registered decorator."""

    def setup_method(self):
        """Set up test fixtures."""
        registry = ChainRegistry()
        registry.clear()
        registry.register("chain1", "mock_chain")

    def test_validate_chain_registered_success(self):
        """Test that registered chain passes validation."""

        @validate_chain_registered()
        def process_chain(chain_id):
            return f"Processing {chain_id}"

        result = process_chain("chain1")
        assert result == "Processing chain1"

    def test_validate_chain_registered_failure(self):
        """Test that unregistered chain raises error."""

        @validate_chain_registered()
        def process_chain(chain_id):
            return f"Processing {chain_id}"

        with pytest.raises(ChainNotFoundError, match="nonexistent"):
            process_chain("nonexistent")

    def test_validate_chain_registered_with_kwargs(self):
        """Test validation with keyword arguments."""

        @validate_chain_registered()
        def process_chain(chain_id, option=None):
            return f"Processing {chain_id} with {option}"

        result = process_chain(chain_id="chain1", option="test")
        assert result == "Processing chain1 with test"

    def test_validate_chain_registered_custom_param_name(self):
        """Test validation with custom parameter name."""

        @validate_chain_registered(chain_param="target_chain")
        def process_chain(target_chain):
            return f"Processing {target_chain}"

        result = process_chain("chain1")
        assert result == "Processing chain1"


class TestThreadSafeDecorator:
    """Tests for thread_safe decorator."""

    def test_thread_safe_basic(self):
        """Test basic thread-safe execution."""

        @thread_safe
        def protected_function(x):
            return x * 2

        result = protected_function(5)
        assert result == 10

    def test_thread_safe_prevents_race_conditions(self):
        """Test that thread_safe prevents race conditions."""
        import threading

        counter = 0

        @thread_safe
        def increment():
            nonlocal counter
            temp = counter
            time.sleep(0.001)  # Simulate work
            counter = temp + 1

        threads = [threading.Thread(target=increment) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert counter == 10  # Should be 10, not less due to thread safety
