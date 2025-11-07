"""
Test that simulates the exact scenario from example.txt:
Multiple queries with large Plotly/JSON outputs that should be truncated.
"""
import sys
sys.path.insert(0, 'src')

from masai.Tools.utilities.deduplication_utils import (
    deduplicate_and_truncate_chat_history
)

# Simulated large Plotly output (similar to example.txt)
LARGE_PLOTLY_OUTPUT = '''# Detailed Brokerage Report with Diagrams ## 1. User Statistics ```plotly {"data":[{"hole":0.3,"labels":["Brokers","Sub-Brokers"],"values":[1,10],"type":"pie"}],"layout":{"template":{"data":{"histogram2dcontour":[{"type":"histogram2dcontour","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"choropleth":[{"type":"choropleth","colorbar":{"outlinewidth":0,"ticks":""}}],"histogram2d":[{"type":"histogram2d","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"heatmap":[{"type":"heatmap","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"heatmapgl":[{"type":"heatmapgl","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"contourcarpet":[{"type":"contourcarpet","colorbar":{"outlinewidth":0,"ticks":""}}],"contour":[{"type":"contour","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"surface":[{"type":"surface","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"mesh3d":[{"type":"mesh3d","colorbar":{"outlinewidth":0,"ticks":""}}],"scatter":[{"fillpattern":{"fillmode":"overlay","size":10,"solidity":0.2},"type":"scatter"}],"parcoords":[{"type":"parcoords","line":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterpolargl":[{"type":"scatterpolargl","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"bar":[{"error_x":{"color":"#2a3f5f"},"error_y":{"color":"#2a3f5f"},"marker":{"line":{"color":"#E5ECF6","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"bar"}],"scattergeo":[{"type":"scattergeo","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterpolar":[{"type":"scatterpolar","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"histogram":[{"marker":{"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"histogram"}],"scattergl":[{"type":"scattergl","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatter3d":[{"type":"scatter3d","line":{"colorbar":{"outlinewidth":0,"ticks":""}},"marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scattermapbox":[{"type":"scattermapbox","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterternary":[{"type":"scatterternary","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scattercarpet":[{"type":"scattercarpet","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"carpet":[{"aaxis":{"endlinecolor":"#2a3f5f","gridcolor":"white","linecolor":"white","minorgridcolor":"white","startlinecolor":"#2a3f5f"},"baxis":{"endlinecolor":"#2a3f5f","gridcolor":"white","linecolor":"white","minorgridcolor":"white","startlinecolor":"#2a3f5f"},"type":"carpet"}],"table":[{"cells":{"fill":{"color":"#EBF0F8"},"line":{"color":"white"}},"header":{"fill":{"color":"#C8D4E3"},"line":{"color":"white"}},"type":"table"}],"barpolar":[{"marker":{"line":{"color":"#E5ECF6","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"barpolar"}],"pie":[{"automargin":true,"type":"pie"}]},"layout":{"autotypenumbers":"strict","colorway":["#636efa","#EF553B","#00cc96","#ab63fa","#FFA15A","#19d3f3","#FF6692","#B6E880","#FF97FF","#FECB52"],"font":{"color":"#2a3f5f"},"hovermode":"closest","hoverlabel":{"align":"left"},"paper_bgcolor":"white","plot_bgcolor":"#E5ECF6","polar":{"bgcolor":"#E5ECF6","angularaxis":{"gridcolor":"white","linecolor":"white","ticks":""},"radialaxis":{"gridcolor":"white","linecolor":"white","ticks":""}},"ternary":{"bgcolor":"#E5ECF6","aaxis":{"gridcolor":"white","linecolor":"white","ticks":""},"baxis":{"gridcolor":"white","linecolor":"white","ticks":""},"caxis":{"gridcolor":"white","linecolor":"white","ticks":""}},"coloraxis":{"colorbar":{"outlinewidth":0,"ticks":""}},"colorscale":{"sequential":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"sequentialminus":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"diverging":[[0,"#8e0152"],[0.1,"#c51b7d"],[0.2,"#de77ae"],[0.3,"#f1b6da"],[0.4,"#fde0ef"],[0.5,"#f7f7f7"],[0.6,"#e6f5d0"],[0.7,"#b8e186"],[0.8,"#7fbc41"],[0.9,"#4d9221"],[1,"#276419"]]},"xaxis":{"gridcolor":"white","linecolor":"white","ticks":"","title":{"standoff":15},"zerolinecolor":"white","automargin":true,"zerolinewidth":2},"yaxis":{"gridcolor":"white","linecolor":"white","ticks":"","title":{"standoff":15},"zerolinecolor":"white","automargin":true,"zerolinewidth":2},"scene":{"xaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2},"yaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2},"zaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2}},"shapedefaults":{"line":{"color":"#2a3f5f"}},"annotationdefaults":{"arrowcolor":"#2a3f5f","arrowhead":0,"arrowwidth":1},"geo":{"bgcolor":"white","landcolor":"#E5ECF6","subunitcolor":"white","showland":true,"showlakes":true,"lakecolor":"white"},"title":{"x":0.05},"mapbox":{"style":"light"}}},"title":{"text":"1.1 User Roles Distribution"},"width":600,"height":400}} ``` This is a large output with many characters.'''

def test_multiple_queries_with_same_output():
    """
    Simulate the exact scenario from example.txt:
    - Query 1: "give me detailed brokerage report" -> returns LARGE_PLOTLY_OUTPUT
    - Query 2: "with 20 diagrams" -> returns LARGE_PLOTLY_OUTPUT (same)
    - Query 3: "hmm" -> returns LARGE_PLOTLY_OUTPUT (same)
    
    Expected: Each subsequent query should truncate the previous output
    """
    print("\n" + "=" * 80)
    print("TEST: Multiple Queries with Same Output (example.txt scenario)")
    print("=" * 80)
    
    chat_history = []
    
    # Query 1
    print("\n--- Query 1: 'give me detailed brokerage report' ---")
    chat_history.append({'role': 'user', 'content': 'give me detailed brokerage report'})
    prompt1 = f'<PREVIOUS TOOL OUTPUT START>\n{LARGE_PLOTLY_OUTPUT}\n<PREVIOUS TOOL OUTPUT END>'
    chat_history.append({'role': 'assistant', 'content': f'<PREVIOUS TOOL OUTPUT START>\n{LARGE_PLOTLY_OUTPUT}\n<PREVIOUS TOOL OUTPUT END>'})
    
    print(f"Chat history size: {sum(len(m['content']) for m in chat_history)} characters")
    print(f"Last message size: {len(chat_history[-1]['content'])} characters")
    
    # Query 2
    print("\n--- Query 2: 'with 20 diagrams' ---")
    prompt2 = f'<PREVIOUS TOOL OUTPUT START>\n{LARGE_PLOTLY_OUTPUT}\n<PREVIOUS TOOL OUTPUT END>'
    chat_history = deduplicate_and_truncate_chat_history(
        chat_history=chat_history,
        component_context=None,
        current_prompt=prompt2,
        similarity_threshold=0.75
    )
    chat_history.append({'role': 'user', 'content': 'with 20 diagrams'})
    chat_history.append({'role': 'assistant', 'content': f'<PREVIOUS TOOL OUTPUT START>\n{LARGE_PLOTLY_OUTPUT}\n<PREVIOUS TOOL OUTPUT END>'})
    
    print(f"Chat history size: {sum(len(m['content']) for m in chat_history)} characters")
    print(f"Last message size: {len(chat_history[-1]['content'])} characters")
    
    # Check if first assistant message was truncated
    first_assistant = next((m for i, m in enumerate(chat_history) if m['role'] == 'assistant' and i < 2), None)
    if first_assistant:
        has_truncation = '[TRUNCATED - Similar to current output]' in first_assistant['content']
        print(f"First assistant message truncated: {has_truncation}")
        assert has_truncation, "First assistant message should be truncated"
    
    # Query 3
    print("\n--- Query 3: 'hmm' ---")
    prompt3 = f'<PREVIOUS TOOL OUTPUT START>\n{LARGE_PLOTLY_OUTPUT}\n<PREVIOUS TOOL OUTPUT END>'
    chat_history = deduplicate_and_truncate_chat_history(
        chat_history=chat_history,
        component_context=None,
        current_prompt=prompt3,
        similarity_threshold=0.75
    )
    chat_history.append({'role': 'user', 'content': 'hmm'})
    chat_history.append({'role': 'assistant', 'content': f'<PREVIOUS TOOL OUTPUT START>\n{LARGE_PLOTLY_OUTPUT}\n<PREVIOUS TOOL OUTPUT END>'})

    print(f"Chat history size: {sum(len(m['content']) for m in chat_history)} characters")
    print(f"Last message size: {len(chat_history[-1]['content'])} characters")

    # Count truncated messages
    truncated_count = sum(1 for m in chat_history if '[TRUNCATED - Similar to current output]' in m.get('content', ''))
    print(f"\nTotal truncated messages: {truncated_count}")

    # Verify truncation is working
    # Note: Truncation happens when the NEXT prompt comes in, so after Query 3 deduplication,
    # we should have at least 1 truncated message (from Query 2)
    assert truncated_count >= 1, "At least 1 message should be truncated"
    
    # Verify total size is reasonable (not accumulating full outputs)
    total_size = sum(len(m['content']) for m in chat_history)
    original_full_size = len(LARGE_PLOTLY_OUTPUT) * 3  # 3 full outputs
    
    print(f"Total chat history size: {total_size} characters")
    print(f"If all 3 outputs were full: {original_full_size} characters")
    print(f"Savings: {original_full_size - total_size} characters ({100 * (original_full_size - total_size) / original_full_size:.1f}%)")
    
    assert total_size < original_full_size * 0.5, "Should save at least 50% of space"
    
    print("\n✅ TEST PASSED: Multiple queries properly truncate similar outputs!")

if __name__ == "__main__":
    test_multiple_queries_with_same_output()
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED! ✅")
    print("=" * 80)

