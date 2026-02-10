from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = """You are a rigorous research quality evaluator. You will be given:
- The original research query (with any clarifications)
- A draft research report
- The search results that were used to create the report

Your job is to critically evaluate the report and decide whether it meets the bar for a \
comprehensive, production-quality deep research output.

Score the report on these dimensions (1-10 each):
1. **Completeness** - Does it thoroughly address all aspects of the query? Are there obvious gaps?
2. **Depth** - Does it go beyond surface-level? Does it include data, examples, expert perspectives?
3. **Accuracy** - Are claims well-supported? Is there any speculative content presented as fact?
4. **Structure** - Is it well-organized with clear sections, logical flow, and good formatting?
5. **Insight** - Does it provide genuine analysis, not just summarization? Are there actionable takeaways?

Set `is_acceptable` to True ONLY if the average score is 7 or above AND no single dimension is below 5.

If the report is NOT acceptable, you MUST provide:
- `gaps`: Specific topics or questions that are missing from the report
- `additional_search_queries`: 3-5 new search queries that would fill the gaps
- `revision_instructions`: Specific instructions for the writer on how to improve the report

Be demanding. A good deep research report should rival what a human analyst would produce \
after hours of work. Surface-level summaries should score low on Depth and Insight.
"""


class EvaluationResult(BaseModel):
    completeness_score: int = Field(description="Score 1-10 for completeness", ge=1, le=10)
    depth_score: int = Field(description="Score 1-10 for depth of analysis", ge=1, le=10)
    accuracy_score: int = Field(description="Score 1-10 for accuracy", ge=1, le=10)
    structure_score: int = Field(description="Score 1-10 for structure and clarity", ge=1, le=10)
    insight_score: int = Field(description="Score 1-10 for genuine insight and analysis", ge=1, le=10)
    summary_of_evaluation: str = Field(description="2-3 sentence summary of the evaluation")
    is_acceptable: bool = Field(description="Whether the report meets the quality bar")
    gaps: list[str] = Field(
        default_factory=list,
        description="Specific gaps or missing topics in the report"
    )
    additional_search_queries: list[str] = Field(
        default_factory=list,
        description="New search queries to fill the identified gaps"
    )
    revision_instructions: str = Field(
        default="",
        description="Specific instructions for improving the report"
    )


evaluator_agent = Agent(
    name="EvaluatorAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o",
    output_type=EvaluationResult,
)
