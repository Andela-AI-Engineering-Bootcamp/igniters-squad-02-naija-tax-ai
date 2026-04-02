# Finance Act text for `query_tax_law`

Place plain-text (`.txt`) or Markdown (`.md` renamed to `.txt`) excerpts of the **Nigerian Finance Acts** and related official tax law sources in this directory.

- Convert PDFs from official sources to text offline; do not commit copyrighted full acts unless your license allows it.
- On first `query_nigerian_tax_law` call, the MCP server ingests all `*.txt` files here into a local ChromaDB store under `.cache/chroma_tax_law`.
- Ingestion runs only when the collection is empty. To re-index after adding files, delete the directory `.cache/chroma_tax_law` and query again.

The sample file `finance_act_sample.txt` is a tiny placeholder for local smoke tests only.
