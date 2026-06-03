from pathlib import Path
from typing import Literal

import pandas as pd
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel


mcp = FastMCP(
    "Tool Metadata Tutorial Server",
    host="127.0.0.1",
    port=8000,
    streamable_http_path="/mcp",
)

DATA_PATH = Path(__file__).parent / "data" / "titanic.csv"
TITANIC_DF = pd.read_csv(DATA_PATH)


class ResumeHit(BaseModel):
    candidate_id: str
    name: str
    headline: str
    match_snippet: str
    score: float


class PdsHit(BaseModel):
    pds_id: str
    project_name: str
    client: str
    match_snippet: str
    score: float


class PassengerRow(BaseModel):
    passenger_id: int
    name: str
    pclass: int
    sex: str
    age: float | None
    fare: float
    survived: int


class SurvivalGroup(BaseModel):
    value: str
    total: int
    survived: int
    survival_rate: float


class SurvivalSummary(BaseModel):
    group_by: str
    groups: list[SurvivalGroup]


RESUME_STORE: list[ResumeHit] = [
    ResumeHit(
        candidate_id="C-1001",
        name="Maya Chen",
        headline="Senior coastal resilience planner and climate adaptation lead",
        match_snippet="Led sea-level rise vulnerability studies, FEMA BRIC applications, and waterfront adaptation plans.",
        score=0.0,
    ),
    ResumeHit(
        candidate_id="C-1002",
        name="Jordan Miles",
        headline="Transportation engineer specializing in complete streets and Vision Zero",
        match_snippet="Designed bus priority corridors, pedestrian safety upgrades, and multimodal capital programs.",
        score=0.0,
    ),
    ResumeHit(
        candidate_id="C-1003",
        name="Priya Nair",
        headline="Healthcare facility strategist and medical campus planner",
        match_snippet="Developed hospital master plans, ambulatory care growth studies, and phasing strategies.",
        score=0.0,
    ),
    ResumeHit(
        candidate_id="C-1004",
        name="Owen Rodriguez",
        headline="Water resources modeler and green infrastructure designer",
        match_snippet="Built hydrologic models for stormwater retrofits, watershed planning, and flood mitigation.",
        score=0.0,
    ),
    ResumeHit(
        candidate_id="C-1005",
        name="Aisha Coleman",
        headline="Public engagement manager for equitable infrastructure programs",
        match_snippet="Facilitated multilingual workshops for transit, housing, and resilience planning efforts.",
        score=0.0,
    ),
]

PDS_STORE: list[PdsHit] = [
    PdsHit(
        pds_id="PDS-2401",
        project_name="Harbor District Coastal Resilience Plan",
        client="City of New Bedford",
        match_snippet="Prepared flood risk mapping, adaptation concepts, and implementation costs for a working waterfront.",
        score=0.0,
    ),
    PdsHit(
        pds_id="PDS-2402",
        project_name="Downtown Complete Streets Program",
        client="Metropolitan Planning Council",
        match_snippet="Delivered corridor alternatives for bus lanes, safer crossings, protected bike lanes, and curb management.",
        score=0.0,
    ),
    PdsHit(
        pds_id="PDS-2403",
        project_name="Regional Medical Campus Master Plan",
        client="North Valley Health System",
        match_snippet="Evaluated inpatient capacity, ambulatory expansion, parking, utilities, and phased construction scenarios.",
        score=0.0,
    ),
    PdsHit(
        pds_id="PDS-2404",
        project_name="Green Stormwater Retrofit Portfolio",
        client="Allegheny Water Authority",
        match_snippet="Screened public parcels for bioretention, detention, and watershed-scale runoff reduction projects.",
        score=0.0,
    ),
    PdsHit(
        pds_id="PDS-2405",
        project_name="Equitable Transit-Oriented Development Strategy",
        client="Capital Region Transit Agency",
        match_snippet="Linked station-area zoning, affordable housing, market analysis, and community benefit priorities.",
        score=0.0,
    ),
]


def _query_tokens(query: str) -> list[str]:
    return [token.casefold() for token in query.split() if token.strip()]


def _match_score(query: str, text: str) -> float:
    tokens = _query_tokens(query)
    if not tokens:
        return 1.0

    normalized_text = text.casefold()
    matches = sum(1 for token in tokens if token in normalized_text)
    return round(matches / len(tokens), 3)


@mcp.tool(name="hello_from_mcp")
def hello_from_mcp() -> str:
    """Return a short greeting from the local MCP server."""
    return "Hello from the local MCP server."


@mcp.tool(name="search_resumes")
def search_resumes(query: str) -> list[ResumeHit]:
    """Search the candidate resume store for people matching a query. Use when the user wants to FIND or shortlist candidates/people. Do NOT use to look up past projects."""
    hits: list[ResumeHit] = []
    for candidate in RESUME_STORE:
        searchable_text = " ".join(
            [candidate.name, candidate.headline, candidate.match_snippet]
        )
        score = _match_score(query, searchable_text)
        if score > 0:
            hits.append(candidate.model_copy(update={"score": score}))

    return sorted(hits, key=lambda hit: hit.score, reverse=True)[:5]


@mcp.tool(name="search_pds")
def search_pds(query: str) -> list[PdsHit]:
    """Search the Project Data Sheet store of the firm's past projects. Use when the user wants the firm's EXPERIENCE / past work on a topic. Do NOT use to find people."""
    hits: list[PdsHit] = []
    for project in PDS_STORE:
        searchable_text = " ".join(
            [project.project_name, project.client, project.match_snippet]
        )
        score = _match_score(query, searchable_text)
        if score > 0:
            hits.append(project.model_copy(update={"score": score}))

    return sorted(hits, key=lambda hit: hit.score, reverse=True)[:5]


@mcp.tool(name="query_titanic_passengers")
def query_titanic_passengers(
    pclass: Literal[1, 2, 3] | None = None,
    sex: Literal["male", "female"] | None = None,
    embarked: Literal["C", "Q", "S"] | None = None,
    min_age: float | None = None,
    max_age: float | None = None,
    survived: bool | None = None,
    limit: int = 20,
) -> list[PassengerRow]:
    """Return Titanic passenger rows matching optional filters. Use when the user wants passenger-level Titanic records."""
    filtered_df = TITANIC_DF

    if pclass is not None:
        filtered_df = filtered_df[filtered_df["Pclass"] == pclass]
    if sex is not None:
        filtered_df = filtered_df[filtered_df["Sex"] == sex]
    if embarked is not None:
        filtered_df = filtered_df[filtered_df["Embarked"] == embarked]
    if min_age is not None:
        filtered_df = filtered_df[filtered_df["Age"].notna() & (filtered_df["Age"] >= min_age)]
    if max_age is not None:
        filtered_df = filtered_df[filtered_df["Age"].notna() & (filtered_df["Age"] <= max_age)]
    if survived is not None:
        filtered_df = filtered_df[filtered_df["Survived"] == int(survived)]

    clamped_limit = max(1, min(limit, 100))
    rows: list[PassengerRow] = []
    for row in filtered_df.head(clamped_limit).itertuples(index=False):
        age = None if pd.isna(row.Age) else float(row.Age)
        rows.append(
            PassengerRow(
                passenger_id=int(row.PassengerId),
                name=str(row.Name),
                pclass=int(row.Pclass),
                sex=str(row.Sex),
                age=age,
                fare=float(row.Fare),
                survived=int(row.Survived),
            )
        )

    return rows


@mcp.tool(name="summarize_titanic_survival")
def summarize_titanic_survival(
    group_by: Literal["sex", "pclass", "embarked", "survived"],
) -> SurvivalSummary:
    """Aggregate survival statistics grouped by one categorical column. Use when the user wants Titanic survival rates by category."""
    column_name = {
        "sex": "Sex",
        "pclass": "Pclass",
        "embarked": "Embarked",
        "survived": "Survived",
    }[group_by]

    groups: list[SurvivalGroup] = []
    for value, group_df in TITANIC_DF.groupby(column_name, dropna=False):
        total = int(len(group_df))
        survived_count = int(group_df["Survived"].sum())
        survival_rate = round(survived_count / total, 3) if total else 0.0
        groups.append(
            SurvivalGroup(
                value=str(value),
                total=total,
                survived=survived_count,
                survival_rate=survival_rate,
            )
        )

    return SurvivalSummary(group_by=group_by, groups=groups)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
