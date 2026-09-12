"""
Weekly AI Health Report: aggregates real tracked data, generates an AI
summary strictly grounded in that data, and renders a PDF via ReportLab.
"""
from datetime import date, timedelta
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from core import database as db
from core.health_calculations import calculate_health_score, calculate_food_score
from core.models import UserContext
from services import ai_client
from services.prompts import report_prompts
import config


def _week_bounds() -> tuple[date, date]:
    today = date.today()
    start = today - timedelta(days=6)
    return start, today


def gather_weekly_data(user_id: int, context: UserContext) -> dict:
    start, end = _week_bounds()

    weight_hist = db.get_weight_history(user_id, limit=10)
    weight_change = None
    if len(weight_hist) >= 2:
        weight_change = round(weight_hist[0]["weight_kg"] - weight_hist[-1]["weight_kg"], 1)

    water_hist = db.get_water_history(user_id, days=7)
    avg_water = round(sum(w["total"] for w in water_hist) / len(water_hist), 0) if water_hist else 0

    sleep_hist = db.get_sleep_history(user_id, limit=7)
    avg_sleep = round(sum(s["duration_hours"] for s in sleep_hist) / len(sleep_hist), 1) if sleep_hist else 0

    exercise_hist = db.get_exercise_history(user_id, limit=14)

    health_score_result = calculate_health_score(user_id, context.profile)
    food_score_result = calculate_food_score(user_id, days=7)

    return {
        "week_start": start.isoformat(),
        "week_end": end.isoformat(),
        "current_weight_kg": weight_hist[0]["weight_kg"] if weight_hist else "no data",
        "weight_change_kg": weight_change if weight_change is not None else "no data",
        "avg_daily_water_ml": avg_water,
        "water_target_ml": context.profile.water_target_ml,
        "avg_sleep_hours": avg_sleep,
        "sleep_target_hours": context.profile.sleep_target_hours,
        "exercise_sessions_logged": len(exercise_hist),
        "health_score": health_score_result["score"],
        "health_score_category": health_score_result["category"],
        "food_score": food_score_result.get("score", 0),
    }


def generate_ai_summary(weekly_data: dict) -> dict:
    prompt = report_prompts.build_weekly_summary_prompt(weekly_data)
    try:
        return ai_client.chat_json(report_prompts.SYSTEM_PROMPT, prompt)
    except ai_client.AIError:
        return {
            "headline": "Weekly summary (AI unavailable)",
            "summary_paragraph": "The AI summary could not be generated right now, but your tracked "
                                  "data below is accurate and based on your real activity this week.",
            "positive_habits": [],
            "areas_for_improvement": [],
            "next_week_goals": [],
        }


def _pdf_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitle", fontSize=20, leading=24, textColor=colors.HexColor("#1B7F5B"), spaceAfter=6))
    styles.add(ParagraphStyle(name="SectionHeader", fontSize=14, leading=18, textColor=colors.HexColor("#0F172A"), spaceBefore=14, spaceAfter=6))
    styles.add(ParagraphStyle(name="Body", fontSize=10.5, leading=15))
    styles.add(ParagraphStyle(name="Disclaimer", fontSize=8.5, leading=12, textColor=colors.grey))
    return styles


def build_pdf_report(user_id: int, username: str, weekly_data: dict, ai_summary: dict) -> str:
    filename = f"weekly_report_{user_id}_{weekly_data['week_end']}.pdf"
    path = config.REPORTS_DIR / filename
    doc = SimpleDocTemplate(str(path), pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = _pdf_styles()
    elements = []

    elements.append(Paragraph("Smart Health Assistant", styles["ReportTitle"]))
    elements.append(Paragraph(
        f"Weekly Wellness Report for {username} &nbsp;|&nbsp; {weekly_data['week_start']} to {weekly_data['week_end']}",
        styles["Body"],
    ))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(ai_summary.get("headline", "Weekly Summary"), styles["SectionHeader"]))
    elements.append(Paragraph(ai_summary.get("summary_paragraph", ""), styles["Body"]))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("This Week at a Glance", styles["SectionHeader"]))
    table_data = [
        ["Metric", "Value"],
        ["Health Score", f"{weekly_data['health_score']} ({weekly_data['health_score_category']})"],
        ["Food Score", str(weekly_data["food_score"])],
        ["Current Weight", f"{weekly_data['current_weight_kg']} kg"],
        ["Weight Change (period)", f"{weekly_data['weight_change_kg']} kg"],
        ["Avg Daily Water", f"{weekly_data['avg_daily_water_ml']} ml (target {weekly_data['water_target_ml']} ml)"],
        ["Avg Sleep", f"{weekly_data['avg_sleep_hours']} hrs (target {weekly_data['sleep_target_hours']} hrs)"],
        ["Exercise Sessions Logged", str(weekly_data["exercise_sessions_logged"])],
    ]
    t = Table(table_data, colWidths=[7 * cm, 8 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B7F5B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 10))

    for header, key in (
        ("Positive Habits", "positive_habits"),
        ("Areas for Improvement", "areas_for_improvement"),
        ("Goals for Next Week", "next_week_goals"),
    ):
        items = ai_summary.get(key) or []
        if items:
            elements.append(Paragraph(header, styles["SectionHeader"]))
            for item in items:
                elements.append(Paragraph(f"• {item}", styles["Body"]))
            elements.append(Spacer(1, 6))

    elements.append(Spacer(1, 14))
    elements.append(Paragraph(config.DISCLAIMER, styles["Disclaimer"]))

    doc.build(elements)
    return str(path)


def generate_weekly_report(user_id: int, username: str, context: UserContext) -> dict:
    weekly_data = gather_weekly_data(user_id, context)
    ai_summary = generate_ai_summary(weekly_data)
    pdf_path = build_pdf_report(user_id, username, weekly_data, ai_summary)

    db.save_weekly_report(
        user_id, weekly_data["week_start"], weekly_data["week_end"],
        {"weekly_data": weekly_data, "ai_summary": ai_summary}, pdf_path,
    )
    return {"weekly_data": weekly_data, "ai_summary": ai_summary, "pdf_path": pdf_path}
