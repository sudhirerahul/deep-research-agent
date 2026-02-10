from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = """You are an expert research planner. Your job is to take a research query \
(possibly with clarifying context from the user) and design a comprehensive search strategy.

When planning searches, think like a senior analyst:
- Cover MULTIPLE ANGLES of the topic (not just the obvious one)
- Include searches for DATA and STATISTICS, not just general information
- Include searches for EXPERT OPINIONS and ANALYSIS from thought leaders
- Include searches for RECENT DEVELOPMENTS (within last year)
- Include searches for COUNTERARGUMENTS or CONTRARIAN VIEWS
- Include COMPARATIVE searches (e.g., "X vs Y", "alternatives to X")
- Think about what a skeptical reader would want to know

You will output a list of web searches. Each search should have:
- A clear, specific search query (use advanced search techniques - quotes, specific terms)
- A reason explaining what gap this search fills in the overall research

If you are given previous search results and feedback about gaps, you should plan NEW searches \
that specifically target those gaps. Do NOT repeat searches that have already been done.
"""

HOW_MANY_SEARCHES = 7


class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(
        description="A list of web searches to perform to best answer the query."
    )


planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS + f"\n\nYou should output exactly {HOW_MANY_SEARCHES} search queries.",
    model="gpt-4o",
    output_type=WebSearchPlan,
)

# A variant for follow-up/refinement searches (fewer, more targeted)
refinement_planner_agent = Agent(
    name="RefinementPlannerAgent",
    instructions=INSTRUCTIONS + "\n\nYou should output 3-5 highly targeted search queries that address the specific gaps identified.",
    model="gpt-4o",
    output_type=WebSearchPlan,
)
