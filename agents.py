import arxiv
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
from fastapi import FastAPI


def fetch_papers(query, max_results=5):
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )
    return [result for result in search.results()]

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

embedder = SentenceTransformer("all-MiniLM-L6-v2")

def summarize_text(text):
    try:
        print("summaryi",summarizer(text, max_length=120, min_length=50, do_sample=False)[0])
        return summarizer(text, max_length=120, min_length=50, do_sample=False)[0]['summary_text']
    except Exception:
        return text[:200]  # fallback if too long

def check_similarity(summary1, summary2):
    emb1 = embedder.encode(summary1, convert_to_tensor=True)
    emb2 = embedder.encode(summary2, convert_to_tensor=True)
    score = util.pytorch_cos_sim(emb1, emb2)
    return float(score)


def synthesize_review(summaries):
    combined = " ".join(summaries)
    return summarizer(combined, max_length=200, min_length=80, do_sample=False)[0]['summary_text']


app = FastAPI()

@app.get("/literature_review/")
def literature_review(query: str, max_papers: int = 3):
    papers = fetch_papers(query, max_results=max_papers)
    summaries = []

    for p in papers:
        summary = summarize_text(p.summary)
        summaries.append(summary)

    # Fact-check similarity (basic version)
    contradictions = []
    for i in range(len(summaries)):
        for j in range(i+1, len(summaries)):
            score = check_similarity(summaries[i], summaries[j])
            if score < 0.4:  # threshold for possible contradiction
                contradictions.append((i, j, score))

    # Synthesized review
    review = synthesize_review(summaries)

    return {
        "query": query,
        "papers": [p.title for p in papers],
        "summaries": summaries,
        "synthesized_review": review,
        "contradictions": contradictions
    }