from src.analyzer.rule_based_flags import detect_rule_based_flags


def test_detects_auto_renewal_clause():
    flags = detect_rule_based_flags("This lease renews automatically unless cancelled.")

    titles = [f.title for f in flags]
    assert "Rinnovo automatico" in titles


def test_detects_early_termination_penalty():
    flags = detect_rule_based_flags("Tenant must pay a penalty for early termination.")

    titles = [f.title for f in flags]
    assert "Penale o recesso anticipato" in titles


def test_detects_short_deadline():
    flags = detect_rule_based_flags("You must respond within 5 days of receiving this notice.")

    titles = [f.title for f in flags]
    assert "Scadenza ravvicinata" in titles


def test_detects_phishing_style_urgency_and_credential_requests():
    flags = detect_rule_based_flags("Please verify your account immediately or it will be suspended.")

    titles = [f.title for f in flags]
    assert "Possibile phishing" in titles


def test_returns_empty_list_when_no_patterns_match():
    flags = detect_rule_based_flags("Just a friendly letter with no legal content.")

    assert flags == []


def test_quote_is_an_exact_substring_of_the_input_text():
    text = "This lease renews automatically unless cancelled."

    flags = detect_rule_based_flags(text)

    assert all(flag.quote in text for flag in flags)


def test_detects_multiple_distinct_patterns_in_the_same_text():
    text = "This lease renews automatically. Tenant must pay a penalty for early termination."

    flags = detect_rule_based_flags(text)

    assert len(flags) == 2
