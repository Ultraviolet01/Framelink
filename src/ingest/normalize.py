"""
Framelink Ingestion — Text & Verdict Normalizer
Normalizes text, verdict labels, dates, publisher metadata, generates stable IDs, and preserves genuine origin & explanation data.
"""

import hashlib
from typing import Dict, Any

def generate_stable_id(prefix: str, text: str) -> str:
    """Generates a deterministic stable ID from text hash"""
    clean = text.strip().lower()
    digest = hashlib.sha256(clean.encode("utf-8")).hexdigest()[:8].upper()
    return f"{prefix}-{digest}"

def normalize_claim_record(raw_claim: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes Data Commons ClaimReview record into standardized schema.
    """
    text = raw_claim.get("text") or "COVID-19 Vaccine Claim"
    claim_reviews = raw_claim.get("claimReview", [{}])
    first_review = claim_reviews[0] if claim_reviews else {}
    
    publisher_info = first_review.get("publisher", {}) if isinstance(first_review, dict) else {}
    publisher_name = publisher_info.get("name") or raw_claim.get("publisher", "FactCheck Organization")
    
    verdict = first_review.get("textualRating") if isinstance(first_review, dict) else raw_claim.get("verdict", "False")
    rating_explanation = first_review.get("ratingExplanation", "") if isinstance(first_review, dict) else ""
    
    appearance_url = raw_claim.get("appearance_url", "")
    speaker_name = raw_claim.get("speaker_name", "")
    publisher_url = raw_claim.get("publisher_url") or (first_review.get("url") if isinstance(first_review, dict) else "")

    claim_variant_id = generate_stable_id("CV", text)
    claim_id = generate_stable_id("CLM", text)
    fact_check_id = generate_stable_id("FC", text + publisher_name)
    publisher_id = generate_stable_id("PUB", publisher_name)

    return {
        "claim_variant_id": claim_variant_id,
        "claim_id": claim_id,
        "fact_check_id": fact_check_id,
        "publisher_id": publisher_id,
        "text": text,
        "publisher_name": publisher_name,
        "verdict": verdict or "False",
        "rating_explanation": rating_explanation,
        "appearance_url": appearance_url,
        "speaker_name": speaker_name,
        "publisher_url": publisher_url,
        "language": "en",
        "date": raw_claim.get("claimDate") or "2021-06-01"
    }
