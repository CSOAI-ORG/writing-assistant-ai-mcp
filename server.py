#!/usr/bin/env python3
"""
Writing Assistant AI MCP Server
==================================
Content writing toolkit for AI agents: headline generation, readability scoring,
tone analysis, outline building, and plagiarism similarity checking.

By MEOK AI Labs | https://meok.ai

Install: pip install mcp
Run:     python server.py
"""


import sys, os
from auth_middleware import check_access

import hashlib
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Optional
from mcp.server.fastmcp import FastMCP

STRIPE_199 = "https://buy.stripe.com/00wfZjcgAeUW4c5cyQ8k90K"

def _add_upgrade_tail(response, tier="free"):
    """Append upgrade nudge to free-tier success responses."""
    if isinstance(response, dict) and tier == "free":
        response["_upgrade_note"] = "Pro tier: unlimited calls + priority support. Upgrade: " + STRIPE_199
    return response


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
FREE_DAILY_LIMIT = 30
_usage: dict[str, list[datetime]] = defaultdict(list)


def _check_rate_limit(caller: str = "anonymous") -> Optional[str]:
    now = datetime.now()
    cutoff = now - timedelta(days=1)
    _usage[caller] = [t for t in _usage[caller] if t > cutoff]
    if len(_usage[caller]) >= FREE_DAILY_LIMIT:
        return f"Free tier limit reached ({FREE_DAILY_LIMIT}/day). Upgrade: https://mcpize.com/writing-assistant-ai-mcp/pro"
    _usage[caller].append(now)
    return None


# ---------------------------------------------------------------------------
# Text analysis utilities
# ---------------------------------------------------------------------------
def _count_syllables(word: str) -> int:
    """Estimate syllable count for an English word."""
    word = word.lower().strip()
    if not word:
        return 0
    if len(word) <= 3:
        return 1
    word = re.sub(r'(?:es|ed|e)$', '', word) or word
    vowel_groups = re.findall(r'[aeiouy]+', word)
    return max(1, len(vowel_groups))


def _tokenize_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s for s in sentences if s.strip()]


def _tokenize_words(text: str) -> list[str]:
    """Extract words from text."""
    return re.findall(r"[a-zA-Z']+", text)


POWER_WORDS = {
    "urgency": ["now", "hurry", "limited", "instant", "fast", "deadline", "immediately", "quick", "rush", "today"],
    "emotion": ["amazing", "incredible", "stunning", "shocking", "heartbreaking", "terrifying", "beautiful", "love", "hate", "fear"],
    "value": ["free", "save", "bonus", "exclusive", "premium", "guaranteed", "proven", "secret", "ultimate", "essential"],
    "curiosity": ["why", "how", "what", "secret", "hidden", "truth", "surprising", "unexpected", "little-known", "revealed"],
    "authority": ["expert", "research", "study", "science", "official", "professional", "certified", "approved", "backed", "tested"],
}

TONE_WORDS = {
    "formal": ["furthermore", "therefore", "consequently", "moreover", "nevertheless", "regarding", "accordingly", "henceforth", "pursuant", "whereby"],
    "casual": ["hey", "cool", "awesome", "yeah", "gonna", "wanna", "kinda", "stuff", "thing", "basically"],
    "academic": ["hypothesis", "methodology", "framework", "paradigm", "analysis", "empirical", "theoretical", "literature", "correlation", "variable"],
    "persuasive": ["imagine", "discover", "transform", "unlock", "guarantee", "proven", "exclusive", "limited", "breakthrough", "revolutionary"],
    "technical": ["implementation", "algorithm", "configuration", "parameter", "protocol", "interface", "module", "architecture", "deployment", "integration"],
    "emotional": ["heartfelt", "passionate", "deeply", "truly", "genuinely", "overwhelming", "touching", "profound", "intimate", "cherished"],
}

FILLER_WORDS = {"very", "really", "just", "quite", "actually", "basically", "literally", "simply", "perhaps", "somewhat", "rather", "fairly"}


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------
def _generate_headlines(topic: str, style: str, count: int,
                        target_audience: str) -> dict:
    """Generate headline variations for a topic."""
    templates = {
        "listicle": [
            "{n} {adj} Ways to {verb} {topic}",
            "Top {n} {topic} Tips That Actually Work",
            "{n} {topic} Mistakes You're Probably Making",
            "{n} Reasons Why {topic} Matters in {year}",
            "The {n} Best {topic} Strategies for {audience}",
        ],
        "how_to": [
            "How to {verb} {topic} Like a Pro",
            "The Complete Guide to {topic} for {audience}",
            "How to Master {topic} in {n} Simple Steps",
            "{topic}: A Step-by-Step Guide for {audience}",
            "How {audience} Can {verb} {topic} Effectively",
        ],
        "question": [
            "Is {topic} Really Worth It for {audience}?",
            "What Makes {topic} So {adj}?",
            "Why Are {audience} Obsessed With {topic}?",
            "Can {topic} Actually {verb} Your Results?",
            "What Nobody Tells You About {topic}",
        ],
        "power": [
            "The Ultimate {topic} Playbook for {audience}",
            "{topic}: The Secret {audience} Don't Want You to Know",
            "Unlock the Power of {topic} Today",
            "Transform Your {topic} With This One Strategy",
            "The Shocking Truth About {topic}",
        ],
        "seo": [
            "{topic}: Everything You Need to Know in {year}",
            "{topic} Guide: Tips, Strategies, and Best Practices",
            "Best {topic} for {audience} [{year} Updated]",
            "{topic} vs Alternatives: Which Is Right for You?",
            "What Is {topic}? Definition, Benefits, and Examples",
        ],
    }

    style_templates = templates.get(style, templates["power"])
    verbs = ["Master", "Improve", "Optimize", "Transform", "Boost", "Elevate"]
    adjectives = ["Proven", "Essential", "Powerful", "Surprising", "Simple", "Effective"]
    numbers = [5, 7, 10, 12, 15]
    year = datetime.now().year

    headlines = []
    for i in range(min(count, 15)):
        tmpl = style_templates[i % len(style_templates)]
        headline = tmpl.format(
            topic=topic, audience=target_audience,
            verb=verbs[i % len(verbs)], adj=adjectives[i % len(adjectives)],
            n=numbers[i % len(numbers)], year=year)
        word_count = len(headline.split())
        char_count = len(headline)
        headlines.append({
            "headline": headline,
            "word_count": word_count,
            "char_count": char_count,
            "seo_length_ok": 50 <= char_count <= 60,
            "power_word_count": sum(1 for w in headline.lower().split() if any(w in words for words in POWER_WORDS.values())),
        })

    return {
        "topic": topic,
        "style": style,
        "target_audience": target_audience,
        "headline_count": len(headlines),
        "headlines": headlines,
        "tips": [
            "Headlines with numbers get 36% more clicks",
            "Use power words to increase emotional engagement",
            "Keep SEO titles between 50-60 characters",
            "Questions in headlines boost curiosity clicks",
        ],
    }


def _score_readability(text: str) -> dict:
    """Calculate multiple readability metrics for text."""
    sentences = _tokenize_sentences(text)
    words = _tokenize_words(text)
    if not words or not sentences:
        return {"error": "Text too short to analyze"}

    num_sentences = len(sentences)
    num_words = len(words)
    num_syllables = sum(_count_syllables(w) for w in words)
    num_chars = sum(len(w) for w in words)

    # Flesch Reading Ease
    flesch = 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (num_syllables / num_words)
    flesch = max(0, min(100, round(flesch, 1)))

    # Flesch-Kincaid Grade Level
    fk_grade = 0.39 * (num_words / num_sentences) + 11.8 * (num_syllables / num_words) - 15.59
    fk_grade = max(0, round(fk_grade, 1))

    # Gunning Fog Index
    complex_words = sum(1 for w in words if _count_syllables(w) >= 3)
    fog = 0.4 * ((num_words / num_sentences) + 100 * (complex_words / num_words))
    fog = round(fog, 1)

    # Coleman-Liau Index
    L = (num_chars / num_words) * 100
    S = (num_sentences / num_words) * 100
    cli = 0.0588 * L - 0.296 * S - 15.8
    cli = round(cli, 1)

    # Average metrics
    avg_sentence_len = round(num_words / num_sentences, 1)
    avg_word_len = round(num_chars / num_words, 1)

    # Reading level label
    if flesch >= 80:
        level = "Very Easy (6th grade)"
    elif flesch >= 60:
        level = "Standard (8th-9th grade)"
    elif flesch >= 40:
        level = "Difficult (college level)"
    elif flesch >= 20:
        level = "Very Difficult (graduate level)"
    else:
        level = "Extremely Difficult (professional)"

    # Find long sentences
    long_sentences = []
    for s in sentences:
        wc = len(s.split())
        if wc > 25:
            long_sentences.append({"sentence": s[:100] + "..." if len(s) > 100 else s, "word_count": wc})

    filler_used = [w for w in words if w.lower() in FILLER_WORDS]

    return {
        "scores": {
            "flesch_reading_ease": flesch,
            "flesch_kincaid_grade": fk_grade,
            "gunning_fog": fog,
            "coleman_liau": cli,
        },
        "reading_level": level,
        "stats": {
            "sentences": num_sentences,
            "words": num_words,
            "syllables": num_syllables,
            "characters": num_chars,
            "avg_sentence_length": avg_sentence_len,
            "avg_word_length": avg_word_len,
            "complex_word_pct": round(complex_words / num_words * 100, 1),
        },
        "issues": {
            "long_sentences": long_sentences[:5],
            "filler_words": dict(Counter(filler_used).most_common(10)),
        },
        "estimated_reading_time_min": round(num_words / 238, 1),
    }


def _analyze_tone(text: str) -> dict:
    """Analyze the tone and style of text."""
    words = _tokenize_words(text)
    words_lower = [w.lower() for w in words]
    word_set = set(words_lower)

    tone_scores = {}
    for tone, indicators in TONE_WORDS.items():
        matches = [w for w in words_lower if w in indicators]
        score = min(1.0, len(matches) / max(len(words) * 0.02, 1))
        tone_scores[tone] = {"score": round(score, 3), "matches": list(set(matches))[:5]}

    primary_tone = max(tone_scores, key=lambda t: tone_scores[t]["score"])

    # Sentence analysis
    sentences = _tokenize_sentences(text)
    exclamations = sum(1 for s in sentences if s.strip().endswith("!"))
    questions = sum(1 for s in sentences if s.strip().endswith("?"))
    passive_markers = len(re.findall(r'\b(?:was|were|been|being|is|are)\s+\w+ed\b', text, re.I))

    # Power word analysis
    power_analysis = {}
    for category, pw_list in POWER_WORDS.items():
        found = [w for w in words_lower if w in pw_list]
        power_analysis[category] = {"count": len(found), "words": list(set(found))[:5]}

    return {
        "primary_tone": primary_tone,
        "tone_scores": tone_scores,
        "voice": {
            "active_vs_passive": "passive-heavy" if passive_markers > len(sentences) * 0.3 else "active",
            "passive_constructions": passive_markers,
            "exclamation_rate": round(exclamations / max(len(sentences), 1), 2),
            "question_rate": round(questions / max(len(sentences), 1), 2),
        },
        "power_words": power_analysis,
        "formality_score": round(
            (tone_scores.get("formal", {}).get("score", 0) +
             tone_scores.get("academic", {}).get("score", 0)) /
            max(0.01, tone_scores.get("casual", {}).get("score", 0) + 0.1), 2
        ),
        "word_count": len(words),
        "unique_word_ratio": round(len(set(words_lower)) / max(len(words_lower), 1), 3),
    }


def _build_outline(topic: str, depth: int, style: str,
                   target_word_count: int) -> dict:
    """Build a structured content outline."""
    structures = {
        "blog": {
            "sections": ["Introduction", "Background / Context", "Main Point 1", "Main Point 2", "Main Point 3", "Practical Tips", "Conclusion", "FAQ"],
            "per_section_words": lambda total, n: [int(total * w) for w in [0.08, 0.12, 0.18, 0.18, 0.18, 0.12, 0.08, 0.06]],
        },
        "essay": {
            "sections": ["Thesis Statement", "Background", "Argument 1", "Argument 2", "Counterargument", "Rebuttal", "Conclusion"],
            "per_section_words": lambda total, n: [int(total * w) for w in [0.05, 0.15, 0.2, 0.2, 0.15, 0.15, 0.1]],
        },
        "tutorial": {
            "sections": ["Overview", "Prerequisites", "Step 1: Setup", "Step 2: Core Implementation", "Step 3: Testing", "Step 4: Deployment", "Troubleshooting", "Next Steps"],
            "per_section_words": lambda total, n: [int(total * w) for w in [0.08, 0.05, 0.15, 0.25, 0.15, 0.15, 0.1, 0.07]],
        },
        "landing_page": {
            "sections": ["Hero / Hook", "Problem Statement", "Solution Overview", "Key Features", "Social Proof", "Pricing / CTA", "FAQ"],
            "per_section_words": lambda total, n: [int(total * w) for w in [0.1, 0.12, 0.15, 0.25, 0.15, 0.13, 0.1]],
        },
        "whitepaper": {
            "sections": ["Executive Summary", "Introduction", "Market Analysis", "Methodology", "Findings", "Recommendations", "Conclusion", "References"],
            "per_section_words": lambda total, n: [int(total * w) for w in [0.08, 0.1, 0.15, 0.15, 0.2, 0.15, 0.1, 0.07]],
        },
    }

    structure = structures.get(style, structures["blog"])
    sections = structure["sections"][:depth + 3] if depth < len(structure["sections"]) else structure["sections"]
    word_alloc = structure["per_section_words"](target_word_count, len(sections))

    outline = []
    for i, section_name in enumerate(sections):
        allocated = word_alloc[i] if i < len(word_alloc) else int(target_word_count / len(sections))
        subsections = []
        if depth >= 2 and i not in [0, len(sections) - 1]:
            sub_count = min(depth, 4)
            for j in range(sub_count):
                subsections.append({
                    "title": f"Sub-point {j + 1} for {section_name}",
                    "estimated_words": int(allocated / sub_count),
                    "notes": f"Expand on aspect {j + 1} of {section_name.lower()} related to {topic}",
                })

        outline.append({
            "section_number": i + 1,
            "title": section_name,
            "estimated_words": allocated,
            "subsections": subsections,
            "key_points": [f"Cover {topic} angle for {section_name.lower()}"],
        })

    return {
        "topic": topic,
        "style": style,
        "target_word_count": target_word_count,
        "depth": depth,
        "section_count": len(outline),
        "outline": outline,
        "seo_suggestions": {
            "primary_keyword": topic.lower(),
            "secondary_keywords": [f"{topic} guide", f"best {topic}", f"{topic} tips", f"how to {topic}"],
            "recommended_headings": "Use H2 for sections, H3 for subsections",
        },
    }


def _check_similarity(text_a: str, text_b: str) -> dict:
    """Check text similarity using multiple algorithms."""
    words_a = set(_tokenize_words(text_a.lower()))
    words_b = set(_tokenize_words(text_b.lower()))

    if not words_a or not words_b:
        return {"error": "Both texts must contain words"}

    # Jaccard similarity
    intersection = words_a & words_b
    union = words_a | words_b
    jaccard = len(intersection) / len(union) if union else 0

    # Cosine similarity on word frequencies
    all_words = list(union)
    freq_a = Counter(_tokenize_words(text_a.lower()))
    freq_b = Counter(_tokenize_words(text_b.lower()))
    vec_a = [freq_a.get(w, 0) for w in all_words]
    vec_b = [freq_b.get(w, 0) for w in all_words]
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    cosine = dot / (mag_a * mag_b) if mag_a and mag_b else 0

    # N-gram overlap (trigrams)
    def ngrams(text, n=3):
        words = text.lower().split()
        return set(tuple(words[i:i + n]) for i in range(len(words) - n + 1))

    tri_a = ngrams(text_a)
    tri_b = ngrams(text_b)
    trigram_overlap = len(tri_a & tri_b) / len(tri_a | tri_b) if (tri_a | tri_b) else 0

    # Overall similarity score
    overall = round((jaccard * 0.3 + cosine * 0.4 + trigram_overlap * 0.3) * 100, 1)

    if overall > 80:
        risk = "HIGH - Very similar content, likely derivative"
    elif overall > 50:
        risk = "MEDIUM - Significant overlap, needs rewriting"
    elif overall > 25:
        risk = "LOW - Some shared vocabulary, generally original"
    else:
        risk = "MINIMAL - Content appears original"

    return {
        "overall_similarity_pct": overall,
        "plagiarism_risk": risk,
        "metrics": {
            "jaccard_similarity": round(jaccard, 4),
            "cosine_similarity": round(cosine, 4),
            "trigram_overlap": round(trigram_overlap, 4),
        },
        "shared_words": sorted(list(intersection))[:30],
        "unique_to_a": sorted(list(words_a - words_b))[:20],
        "unique_to_b": sorted(list(words_b - words_a))[:20],
        "text_a_words": len(words_a),
        "text_b_words": len(words_b),
    }


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "Writing Assistant AI MCP",
    instructions="Content writing toolkit: headline generation, readability scoring, tone analysis, outline building, and plagiarism similarity checking. By MEOK AI Labs.")


@mcp.tool()
def generate_headlines(topic: str, style: str = "power", count: int = 5,
                       target_audience: str = "professionals", api_key: str = "") -> dict:
    """Generate headline variations for a given topic. Returns multiple options
    with SEO length checks and power word analysis.

    Args:
        topic: The subject/topic for headlines
        style: Headline style (listicle, how_to, question, power, seo)
        count: Number of headlines to generate (max 15)
        target_audience: Who the content is for
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": STRIPE_199}

    err = _check_rate_limit()
    if err:
        return {"error": err}
    try:
        return _generate_headlines(topic, style, min(count, 15), target_audience)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def score_readability(text: str, api_key: str = "") -> dict:
    """Calculate readability metrics for text: Flesch Reading Ease, Flesch-Kincaid
    Grade Level, Gunning Fog Index, Coleman-Liau Index. Also flags long sentences
    and filler words.

    Args:
        text: The text to analyze (minimum ~50 words recommended)
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": STRIPE_199}

    err = _check_rate_limit()
    if err:
        return {"error": err}
    try:
        return _score_readability(text)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def analyze_tone(text: str, api_key: str = "") -> dict:
    """Analyze the tone and style of text. Detects formal, casual, academic,
    persuasive, technical, and emotional tones. Also checks active vs passive
    voice and power word usage.

    Args:
        text: The text to analyze
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": STRIPE_199}

    err = _check_rate_limit()
    if err:
        return {"error": err}
    try:
        return _analyze_tone(text)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def build_outline(topic: str, depth: int = 2, style: str = "blog",
                  target_word_count: int = 1500, api_key: str = "") -> dict:
    """Build a structured content outline with sections, word allocations,
    and SEO keyword suggestions.

    Args:
        topic: The main topic to outline
        depth: Outline depth 1-4 (higher = more subsections)
        style: Content format (blog, essay, tutorial, landing_page, whitepaper)
        target_word_count: Target total word count
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": STRIPE_199}

    err = _check_rate_limit()
    if err:
        return {"error": err}
    try:
        return _build_outline(topic, min(depth, 4), style, target_word_count)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def check_similarity(text_a: str, text_b: str, api_key: str = "") -> dict:
    """Check similarity between two texts using Jaccard, cosine, and trigram
    overlap metrics. Returns a plagiarism risk assessment.

    Args:
        text_a: First text
        text_b: Second text to compare against
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": STRIPE_199}

    err = _check_rate_limit()
    if err:
        return {"error": err}
    try:
        return _check_similarity(text_a, text_b)
    except Exception as e:
        return {"error": str(e)}


def main():
    mcp.run()

if __name__ == '__main__':
    main()


# ── MEOK monetization layer (Stripe upgrade · PAYG · pricing) ──────────
# Free tier is zero-config. Upgrade to Pro (unlimited) or pay-as-you-go per call.
import os as _meok_os
MEOK_STRIPE_UPGRADE = "https://buy.stripe.com/00wfZjcgAeUW4c5cyQ8k90K"  # Pro (unlimited)
MEOK_PAYG_KEY = _meok_os.environ.get("MEOK_PAYG_KEY", "")  # set to enable PAYG (x402 / ~GBP0.05 per call)
MEOK_PRICING = "https://meok.ai/pricing"


def meok_upsell(tier: str = "free") -> dict:
    """Monetization options for free-tier callers: Pro upgrade, PAYG, or pricing page."""
    if tier != "free":
        return {}
    return {"upgrade_url": MEOK_STRIPE_UPGRADE,
            "payg_enabled": bool(MEOK_PAYG_KEY),
            "pricing": MEOK_PRICING}
