"""
Test the query_file_chunks function after seeding.

Usage:
    python -m scripts.test_query "your search query here"
    python -m scripts.test_query "your search query" --json output.json
    python -m scripts.test_query "your search query" --md output.md
"""

from lib.constants import DEFAULT_MATCH_THRESHOLD
from lib.supabase.util import get_supabase_client
from lib.util.embedding import get_embedding
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


def query_chunks(query: str, match_threshold: float = DEFAULT_MATCH_THRESHOLD, match_count: int = 10) -> list[dict]:
    """
    Query the database for matching chunks.

    Args:
        query: Natural language search query
        match_threshold: Minimum similarity score (0-1)
        match_count: Maximum number of results

    Returns:
        List of matching chunk records
    """
    # Generate embedding for query
    query_embedding = get_embedding(query)

    # Call the database function
    client = get_supabase_client()
    result = client._client.rpc(
        "query_file_chunks",
        {
            "query_embedding": query_embedding,
            "match_threshold": match_threshold,
            "match_count": match_count,
        }
    ).execute()

    return result.data or []


def print_results(query: str, results: list[dict], threshold: float, count: int):
    """Print results to console."""
    print(f"Query: \"{query}\"")
    print(f"Threshold: {threshold}, Max results: {count}")
    print("-" * 50)

    if not results:
        print("\nNo matching results found.")
        return

    print(f"\nFound {len(results)} results:\n")

    for i, row in enumerate(results, 1):
        print(f"[{i}] {row['file_name']} (similarity: {row['similarity']:.3f})")
        print(f"    Path: {row['file_path']}")
        print(f"    Chunk {row['chunk_index']}: {row['content'][:150]}...")
        if row.get('chunk_metadata'):
            meta = row['chunk_metadata']
            if 'page_start' in meta:
                print(f"    Pages: {meta['page_start']}-{meta['page_end']}")
        print()


def export_to_json(query: str, results: list[dict], output_path: str, threshold: float, count: int):
    """Export query results to a JSON file."""
    output = {
        "query": query,
        "threshold": threshold,
        "max_results": count,
        "found": len(results),
        "generated_at": datetime.now().isoformat(),
        "results": results,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nResults exported to: {output_path}")


def export_to_markdown(query: str, results: list[dict], output_path: str, threshold: float, count: int):
    """Export query results to a Markdown file."""
    lines = [
        "# Search Results",
        "",
        f"**Query:** \"{query}\"",
        f"**Threshold:** {threshold} | **Max results:** {count} | **Found:** {len(results)}",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
    ]

    if not results:
        lines.append("*No matching results found.*")
    else:
        for i, row in enumerate(results, 1):
            lines.append(f"## [{i}] {row['file_name']}")
            lines.append("")
            lines.append(f"**Similarity:** {row['similarity']:.3f}")
            lines.append("")
            lines.append(f"**Path:** `{row['file_path']}`")
            lines.append("")

            if row.get('chunk_metadata'):
                meta = row['chunk_metadata']
                if 'page_start' in meta:
                    lines.append(
                        f"**Pages:** {meta['page_start']} - {meta['page_end']} | **Chunk index:** {row['chunk_index']}")
                elif 'start_time' in meta:
                    lines.append(
                        f"**Time:** {meta['start_time']:.1f}s - {meta['end_time']:.1f}s | **Chunk index:** {row['chunk_index']}")
                lines.append("")

            lines.append("### Content")
            lines.append("")
            lines.append("```")
            lines.append(row['content'])
            lines.append("```")
            lines.append("")
            lines.append("---")
            lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nResults exported to: {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Query the database and optionally export to JSON or Markdown")
    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument("--threshold", type=float, default=DEFAULT_MATCH_THRESHOLD,
                        help="Minimum similarity threshold (0-1)")
    parser.add_argument("--count", type=int, default=10,
                        help="Maximum number of results")
    parser.add_argument("--json", type=str, help="Export results to JSON file")
    parser.add_argument(
        "--md", type=str, help="Export results to Markdown file")

    args = parser.parse_args()

    print("Generating query embedding...")
    results = query_chunks(args.query, args.threshold, args.count)

    print_results(args.query, results, args.threshold, args.count)

    if args.json:
        export_to_json(args.query, results, args.json,
                       args.threshold, args.count)

    if args.md:
        export_to_markdown(args.query, results, args.md,
                           args.threshold, args.count)


if __name__ == "__main__":
    main()
