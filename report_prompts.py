"""Prompt template for the weekly AI wellness summary."""
import json

SYSTEM_PROMPT = """You are a wellness report writer inside "Smart Health \
Assistant". You summarize a user's week from their tracked data only — \
never invent numbers that were not provided.

Rules:
- Base everything strictly on the data given.
- Avoid clinical or diagnostic language.
- Be encouraging but honest; do not overstate certainty.
- Respond ONLY with valid JSON matching the schema.
"""


def build_weekly_summary_prompt(weekly_data: dict) -> str:
    return f"""Weekly tracked data (JSON):
{json.dumps(weekly_data, indent=2)}

Task: Write a short, encouraging weekly wellness summary strictly based on \
this data.

Return JSON with this schema:
{{
  "headline": "one short sentence",
  "summary_paragraph": "2-4 sentences",
  "positive_habits": ["..."],
  "areas_for_improvement": ["..."],
  "next_week_goals": ["..."]
}}
"""
