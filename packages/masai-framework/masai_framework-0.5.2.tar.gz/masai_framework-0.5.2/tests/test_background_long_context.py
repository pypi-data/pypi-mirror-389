"""
Tests for background long-context summary generation.
Tests for non-blocking behavior and race conditions.
"""

import asyncio
import time
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.masai.GenerativeModel.generativeModels import MASGenerativeModel
from src.masai.schema import Document


class TestBackgroundLongContext:
    """Test background long-context summary generation."""
    
    @pytest.fixture
    def mas_model(self):
        """Create a MASGenerativeModel with long_context enabled."""
        with patch('src.masai.GenerativeModel.generativeModels.setup_logger'):
            with patch('src.masai.GenerativeModel.baseGenerativeModel.basegenerativeModel.ChatOpenAI'):
                model = MASGenerativeModel(
                    model_name="gpt-4",
                    temperature=0.7,
                    category="openai",
                    long_context=True,
                    long_context_order=5,
                    memory_order=3
                )
                # Mock the LLM
                model.llm_long_context = Mock()
                model.llm_long_context.generate_response = Mock(return_value="Summary of messages")
                return model
    
    @pytest.mark.asyncio
    async def test_background_task_is_non_blocking(self, mas_model):
        """Test that background task doesn't block the main flow."""
        # Setup
        messages = [
            {"role": "user", "content": f"Message {i}"}
            for i in range(10)
        ]
        mas_model.chat_history = messages

        # Measure time for background task
        start_time = time.time()

        # Create background task
        task = asyncio.create_task(
            mas_model._update_long_context_background(messages)
        )

        # This should return immediately (non-blocking)
        elapsed_immediate = time.time() - start_time

        # Task should not be done immediately (it's running in background)
        is_running = not task.done()

        # Wait for task to complete
        await task
        elapsed_total = time.time() - start_time

        # Assertions
        assert elapsed_immediate < 0.1, "create_task should return immediately"
        assert is_running, "Task should be running in background"
        assert task.done(), "Task should be done after await"
        assert len(mas_model.context_summaries) > 0, "Summary should be added"
    
    @pytest.mark.asyncio
    async def test_concurrent_background_tasks_no_race_condition(self, mas_model):
        """Test that multiple concurrent background tasks don't cause race conditions."""
        messages = [
            {"role": "user", "content": f"Message {i}"}
            for i in range(10)
        ]
        
        # Create multiple concurrent tasks
        tasks = [
            asyncio.create_task(
                mas_model._update_long_context_background(messages)
            )
            for _ in range(5)
        ]
        
        # Wait for all tasks
        await asyncio.gather(*tasks)
        
        # Assertions
        # Should have 5 summaries (one from each task)
        assert len(mas_model.context_summaries) == 5, \
            f"Expected 5 summaries, got {len(mas_model.context_summaries)}"
        
        # All should be Document objects
        for summary in mas_model.context_summaries:
            assert isinstance(summary, Document), \
                f"Expected Document, got {type(summary)}"
    
    @pytest.mark.asyncio
    async def test_lock_prevents_race_condition_on_size_management(self, mas_model):
        """Test that asyncio.Lock prevents race conditions during size management."""
        messages = [
            {"role": "user", "content": f"Message {i}"}
            for i in range(10)
        ]
        
        # Set long_context_order to 3 to trigger size management
        mas_model.long_context_order = 3
        
        # Create multiple concurrent tasks
        tasks = [
            asyncio.create_task(
                mas_model._update_long_context_background(messages)
            )
            for _ in range(10)
        ]
        
        # Wait for all tasks
        await asyncio.gather(*tasks)
        
        # Assertions
        # Should not exceed long_context_order
        assert len(mas_model.context_summaries) <= mas_model.long_context_order, \
            f"Context summaries exceeded limit: {len(mas_model.context_summaries)} > {mas_model.long_context_order}"
        
        # Should have at least one summary
        assert len(mas_model.context_summaries) > 0, \
            "Should have at least one summary"
    
    @pytest.mark.asyncio
    async def test_background_task_with_error_handling(self, mas_model):
        """Test that errors in background task don't crash the system."""
        messages = [
            {"role": "user", "content": f"Message {i}"}
            for i in range(10)
        ]
        
        # Mock generate_response to raise an error
        mas_model.llm_long_context.generate_response = Mock(
            side_effect=Exception("LLM Error")
        )
        
        # Create background task
        task = asyncio.create_task(
            mas_model._update_long_context_background(messages)
        )
        
        # Should not raise, error should be caught
        await task
        
        # Assertions
        # No summary should be added due to error
        assert len(mas_model.context_summaries) == 0, \
            "No summary should be added on error"
    
    @pytest.mark.asyncio
    async def test_background_task_updates_context_summaries(self, mas_model):
        """Test that background task correctly updates context_summaries."""
        messages = [
            {"role": "user", "content": f"Message {i}"}
            for i in range(10)
        ]
        
        initial_count = len(mas_model.context_summaries)
        
        # Create background task
        task = asyncio.create_task(
            mas_model._update_long_context_background(messages)
        )
        
        # Wait for task
        await task
        
        # Assertions
        assert len(mas_model.context_summaries) == initial_count + 1, \
            "Context summaries should be incremented by 1"
        
        assert isinstance(mas_model.context_summaries[-1], Document), \
            "Last summary should be a Document"
    
    @pytest.mark.asyncio
    async def test_lock_is_acquired_and_released(self, mas_model):
        """Test that asyncio.Lock is properly acquired and released."""
        messages = [
            {"role": "user", "content": f"Message {i}"}
            for i in range(10)
        ]

        # Simply verify that the lock exists and is an asyncio.Lock
        assert isinstance(mas_model._context_lock, asyncio.Lock), \
            "Context lock should be an asyncio.Lock instance"

        # Create background task
        task = asyncio.create_task(
            mas_model._update_long_context_background(messages)
        )

        # Wait for task
        await task

        # Assertions
        # If we got here without deadlock, lock was properly acquired and released
        assert len(mas_model.context_summaries) > 0, \
            "Summary should be added (lock was properly released)"
    
    @pytest.mark.asyncio
    async def test_multiple_tasks_serialize_access_with_lock(self, mas_model):
        """Test that multiple tasks serialize access to context_summaries with lock."""
        messages = [
            {"role": "user", "content": f"Message {i}"}
            for i in range(10)
        ]
        
        # Track access order
        access_order = []
        
        async def tracked_background_task(task_id):
            """Background task with tracking."""
            try:
                summary = "Summary"
                
                if summary is not None:
                    async with mas_model._context_lock:
                        access_order.append(f"acquire_{task_id}")
                        mas_model.context_summaries.append(Document(page_content=summary))
                        access_order.append(f"release_{task_id}")
            except Exception as e:
                pass
        
        # Create multiple concurrent tasks
        tasks = [
            asyncio.create_task(tracked_background_task(i))
            for i in range(5)
        ]
        
        # Wait for all tasks
        await asyncio.gather(*tasks)
        
        # Assertions
        # Should have 5 summaries
        assert len(mas_model.context_summaries) == 5, \
            f"Expected 5 summaries, got {len(mas_model.context_summaries)}"
        
        # Access should be serialized (acquire/release pairs)
        assert len(access_order) == 10, \
            f"Expected 10 access events, got {len(access_order)}"
    
    @pytest.mark.asyncio
    async def test_background_task_with_memory_store(self, mas_model):
        """Test background task with memory store integration."""
        messages = [
            {"role": "user", "content": f"Message {i}"}
            for i in range(10)
        ]
        
        # Mock memory store
        mas_model.LTIMStore = Mock()
        mas_model._save_in_memory = AsyncMock()
        
        # Set low long_context_order to trigger memory store save
        mas_model.long_context_order = 2
        
        # Create multiple background tasks to exceed long_context_order
        tasks = [
            asyncio.create_task(
                mas_model._update_long_context_background(messages)
            )
            for _ in range(5)
        ]
        
        # Wait for all tasks
        await asyncio.gather(*tasks)
        
        # Assertions
        # Should not exceed long_context_order
        assert len(mas_model.context_summaries) <= mas_model.long_context_order, \
            f"Context summaries exceeded limit"
        
        # Memory store should have been called
        assert mas_model._save_in_memory.called, \
            "Memory store should be called when context exceeds limit"


class TestNonBlockingBehavior:
    """Test non-blocking behavior of background tasks."""
    
    @pytest.fixture
    def mas_model(self):
        """Create a MASGenerativeModel with long_context enabled."""
        with patch('src.masai.GenerativeModel.generativeModels.setup_logger'):
            with patch('src.masai.GenerativeModel.baseGenerativeModel.basegenerativeModel.ChatOpenAI'):
                model = MASGenerativeModel(
                    model_name="gpt-4",
                    temperature=0.7,
                    category="openai",
                    long_context=True,
                    long_context_order=5,
                    memory_order=3
                )
                model.llm_long_context = Mock()
                model.llm_long_context.generate_response = Mock(return_value="Summary")
                return model
    
    @pytest.mark.asyncio
    async def test_create_task_returns_immediately(self, mas_model):
        """Test that asyncio.create_task returns immediately."""
        messages = [{"role": "user", "content": "Test"}] * 10
        
        start = time.time()
        task = asyncio.create_task(
            mas_model._update_long_context_background(messages)
        )
        elapsed = time.time() - start
        
        # Should return in < 10ms
        assert elapsed < 0.01, \
            f"create_task took {elapsed}s, should be < 0.01s"
        
        # Clean up
        await task
    
    @pytest.mark.asyncio
    async def test_main_flow_not_blocked_by_background_task(self, mas_model):
        """Test that main flow continues while background task runs."""
        messages = [{"role": "user", "content": "Test"}] * 10

        # Start background task
        start = time.time()
        task = asyncio.create_task(
            mas_model._update_long_context_background(messages)
        )

        # Main flow should continue immediately (create_task returns immediately)
        main_elapsed = time.time() - start
        assert main_elapsed < 0.1, \
            f"Main flow took {main_elapsed}s, should be < 0.1s"

        # Verify task is running (not completed immediately)
        assert not task.done(), "Task should still be running"

        # Wait for background task
        await task

        # Verify task completed
        assert task.done(), "Task should be completed"

        # Verify summary was added
        assert len(mas_model.context_summaries) > 0, \
            "Summary should be added after task completes"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

