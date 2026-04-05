"""
CopyPasteDetector — Detects copy-paste propagation across clinical notes.

Identifies duplicated text blocks carried forward between encounters
without clinical review, a common documentation deficiency in long-term
care settings that compromises data integrity.

Author: Michael Kwakye Agyapong
"""

from typing import List, Tuple
from .analyzer import Deficiency


def _jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard similarity between two text strings."""
    set1 = set(text1.lower().split())
    set2 = set(text2.lower().split())
    if not set1 or not set2:
        return 0.0
    intersection = set1 & set2
    union = set1 | set2
    return len(intersection) / len(union)


def _ngram_similarity(text1: str, text2: str, n: int = 3) -> float:
    """Calculate n-gram overlap similarity between two texts."""
    def get_ngrams(text, n):
        words = text.lower().split()
        return set(tuple(words[i:i+n]) for i in range(len(words) - n + 1))

    ngrams1 = get_ngrams(text1, n)
    ngrams2 = get_ngrams(text2, n)
    if not ngrams1 or not ngrams2:
        return 0.0
    intersection = ngrams1 & ngrams2
    union = ngrams1 | ngrams2
    return len(intersection) / len(union)


class CopyPasteDetector:
    """
    Detects copy-paste propagation in clinical documentation.

    Uses Jaccard similarity and n-gram overlap to identify text blocks
    that have been copied from prior notes without clinical update.
    This is a well-documented source of documentation error in EHR
    systems, particularly in long-term care settings where longitudinal
    care generates repeated documentation about stable conditions.

    Parameters
    ----------
    config : dict
        Configuration dictionary with copy_paste settings.
    """

    def __init__(self, config: dict):
        cp_config = config.get("copy_paste", {})
        self.similarity_threshold = cp_config.get("similarity_threshold", 0.85)
        self.min_text_length = cp_config.get("min_text_length", 50)
        self.lookback_window = cp_config.get("lookback_window", 10)

    def detect(
        self,
        current_note: str,
        prior_notes: List[str],
    ) -> Tuple[List[Deficiency], float]:
        """
        Detect copy-paste content in the current note by comparing
        against prior notes.

        Parameters
        ----------
        current_note : str
            The clinical note to analyze.
        prior_notes : list of str
            Prior notes for comparison.

        Returns
        -------
        tuple of (list of Deficiency, float)
            Detected deficiencies and a copy-paste-free score (0-100).
        """
        deficiencies = []
        max_similarity = 0.0

        if not prior_notes or len(current_note) < self.min_text_length:
            return deficiencies, 100.0

        # Split current note into paragraphs for granular comparison
        paragraphs = [p.strip() for p in current_note.split("\n\n") if
                       len(p.strip()) >= self.min_text_length]

        for para in paragraphs:
            for i, prior_note in enumerate(prior_notes[-self.lookback_window:]):
                # Full text similarity
                jaccard = _jaccard_similarity(para, prior_note)
                ngram = _ngram_similarity(para, prior_note)
                combined = 0.6 * jaccard + 0.4 * ngram

                if combined > max_similarity:
                    max_similarity = combined

                if combined >= self.similarity_threshold:
                    severity = self._classify_severity(combined)
                    deficiencies.append(Deficiency(
                        category="Copy-Paste",
                        severity=severity,
                        description=(
                            f"{combined * 100:.0f}% similarity detected with "
                            f"prior note (note {i + 1} of {len(prior_notes)}) — "
                            f"possible carried-forward content without clinical update."
                        ),
                        text_span=para[:200] + "..." if len(para) > 200 else para,
                        recommended_action=(
                            "Review and update carried-forward text to reflect "
                            "current clinical status. Remove outdated information "
                            "and add current assessment findings."
                        ),
                    ))

        # Calculate copy-paste-free score
        if max_similarity >= self.similarity_threshold:
            score = max(0.0, (1.0 - max_similarity) * 100)
        else:
            score = 100.0

        return deficiencies, score

    def _classify_severity(self, similarity: float) -> str:
        """Classify deficiency severity based on similarity level."""
        if similarity >= 0.95:
            return "HIGH"
        elif similarity >= 0.90:
            return "MEDIUM"
        else:
            return "LOW"
