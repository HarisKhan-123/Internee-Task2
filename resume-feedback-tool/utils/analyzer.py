"""
LLM-driven resume analysis using LangChain's Groq integration
(free-tier inference, instead of the paid OpenAI API).

Get a free Groq API key at: https://console.groq.com/keys
"""
import os
from typing import List, Optional

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

# Free-tier-friendly model on Groq. As of Aug 16, 2026, Groq deprecated
# llama-3.3-70b-versatile and llama-3.1-8b-instant for free/developer-tier
# accounts (they're now Enterprise-only). openai/gpt-oss-120b is the current
# free-tier replacement — swap to openai/gpt-oss-20b for faster/cheaper
# responses, or check console.groq.com/docs/models for the current list.
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

SYSTEM_PROMPT = """You are an expert technical recruiter and resume coach with 15 years \
of experience reviewing resumes across engineering, marketing, and business roles.

You will be given the raw text extracted from a candidate's resume. Analyze it and \
call the ResumeFeedback tool with your assessment.

Be specific and reference actual content from the resume where possible. Be honest but \
constructive. Give 3-6 items per list. If a section is genuinely strong, say so rather than \
inventing criticism."""


# ---- Structured output schema (LangChain uses this to force valid JSON) ----

class SectionFeedback(BaseModel):
    score: int = Field(description="Score from 0-100 for this section")
    comments: List[str] = Field(description="3-6 specific comments about this section")


class ImprovementItem(BaseModel):
    issue: str = Field(description="Short issue title")
    suggestion: str = Field(description="Concrete, actionable fix for the issue")


class ResumeFeedback(BaseModel):
    """Structured feedback on a candidate's resume."""
    overall_score: int = Field(description="Overall resume score from 0-100")
    summary: str = Field(description="2-3 sentence overall impression")
    strengths: List[str] = Field(description="3-6 genuine strengths of the resume")
    structure_feedback: SectionFeedback = Field(
        description="Feedback on formatting, structure, and organization"
    )
    skills_feedback: SectionFeedback = Field(
        description="Feedback on the skills section, relevance, and presentation"
    )
    content_feedback: SectionFeedback = Field(
        description="Feedback on bullet points, quantified impact, action verbs, clarity"
    )
    improvement_areas: List[ImprovementItem] = Field(
        description="3-6 concrete improvement suggestions"
    )
    missing_sections: List[str] = Field(
        default_factory=list, description="Sections that appear to be missing or weak"
    )
    ats_notes: List[str] = Field(
        default_factory=list,
        description="Notes on applicant-tracking-system friendliness and keyword usage",
    )


class AnalysisError(Exception):
    """Raised when resume analysis fails."""
    pass


def _get_llm() -> ChatGroq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise AnalysisError(
            "GROQ_API_KEY is not set. Get a free key at https://console.groq.com/keys "
            "and set it as an environment variable (or in a .env file)."
        )
    return ChatGroq(
        model=GROQ_MODEL,
        api_key=api_key,
        temperature=0.4,
        max_tokens=2000,
    )


def analyze_resume(resume_text: str) -> dict:
    """
    Send extracted resume text to Groq (via LangChain) and return structured
    feedback as a dict. Truncates very long resumes to stay well within
    context limits.
    """
    llm = _get_llm()
    structured_llm = llm.with_structured_output(ResumeFeedback)

    # Guard against extremely long documents
    max_chars = 12000
    truncated = resume_text[:max_chars]

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Here is the resume text:\n\n{truncated}"),
    ]

    try:
        result: Optional[ResumeFeedback] = structured_llm.invoke(messages)
    except Exception as exc:
        raise AnalysisError(f"Groq API request failed: {exc}") from exc

    if result is None:
        raise AnalysisError("The model did not return structured feedback. Try again.")

    return result.model_dump()
