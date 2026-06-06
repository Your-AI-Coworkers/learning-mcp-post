from __future__ import annotations

from countries_tools import country_count, get_country, search_countries


def register(mcp) -> None:
    @mcp.tool()
    def country_count_tool() -> int:
        """Return the number of rows in the countries SQLite database."""
        return country_count()

    @mcp.tool()
    def search_countries_tool(name_like: str) -> list[dict[str, str]]:
        """Search countries by partial name match."""
        return search_countries(name_like)

    @mcp.tool()
    def get_country_tool(country: str) -> dict[str, str] | None:
        """Return a single country row by exact country name."""
        return get_country(country)
