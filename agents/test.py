import arxiv

search = arxiv.Search(
    query="cat:gr-qc OR cat:astro-ph.CO OR cat:hep-th",
    max_results=3
)

for result in search.results():
    print(result.primary_category, result.categories)
