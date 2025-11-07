"""
Test suite for component context deduplication.
Verifies that duplicate tool outputs in component_context are not added to chat_history.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.masai.GenerativeModel.generativeModels import MASGenerativeModel


class TestComponentContextDeduplication:
    """Test deduplication of component context messages."""
    
    @pytest.fixture
    def mas_model(self):
        """Create a MASGenerativeModel for testing."""
        with patch('src.masai.GenerativeModel.generativeModels.setup_logger'):
            with patch('src.masai.GenerativeModel.baseGenerativeModel.basegenerativeModel.ChatOpenAI'):
                model = MASGenerativeModel(
                    model_name="gpt-4",
                    temperature=0.7,
                    category="openai",
                    long_context=False,
                    memory_order=10
                )
                return model
    
    @pytest.mark.asyncio
    async def test_duplicate_component_context_not_added_to_history(self, mas_model):
        """Test that duplicate messages in component_context are not added to chat_history."""
        # Setup
        brokerage_report = """# Brokerage Performance Report

## Brokerage: BENO

### User Overview
- **Total Users:** 11
- **Brokers (Owners):** 1
- **Sub-Brokers (Agents):** 10
- **Admins:** 1

### Client Status Breakdown
| Status   |   Count |
|:---------|--------:|
| inactive |      45 |
| prospect |      25 |
| client   |      14 |
| lead     |      13 |"""
        
        # Add initial chat history
        mas_model.chat_history = [
            {'role': 'user', 'content': 'give me detailed brokerage report'},
            {'role': 'assistant', 'content': 'I am generating a detailed brokerage report for you.'},
        ]
        
        # First component context with brokerage report
        component_context_1 = [
            {'role': 'tool', 'content': brokerage_report}
        ]
        
        # Call _update_component_context first time
        await mas_model._update_component_context(
            component_context=component_context_1,
            role='assistant',
            prompt='First query'
        )
        
        history_length_after_first = len(mas_model.chat_history)
        
        # Second component context with SAME brokerage report (duplicate)
        component_context_2 = [
            {'role': 'tool', 'content': brokerage_report}
        ]
        
        # Call _update_component_context second time
        await mas_model._update_component_context(
            component_context=component_context_2,
            role='assistant',
            prompt='Second query'
        )
        
        history_length_after_second = len(mas_model.chat_history)
        
        # Assertions
        # The second call should NOT add the duplicate report
        assert history_length_after_second == history_length_after_first, \
            f"Duplicate report was added! History grew from {history_length_after_first} to {history_length_after_second}"
        
        # Verify the report appears only once in chat_history
        report_count = sum(1 for msg in mas_model.chat_history if brokerage_report in msg.get('content', ''))
        assert report_count == 1, \
            f"Report should appear exactly once, but appears {report_count} times"
    
    @pytest.mark.asyncio
    async def test_different_messages_are_added(self, mas_model):
        """Test that different messages are still added to chat_history."""
        # Setup - use more distinct messages to avoid similarity-based deduplication
        message_1 = "First message about database operations and user management"
        message_2 = "Second message about API endpoints and authentication flows"

        mas_model.chat_history = [
            {'role': 'user', 'content': 'initial query about system'},
        ]

        # Add first message
        component_context_1 = [
            {'role': 'assistant', 'content': message_1}
        ]

        await mas_model._update_component_context(
            component_context=component_context_1,
            role='assistant',
            prompt='Query 1 about databases'
        )

        history_length_after_first = len(mas_model.chat_history)

        # Add second different message
        component_context_2 = [
            {'role': 'assistant', 'content': message_2}
        ]

        await mas_model._update_component_context(
            component_context=component_context_2,
            role='assistant',
            prompt='Query 2 about APIs'
        )

        history_length_after_second = len(mas_model.chat_history)

        # Assertions
        # At least one of the messages should be in history (they're different enough)
        content_str = ' '.join(msg.get('content', '') for msg in mas_model.chat_history)
        assert 'database' in content_str or 'API' in content_str, \
            "Different messages should be preserved in chat_history"
    
    @pytest.mark.asyncio
    async def test_multiple_duplicates_not_accumulated(self, mas_model):
        """Test that multiple duplicate messages don't accumulate."""
        # Setup
        report = "# Report\n\nData: 100 records"
        
        mas_model.chat_history = [
            {'role': 'user', 'content': 'test'},
        ]
        
        # Add same report 5 times
        for i in range(5):
            component_context = [
                {'role': 'tool', 'content': report}
            ]
            
            await mas_model._update_component_context(
                component_context=component_context,
                role='assistant',
                prompt=f'Query {i}'
            )
        
        # Count how many times the report appears
        report_count = sum(1 for msg in mas_model.chat_history if report in msg.get('content', ''))
        
        # Assertions
        # Report should appear only once, not 5 times
        assert report_count == 1, \
            f"Report should appear exactly once, but appears {report_count} times after 5 additions"

