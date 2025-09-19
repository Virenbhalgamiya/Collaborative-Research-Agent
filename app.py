import streamlit as st
from agents import fetch_papers, summarize_text, check_similarity, synthesize_review

# Add imports for visualization
import networkx as nx
import matplotlib.pyplot as plt

st.set_page_config(page_title="Collaborative Research Agent", layout="wide")
st.title("🤖 Collaborative Research Agent")

st.write("""
This agent fetches academic papers from **Arxiv**, summarizes them, checks for contradictions, 
and synthesizes a mini literature review.
""")

query = st.text_input("Enter research topic:", "AI in Education")
max_papers = st.number_input("Max papers to fetch:", min_value=1, max_value=20, value=5)
num_papers = st.slider("Number of papers to fetch:", min_value=1, max_value=int(max_papers), value=min(3, int(max_papers)))

if st.button("Generate Review"):
    with st.spinner("Fetching and processing papers..."):
        papers = fetch_papers(query, max_results=num_papers)
        summaries = []

        for p in papers:
            summary = summarize_text(p.summary)
            summaries.append(summary)

        # Check contradictions and similarities
        contradictions = []
        similarities = []
        for i in range(len(summaries)):
            for j in range(i+1, len(summaries)):
                score = check_similarity(summaries[i], summaries[j])
                similarities.append((i, j, score))
                if score < 0.4:
                    contradictions.append((i, j, score))

        # Synthesized review
        synthesized = synthesize_review(summaries)

    # Display results
    st.subheader("📄 Papers Found")
    for idx, p in enumerate(papers):
        st.markdown(f"**{idx+1}. {p.title}**")
        st.write(f"*Authors:* {', '.join([a.name for a in p.authors])}")
        st.write(f"*Published:* {p.published.date()}")
        st.write(f"*Summary:* {summaries[idx]}")
        st.write("---")

    st.subheader("🧠 Synthesized Mini-Review")
    st.write(synthesized)

    if contradictions:
        st.subheader("⚠️ Possible Contradictions")
        for c in contradictions:
            st.write(f"Paper {c[0]+1} and Paper {c[1]+1} similarity: {c[2]:.2f}")
    else:
        st.success("No major contradictions detected!")

    # Visualization
    st.subheader("📊 Paper Relationship Graph")
    G = nx.Graph()
    for idx, p in enumerate(papers):
        G.add_node(idx, label=p.title[:30] + ("..." if len(p.title) > 30 else ""))  # Shorten long titles

    for i, j, score in similarities:
        color = "red" if score < 0.4 else "green"
        width = 3 if color == "red" else 1
        G.add_edge(i, j, weight=score, color=color, width=width)

    pos = nx.spring_layout(G, seed=42)
    edge_colors = [G[u][v]['color'] for u, v in G.edges()]
    edge_widths = [G[u][v]['width'] for u, v in G.edges()]
    node_labels = {i: G.nodes[i]['label'] for i in G.nodes()}

    plt.figure(figsize=(10, 7))
    nx.draw_networkx_nodes(G, pos, node_color='skyblue', node_size=1200)
    nx.draw_networkx_edges(G, pos, edge_color=edge_colors, width=edge_widths)
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=9)

    # Legend
    import matplotlib.patches as mpatches
    red_patch = mpatches.Patch(color='red', label='Contradiction (<0.4 similarity)')
    green_patch = mpatches.Patch(color='green', label='Similarity (>=0.4)')
    plt.legend(handles=[red_patch, green_patch], loc='upper left')

    plt.axis('off')
    st.pyplot(plt)
st.write("### Note: This is a prototype. Results may vary based on the input topic and number of papers.")