import re

from src.analyzer.schemas import RedFlag

_RULES = [
    {
        "pattern": re.compile(r"rinnov\w*\s+automatic\w*|renews?\s+automatically", re.IGNORECASE),
        "title": "Rinnovo automatico",
        "description": (
            "Il documento sembra contenere una clausola di rinnovo automatico: "
            "verifica i termini e le scadenze per la disdetta."
        ),
        "severity": "medium",
    },
    {
        "pattern": re.compile(r"penalt(?:y|ies)|penale\w*|recesso\s+anticipat\w*", re.IGNORECASE),
        "title": "Penale o recesso anticipato",
        "description": (
            "Il documento menziona una penale o una clausola di recesso anticipato: "
            "verifica l'importo e le condizioni applicate."
        ),
        "severity": "high",
    },
    {
        "pattern": re.compile(r"entro\s+\d+\s+giorni|within\s+\d+\s+days", re.IGNORECASE),
        "title": "Scadenza ravvicinata",
        "description": (
            "Il documento indica una scadenza espressa in giorni: "
            "verifica che i tempi indicati siano rispettabili."
        ),
        "severity": "medium",
    },
]


def detect_rule_based_flags(text: str) -> list[RedFlag]:
    flags = []
    for rule in _RULES:
        match = rule["pattern"].search(text)
        if match:
            flags.append(
                RedFlag(
                    title=rule["title"],
                    description=rule["description"],
                    severity=rule["severity"],
                    quote=match.group(0),
                )
            )
    return flags
