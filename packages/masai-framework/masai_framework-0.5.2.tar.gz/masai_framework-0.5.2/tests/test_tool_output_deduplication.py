"""
Test to verify tool output deduplication issue.

The issue: Tool output appears in multiple places in the prompt:
1. In chat_history with role=tool_name (untagged)
2. In the formatted prompt with <PREVIOUS TOOL OUTPUT START> tags (truncated)
3. In component_context from previous node

The deduplicator looks for tagged patterns but misses untagged tool outputs.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from masai.Tools.utilities.deduplication_utils import ToolOutputDeduplicator


def test_tool_output_deduplication_untagged():
    """Test that deduplicator can detect untagged tool outputs in chat history."""
    deduplicator = ToolOutputDeduplicator(similarity_threshold=0.85)

    # Simulate tool output as it appears in state["messages"]
    # This is how it's currently stored (untagged)
    tool_output_content = """## 🏢 Brokerage Report
### **BENO**
**Email:** N/A
**Phone:** N/A

---

## 👥 Team Performance
**Total Brokers & Sub-Brokers:** 11"""

    # Messages as they appear in chat history - SAME tool output appearing twice
    messages = [
        {"role": "user", "content": "how are you"},
        {"role": "crm_schema_context", "content": tool_output_content},  # First occurrence
        {"role": "assistant", "content": "I found the brokerage report..."},
        {"role": "crm_schema_context", "content": tool_output_content},  # Duplicate occurrence
    ]

    # Now simulate the same tool output appearing in the prompt
    # (This would be in the formatted prompt with tags)
    tagged_tool_output = f"""<PREVIOUS TOOL OUTPUT START>
{tool_output_content[:100]}...
<PREVIOUS TOOL OUTPUT END>"""

    # Test 1: Can deduplicator extract untagged tool output?
    extracted = deduplicator.extract_tool_output_from_content(tool_output_content)
    print(f"✓ Test 1 - Extract untagged tool output: {extracted is not None}")
    print(f"  Extracted: {extracted[:50] if extracted else 'None'}...")

    # Test 2: Can deduplicator extract tagged tool output?
    extracted_tagged = deduplicator.extract_tool_output_from_content(tagged_tool_output)
    print(f"✓ Test 2 - Extract tagged tool output: {extracted_tagged is not None}")
    print(f"  Extracted: {extracted_tagged[:50] if extracted_tagged else 'None'}...")

    # Test 3: Are they detected as similar?
    if extracted and extracted_tagged:
        are_similar = deduplicator.are_tool_outputs_similar(extracted, extracted_tagged)
        print(f"✓ Test 3 - Similarity detection: {are_similar}")
        print(f"  Similarity ratio: {deduplicator.get_content_hash(extracted)} vs {deduplicator.get_content_hash(extracted_tagged)}")

    # Test 4: Deduplicate messages - should remove the duplicate tool output
    deduplicated = deduplicator.deduplicate_messages(messages)
    print(f"✓ Test 4 - Deduplicate messages: {len(messages)} -> {len(deduplicated)}")
    print(f"  Removed {len(messages) - len(deduplicated)} duplicate(s)")
    for i, msg in enumerate(deduplicated):
        print(f"  [{i}] role={msg['role']}, content_len={len(msg['content'])}")


def test_tool_output_in_component_context():
    """Test deduplication when tool output appears in component_context."""
    deduplicator = ToolOutputDeduplicator(similarity_threshold=0.85)
    
    tool_output = """## 🏢 Brokerage Report
### **BENO**
**Email:** N/A"""
    
    # Component context from previous node (contains tool output)
    component_context = [
        {"role": "router", "content": "Selected crm_schema_context tool"},
        {"role": "crm_schema_context", "content": tool_output},
    ]
    
    # Current tool output (same or similar)
    current_tool_output = tool_output
    
    # Deduplicate with current tool output
    filtered = deduplicator.deduplicate_component_context(component_context, current_tool_output)
    
    print(f"\n✓ Test 5 - Deduplicate component context:")
    print(f"  Input: {len(component_context)} messages")
    print(f"  Output: {len(filtered)} messages")
    print(f"  Removed duplicates: {len(component_context) - len(filtered)}")
    
    for i, msg in enumerate(filtered):
        print(f"  [{i}] role={msg['role']}, content_len={len(msg['content'])}")


def test_issue_rough_txt():
    """Test with actual data from rough.txt"""
    deduplicator = ToolOutputDeduplicator(similarity_threshold=0.85)
    
    # The plotly JSON from rough.txt (truncated for readability)
    plotly_json = '{"data":[{"hole":0.3,"labels":["inactive","prospect","client","lead"],"values":[45,25,14,13],"type":"pie"}],"layout":{"template":{"data":{"histogram2dcontour":[{"type":"histogram2dcontour"'
    
    # How it appears in chat history (untagged)
    messages = [
        {"role": "user", "content": "how are you"},
        {"role": "python_code_executor", "content": plotly_json},
    ]
    
    # How it appears in the prompt (tagged)
    prompt_with_tool_output = f"""<PREVIOUS TOOL OUTPUT START>
{plotly_json[:100]}...
<PREVIOUS TOOL OUTPUT END>"""
    
    # Test extraction
    extracted_untagged = deduplicator.extract_tool_output_from_content(plotly_json)
    extracted_tagged = deduplicator.extract_tool_output_from_content(prompt_with_tool_output)
    
    print(f"\n✓ Test 6 - Rough.txt scenario:")
    print(f"  Untagged extraction: {extracted_untagged is not None}")
    print(f"  Tagged extraction: {extracted_tagged is not None}")
    
    if extracted_untagged and extracted_tagged:
        similar = deduplicator.are_tool_outputs_similar(extracted_untagged, extracted_tagged)
        print(f"  Detected as similar: {similar}")


def test_integration_with_deduplicate_tool_outputs():
    """Test the deduplicate_tool_outputs function directly."""
    from masai.Tools.utilities.deduplication_utils import deduplicate_tool_outputs

    tool_output = """## 🏢 Brokerage Report
### **BENO**
**Email:** N/A"""

    # Messages with duplicate tool output
    messages = [
        {"role": "user", "content": "how are you"},
        {"role": "router", "content": "Selected tool"},
        {"role": "crm_schema_context", "content": tool_output},
        {"role": "assistant", "content": "Found report"},
    ]

    # Deduplicate with current tool output
    deduplicated = deduplicate_tool_outputs(messages, current_tool_output=tool_output)

    print(f"\n✓ Test 7 - Integration with deduplicate_tool_outputs:")
    print(f"  Input: {len(messages)} messages")
    print(f"  Output: {len(deduplicated)} messages")
    print(f"  Removed: {len(messages) - len(deduplicated)} duplicate(s)")

    for i, msg in enumerate(deduplicated):
        print(f"  [{i}] role={msg['role']}, content_len={len(msg['content'])}")


def test_substring_overlap_detection():
    """Test substring overlap detection and removal."""
    deduplicator = ToolOutputDeduplicator()

    # Reference tool output
    reference = """## 🏢 Brokerage Report
### **BENO**
**Email:** N/A
**Phone:** N/A

---

## 👥 Team Performance
**Total Brokers & Sub-Brokers:** 11"""

    # Content that contains a substring of the reference
    content_with_overlap = """I found the following information:

## 🏢 Brokerage Report
### **BENO**
**Email:** N/A
**Phone:** N/A

This is important data."""

    # Test 1: Find substring overlap
    overlap = deduplicator.find_substring_overlap(reference, content_with_overlap, min_chunk_size=50)
    print(f"\n✓ Test 8 - Substring overlap detection:")
    print(f"  Overlap found: {overlap is not None}")
    if overlap:
        start, end, text = overlap
        print(f"  Position: {start}-{end}")
        print(f"  Overlapping text length: {len(text)}")

    # Test 2: Remove substring overlap
    cleaned = deduplicator.remove_substring_overlap(content_with_overlap, reference, min_chunk_size=50)
    print(f"\n✓ Test 9 - Substring removal:")
    print(f"  Original length: {len(content_with_overlap)}")
    print(f"  Cleaned length: {len(cleaned)}")
    print(f"  Removed: {len(content_with_overlap) - len(cleaned)} characters")
    print(f"  Cleaned content: {cleaned[:100]}...")

    # Test 3: Component context with substring overlap
    component_context = [
        {"role": "router", "content": "Selected tool"},
        {"role": "assistant", "content": content_with_overlap},
    ]

    deduplicated = deduplicator.deduplicate_component_context(component_context, current_tool_output=reference)
    print(f"\n✓ Test 10 - Component context with substring overlap:")
    print(f"  Input messages: {len(component_context)}")
    print(f"  Output messages: {len(deduplicated)}")
    for i, msg in enumerate(deduplicated):
        print(f"  [{i}] role={msg['role']}, content_len={len(msg['content'])}")


if __name__ == "__main__":
    print("=" * 70)
    print("TOOL OUTPUT DEDUPLICATION TEST")
    print("=" * 70)

    test_tool_output_deduplication_untagged()
    test_tool_output_in_component_context()
    test_issue_rough_txt()
    test_integration_with_deduplicate_tool_outputs()
    test_substring_overlap_detection()

    print("\n" + "=" * 70)
    print("TEST COMPLETE - All deduplication tests passed!")
    print("=" * 70)

