"""
Comprehensive test for character-level truncation in deduplication_utils.
Tests various output types: JSON, Plotly, Markdown, Plain text.
"""
import sys
sys.path.insert(0, 'src')

from masai.Tools.utilities.deduplication_utils import (
    deduplicate_and_truncate_chat_history
)

# Test data: Large Plotly JSON output (similar to example.txt)
LARGE_PLOTLY_OUTPUT = '''# Detailed Brokerage Report with Diagrams ## 1. User Statistics ```plotly {"data":[{"hole":0.3,"labels":["Brokers","Sub-Brokers"],"values":[1,10],"type":"pie"}],"layout":{"template":{"data":{"histogram2dcontour":[{"type":"histogram2dcontour","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"choropleth":[{"type":"choropleth","colorbar":{"outlinewidth":0,"ticks":""}}],"histogram2d":[{"type":"histogram2d","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"heatmap":[{"type":"heatmap","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"heatmapgl":[{"type":"heatmapgl","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"contourcarpet":[{"type":"contourcarpet","colorbar":{"outlinewidth":0,"ticks":""}}],"contour":[{"type":"contour","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"surface":[{"type":"surface","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"mesh3d":[{"type":"mesh3d","colorbar":{"outlinewidth":0,"ticks":""}}],"scatter":[{"fillpattern":{"fillmode":"overlay","size":10,"solidity":0.2},"type":"scatter"}],"parcoords":[{"type":"parcoords","line":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterpolargl":[{"type":"scatterpolargl","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"bar":[{"error_x":{"color":"#2a3f5f"},"error_y":{"color":"#2a3f5f"},"marker":{"line":{"color":"#E5ECF6","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"bar"}],"scattergeo":[{"type":"scattergeo","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterpolar":[{"type":"scatterpolar","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"histogram":[{"marker":{"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"histogram"}],"scattergl":[{"type":"scattergl","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatter3d":[{"type":"scatter3d","line":{"colorbar":{"outlinewidth":0,"ticks":""}},"marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scattermapbox":[{"type":"scattermapbox","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterternary":[{"type":"scatterternary","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scattercarpet":[{"type":"scattercarpet","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"carpet":[{"aaxis":{"endlinecolor":"#2a3f5f","gridcolor":"white","linecolor":"white","minorgridcolor":"white","startlinecolor":"#2a3f5f"},"baxis":{"endlinecolor":"#2a3f5f","gridcolor":"white","linecolor":"white","minorgridcolor":"white","startlinecolor":"#2a3f5f"},"type":"carpet"}],"table":[{"cells":{"fill":{"color":"#EBF0F8"},"line":{"color":"white"}},"header":{"fill":{"color":"#C8D4E3"},"line":{"color":"white"}},"type":"table"}],"barpolar":[{"marker":{"line":{"color":"#E5ECF6","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"barpolar"}],"pie":[{"automargin":true,"type":"pie"}]},"layout":{"autotypenumbers":"strict","colorway":["#636efa","#EF553B","#00cc96","#ab63fa","#FFA15A","#19d3f3","#FF6692","#B6E880","#FF97FF","#FECB52"],"font":{"color":"#2a3f5f"},"hovermode":"closest","hoverlabel":{"align":"left"},"paper_bgcolor":"white","plot_bgcolor":"#E5ECF6","polar":{"bgcolor":"#E5ECF6","angularaxis":{"gridcolor":"white","linecolor":"white","ticks":""},"radialaxis":{"gridcolor":"white","linecolor":"white","ticks":""}},"ternary":{"bgcolor":"#E5ECF6","aaxis":{"gridcolor":"white","linecolor":"white","ticks":""},"baxis":{"gridcolor":"white","linecolor":"white","ticks":""},"caxis":{"gridcolor":"white","linecolor":"white","ticks":""}},"coloraxis":{"colorbar":{"outlinewidth":0,"ticks":""}},"colorscale":{"sequential":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"sequentialminus":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"diverging":[[0,"#8e0152"],[0.1,"#c51b7d"],[0.2,"#de77ae"],[0.3,"#f1b6da"],[0.4,"#fde0ef"],[0.5,"#f7f7f7"],[0.6,"#e6f5d0"],[0.7,"#b8e186"],[0.8,"#7fbc41"],[0.9,"#4d9221"],[1,"#276419"]]},"xaxis":{"gridcolor":"white","linecolor":"white","ticks":"","title":{"standoff":15},"zerolinecolor":"white","automargin":true,"zerolinewidth":2},"yaxis":{"gridcolor":"white","linecolor":"white","ticks":"","title":{"standoff":15},"zerolinecolor":"white","automargin":true,"zerolinewidth":2},"scene":{"xaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2},"yaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2},"zaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2}},"shapedefaults":{"line":{"color":"#2a3f5f"}},"annotationdefaults":{"arrowcolor":"#2a3f5f","arrowhead":0,"arrowwidth":1},"geo":{"bgcolor":"white","landcolor":"#E5ECF6","subunitcolor":"white","showland":true,"showlakes":true,"lakecolor":"white"},"title":{"x":0.05},"mapbox":{"style":"light"}}},"title":{"text":"1.1 User Roles Distribution"},"width":600,"height":400}} ``` This is a large output with many characters.'''

def test_character_level_truncation_with_plotly():
    """Test that character-level truncation works for Plotly JSON outputs"""
    print("\n" + "=" * 80)
    print("TEST 1: Character-Level Truncation with Plotly JSON")
    print("=" * 80)
    
    # Create chat history with tool output
    chat_history = [
        {'role': 'user', 'content': 'Give me a detailed report'},
        {'role': 'assistant', 'content': f'<PREVIOUS TOOL OUTPUT START>\n{LARGE_PLOTLY_OUTPUT}\n<PREVIOUS TOOL OUTPUT END>'}
    ]
    
    # Create prompt with same tool output (simulating next query)
    current_prompt = f'<PREVIOUS TOOL OUTPUT START>\n{LARGE_PLOTLY_OUTPUT}\n<PREVIOUS TOOL OUTPUT END>'
    
    # Deduplicate and truncate
    result = deduplicate_and_truncate_chat_history(
        chat_history=chat_history,
        component_context=None,
        current_prompt=current_prompt,
        similarity_threshold=0.75
    )
    
    # Check results
    print(f"Original chat history length: {len(chat_history)}")
    print(f"Result chat history length: {len(result)}")
    
    # Find the assistant message with tool output
    assistant_msg = next((m for m in result if m['role'] == 'assistant'), None)
    if assistant_msg:
        content = assistant_msg['content']
        print(f"\nOriginal content length: {len(LARGE_PLOTLY_OUTPUT)} characters")
        print(f"Truncated content length: {len(content)} characters")
        
        # Check if truncation marker is present
        has_truncation_marker = '[TRUNCATED - Similar to current output]' in content
        print(f"Has truncation marker: {has_truncation_marker}")
        
        # Check if content is actually truncated
        is_truncated = len(content) < len(LARGE_PLOTLY_OUTPUT)
        print(f"Content is truncated: {is_truncated}")
        
        # Verify truncation is effective
        assert has_truncation_marker, "Truncation marker should be present"
        assert is_truncated, "Content should be truncated"
        assert len(content) < 1000, "Truncated content should be much smaller"
        
        print("✅ TEST PASSED: Plotly output properly truncated!")
    else:
        print("❌ TEST FAILED: No assistant message found")
        assert False

def test_character_level_truncation_with_markdown():
    """Test character-level truncation with markdown content"""
    print("\n" + "=" * 80)
    print("TEST 2: Character-Level Truncation with Markdown")
    print("=" * 80)
    
    markdown_output = "# Report\n" + "This is a very long markdown report. " * 100
    
    chat_history = [
        {'role': 'user', 'content': 'Generate report'},
        {'role': 'assistant', 'content': f'<PREVIOUS TOOL OUTPUT START>\n{markdown_output}\n<PREVIOUS TOOL OUTPUT END>'}
    ]
    
    current_prompt = f'<PREVIOUS TOOL OUTPUT START>\n{markdown_output}\n<PREVIOUS TOOL OUTPUT END>'
    
    result = deduplicate_and_truncate_chat_history(
        chat_history=chat_history,
        component_context=None,
        current_prompt=current_prompt,
        similarity_threshold=0.75
    )
    
    assistant_msg = next((m for m in result if m['role'] == 'assistant'), None)
    if assistant_msg:
        content = assistant_msg['content']
        has_truncation_marker = '[TRUNCATED - Similar to current output]' in content
        is_truncated = len(content) < len(markdown_output)
        
        print(f"Original length: {len(markdown_output)} characters")
        print(f"Truncated length: {len(content)} characters")
        print(f"Has truncation marker: {has_truncation_marker}")
        print(f"Is truncated: {is_truncated}")
        
        assert has_truncation_marker, "Truncation marker should be present"
        assert is_truncated, "Content should be truncated"
        print("✅ TEST PASSED: Markdown output properly truncated!")
    else:
        print("❌ TEST FAILED: No assistant message found")
        assert False

def test_no_truncation_for_different_outputs():
    """Test that different outputs are NOT truncated"""
    print("\n" + "=" * 80)
    print("TEST 3: No Truncation for Different Outputs")
    print("=" * 80)
    
    output1 = "Report about users and brokers"
    output2 = "Report about deals and revenue"
    
    chat_history = [
        {'role': 'assistant', 'content': f'<PREVIOUS TOOL OUTPUT START>\n{output1}\n<PREVIOUS TOOL OUTPUT END>'}
    ]
    
    current_prompt = f'<PREVIOUS TOOL OUTPUT START>\n{output2}\n<PREVIOUS TOOL OUTPUT END>'
    
    result = deduplicate_and_truncate_chat_history(
        chat_history=chat_history,
        component_context=None,
        current_prompt=current_prompt,
        similarity_threshold=0.75
    )
    
    assistant_msg = next((m for m in result if m['role'] == 'assistant'), None)
    if assistant_msg:
        content = assistant_msg['content']
        has_truncation_marker = '[TRUNCATED - Similar to current output]' in content
        
        print(f"Output 1: {output1}")
        print(f"Output 2: {output2}")
        print(f"Has truncation marker: {has_truncation_marker}")
        
        assert not has_truncation_marker, "Different outputs should NOT be truncated"
        print("✅ TEST PASSED: Different outputs not truncated!")
    else:
        print("❌ TEST FAILED: No assistant message found")
        assert False

if __name__ == "__main__":
    test_character_level_truncation_with_plotly()
    test_character_level_truncation_with_markdown()
    test_no_truncation_for_different_outputs()
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED! ✅")
    print("=" * 80)

