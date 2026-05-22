"""
Student Response Helpfulness Evaluator — Traditional ML Edition
===============================================================
Uses scikit-learn (TF-IDF, cosine similarity, feature scaling)
and pure-Python NLP to evaluate helpfulness without any LLM API.

Features extracted per (inquiry, response) pair:
  1. Semantic Relevance   – TF-IDF cosine similarity
  2. Completeness         – Response length relative to inquiry complexity
  3. Readability          – Flesch-Kincaid Reading Ease (pure Python)
  4. Sentiment Polarity   – Lexicon-based positive/negative word ratio
  5. Keyword Coverage     – Fraction of inquiry keywords answered
  6. Specificity          – Number ratio / technical term density

All sub-scores are scaled to [0, 1] and combined into a weighted
helpfulness score. The threshold for "helpful" is 0.50.
"""

import re
import math
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler


# ── Sentiment lexicons (concise but effective) ────────────────────────────────

POSITIVE_WORDS = {
    "good", "great", "excellent", "correct", "right", "clear", "helpful",
    "accurate", "complete", "detailed", "thorough", "well", "best", "proper",
    "effective", "useful", "informative", "specific", "precise", "exact",
    "explain", "example", "because", "therefore", "thus", "result", "means",
    "process", "step", "method", "formula", "equation", "defined", "shows",
}

NEGATIVE_WORDS = {
    "wrong", "bad", "unclear", "vague", "incomplete", "missing", "confusing",
    "irrelevant", "unhelpful", "incorrect", "error", "fail", "poor", "weak",
    "just", "only", "simply", "maybe", "perhaps", "idk", "dunno", "stuff",
    "things", "whatever", "etc", "somehow", "kind", "sort",
}

# Stopwords (inline to avoid NLTK dependency)
STOPWORDS = {
    "a", "an", "the", "is", "it", "in", "of", "to", "and", "or", "for",
    "with", "on", "at", "by", "this", "that", "are", "was", "be", "as",
    "from", "but", "not", "you", "i", "we", "they", "he", "she", "do",
    "does", "did", "has", "have", "had", "will", "would", "can", "could",
    "should", "its", "what", "how", "why", "when", "where", "which", "who",
    "me", "my", "your", "our", "their", "there", "here", "so", "if", "then",
    "than", "more", "some", "about", "into", "also", "just",
}


# ── Text utilities ────────────────────────────────────────────────────────────

def tokenize(text: str) -> list[str]:
    """Lowercase, strip punctuation, split into word tokens."""
    return re.findall(r"\b[a-z]+\b", text.lower())


def sentences(text: str) -> list[str]:
    """Split text into sentences using punctuation heuristics."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p]


def syllable_count(word: str) -> int:
    """Approximate syllable count for Flesch-Kincaid."""
    word = word.lower().rstrip("e")
    count = len(re.findall(r"[aeiou]+", word))
    return max(1, count)


# ── Individual feature scorers ────────────────────────────────────────────────

def score_relevance(inquiry: str, response: str) -> float:
    """TF-IDF cosine similarity between inquiry and response (0–1)."""
    try:
        vectorizer = TfidfVectorizer(stop_words="english", min_df=1)
        tfidf = vectorizer.fit_transform([inquiry, response])
        sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        return float(np.clip(sim, 0.0, 1.0))
    except Exception:
        return 0.0


def score_completeness(inquiry: str, response: str) -> float:
    """
    Completeness heuristic:
      - Inquiry word count determines expected response length.
      - Penalises very short responses, rewards detail (up to a ceiling).
    """
    inq_words = len(tokenize(inquiry))
    resp_words = len(tokenize(response))
    # Expect at least 3–5× the inquiry word count for a complete answer
    expected_min = max(20, inq_words * 3)
    expected_good = max(60, inq_words * 6)
    if resp_words == 0:
        return 0.0
    if resp_words >= expected_good:
        return 1.0
    return float(resp_words / expected_good)


def score_readability(response: str) -> float:
    """
    Flesch-Kincaid Reading Ease scaled to [0, 1].
    Higher = easier to read for a student.
    Formula: 206.835 – 1.015*(words/sentences) – 84.6*(syllables/words)
    Scores: 90–100 very easy, 60–70 standard, <30 very difficult.
    We target student-friendly range ~50–80 → map 0–100 to 0–1
    (penalise both extremes: too hard and too simplistic).
    """
    sents = sentences(response)
    words = tokenize(response)
    if not sents or not words:
        return 0.0
    avg_sent_len = len(words) / len(sents)
    avg_syllables = sum(syllable_count(w) for w in words) / len(words)
    fk_score = 206.835 - 1.015 * avg_sent_len - 84.6 * avg_syllables
    fk_score = max(0.0, min(100.0, fk_score))
    # Ideal for students: 50–80 → penalise being outside this zone
    ideal_low, ideal_high = 40.0, 85.0
    if ideal_low <= fk_score <= ideal_high:
        return 1.0
    elif fk_score < ideal_low:
        return float(fk_score / ideal_low)
    else:
        return float(1.0 - (fk_score - ideal_high) / (100.0 - ideal_high))


def score_sentiment(response: str) -> float:
    """
    Lexicon-based sentiment ratio.
    More positive/informative words → higher score.
    """
    tokens = set(tokenize(response))
    pos_hits = len(tokens & POSITIVE_WORDS)
    neg_hits = len(tokens & NEGATIVE_WORDS)
    total = pos_hits + neg_hits
    if total == 0:
        return 0.5   # neutral — neither good nor bad
    return float(pos_hits / total)


def score_keyword_coverage(inquiry: str, response: str) -> float:
    """
    Fraction of meaningful inquiry keywords that appear in the response.
    Filters stopwords to focus on content words.
    """
    inq_tokens = {w for w in tokenize(inquiry) if w not in STOPWORDS and len(w) > 2}
    if not inq_tokens:
        return 0.5
    resp_tokens = set(tokenize(response))
    covered = inq_tokens & resp_tokens
    return float(len(covered) / len(inq_tokens))


def score_specificity(response: str) -> float:
    """
    Specificity = presence of numbers, formulas, and non-stopword variety.
    Rewards concrete, detailed answers.
    """
    # Count numeric tokens (stats, formulae, measurements)
    numeric_hits = len(re.findall(r"\b\d+\.?\d*\b", response))

    # Unique meaningful words (type-token ratio on content words)
    tokens = [w for w in tokenize(response) if w not in STOPWORDS]
    if not tokens:
        return 0.0
    ttr = len(set(tokens)) / len(tokens)   # 0–1; higher = more varied vocab

    # Presence of explanatory connectors
    connectors = {"because", "therefore", "thus", "since", "which", "means",
                  "result", "hence", "so", "due", "leads", "causes", "shows"}
    connector_hits = len(set(tokens) & connectors)

    numeric_score = min(1.0, numeric_hits / 3.0)       # cap at 3 numbers
    connector_score = min(1.0, connector_hits / 2.0)   # cap at 2 connectors
    return float(0.4 * ttr + 0.3 * numeric_score + 0.3 * connector_score)


# ── Main evaluator ────────────────────────────────────────────────────────────

WEIGHTS = {
    "relevance":         0.30,
    "completeness":      0.25,
    "keyword_coverage":  0.20,
    "specificity":       0.15,
    "readability":       0.05,
    "sentiment":         0.05,
}

HELPFULNESS_THRESHOLD = 0.50


def evaluate_helpfulness(student_inquiry: str, response: str) -> dict:
    """
    Evaluate whether a response to a student inquiry is helpful.

    Parameters
    ----------
    student_inquiry : str   The student's original question.
    response        : str   The answer given to the student.

    Returns
    -------
    dict with keys:
        is_helpful  bool        Overall judgment (True / False)
        score       float       Weighted score 0–10
        breakdown   dict        Individual sub-scores (0–1 each)
        label       str         "Helpful" | "Partially Helpful" | "Not Helpful"
        feedback    list[str]   Actionable suggestions for weak areas
    """
    scores = {
        "relevance":         score_relevance(student_inquiry, response),
        "completeness":      score_completeness(student_inquiry, response),
        "keyword_coverage":  score_keyword_coverage(student_inquiry, response),
        "specificity":       score_specificity(response),
        "readability":       score_readability(response),
        "sentiment":         score_sentiment(response),
    }

    weighted = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS)
    normalised_score = round(weighted * 10, 2)  # 0–10 scale

    # Determine label
    if weighted >= HELPFULNESS_THRESHOLD:
        is_helpful = True
        label = "Helpful" if weighted >= 0.70 else "Partially Helpful"
    else:
        is_helpful = False
        label = "Not Helpful"

    # Generate feedback for weak dimensions
    feedback = []
    if scores["relevance"] < 0.35:
        feedback.append("Response appears off-topic — make sure it directly addresses the question.")
    if scores["completeness"] < 0.40:
        feedback.append("Response is too brief; provide more detail and explanation.")
    if scores["keyword_coverage"] < 0.40:
        feedback.append("Key terms from the inquiry are missing in the response.")
    if scores["specificity"] < 0.35:
        feedback.append("Add concrete examples, numbers, or step-by-step reasoning.")
    if scores["readability"] < 0.40:
        feedback.append("Adjust sentence length and vocabulary for student-level clarity.")
    if scores["sentiment"] < 0.35:
        feedback.append("Use clearer, more informative language instead of vague terms.")
    if not feedback:
        feedback.append("Response meets all quality criteria — no major improvements needed.")

    return {
        "is_helpful":   is_helpful,
        "score":        normalised_score,
        "label":        label,
        "breakdown":    {k: round(v, 3) for k, v in scores.items()},
        "weights_used": WEIGHTS,
        "feedback":     feedback,
    }


# ── Pretty printer ────────────────────────────────────────────────────────────

BAR_WIDTH = 20

def _bar(value: float) -> str:
    filled = round(value * BAR_WIDTH)
    return "█" * filled + "░" * (BAR_WIDTH - filled)

def print_evaluation(inquiry: str, response: str, result: dict):
    label_icons = {"Helpful": "✅", "Partially Helpful": "⚠️", "Not Helpful": "❌"}
    icon = label_icons.get(result["label"], "❓")

    print("\n" + "═" * 65)
    print("  📚  STUDENT RESPONSE HELPFULNESS EVALUATOR  (ML Edition)")
    print("═" * 65)
    print(f"\n  🎓 Inquiry :\n     {inquiry}")
    print(f"\n  💬 Response:\n     {response}")
    print(f"\n  {icon}  Verdict : {result['label']}")
    print(f"  📊 Score   : {result['score']} / 10\n")

    print("  Sub-scores (feature breakdown):")
    print("  " + "-" * 53)
    for feature, val in result["breakdown"].items():
        w = result["weights_used"][feature]
        print(f"  {feature:<20} {_bar(val)}  {val:.2f}  (w={w})")

    print("\n  💡 Feedback:")
    for tip in result["feedback"]:
        print(f"     • {tip}")
    print("═" * 65)


# ── Demo ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_cases = [
        (
            "Can you explain what photosynthesis is?",
            (
                "Photosynthesis is the process by which green plants use sunlight, "
                "water, and carbon dioxide to produce glucose and oxygen. The chemical "
                "equation is: 6CO₂ + 6H₂O + light → C₆H₁₂O₆ + 6O₂. It takes place "
                "in chloroplasts, which contain chlorophyll—the green pigment that "
                "captures light energy. There are two stages: the light-dependent "
                "reactions and the Calvin cycle (light-independent reactions)."
            ),
        ),
        (
            "How do I solve a quadratic equation?",
            "You just plug numbers into the formula.",
        ),
        (
            "What caused World War I?",
            (
                "World War I was triggered by the assassination of Archduke Franz "
                "Ferdinand in 1914, but underlying causes included militarism, alliance "
                "systems (Triple Entente vs Triple Alliance), imperialism, and rising "
                "nationalism. The alliance structure meant that a local conflict rapidly "
                "escalated into a continental, then global, war."
            ),
        ),
        (
            "What is Newton's second law of motion?",
            "It has something to do with force and mass maybe.",
        ),
    ]

    for inquiry, response in test_cases:
        result = evaluate_helpfulness(inquiry, response)
        print_evaluation(inquiry, response, result)