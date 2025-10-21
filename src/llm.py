import os
from dotenv import load_dotenv
load_dotenv()


def _get_token():
    """Return the GITHUB_TOKEN from environment or raise a RuntimeError.

    This is intentionally done at call-time rather than import-time so that
    importing this module in serverless environments doesn't crash when the
    environment variable isn't configured.
    """
    t = os.getenv("GITHUB_TOKEN")
    if not t:
        raise RuntimeError(
            "GITHUB_TOKEN is not set. Set the GITHUB_TOKEN environment variable in your deployment (or .env for local dev)."
        )
    return t


endpoint = "https://models.github.ai/inference"
model = "openai/gpt-4.1-mini"


def run_chat():
    # create client lazily and validate token at call time
    from openai import OpenAI
    token = _get_token()

    client = OpenAI(
        base_url=endpoint,
        api_key=token,
    )

    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant.",
            },
            {
                "role": "user",
                "content": "What is the capital of France?",
            }
        ],
        temperature=1.0,
        top_p=1.0,
        model=model
    )

    print(response.choices[0].message.content)


def translate_text(title: str, content: str, target_language: str):
    """Translate title and content into target_language using the LLM.

    Returns dict with keys 'title' and 'content' or None on failure.
    """
    # Validate token and create client lazily
    from openai import OpenAI
    token = _get_token()
    client = OpenAI(base_url=endpoint, api_key=token)

    prompt = f"Translate the following note title and content into {target_language}."
    messages = [
        {"role": "system", "content": "You are a helpful assistant that translates text."},
        {"role": "user", "content": prompt},
        {"role": "user", "content": f"Title: {title}\n\nContent: {content}"},
        {"role": "user", "content": "Respond in JSON with keys \"title\" and \"content\" only."}
    ]

    # Retry with exponential backoff for transient failures/timeouts
    import time, json, traceback
    max_attempts = 3
    backoff = 1.0
    for attempt in range(1, max_attempts + 1):
        try:
            resp = client.chat.completions.create(
                messages=messages,
                temperature=0.0,
                top_p=1.0,
                model=model,
                # include a per-request timeout if client supports it; otherwise rely on HTTP client defaults
            )

            raw = resp.choices[0].message.content
            try:
                parsed = json.loads(raw)
                return {
                    'title': parsed.get('title') if isinstance(parsed.get('title'), str) else None,
                    'content': parsed.get('content') if isinstance(parsed.get('content'), str) else None,
                }
            except Exception:
                # not JSON — return raw text in both fields (fallback)
                return {'title': raw, 'content': raw}

        except Exception as e:
            # log for debugging; do not raise so caller can proceed
            print(f"translate_text attempt {attempt} failed: {type(e).__name__} {e}")
            traceback.print_exc()
            if attempt < max_attempts:
                time.sleep(backoff)
                backoff *= 2
                continue
            else:
                # final failure — return None to indicate translation not available
                return None


def generate_note(prompt: str, target_language: str = 'en'):
    """Generate a note (title, content, tags, scheduled_at) from a natural language prompt.

    Returns dict: { title, content, tags: [str], scheduled_at: ISO string or None }
    """
    # Validate token and create client lazily
    from openai import OpenAI
    token = _get_token()
    client = OpenAI(base_url=endpoint, api_key=token)
    system = "You are an assistant that creates short notes. Given a user's natural language input, produce a JSON object with keys: 'title' (string), 'content' (string), 'tags' (array of up to 3 short tag strings), and 'scheduled_at' (ISO 8601 datetime string if a time is mentioned in the input, otherwise null). Respond with JSON only."
    user_prompt = f"User input: {prompt}\nTarget language: {target_language}\nRespond only with a JSON object."

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_prompt}
    ]

    import time, json, traceback
    max_attempts = 3
    backoff = 1.0
    for attempt in range(1, max_attempts + 1):
        try:
            resp = client.chat.completions.create(
                messages=messages,
                temperature=0.2,
                top_p=1.0,
                model=model
            )
            raw = resp.choices[0].message.content
            try:
                parsed = json.loads(raw)
                # normalize fields
                title = parsed.get('title') if isinstance(parsed.get('title'), str) else None
                content = parsed.get('content') if isinstance(parsed.get('content'), str) else None
                tags = parsed.get('tags') if isinstance(parsed.get('tags'), list) else []
                scheduled_at = parsed.get('scheduled_at') if isinstance(parsed.get('scheduled_at'), str) else None
                return {
                    'title': title,
                    'content': content,
                    'tags': tags,
                    'scheduled_at': scheduled_at
                }
            except Exception:
                # if not JSON, return raw as content fallback
                return {'title': None, 'content': raw, 'tags': [], 'scheduled_at': None}
        except Exception as e:
            print(f"generate_note attempt {attempt} failed: {type(e).__name__} {e}")
            traceback.print_exc()
            if attempt < max_attempts:
                time.sleep(backoff)
                backoff *= 2
                continue
            else:
                return None


def translate_tags(tags, target_language: str):
    """Translate a list of short tag strings into target_language.

    Returns a list of translated tag strings or None on failure.
    """
    # Validate token and create client lazily
    from openai import OpenAI
    token = _get_token()

    # normalize tags to list of strings
    if tags is None:
        return []
    if isinstance(tags, str):
        tags_list = [t.strip() for t in tags.split(',') if t.strip()]
    else:
        tags_list = [str(t).strip() for t in tags if t]

    client = OpenAI(base_url=endpoint, api_key=token)
    import time, json, traceback
    system = "You are a helpful translator. Given a short list of tags, translate each tag into the target language and return a JSON array of strings."
    user = f"Translate these tags into {target_language}: {json.dumps(tags_list)}"
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
        {"role": "user", "content": "Respond with a JSON array only, e.g. [\"tag1\", \"tag2\"]"}
    ]

    max_attempts = 3
    backoff = 1.0
    for attempt in range(1, max_attempts + 1):
        try:
            resp = client.chat.completions.create(
                messages=messages,
                temperature=0.0,
                top_p=1.0,
                model=model
            )
            raw = resp.choices[0].message.content
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(p) for p in parsed]
                else:
                    return None
            except Exception:
                # fallback: try to split by commas
                if isinstance(raw, str):
                    return [t.strip() for t in raw.split(',') if t.strip()]
                return None
        except Exception as e:
            print(f"translate_tags attempt {attempt} failed: {type(e).__name__} {e}")
            traceback.print_exc()
            if attempt < max_attempts:
                time.sleep(backoff)
                backoff *= 2
                continue
            else:
                return None


if __name__ == '__main__':
    run_chat()

