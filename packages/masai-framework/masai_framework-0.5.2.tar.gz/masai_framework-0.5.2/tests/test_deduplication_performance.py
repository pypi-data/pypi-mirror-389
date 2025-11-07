"""
Performance test for deduplication process with 100 messages.
Measures time taken for deduplicate_and_truncate_chat_history() function.
"""

import pytest
import timeit
from src.masai.Tools.utilities.deduplication_utils import deduplicate_and_truncate_chat_history


class TestDeduplicationPerformance:
    """Performance tests for deduplication with large chat histories."""

    def test_deduplication_performance_100_messages(self):
        """
        Test deduplication performance with 100 messages.
        Measures time taken for the entire process.
        """
        # Create 100 messages with varying content
        chat_history = []
        for i in range(100):
            chat_history.append({
                'role': 'user' if i % 2 == 0 else 'assistant',
                'content': f'Message {i}: This is a test message with some content. ' * 10
            })

        # Create a prompt with tool output
        current_prompt = """
        Query: What is the status?

        <PREVIOUS TOOL OUTPUT START>
        Brokerage Report: BENO
        Total Users: 11
        Brokers: 1
        Sub-Brokers: 10
        Active Brokers: 1
        Inactive Brokers: 0
        Total Transactions: 5000
        Successful: 4950
        Failed: 50
        Average Transaction Value: $1000
        <PREVIOUS TOOL OUTPUT END>

        Analysis: The report shows important data.
        """

        # Measure time for deduplication using timeit for high precision
        def run_dedup():
            return deduplicate_and_truncate_chat_history(
                chat_history=chat_history,
                component_context=None,
                current_prompt=current_prompt,
                similarity_threshold=0.75
            )

        # Run once to get result
        result = run_dedup()

        # Run 5 times and measure average
        times = timeit.repeat(run_dedup, number=1, repeat=5)
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        # Print performance metrics
        print(f"\n{'='*70}")
        print(f"DEDUPLICATION PERFORMANCE TEST (100 Messages)")
        print(f"{'='*70}")
        print(f"Input messages: {len(chat_history)}")
        print(f"Output messages: {len(result)}")
        print(f"Average time: {avg_time*1000:.2f} ms")
        print(f"Min time: {min_time*1000:.2f} ms")
        print(f"Max time: {max_time*1000:.2f} ms")
        print(f"Time per message (avg): {(avg_time / len(chat_history)) * 1000:.3f} ms")
        print(f"Messages per second: {len(chat_history) / avg_time:.0f}")
        print(f"{'='*70}\n")

        # Assertions
        assert len(result) > 0, "Result should not be empty"
        assert avg_time < 5.0, f"Deduplication should complete in < 5 seconds, took {avg_time:.4f}s"

    def test_deduplication_performance_with_component_context(self):
        """
        Test deduplication performance with component_context.
        Measures time taken when extending history with component_context.
        """
        # Create 100 messages
        chat_history = []
        for i in range(100):
            chat_history.append({
                'role': 'user' if i % 2 == 0 else 'assistant',
                'content': f'Message {i}: Content with tool output. ' * 5
            })

        # Create component_context with 20 messages
        component_context = []
        for i in range(20):
            component_context.append({
                'role': 'assistant',
                'content': f'Component message {i}: Additional context. ' * 5
            })

        # Create a prompt with tool output
        current_prompt = """
        <PREVIOUS TOOL OUTPUT START>
        Tool Output Data: Sample data for testing
        Line 1: Data
        Line 2: More data
        <PREVIOUS TOOL OUTPUT END>
        """

        # Measure time using timeit
        def run_dedup():
            return deduplicate_and_truncate_chat_history(
                chat_history=chat_history,
                component_context=component_context,
                current_prompt=current_prompt,
                similarity_threshold=0.75
            )

        result = run_dedup()
        times = timeit.repeat(run_dedup, number=1, repeat=5)
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        total_input = len(chat_history) + len(component_context)

        # Print performance metrics
        print(f"\n{'='*70}")
        print(f"DEDUPLICATION WITH COMPONENT CONTEXT (120 Messages)")
        print(f"{'='*70}")
        print(f"Input chat_history: {len(chat_history)}")
        print(f"Input component_context: {len(component_context)}")
        print(f"Total input: {total_input}")
        print(f"Output messages: {len(result)}")
        print(f"Average time: {avg_time*1000:.2f} ms")
        print(f"Min time: {min_time*1000:.2f} ms")
        print(f"Max time: {max_time*1000:.2f} ms")
        print(f"Time per message (avg): {(avg_time / total_input) * 1000:.3f} ms")
        print(f"Messages per second: {total_input / avg_time:.0f}")
        print(f"{'='*70}\n")

        assert len(result) > 0, "Result should not be empty"
        assert avg_time < 5.0, f"Deduplication should complete in < 5 seconds, took {avg_time:.4f}s"

    def test_deduplication_performance_with_similar_messages(self):
        """
        Test deduplication performance with many similar messages.
        Measures time taken when processing similar content.
        """
        # Create 100 messages with similar content (to test similarity matching)
        base_content = """
        Brokerage Report: BENO
        Total Users: 11
        Brokers: 1
        Sub-Brokers: 10
        Active Brokers: 1
        Inactive Brokers: 0
        Total Transactions: 5000
        Successful: 4950
        Failed: 50
        Average Transaction Value: $1000
        """

        chat_history = []
        for i in range(100):
            chat_history.append({
                'role': 'user' if i % 2 == 0 else 'assistant',
                'content': f"""
                Query {i}: What is the status?

                <PREVIOUS TOOL OUTPUT START>
                {base_content}
                <PREVIOUS TOOL OUTPUT END>

                Analysis: The report shows important data.
                """
            })

        # Create a prompt with similar tool output
        current_prompt = f"""
        <PREVIOUS TOOL OUTPUT START>
        {base_content}
        <PREVIOUS TOOL OUTPUT END>
        """

        # Measure time using timeit
        def run_dedup():
            return deduplicate_and_truncate_chat_history(
                chat_history=chat_history,
                component_context=None,
                current_prompt=current_prompt,
                similarity_threshold=0.75
            )

        result = run_dedup()
        times = timeit.repeat(run_dedup, number=1, repeat=5)
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        # Print performance metrics
        print(f"\n{'='*70}")
        print(f"DEDUPLICATION WITH SIMILAR MESSAGES (100 Messages)")
        print(f"{'='*70}")
        print(f"Input messages: {len(chat_history)}")
        print(f"Output messages: {len(result)}")
        print(f"Messages truncated: {len(chat_history) - len(result)}")
        print(f"Average time: {avg_time*1000:.2f} ms")
        print(f"Min time: {min_time*1000:.2f} ms")
        print(f"Max time: {max_time*1000:.2f} ms")
        print(f"Time per message (avg): {(avg_time / len(chat_history)) * 1000:.3f} ms")
        print(f"Messages per second: {len(chat_history) / avg_time:.0f}")
        print(f"{'='*70}\n")

        assert len(result) > 0, "Result should not be empty"
        assert avg_time < 5.0, f"Deduplication should complete in < 5 seconds, took {avg_time:.4f}s"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])

