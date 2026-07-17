import os
import json
import time
import sys
from database.db import get_connection
from config import settings

IMAGE_DIR = os.path.join(settings.BASE_DIR, "data", "images")

DASHSCOPE_BASE = "https://dashscope.aliyuncs.com/api/v1"


def _ensure_image_dir():
    os.makedirs(IMAGE_DIR, exist_ok=True)


def _log(shot_id, **kwargs):
    """Log image generation events. Never logs API key."""
    parts = [f"[ImageGen shot={shot_id}]"]
    for k, v in kwargs.items():
        if "key" in k.lower() or "secret" in k.lower() or "token" in k.lower():
            continue
        parts.append(f"{k}={v}")
    print(" ".join(parts), file=sys.stderr, flush=True)


# ── Public API ──────────────────────────────────────────────────────────

def generate_shot_image(visual_description, character_action, style_id="american_comic"):
    from services.prompt_builder import build_shot_prompt
    from config.visual_styles import build_positive_prompt

    fake_scene_prompt = {
        "shared_positive": build_positive_prompt(style_id),
        "shared_negative": "",
    }
    fake_shot = {
        "visual_description": visual_description,
        "character_action": character_action,
        "order": 1,
    }
    prompt_data = build_shot_prompt(fake_shot, fake_scene_prompt)
    full_prompt = f"{prompt_data['positive']} --no {prompt_data['negative']}"
    shot_id = int(time.time() * 1000) % 100000
    return _generate_image(full_prompt, shot_id)


def generate_scene_images(scene_id, style_id="american_comic"):
    from services.scene_service import get_scene
    from services.prompt_builder import build_all_shot_prompts

    scene = get_scene(scene_id)
    if not scene:
        return {}

    all_prompts = build_all_shot_prompts(scene, style_id)
    results = {}

    for i, shot in enumerate(scene.get("shots", [])):
        shot_id = shot["id"]
        prompt_data = all_prompts[i] if i < len(all_prompts) else {}
        positive = prompt_data.get("positive", "")
        negative = prompt_data.get("negative", "")

        full_prompt = f"{positive} --no {negative}"
        _save_shot_prompts(shot_id, positive, negative)

        try:
            image_path = _generate_image(full_prompt, shot_id)
            _save_shot_image_path(shot_id, image_path)
            results[shot_id] = image_path
        except Exception as e:
            _log(shot_id, status="FAILED", error=str(e))
            results[shot_id] = None

    return results


# ── Provider Router ─────────────────────────────────────────────────────

def _generate_image(prompt, shot_id):
    provider = settings.IMAGE_PROVIDER

    if not provider:
        raise RuntimeError(
            "IMAGE_PROVIDER is not configured. "
            "Set IMAGE_PROVIDER in .env (dashscope or openai)."
        )

    if provider == "dashscope":
        return _generate_dashscope(prompt, shot_id)

    if provider == "openai":
        return _generate_openai(prompt, shot_id)

    raise RuntimeError(f"Unknown IMAGE_PROVIDER: {provider}")


# ── DashScope ───────────────────────────────────────────────────────────

def _get_dashscope_endpoint():
    """Determine the correct DashScope API endpoint based on the model."""
    model = (settings.IMAGE_MODEL or "").lower()

    if model.startswith("wan2.7"):
        return f"{DASHSCOPE_BASE}/services/aigc/multimodal-generation/generation"

    return f"{DASHSCOPE_BASE}/services/aigc/text2image/image-synthesis"


def _generate_dashscope(prompt, shot_id):
    api_key = settings.IMAGE_API_KEY or os.getenv("DASHSCOPE_API_KEY", "")
    if not api_key:
        raise RuntimeError("IMAGE_API_KEY is not configured for DashScope.")

    base_url = settings.IMAGE_BASE_URL
    if base_url and "/apps/anthropic" in base_url:
        _log(shot_id, warning="IMAGE_BASE_URL contains /apps/anthropic, ignoring",
             base_url=base_url)
        base_url = ""

    endpoint = _get_dashscope_endpoint()
    model = settings.IMAGE_MODEL or "wan2.1-t2i-turbo"
    size = (settings.IMAGE_SIZE or "1024x1024").replace("x", "*")

    _log(shot_id, endpoint=endpoint, model=model, size=size, status="SUBMITTING")

    import requests

    # Build request body based on endpoint type
    is_multimodal = "multimodal" in endpoint
    if is_multimodal:
        input_data = {
            "messages": [
                {"role": "user", "content": [{"text": prompt}]}
            ]
        }
    else:
        input_data = {"prompt": prompt}

    # Submit task — try async first, fall back to sync
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    for mode in ("async", "sync"):
        if mode == "async":
            headers["X-DashScope-Async"] = "enable"
        else:
            headers.pop("X-DashScope-Async", None)
            _log(shot_id, note="Retrying in synchronous mode")

        resp = requests.post(
            endpoint,
            headers=headers,
            json={
                "model": model,
                "input": input_data,
                "parameters": {"size": size, "n": 1},
            },
            timeout=120,
        )

        if resp.status_code != 200:
            # If async was rejected, try sync
            data = resp.json() if resp.text else {}
            code = data.get("code", "")
            if mode == "async" and "async" in data.get("message", "").lower():
                continue
            _log(shot_id, status="FAILED",
                 http_status=resp.status_code, response=resp.text[:500], mode=mode)
            raise RuntimeError(
                f"DashScope returned HTTP {resp.status_code}: {resp.text[:300]}"
            )

        data = resp.json()

        # Check if async task was created
        task_id = data.get("output", {}).get("task_id", "")

        if task_id:
            # Async flow — poll for result
            _log(shot_id, task_id=task_id, mode=mode, status="POLLING")
            return _poll_dashscope_task(task_id, api_key, shot_id)

        # Sync flow — check for direct result
        output = data.get("output", {})

        # text2image format: output.results[].url
        results = output.get("results", [])
        # multimodal format: output.choices[].message.content[]
        choices = output.get("choices", [])

        image_url = ""
        if results:
            if isinstance(results[0], dict):
                image_url = results[0].get("url", "") or results[0].get("b64_json", "")
        elif choices:
            # Extract image URL from multimodal chat response
            msg = choices[0].get("message", {}) if choices else {}
            contents = msg.get("content", []) if isinstance(msg, dict) else []
            for c in contents:
                if isinstance(c, dict) and c.get("image"):
                    image_url = c["image"]
                    break
                elif isinstance(c, dict) and c.get("image_url"):
                    image_url = c["image_url"]
                    break

        if not image_url:
            image_url = data.get("data", [{}])[0].get("url", "") if data.get("data") else ""

        if image_url:
            if image_url.startswith("data:"):
                _log(shot_id, mode=mode, status="SUCCEEDED_B64")
                return _save_b64_json(image_url, shot_id)
            _log(shot_id, mode=mode, status="SUCCEEDED")
            return _download_and_validate(image_url, shot_id)

        # No task_id and no direct results
        _log(shot_id, status="NO_RESULT",
             response=json.dumps(data, ensure_ascii=False)[:500], mode=mode)

    raise RuntimeError(
        "DashScope did not return a task_id or direct image result."
    )


def _poll_dashscope_task(task_id, api_key, shot_id):
    """Poll async DashScope task until completion."""
    import requests

    task_url = f"{DASHSCOPE_BASE}/tasks/{task_id}"
    for attempt in range(30):
        time.sleep(2)
        poll_resp = requests.get(
            task_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )
        if poll_resp.status_code != 200:
            _log(shot_id, status="POLL_FAILED",
                 http_status=poll_resp.status_code, attempt=attempt + 1)
            continue

        poll_data = poll_resp.json()
        task_status = poll_data.get("output", {}).get("task_status", "")

        if task_status == "SUCCEEDED":
            results = poll_data.get("output", {}).get("results", [])
            if not results:
                raise RuntimeError("DashScope task SUCCEEDED but results are empty.")
            image_url = results[0].get("url", "")
            if not image_url:
                raise RuntimeError("DashScope task SUCCEEDED but image URL is empty.")
            _log(shot_id, task_id=task_id, status="SUCCEEDED", attempt=attempt + 1)
            return _download_and_validate(image_url, shot_id)

        elif task_status == "FAILED":
            error_msg = poll_data.get("output", {}).get("message", "unknown")
            _log(shot_id, task_id=task_id, status="FAILED", error=error_msg)
            raise RuntimeError(f"DashScope task {task_id} FAILED: {error_msg}")

    _log(shot_id, task_id=task_id, status="TIMEOUT", attempts=30)
    raise RuntimeError(f"DashScope task {task_id} timed out after 60 seconds.")


# ── OpenAI ──────────────────────────────────────────────────────────────

def _generate_openai(prompt, shot_id):
    api_key = settings.IMAGE_API_KEY or ""
    if not api_key:
        raise RuntimeError("IMAGE_API_KEY is not configured for OpenAI.")

    model = settings.IMAGE_MODEL or "dall-e-3"
    size = (settings.IMAGE_SIZE or "1024x1024")
    url = "https://api.openai.com/v1/images/generations"

    _log(shot_id, endpoint=url, model=model, size=size, status="REQUESTING")

    import requests

    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={"model": model, "prompt": prompt, "n": 1, "size": size},
        timeout=120,
    )

    if resp.status_code != 200:
        _log(shot_id, status="FAILED",
             http_status=resp.status_code, response=resp.text[:500])
        raise RuntimeError(
            f"OpenAI returned HTTP {resp.status_code}: {resp.text[:300]}"
        )

    data = resp.json()
    image_url = data.get("data", [{}])[0].get("url", "")
    if not image_url:
        _log(shot_id, status="NO_URL", response=json.dumps(data, ensure_ascii=False)[:500])
        raise RuntimeError("OpenAI response missing image URL.")

    _log(shot_id, status="SUCCEEDED")
    return _download_and_validate(image_url, shot_id)


# ── Download & Validation ───────────────────────────────────────────────

def _download_and_validate(url, shot_id):
    """Download image, validate Content-Type and image integrity."""
    import requests

    _ensure_image_dir()

    resp = requests.get(url, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Image download failed: HTTP {resp.status_code}")

    content_type = resp.headers.get("Content-Type", "")
    valid_types = ("image/png", "image/jpeg", "image/webp", "image/gif",
                   "image/svg+xml", "application/octet-stream")
    if content_type and not any(content_type.startswith(t.split("/")[0] + "/")
                                for t in valid_types if "*" not in t):
        if not any(content_type.startswith(vt.split("/")[0])
                   for vt in valid_types if "/" in vt):
            raise RuntimeError(
                f"Invalid Content-Type: {content_type}. Expected image/*."
            )

    body = resp.content
    if len(body) < 100:
        raise RuntimeError(f"Downloaded file too small: {len(body)} bytes")

    # Detect extension from Content-Type
    ext = ".png"
    if "jpeg" in content_type or "jpg" in content_type:
        ext = ".jpg"
    elif "webp" in content_type:
        ext = ".webp"
    elif "gif" in content_type:
        ext = ".gif"
    elif "svg" in content_type:
        ext = ".svg"

    filename = f"shot_{shot_id}_{int(time.time())}{ext}"
    filepath = os.path.join(IMAGE_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(body)

    # Validate image integrity with Pillow (skip SVG)
    if ext != ".svg":
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(body))
            img.verify()
            _log(shot_id, filepath=filepath, content_type=content_type,
                 size=len(body), verified="OK")
        except Exception as e:
            # Remove corrupted file
            try:
                os.remove(filepath)
            except OSError:
                pass
            raise RuntimeError(f"Image verification failed: {e}")

    return filepath


def _save_b64_json(data_url, shot_id):
    """Save a base64 data URL as an image file."""
    import base64
    _ensure_image_dir()

    # data:image/png;base64,xxxx
    header, encoded = data_url.split(",", 1)
    ext = ".png"
    if "jpeg" in header or "jpg" in header:
        ext = ".jpg"
    elif "webp" in header:
        ext = ".webp"

    filename = f"shot_{shot_id}_{int(time.time())}{ext}"
    filepath = os.path.join(IMAGE_DIR, filename)

    body = base64.b64decode(encoded)
    with open(filepath, "wb") as f:
        f.write(body)

    from PIL import Image
    import io
    img = Image.open(io.BytesIO(body))
    img.verify()
    _log(shot_id, filepath=filepath, size=len(body), verified="OK")
    return filepath


# ── DB Helpers ──────────────────────────────────────────────────────────

def _save_shot_image_path(shot_id, image_path):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE scene_shots SET image_path = ? WHERE id = ?",
        (image_path, shot_id),
    )
    conn.commit()
    conn.close()


def _save_shot_prompts(shot_id, positive, negative):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE scene_shots SET prompt_positive = ?, prompt_negative = ? WHERE id = ?",
        (positive, negative, shot_id),
    )
    conn.commit()
    conn.close()


def get_shot_image(shot_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT image_path FROM scene_shots WHERE id = ?", (shot_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row and row["image_path"]:
        return row["image_path"]
    return None
