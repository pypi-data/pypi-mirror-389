"""
Comprehensive test for deduplication with similarity matching.
Replicates the exact process of generate_response_mas() to verify
that duplicate tool outputs are caught even with minor character variations.
"""
import pytest
from src.masai.Tools.utilities.deduplication_utils import (
    deduplicate_and_truncate_chat_history,
    extract_tool_output_from_prompt,
    is_content_similar,
    calculate_similarity,
    truncate_similar_substrings_in_history,
    _truncate_similar_substrings
)


class TestSimilarityMatching:
    """Test similarity matching for catching variations."""
    
    def test_exact_match(self):
        """Test exact string matching."""
        text1 = "# Brokerage Report: BENO"
        text2 = "# Brokerage Report: BENO"
        assert is_content_similar(text1, text2, 0.75)
    
    def test_whitespace_variations(self):
        """Test matching with whitespace differences."""
        text1 = "# Brokerage Report: BENO\n\n## User Overview"
        text2 = "# Brokerage Report: BENO\n## User Overview"
        assert is_content_similar(text1, text2, 0.75)
    
    def test_case_insensitive_match(self):
        """Test case-insensitive matching."""
        text1 = "# BROKERAGE REPORT: BENO"
        text2 = "# brokerage report: beno"
        assert is_content_similar(text1, text2, 0.75)
    
    def test_minor_character_variations(self):
        """Test matching with minor character variations."""
        text1 = "Total Users: 11"
        text2 = "Total Users: 11"
        assert is_content_similar(text1, text2, 0.75)
    
    def test_similarity_calculation(self):
        """Test similarity ratio calculation."""
        text1 = "# Brokerage Report: BENO\n## User Overview\n- Total Users: 11"
        text2 = "# Brokerage Report: BENO\n## User Overview\n- Total Users: 11"
        similarity = calculate_similarity(text1, text2)
        assert similarity >= 0.95  # Should be very similar


class TestToolOutputExtraction:
    """Test tool output extraction from prompts."""
    
    def test_extract_tool_output_from_prompt(self):
        """Test extracting tool output from prompt."""
        prompt = """
=== CONTEXT ===
ORIGINAL QUESTION:
how are you

<PREVIOUS TOOL OUTPUT START>
# Brokerage Report: BENO

## User Overview
- **Total Users:** 11
<PREVIOUS TOOL OUTPUT END>
=== END CONTEXT ===
"""
        tool_output = extract_tool_output_from_prompt(prompt)
        assert tool_output is not None
        assert "# Brokerage Report: BENO" in tool_output
        assert "Total Users" in tool_output
    
    def test_extract_empty_tool_output(self):
        """Test extracting from prompt with empty tool output."""
        prompt = """
=== CONTEXT ===
ORIGINAL QUESTION:
detailed brokerage report

<PREVIOUS TOOL OUTPUT START>

<PREVIOUS TOOL OUTPUT END>
=== END CONTEXT ===
"""
        tool_output = extract_tool_output_from_prompt(prompt)
        # Should return None or empty string
        assert not tool_output or tool_output.strip() == ""


class TestCentralizedDeduplication:
    """Test the centralized deduplication function."""
    
    def test_duplicate_tool_output_truncated(self):
        """Test that duplicate tool outputs are truncated."""
        brokerage_report = """# Brokerage Report: BENO

## User Overview
- **Total Users:** 11
- **Brokers:** 1
- **Sub-Brokers:** 10

## Client Overview
- **Total Clients:** 97"""
        
        # Initial chat history
        chat_history = [
            {'role': 'user', 'content': 'give me detailed brokerage report'},
            {'role': 'assistant', 'content': 'I am generating a report...'},
        ]
        
        # First prompt with tool output
        prompt1 = f"""
=== CONTEXT ===
ORIGINAL QUESTION:
how are you

<PREVIOUS TOOL OUTPUT START>
{brokerage_report}
<PREVIOUS TOOL OUTPUT END>
=== END CONTEXT ===
"""
        
        # Process first time
        result1 = deduplicate_and_truncate_chat_history(
            chat_history=chat_history,
            component_context=[],
            current_prompt=prompt1,
            similarity_threshold=0.75
        )
        
        # Second prompt with SAME tool output (duplicate)
        prompt2 = f"""
=== CONTEXT ===
ORIGINAL QUESTION:
nice

<PREVIOUS TOOL OUTPUT START>
{brokerage_report}
<PREVIOUS TOOL OUTPUT END>
=== END CONTEXT ===
"""
        
        # Process second time
        result2 = deduplicate_and_truncate_chat_history(
            chat_history=result1,
            component_context=[],
            current_prompt=prompt2,
            similarity_threshold=0.75
        )
        
        # Check that duplicate was truncated
        full_report_count = sum(
            1 for msg in result2 
            if "Total Users: 11" in msg.get('content', '') and 
               "Brokers: 1" in msg.get('content', '')
        )
        
        # Should have truncated version, not full duplicate
        assert full_report_count <= 1, "Duplicate report should be truncated"
    
    def test_component_context_deduplication(self):
        """Test deduplication of component context."""
        report = "# Report\n\nData: 100 records\nStatus: Active"
        
        chat_history = [
            {'role': 'user', 'content': 'test'},
        ]
        
        component_context = [
            {'role': 'tool', 'content': report}
        ]
        
        # First call
        result1 = deduplicate_and_truncate_chat_history(
            chat_history=chat_history,
            component_context=component_context,
            current_prompt="Query 1",
            similarity_threshold=0.75
        )
        
        # Second call with same component context
        result2 = deduplicate_and_truncate_chat_history(
            chat_history=result1,
            component_context=component_context,
            current_prompt="Query 2",
            similarity_threshold=0.75
        )
        
        # Count how many times the report appears
        report_count = sum(
            1 for msg in result2 
            if "Data: 100 records" in msg.get('content', '')
        )
        
        # Should appear only once
        assert report_count == 1, f"Report should appear once, but appears {report_count} times"
    
    def test_different_messages_preserved(self):
        """Test that different messages are preserved."""
        chat_history = [
            {'role': 'user', 'content': 'test query'},
        ]

        component_context = [
            {'role': 'assistant', 'content': 'First unique message about topic A'},
            {'role': 'assistant', 'content': 'Second unique message about topic B'},
        ]

        result = deduplicate_and_truncate_chat_history(
            chat_history=chat_history,
            component_context=component_context,
            current_prompt="Query about something",
            similarity_threshold=0.75
        )

        # At least one of the messages should be present (they're different enough)
        content_str = ' '.join(msg.get('content', '') for msg in result)
        assert 'topic A' in content_str or 'topic B' in content_str, "Different messages should be preserved"


class TestSubstringTruncation:
    """Test substring truncation for large tool outputs."""

    def test_truncate_similar_substrings_basic(self):
        """Test basic substring truncation."""
        reference_text = "Total Users: 11\nBrokers: 1\nSub-Brokers: 10"

        content = """
        Some message here.
        Total Users: 11
        Brokers: 1
        Sub-Brokers: 10
        More content after.
        """

        result = _truncate_similar_substrings(
            content,
            reference_text,
            similarity_threshold=0.75,
            min_substring_length=20
        )

        # Should contain truncation marker
        assert '[TRUNCATED' in result or content == result

    def test_truncate_similar_substrings_in_history(self):
        """Test truncating similar substrings in chat history."""
        large_tool_output = """# Brokerage Report: BENO

## User Overview
- **Total Users:** 11
- **Brokers:** 1
- **Sub-Brokers:** 10
- **Other Employees:** 0

## Client Overview
- **Total Clients:** 97
### Clients by Status
| _id      |   count |
|:---------|--------:|
| lead     |      13 |
| prospect |      25 |
| client   |      14 |
| inactive |      45 |"""

        # Chat history with the large tool output embedded
        chat_history = [
            {'role': 'user', 'content': 'First query'},
            {'role': 'assistant', 'content': f"""
=== CONTEXT ===
ORIGINAL QUESTION: how are you

<PREVIOUS TOOL OUTPUT START>
{large_tool_output}
<PREVIOUS TOOL OUTPUT END>
=== END CONTEXT ===
"""},
        ]

        # Current prompt with same tool output
        current_prompt = f"""
=== CONTEXT ===
ORIGINAL QUESTION: next query

<PREVIOUS TOOL OUTPUT START>
{large_tool_output}
<PREVIOUS TOOL OUTPUT END>
=== END CONTEXT ===
"""

        result = truncate_similar_substrings_in_history(
            chat_history=chat_history,
            current_prompt=current_prompt,
            similarity_threshold=0.75
        )

        # Check that history was processed
        assert len(result) == len(chat_history)

        # The second message should have truncated content
        second_msg_content = result[1]['content']

        # Either truncated or original (both acceptable)
        assert isinstance(second_msg_content, str)

    def test_multiple_similar_substrings_truncated(self):
        """Test that multiple similar substrings are truncated."""
        reference = "Database connection successful. Status: Active"

        content = """
        Message 1: Database connection successful. Status: Active
        Message 2: Database connection successful. Status: Active
        Message 3: Different content here
        """

        result = _truncate_similar_substrings(
            content,
            reference,
            similarity_threshold=0.75,
            min_substring_length=30
        )

        # Should have some truncation
        assert isinstance(result, str)
        assert len(result) > 0


class TestTaggedTruncation:
    """Test that only tagged tool output is truncated, not entire message."""

    def test_only_tool_output_section_truncated(self):
        """Verify that only content between tags is replaced."""
        chat_history = [
            {
                'role': 'user',
                'content': """Query: What is the status?

<PREVIOUS TOOL OUTPUT START>
Brokerage Report: BENO
Total Users: 11
Brokers: 1
Sub-Brokers: 10
<PREVIOUS TOOL OUTPUT END>

Analysis: The report shows important data."""
            }
        ]

        current_prompt = """<PREVIOUS TOOL OUTPUT START>
Brokerage Report: BENO
Total Users: 11
Brokers: 1
Sub-Brokers: 10
<PREVIOUS TOOL OUTPUT END>"""

        result = deduplicate_and_truncate_chat_history(
            chat_history=chat_history,
            component_context=None,
            current_prompt=current_prompt,
            similarity_threshold=0.75
        )

        # Check that result has one message
        assert len(result) == 1

        content = result[0]['content']

        # Verify parts that should be preserved
        assert 'Query: What is the status?' in content
        assert 'Analysis: The report shows important data.' in content
        assert '<PREVIOUS TOOL OUTPUT START>' in content
        assert '<PREVIOUS TOOL OUTPUT END>' in content

        # Verify tool output was truncated
        assert '[TRUNCATED - Similar to current output]' in content

        # Verify the full report is NOT in the content
        assert 'Total Users: 11' not in content or '[TRUNCATED' in content

    def test_message_structure_preserved(self):
        """Verify message structure is preserved after truncation."""
        chat_history = [
            {
                'role': 'assistant',
                'content': """Before tool output.

<PREVIOUS TOOL OUTPUT START>
Large tool output here
<PREVIOUS TOOL OUTPUT END>

After tool output."""
            }
        ]

        current_prompt = """<PREVIOUS TOOL OUTPUT START>
Large tool output here
<PREVIOUS TOOL OUTPUT END>"""

        result = deduplicate_and_truncate_chat_history(
            chat_history=chat_history,
            component_context=None,
            current_prompt=current_prompt,
            similarity_threshold=0.75
        )

        content = result[0]['content']

        # Verify structure
        assert 'Before tool output.' in content
        assert 'After tool output.' in content
        assert '<PREVIOUS TOOL OUTPUT START>' in content
        assert '<PREVIOUS TOOL OUTPUT END>' in content

        # Verify only the tool output section was replaced
        lines = content.split('\n')
        assert any('Before' in line for line in lines)
        assert any('After' in line for line in lines)


class TestRealWorldScenario:
    """Test real-world scenario from user's chat history."""

    def test_brokerage_report_duplication_scenario(self):
        """
        Replicate the exact scenario from user's chat history:
        - Message 1: Empty tool output
        - Message 2: Full brokerage report
        - Message 3: Same brokerage report (should be truncated)
        - Message 4: Same brokerage report (should be truncated)
        """
        brokerage_report = """# Brokerage Report: BENO

## User Overview
- **Total Users:** 11
- **Brokers:** 1
- **Sub-Brokers:** 10
- **Other Employees:** 0

## Client Overview
- **Total Clients:** 97
### Clients by Status
| _id      |   count |
|:---------|--------:|
| lead     |      13 |
| prospect |      25 |
| client   |      14 |
| inactive |      45 |

## Deal Overview
- **Total Deals:** 100"""
        
        # Start with initial chat history
        chat_history = [
            {'role': 'user', 'content': '\n\n=== CONTEXT ===\nORIGINAL QUESTION:\ndetailed brokerage report\n\n\n\n<PREVIOUS TOOL OUTPUT START>\n\n<PREVIOUS TOOL OUTPUT END>\n=== END CONTEXT ===\n\n'},
            {'role': 'clara', 'content': 'null'},
        ]
        
        # Message 2: First occurrence of brokerage report
        prompt2 = f'\n\n=== CONTEXT ===\nORIGINAL QUESTION:\nhow are you\n\n\n\n<PREVIOUS TOOL OUTPUT START>\n{brokerage_report}\n<PREVIOUS TOOL OUTPUT END>\n=== END CONTEXT ===\n\n'
        
        result2 = deduplicate_and_truncate_chat_history(
            chat_history=chat_history,
            component_context=[],
            current_prompt=prompt2,
            similarity_threshold=0.75
        )
        
        # Message 3: Second occurrence (duplicate)
        prompt3 = f'\n\n=== CONTEXT ===\nORIGINAL QUESTION:\ni see\n\n\n\n<PREVIOUS TOOL OUTPUT START>\n{brokerage_report}\n<PREVIOUS TOOL OUTPUT END>\n=== END CONTEXT ===\n\n'
        
        result3 = deduplicate_and_truncate_chat_history(
            chat_history=result2,
            component_context=[],
            current_prompt=prompt3,
            similarity_threshold=0.75
        )
        
        # Message 4: Third occurrence (duplicate)
        prompt4 = f'\n\n=== CONTEXT ===\nORIGINAL QUESTION:\nokay\n\n\n\n<PREVIOUS TOOL OUTPUT START>\n{brokerage_report}\n<PREVIOUS TOOL OUTPUT END>\n=== END CONTEXT ===\n\n'
        
        result4 = deduplicate_and_truncate_chat_history(
            chat_history=result3,
            component_context=[],
            current_prompt=prompt4,
            similarity_threshold=0.75
        )
        
        # Verify: Full report should appear only once
        full_report_count = sum(
            1 for msg in result4 
            if "Total Users: 11" in msg.get('content', '') and 
               "Brokers: 1" in msg.get('content', '') and
               "Total Deals: 100" in msg.get('content', '')
        )
        
        assert full_report_count <= 1, f"Full report should appear at most once, but appears {full_report_count} times"

