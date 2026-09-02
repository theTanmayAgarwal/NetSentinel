"""Teaching Generalization Rate (TGR) Evaluation Engine.

Evaluates semantic generalization on held-out unseen command variants after training.
TGR = (correctly classified held-out similar examples / total held-out similar examples) * 100
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from app.training.service import TrainingService


# Evaluation pairs: (taught training exemplar, held-out test variant)
HELD_OUT_EVALUATION_DATASET = [
    {
        "train": {
            "raw_text": "set xyz secure-admin-timeout 300",
            "category": "authentication",
            "parameter": "admin_session_timeout",
            "expected_value": "300",
            "control_id": "CIS-NET-18",
            "vendor": "unknown",
        },
        "held_out": [
            {
                "raw_text": "set xyz secure-admin-timeout 240",
                "expected_category": "authentication",
                "expected_parameter": "admin_session_timeout",
            },
            {
                "raw_text": "set xyz secure-admin-timeout 600",
                "expected_category": "authentication",
                "expected_parameter": "admin_session_timeout",
            },
        ],
    },
    {
        "train": {
            "raw_text": "system security password-policy min-length 14",
            "category": "password_policy",
            "parameter": "min_password_length",
            "expected_value": "14",
            "control_id": "CIS-NET-09",
            "vendor": "unknown",
        },
        "held_out": [
            {
                "raw_text": "system security password-policy min-length 16",
                "expected_category": "password_policy",
                "expected_parameter": "min_password_length",
            },
        ],
    },
]


def evaluate_tgr(training_service: TrainingService) -> Dict[str, Any]:
    """Calculate the Teaching Generalization Rate across the held-out evaluation dataset."""
    total_held_out = 0
    correct_held_out = 0
    eval_details = []

    for item in HELD_OUT_EVALUATION_DATASET:
        train_spec = item["train"]
        held_out_list = item["held_out"]

        # Ensure the training exemplar exists in the training service
        training_service.teach_exemplar(
            raw_text=train_spec["raw_text"],
            category=train_spec["category"],
            parameter=train_spec["parameter"],
            expected_value=train_spec["expected_value"],
            control_id=train_spec.get("control_id"),
            vendor=train_spec.get("vendor"),
        )

        for ho in held_out_list:
            total_held_out += 1
            res = training_service.classify_unknown_line(ho["raw_text"])

            suggested = res.get("suggested") or {}
            is_correct = (
                res.get("confidence", 0.0) >= 0.60
                and suggested.get("category") == ho["expected_category"]
                and suggested.get("parameter") == ho["expected_parameter"]
            )

            if is_correct:
                correct_held_out += 1

            eval_details.append(
                {
                    "held_out_command": ho["raw_text"],
                    "trained_command": train_spec["raw_text"],
                    "classified_category": suggested.get("category"),
                    "expected_category": ho["expected_category"],
                    "confidence": res.get("confidence", 0.0),
                    "is_correct": is_correct,
                }
            )

    tgr_rate = round((correct_held_out / total_held_out * 100.0), 1) if total_held_out > 0 else 0.0

    return {
        "tgr_percentage": tgr_rate,
        "total_held_out": total_held_out,
        "correctly_classified": correct_held_out,
        "evaluation_details": eval_details,
    }
