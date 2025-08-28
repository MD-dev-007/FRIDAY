import yaml
import re
from typing import Dict, List, Optional
from pathlib import Path


def load_persona_config(root_path: Optional[Path] = None):
    """Load persona configuration from src/config; fall back to defaults."""
    base = root_path if root_path else Path(__file__).resolve().parent.parent
    cfg_path = base / 'src' / 'config' / 'persona_config.yaml'
    try:
        with open(cfg_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        return get_default_config()


def get_default_config():
    return {
        'persona': {
            'name': 'FRIDAY',
            'respect_title': 'Exynos Thinkers',
            'traits': ['Motivational, supportive', 'Timely humor, but not spammy', 'Clear and direct answers'],
            'signature_style': ['Always end with a motivational nudge', 'Occasionally add light contextual joke']
        },
        'adaptive_tone': {
            'default': ['Be encouraging and supportive', 'Add one motivational line']
        }
    }


# Sentiment detection patterns
SENTIMENT_PATTERNS = {
    'sad': [r'\b(sad|depressed|down|blue|unhappy|miserable|hopeless)\b', r'\b(crying|tears|😢|😭|💔)\b'],
    'angry': [r'\b(angry|mad|furious|irritated|annoyed|frustrated|pissed|rage|😠|😡|🤬)\b', r'\b(hate|dislike|terrible|awful|horrible|frustrating)\b'],
    'playful': [r'\b(fun|joke|lol|haha|😄|😆|😂)\b', r'\b(playful|silly|goofy|funny)\b'],
    'stressed': [r'\b(stressed|overwhelmed|anxious|worried|panic|😰|😨|😱)\b', r'\b(deadline|pressure|urgent|rush)\b'],
    'focused': [r'\b(focus|concentrate|serious|important|critical)\b', r'\b(work|task|project|deadline)\b']
}


def detect_sentiment(text: str) -> str:
    """Detect user sentiment from text patterns"""
    text_lower = text.lower()

    for sentiment, patterns in SENTIMENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return sentiment

    return 'default'


def _format_depth_sections() -> str:
    return (
        "Assistant:\n"
        "- Summary: <1-2 lines>\n"
        "- Details: <bullets or steps>\n"
        "- Example: <short snippet if applicable>\n"
        "- Next steps: <1-3 actions>\n"
        "Motivational nudge: <one-liner>"
    )


def generate_adaptive_prompt(user_input: str, config: Dict = None) -> str:
    """Generate adaptive persona prompt based on friday_v2 schema with tone and depth."""
    if config is None:
        config = load_persona_config()

    # Support both old and new schema gracefully
    persona_cfg = config.get('persona', {})
    name = persona_cfg.get('name', 'FRIDAY')
    respect_title = persona_cfg.get('respect_title') or persona_cfg.get('core', {}).get('primary_address', 'Exynos Thinkers')

    # Traits/signature (new schema encodes weights; render names only)
    traits_list = []
    for item in persona_cfg.get('traits', []):
        if isinstance(item, dict):
            for k in item.keys():
                traits_list.append(k)
        else:
            traits_list.append(str(item))

    signature_style = []
    for item in persona_cfg.get('signature_style', []):
        if isinstance(item, str):
            signature_style.append(item)
        elif isinstance(item, dict):
            for k, v in item.items():
                signature_style.append(f"{k}: {v}")

    # Adaptive tone profiles (new schema)
    tone_profiles = persona_cfg.get('adaptive_tone_profiles') or config.get('adaptive_tone') or {}

    sentiment = detect_sentiment(user_input)
    tone_profile = tone_profiles.get(sentiment, tone_profiles.get('default', {}))

    tone_desc = []
    if isinstance(tone_profile, dict):
        for k, v in tone_profile.items():
            tone_desc.append(f"{k}: {v}")
    elif isinstance(tone_profile, list):
        tone_desc.extend([str(x) for x in tone_profile])

    # Conversational rules and safety: normalize to strings
    rules_raw = persona_cfg.get('conversational_rules', [])
    rules_list: List[str] = []
    for item in rules_raw:
        if isinstance(item, dict):
            for k, v in item.items():
                rules_list.append(f"{k}: {v}")
        else:
            rules_list.append(str(item))

    safety_raw = persona_cfg.get('safety', [])
    safety_list: List[str] = []
    for item in safety_raw:
        if isinstance(item, dict):
            for k, v in item.items():
                safety_list.append(f"{k}: {v}")
        else:
            safety_list.append(str(item))

    base_prompt = (
        f"You are {name} — a motivational, technically-capable assistant.\n"
        f"Always address the team as \"{respect_title}\".\n\n"
        f"Core traits: {', '.join(traits_list) if traits_list else 'motivational, supportive, direct'}.\n"
        f"Signature style: {', '.join(signature_style) if signature_style else 'end with a motivational nudge; occasional light joke'}.\n\n"
        f"Conversational rules: {', '.join(rules_list)}\n"
        f"Safety: {', '.join(safety_list)}\n\n"
        f"Adaptive tone now: {', '.join(tone_desc) if tone_desc else 'encouraging, high directness, light humor'}.\n"
    )

    # If user asks for depth, include sectioned template hint
    if re.search(r"(deep|details|explain|long|in\s*depth|comprehensive|more detail)", user_input, re.I):
        base_prompt += "\nRespond using structured sections.\n" + _format_depth_sections()

    return base_prompt


SYSTEM_PROMPT = """
You are FRIDAY — Exynos Thinkers' friendly, respectful, high-signal assistant.

Rules:
- Address the team as "Exynos Thinkers".
- Be motivating by default; one short line of encouragement max.
- Humor: only when asked or when mood is casual; keep jokes one-liners.
- Answers: crystal-clear, direct, stepwise if needed. No self-intro, no over-explaining.
- If memory context is present, use it briefly ("Last time you said…").
- Keep replies under ~6 sentences unless the team asks for depth.
"""


