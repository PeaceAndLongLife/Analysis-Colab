"""
Student Response Helpfulness Evaluator — Traditional ML Edition
===============================================================
Packages used (no hand-rolled replacements):
  • scikit-learn  — TF-IDF vectorisation, cosine similarity,
                    built-in English stop-word list, token analyser
  • vaderSentiment — VADER lexicon-based sentiment (ships its own
                    lexicon; no NLTK corpus download needed)
  • numpy          — weighted score aggregation & clipping

The only non-library code is a ~10-line Flesch-Kincaid syllable
approximation, which no installable package provides without NLTK's
cmudict corpus (blocked in this environment).
"""

import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# ── Shared objects (instantiated once) ───────────────────────────────────────

_sia = SentimentIntensityAnalyzer()          # VADER — ships its own 7 500-word lexicon

# sklearn's TF-IDF analyser handles lower-casing, punctuation stripping,
# and stop-word removal — no hand-rolled tokeniser needed
_tfidf = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)


# ── Minimal syllable helper (no suitable package works without NLTK cmudict) ──

def _count_syllables(word: str) -> int:
    """Regex vowel-group approximation — only fallback where no lib suffices."""
    word = word.lower().rstrip("e") or word.lower()
    return max(1, len(re.findall(r"[aeiou]+", word)))


# ── Feature scorers — each delegates to a library wherever possible ───────────

def feat_semantic_relevance(inquiry: str, response: str) -> float:
    """
    sklearn TF-IDF (1-2 grams, English stop-words) + cosine similarity.
    Measures how on-topic the response is relative to the inquiry.
    """
    try:
        matrix = _tfidf.fit_transform([inquiry, response])
        return float(np.clip(cosine_similarity(matrix[0:1], matrix[1:2])[0][0], 0, 1))
    except Exception:
        return 0.0


def feat_sentiment(response: str) -> float:
    """
    VADER compound score (vaderSentiment library).
    Maps [-1, +1] to [0, 1]; positive/informative language scores higher.
    """
    compound = _sia.polarity_scores(response)["compound"]   # library call
    return float((compound + 1) / 2)


def feat_keyword_coverage(inquiry: str, response: str) -> float:
    """
    Fraction of meaningful inquiry tokens (sklearn stop-word filtered)
    that appear anywhere in the response.
    sklearn's built-in analyser does tokenisation + stop-word removal.
    """
    analyse = TfidfVectorizer(stop_words="english").build_analyzer()
    inq_tokens  = set(analyse(inquiry))
    resp_tokens = set(analyse(response))
    if not inq_tokens:
        return 0.5
    return float(len(inq_tokens & resp_tokens) / len(inq_tokens))


def feat_completeness(inquiry: str, response: str) -> float:
    """
    Response length vs. a minimum expected length derived from inquiry
    complexity (word count as proxy). Uses sklearn's analyser for counts.
    """
    analyse = TfidfVectorizer(stop_words="english").build_analyzer()
    inq_words  = len(analyse(inquiry))
    resp_words = len(analyse(response))
    # Expect at least 4x the inquiry content words; score plateaus at 8x
    expected_good = max(40, inq_words * 8)
    return float(np.clip(resp_words / expected_good, 0, 1))


def feat_readability(response: str) -> float:
    """
    Flesch-Kincaid Reading Ease.
    Ideal student range ~40-80; scores outside are penalised.
    (textstat requires NLTK cmudict which is unavailable here.)
    """
    words = re.findall(r"\b[a-z]+\b", response.lower())
    sents = [s for s in re.split(r"(?<=[.!?])\s+", response.strip()) if s]
    if not words or not sents:
        return 0.0
    asl  = len(words) / len(sents)
    asw  = sum(_count_syllables(w) for w in words) / len(words)
    fk   = float(np.clip(206.835 - 1.015 * asl - 84.6 * asw, 0, 100))
    if 40 <= fk <= 80:
        return 1.0
    return float(fk / 40) if fk < 40 else float(1 - (fk - 80) / 20)


def feat_specificity(response: str) -> float:
    """
    Rewards concrete detail:
      - numeric tokens  (formulae, measurements, years, etc.)
      - causal/logical connectors (because, therefore, thus ...)
    Uses sklearn's ENGLISH_STOP_WORDS for content-word filtering.
    """
    tokens       = re.findall(r"\b\w+\b", response.lower())
    content_toks = [t for t in tokens if t not in ENGLISH_STOP_WORDS]  # sklearn list
    numerics     = re.findall(r"\b\d+\.?\d*\b", response)
    connectors   = {"because", "therefore", "thus", "hence", "since",
                    "result", "leads", "causes", "consequently", "means"}
    conn_hits    = len(set(content_toks) & connectors)

    numeric_score   = float(np.clip(len(numerics) / 3, 0, 1))
    connector_score = float(np.clip(conn_hits / 2,    0, 1))
    ttr = len(set(content_toks)) / len(content_toks) if content_toks else 0

    return float(0.4 * ttr + 0.35 * numeric_score + 0.25 * connector_score)


# ── Weighted aggregation ──────────────────────────────────────────────────────

WEIGHTS = {
    "semantic_relevance": 0.30,
    "completeness":       0.25,
    "keyword_coverage":   0.20,
    "specificity":        0.15,
    "readability":        0.05,
    "sentiment":          0.05,
}

THRESHOLD = 0.50   # weighted score above which a response is "helpful"


def evaluate_helpfulness(student_inquiry: str, response: str) -> dict:
    """
    Evaluate whether a response to a student inquiry is helpful.

    Returns
    -------
    dict
        is_helpful  bool        Overall pass/fail
        score       float       0-10 weighted score
        label       str         "Helpful" | "Partially Helpful" | "Not Helpful"
        breakdown   dict        Per-feature 0-1 scores
        feedback    list[str]   Targeted improvement tips for weak dimensions
    """
    scores = {
        "semantic_relevance": feat_semantic_relevance(student_inquiry, response),
        "completeness":       feat_completeness(student_inquiry, response),
        "keyword_coverage":   feat_keyword_coverage(student_inquiry, response),
        "specificity":        feat_specificity(response),
        "readability":        feat_readability(response),
        "sentiment":          feat_sentiment(response),
    }

    weighted = float(sum(scores[k] * WEIGHTS[k] for k in WEIGHTS))
    score_10 = round(weighted * 10, 2)

    if weighted >= 0.70:
        label, is_helpful = "Helpful", True
    elif weighted >= THRESHOLD:
        label, is_helpful = "Partially Helpful", True
    else:
        label, is_helpful = "Not Helpful", False

    feedback = []
    if scores["semantic_relevance"] < 0.35:
        feedback.append("Response seems off-topic — address the inquiry more directly.")
    if scores["completeness"] < 0.40:
        feedback.append("Too brief — expand with more detail and explanation.")
    if scores["keyword_coverage"] < 0.40:
        feedback.append("Key terms from the question are missing in the response.")
    if scores["specificity"] < 0.35:
        feedback.append("Add concrete examples, numbers, or step-by-step reasoning.")
    if scores["readability"] < 0.40:
        feedback.append("Adjust sentence length and vocabulary for student readability.")
    if scores["sentiment"] < 0.40:
        feedback.append("Use clearer, more positive and informative language.")
    if not feedback:
        feedback.append("All quality criteria met — no major improvements needed.")

    return {
        "is_helpful": is_helpful,
        "score":      score_10,
        "label":      label,
        "breakdown":  {k: round(v, 3) for k, v in scores.items()},
        "weights":    WEIGHTS,
        "feedback":   feedback,
    }


# ── Pretty printer ────────────────────────────────────────────────────────────

_BAR = 22

def _bar(v: float) -> str:
    n = round(v * _BAR)
    return "█" * n + "░" * (_BAR - n)

def print_evaluation(inquiry: str, response: str, result: dict) -> None:
    icons = {"Helpful": "✅", "Partially Helpful": "⚠️", "Not Helpful": "❌"}
    icon  = icons[result["label"]]
    print("\n" + "═" * 68)
    print("  📚  STUDENT RESPONSE HELPFULNESS EVALUATOR")
    print("═" * 68)
    print(f"\n  🎓 Inquiry : {inquiry}")
    print(f"  💬 Response: {response[:120]}{'...' if len(response) > 120 else ''}")
    print(f"\n  {icon}  Verdict : {result['label']}   |   Score: {result['score']} / 10\n")
    print(f"  {'Feature':<22}  {'Score bar':<24}  Raw   Weight")
    print("  " + "-" * 60)
    for feat, val in result["breakdown"].items():
        w = result["weights"][feat]
        print(f"  {feat:<22}  {_bar(val)}  {val:.3f}   {w}")
    print("\n  💡 Feedback:")
    for tip in result["feedback"]:
        print(f"     • {tip}")
    print("═" * 68)


# ── Demo ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cases = [
        (
            "Can you explain what photosynthesis is?",
            "Photosynthesis is the process by which green plants use sunlight, water, "
            "and carbon dioxide to produce glucose and oxygen. The equation is: "
            "6CO2 + 6H2O + light -> C6H12O6 + 6O2. It takes place in chloroplasts, "
            "using chlorophyll to capture light energy, through two stages: the "
            "light-dependent reactions and the Calvin cycle.",
        ),
        (
            "How do I solve a quadratic equation?",
            "You just plug numbers into the formula.",
        ),
        (
            "What caused World War I?",
            "World War I was triggered by the assassination of Archduke Franz Ferdinand "
            "in 1914, but underlying causes included militarism, the alliance systems "
            "(Triple Entente vs. Triple Alliance), imperialism, and rising nationalism. "
            "These factors meant a local conflict rapidly escalated into a global war.",
        ),
        (
            "What is Newton's second law of motion?",
            "It has something to do with force and mass, maybe.",
        ),
    ]

    for inquiry, response in cases:
        result = evaluate_helpfulness(inquiry, response)
        print_evaluation(inquiry, response, result)