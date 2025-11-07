"""
Test with user's exact scenario to understand the duplication issue.
"""
import pytest
from src.masai.Tools.utilities.deduplication_utils import deduplicate_and_truncate_chat_history

BROKERAGE_REPORT = """## Brokerage Report: BENO
**Company Name:** BENO
**Status:** Activated

### Team Overview
**Total Users:** 11
- **Brokers (Owners):** 1
- **Sub-Brokers (Sales Agents):** 10
- **Admins:** 0
- **Other Employees:** 0

### Clients Overview
**Total Clients:** 97

### Deals Overview
**Total Deals:** 100
**Deals by Stage:**
- Closed-Lost: 39
- Closed-Won: 37
- Qualification: 12
- Negotiation: 6
- Needs-Analysis: 5
- Proposal: 1

### Revenues Overview
**Total Expected Commission:** $6,614,383.32
**Total Paid Commission:** $313,000.14

### Policies Overview
**Total Policies:** 8

### Tasks Overview
**Total Tasks:** 3
**Tasks by Status:**
- Pending: 2
- Completed: 1"""


def test_user_scenario_multiple_queries():
    """
    Simulate user's exact scenario:
    1. Query: "Now tell me what is the time" → Tool output: Brokerage Report
    2. Query: "nice" → Tool output: Same Brokerage Report
    3. Query: "give me bid brokerage report" → Tool output: Same Brokerage Report
    4. Query: "good" → Tool output: Same Brokerage Report
    5. Query: "yeah" → Tool output: Same Brokerage Report
    """
    
    # Initial chat history (empty)
    chat_history = []
    
    # Query 1: "Now tell me what is the time"
    prompt_1 = f"=== CONTEXT ===\nORIGINAL QUESTION: Now tell me what is the time\n<PREVIOUS TOOL OUTPUT START>\n{BROKERAGE_REPORT}\n<PREVIOUS TOOL OUTPUT END>\n=== END CONTEXT ==="
    
    # Add to chat history (simulating what happens in response method)
    chat_history.append({'role': 'user', 'content': prompt_1})
    chat_history.append({'role': 'assistant', 'content': 'The current time is Monday, October 27, 2025, 02:07 PM.'})
    
    # Deduplicate after adding (as per new fix)
    chat_history = deduplicate_and_truncate_chat_history(
        chat_history=chat_history,
        component_context=None,
        current_prompt=prompt_1,
        similarity_threshold=0.75
    )
    
    print("\n=== After Query 1 ===")
    print(f"Chat history length: {len(chat_history)}")
    for i, msg in enumerate(chat_history):
        content_preview = msg['content'][:100] if len(msg['content']) > 100 else msg['content']
        print(f"{i}: {msg['role']} - {content_preview}...")
    
    # Query 2: "nice"
    prompt_2 = f"=== CONTEXT ===\nORIGINAL QUESTION: nice\n<PREVIOUS TOOL OUTPUT START>\n{BROKERAGE_REPORT}\n<PREVIOUS TOOL OUTPUT END>\n=== END CONTEXT ==="
    
    chat_history.append({'role': 'user', 'content': prompt_2})
    chat_history.append({'role': 'assistant', 'content': 'Glad you found the report useful!'})
    
    chat_history = deduplicate_and_truncate_chat_history(
        chat_history=chat_history,
        component_context=None,
        current_prompt=prompt_2,
        similarity_threshold=0.75
    )
    
    print("\n=== After Query 2 ===")
    print(f"Chat history length: {len(chat_history)}")
    for i, msg in enumerate(chat_history):
        content_preview = msg['content'][:100] if len(msg['content']) > 100 else msg['content']
        print(f"{i}: {msg['role']} - {content_preview}...")
    
    # Query 3: "give me bid brokerage report"
    prompt_3 = f"=== CONTEXT ===\nORIGINAL QUESTION: give me bid brokerage report\n<PREVIOUS TOOL OUTPUT START>\n{BROKERAGE_REPORT}\n<PREVIOUS TOOL OUTPUT END>\n=== END CONTEXT ==="
    
    chat_history.append({'role': 'user', 'content': prompt_3})
    chat_history.append({'role': 'assistant', 'content': 'I am generating a comprehensive brokerage report for you.'})
    
    chat_history = deduplicate_and_truncate_chat_history(
        chat_history=chat_history,
        component_context=None,
        current_prompt=prompt_3,
        similarity_threshold=0.75
    )
    
    print("\n=== After Query 3 ===")
    print(f"Chat history length: {len(chat_history)}")
    for i, msg in enumerate(chat_history):
        content_preview = msg['content'][:100] if len(msg['content']) > 100 else msg['content']
        print(f"{i}: {msg['role']} - {content_preview}...")
    
    # Query 4: "good"
    prompt_4 = f"=== CONTEXT ===\nORIGINAL QUESTION: good\n<PREVIOUS TOOL OUTPUT START>\n{BROKERAGE_REPORT}\n<PREVIOUS TOOL OUTPUT END>\n=== END CONTEXT ==="
    
    chat_history.append({'role': 'user', 'content': prompt_4})
    chat_history.append({'role': 'assistant', 'content': 'Glad you found the report useful!'})
    
    chat_history = deduplicate_and_truncate_chat_history(
        chat_history=chat_history,
        component_context=None,
        current_prompt=prompt_4,
        similarity_threshold=0.75
    )
    
    print("\n=== After Query 4 ===")
    print(f"Chat history length: {len(chat_history)}")
    for i, msg in enumerate(chat_history):
        content_preview = msg['content'][:100] if len(msg['content']) > 100 else msg['content']
        print(f"{i}: {msg['role']} - {content_preview}...")
    
    # Query 5: "yeah"
    prompt_5 = f"=== CONTEXT ===\nORIGINAL QUESTION: yeah\n<PREVIOUS TOOL OUTPUT START>\n{BROKERAGE_REPORT}\n<PREVIOUS TOOL OUTPUT END>\n=== END CONTEXT ==="
    
    chat_history.append({'role': 'user', 'content': prompt_5})
    chat_history.append({'role': 'assistant', 'content': 'Is there anything else I can help you with?'})
    
    chat_history = deduplicate_and_truncate_chat_history(
        chat_history=chat_history,
        component_context=None,
        current_prompt=prompt_5,
        similarity_threshold=0.75
    )
    
    print("\n=== After Query 5 (FINAL) ===")
    print(f"Chat history length: {len(chat_history)}")
    for i, msg in enumerate(chat_history):
        content_preview = msg['content'][:150] if len(msg['content']) > 150 else msg['content']
        print(f"{i}: {msg['role']} - {content_preview}...")
    
    # Count how many times the brokerage report appears
    brokerage_count = 0
    truncated_count = 0
    full_report_lines = 0

    print(f"\n=== DETAILED ANALYSIS ===")
    for i, msg in enumerate(chat_history):
        if 'Company Name' in msg['content'] and 'BENO' in msg['content']:
            brokerage_count += 1
            # Count lines in the report
            lines = msg['content'].count('\n')
            full_report_lines += lines
            print(f"Message {i}: Contains FULL brokerage report ({lines} lines)")

        if '[TRUNCATED - Similar to current output]' in msg['content']:
            truncated_count += 1
            print(f"Message {i}: Contains TRUNCATED marker")

    print(f"\n=== SUMMARY ===")
    print(f"Full brokerage reports: {brokerage_count}")
    print(f"Truncated reports: {truncated_count}")
    print(f"Total lines in full reports: {full_report_lines}")
    print(f"Total messages: {len(chat_history)}")

    # The issue: are we still seeing duplicates?
    print(f"\n=== ISSUE ===")
    if brokerage_count > 1:
        print(f"PROBLEM: {brokerage_count} full brokerage reports found!")
        print(f"   Expected: At most 1 full report + truncated versions")
        print(f"\n=== FIRST MESSAGE CONTENT ===")
        print(chat_history[0]['content'][:500])
    else:
        print(f"OK: Only 1 full brokerage report")


if __name__ == "__main__":
    test_user_scenario_multiple_queries()

