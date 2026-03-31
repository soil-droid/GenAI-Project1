"""
Wikipedia MCP Server
Exposes Wikipedia search and retrieval tools via SSE transport.
Deployed as a standalone Cloud Run service.
"""

import os
import uvicorn
import wikipedia
from mcp.server.fastmcp import FastMCP

# ── MCP Server Setup ─────────────────────────────────────────────────────────
mcp = FastMCP(
    name="wikipedia-mcp-server",
    instructions="Provides tools to search and retrieve content from Wikipedia.",
)


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def search_wikipedia(query: str) -> str:
    """Search Wikipedia for articles related to the query.
    Returns a ranked list of relevant article titles.

    Args:
        query: The search term or question to look up on Wikipedia.
    """
    try:
        results = wikipedia.search(query, results=6)
        if not results:
            return "No Wikipedia articles found for this query. Try different keywords."
        lines = [f"  {i+1}. {title}" for i, title in enumerate(results)]
        return "Relevant Wikipedia articles found:\n" + "\n".join(lines)
    except Exception as e:
        return f"Search failed: {str(e)}"


@mcp.tool()
def get_article_summary(title: str) -> str:
    """Get a concise summary of a Wikipedia article by its title.
    Use exact titles returned from search_wikipedia for best results.

    Args:
        title: The exact Wikipedia article title to summarize.
    """
    try:
        page = wikipedia.page(title, auto_suggest=True)
        summary = wikipedia.summary(title, sentences=6, auto_suggest=True)
        return (
            f"📄 Article: {page.title}\n"
            f"🔗 URL: {page.url}\n\n"
            f"Summary:\n{summary}"
        )
    except wikipedia.DisambiguationError as e:
        options = ", ".join(e.options[:6])
        return (
            f"'{title}' is ambiguous. "
            f"Please specify one of: {options}"
        )
    except wikipedia.PageError:
        return (
            f"No page found for '{title}'. "
            f"Try searching first with search_wikipedia."
        )
    except Exception as e:
        return f"Error fetching summary: {str(e)}"


@mcp.tool()
def get_article_content(title: str, section: str = "") -> str:
    """Get detailed content from a Wikipedia article.
    Optionally target a specific section for focused information.

    Args:
        title: The Wikipedia article title.
        section: (Optional) A specific section name within the article.
    """
    try:
        page = wikipedia.page(title, auto_suggest=True)

        if section:
            content = page.section(section)
            if not content:
                available = ", ".join(page.sections[:8])
                return (
                    f"Section '{section}' not found in '{page.title}'.\n"
                    f"Available sections: {available}"
                )
            return (
                f"📄 {page.title}  ›  {section}\n"
                f"🔗 {page.url}\n\n"
                f"{content[:2500]}"
            )

        # Return intro content (first 3000 chars) with section list
        sections_preview = "\n".join(f"  • {s}" for s in page.sections[:10])
        return (
            f"📄 {page.title}\n"
            f"🔗 {page.url}\n\n"
            f"{page.content[:3000]}\n\n"
            f"--- Sections in this article ---\n{sections_preview}"
        )

    except wikipedia.DisambiguationError as e:
        return f"Ambiguous title. Options: {', '.join(e.options[:5])}"
    except wikipedia.PageError:
        return f"Page '{title}' not found."
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def get_related_topics(title: str) -> str:
    """Get a list of articles that are linked from a given Wikipedia article.
    Useful for exploring related concepts.

    Args:
        title: The Wikipedia article title to find related topics for.
    """
    try:
        page = wikipedia.page(title, auto_suggest=True)
        links = list(page.links)[:20]
        formatted = "\n".join(f"  • {link}" for link in links)
        return f"Topics related to '{page.title}':\n{formatted}"
    except Exception as e:
        return f"Error: {str(e)}"


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # sse_app() exposes the MCP server at /sse endpoint
    starlette_app = mcp.sse_app()
    uvicorn.run(starlette_app, host="0.0.0.0", port=port, log_level="info")
