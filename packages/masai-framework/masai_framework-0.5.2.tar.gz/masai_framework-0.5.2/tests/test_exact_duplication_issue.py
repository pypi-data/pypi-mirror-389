"""
Test to replicate the EXACT duplication issue from the user's chat history.
The brokerage report is wrapped in different formatting each time.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.masai.GenerativeModel.generativeModels import MASGenerativeModel


class TestExactDuplicationIssue:
    """Test the exact duplication issue with formatted prompts."""
    
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
    async def test_exact_user_scenario_with_formatted_prompts(self, mas_model):
        """
        Replicate the EXACT scenario from user's chat history.
        The brokerage report is wrapped in === CONTEXT === formatting.
        """
        
        # The brokerage report content (core data)
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
- **Total Deals:** 100
### Deals by Stage
| Stage          |   Count | Expected Value   | Closed Value   |
|:---------------|--------:|:-----------------|:---------------|
| Closed Won     |      37 | $0.00            | $0.00          |
| Negotiation    |       6 | $0.00            | $0.00          |
| Qualification  |      12 | $0.00            | $0.00          |
| Needs Analysis |       5 | $0.00            | $0.00          |
| Proposal       |       1 | $0.00            | $0.00          |
| Closed Lost    |      39 | $0.00            | $0.00          |

## Policy Overview
- **Total Policies:** 8
### Policies by Status
| _id      |   count |
|:---------|--------:|
| archived |       1 |
| draft    |       2 |
| active   |       5 |

## Revenue Overview
- **Total Expected Commission:** $6,614,383.32
- **Total Paid Commission:** $313,000.14

## Task Overview
- **Total Tasks:** 3
### Tasks by Status
| _id       |   count |
|:----------|--------:|
| completed |       1 |
| pending   |       2 |"""
        
        # Prompt 1: "how are you" with brokerage report
        prompt_1 = f"""

=== CONTEXT ===
ORIGINAL QUESTION:
how are you



<PREVIOUS TOOL OUTPUT START>
{brokerage_report}
<PREVIOUS TOOL OUTPUT END>
=== END CONTEXT ===

"""
        
        # Prompt 2: "i see" with SAME brokerage report (slightly different formatting)
        prompt_2 = f"""

=== CONTEXT ===
ORIGINAL QUESTION:
i see



<PREVIOUS TOOL OUTPUT START>
{brokerage_report}
<PREVIOUS TOOL OUTPUT END>
=== END CONTEXT ===

"""
        
        # Prompt 3: "okay" with SAME brokerage report
        prompt_3 = f"""

=== CONTEXT ===
ORIGINAL QUESTION:
okay



<PREVIOUS TOOL OUTPUT START>
{brokerage_report}
<PREVIOUS TOOL OUTPUT END>
=== END CONTEXT ===

"""
        
        # Initialize chat history
        mas_model.chat_history = [
            {'role': 'user', 'content': 'detailed brokerage report'},
            {'role': 'clara', 'content': 'null'},
        ]

        print("\n" + "="*80)
        print("INITIAL CHAT HISTORY LENGTH:", len(mas_model.chat_history))
        print("="*80)

        # Call 1: Simulate adding prompt_1 to chat history (like generate_response_mas does)
        print("\n--- CALL 1: Adding prompt_1 with brokerage report ---")
        is_dup_1 = False
        for history_msg in mas_model.chat_history:
            if mas_model._is_content_duplicate(prompt_1, history_msg.get('content', '')):
                is_dup_1 = True
                break

        if not is_dup_1:
            mas_model.chat_history.append({'role': 'user', 'content': prompt_1})

        history_length_after_call_1 = len(mas_model.chat_history)
        print(f"Chat history length after call 1: {history_length_after_call_1}")
        print(f"Prompt 1 was duplicate: {is_dup_1}")

        # Count brokerage report occurrences
        report_count_1 = sum(1 for msg in mas_model.chat_history if "Brokerage Report: BENO" in msg.get('content', ''))
        print(f"Brokerage report occurrences: {report_count_1}")

        # Call 2: Simulate adding prompt_2 (SAME report, different question)
        print("\n--- CALL 2: Adding prompt_2 with SAME brokerage report ---")
        is_dup_2 = False
        for history_msg in mas_model.chat_history:
            if mas_model._is_content_duplicate(prompt_2, history_msg.get('content', '')):
                is_dup_2 = True
                break

        if not is_dup_2:
            mas_model.chat_history.append({'role': 'user', 'content': prompt_2})

        history_length_after_call_2 = len(mas_model.chat_history)
        print(f"Chat history length after call 2: {history_length_after_call_2}")
        print(f"Prompt 2 was duplicate: {is_dup_2}")

        # Count brokerage report occurrences
        report_count_2 = sum(1 for msg in mas_model.chat_history if "Brokerage Report: BENO" in msg.get('content', ''))
        print(f"Brokerage report occurrences: {report_count_2}")

        # Call 3: Simulate adding prompt_3 (SAME report, different question)
        print("\n--- CALL 3: Adding prompt_3 with SAME brokerage report ---")
        is_dup_3 = False
        for history_msg in mas_model.chat_history:
            if mas_model._is_content_duplicate(prompt_3, history_msg.get('content', '')):
                is_dup_3 = True
                break

        if not is_dup_3:
            mas_model.chat_history.append({'role': 'user', 'content': prompt_3})

        history_length_after_call_3 = len(mas_model.chat_history)
        print(f"Chat history length after call 3: {history_length_after_call_3}")
        print(f"Prompt 3 was duplicate: {is_dup_3}")

        # Count brokerage report occurrences
        report_count_3 = sum(1 for msg in mas_model.chat_history if "Brokerage Report: BENO" in msg.get('content', ''))
        print(f"Brokerage report occurrences: {report_count_3}")
        
        print("\n" + "="*80)
        print("FINAL RESULTS:")
        print(f"  Initial history length: 2")
        print(f"  After call 1: {history_length_after_call_1}")
        print(f"  After call 2: {history_length_after_call_2}")
        print(f"  After call 3: {history_length_after_call_3}")
        print(f"  Total brokerage report occurrences: {report_count_3}")
        print("="*80)
        
        # Assertions
        # The report should appear only ONCE, not 3 times
        assert report_count_3 == 1, \
            f"❌ FAILED: Report appears {report_count_3} times, should appear 1 time"
        
        print("\n✅ TEST PASSED: Brokerage report appears only once!")

