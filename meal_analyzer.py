"""AI Meal Analyzer: identifies food from an uploaded image and estimates nutrition."""
import base64
import io
from PIL import Image

from core import database as db
from core.models import UserContext
from core.utils import validate_image_upload, safe_filename
from services import ai_client
from services.prompts import meal_analysis_prompts
import config


def _prepare_image(uploaded_file) -> tuple[str, str, str]:
    """Validates, resizes if needed, saves to disk, returns (b64, mime, saved_path)."""
    ok, msg = validate_image_upload(uploaded_file)
    if not ok:
        raise ValueError(msg)

    image = Image.open(uploaded_file)
    image = image.convert("RGB")
    image.thumbnail((1024, 1024))

    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=85)
    img_bytes = buf.getvalue()
    b64 = base64.b64encode(img_bytes).decode("utf-8")

    filename = safe_filename("meal", uploaded_file.name.rsplit(".", 1)[0]) + ".jpg"
    save_path = config.REPORTS_DIR.parent / "data" / "meal_images"
    save_path.mkdir(exist_ok=True, parents=True)
    full_path = save_path / filename
    with open(full_path, "wb") as f:
        f.write(img_bytes)

    return b64, "image/jpeg", str(full_path)


def analyze_meal_image(user_id: int, context: UserContext, uploaded_file, meal_type: str = "meal") -> dict:
    b64, mime, saved_path = _prepare_image(uploaded_file)
    ctx_dict = context.to_prompt_dict()
    prompt = meal_analysis_prompts.build_meal_analysis_prompt(ctx_dict)

    raw = ai_client.analyze_image(meal_analysis_prompts.SYSTEM_PROMPT, prompt, b64, mime)

    import json
    try:
        start, end = raw.find("{"), raw.rfind("}")
        analysis = json.loads(raw[start:end + 1]) if start != -1 else {"feedback": raw}
    except json.JSONDecodeError:
        analysis = {"feedback": raw}

    analysis.setdefault(
        "disclaimer", "Image-based nutrition analysis is only an estimate and may be inaccurate."
    )

    db.add_meal(user_id, meal_type, analysis.get("identified_food", "Unknown"), saved_path, analysis)
    if analysis.get("identified_food"):
        db.add_food_log(user_id, analysis["identified_food"], meal_type, source="image_ai")

    return analysis
