import pytest

from app.guardrails.output import (
    candidate_answer_issues,
    mentions_cv,
    question_issues,
    transition_issues,
    wrong_language,
)


@pytest.mark.parametrize(
    ("text", "language"),
    [
        ("Hangi projede React kullandınız ve sizin rolünüz neydi?", "tr"),
        ("REST API tasarlarken HTTP durum kodlarını nasıl kullanırsınız?", "tr"),
        ("Could you describe a time you handled a conflict in your team?", "en"),
    ],
)
def test_good_questions_pass(text: str, language: str) -> None:
    assert question_issues(text, language) == []


def test_question_issues_detect_problems() -> None:
    issues = question_issues("Harika bir cevap! Peki ya testler? Ve CI?", "tr")
    assert any("övgü" in i for i in issues) and any("birden fazla" in i for i in issues)
    assert question_issues("", "tr") == ["boş"]
    assert any("uzun" in i for i in question_issues("Bu " * 200 + "nedir?", "tr"))


def test_wrong_language_detection() -> None:
    assert wrong_language("What did you build with FastAPI?", "tr")
    assert wrong_language("Bu projede neler yaptınız?", "en")
    assert not wrong_language("FastAPI ile neler yaptınız?", "tr")
    assert not wrong_language("How did you use Docker in that project?", "en")


def test_transition_rules() -> None:
    assert transition_issues("", "en") == []
    assert transition_issues("Thanks, noted.", "en") == []
    assert transition_issues("That is a clear example of effective communication.", "en")
    assert transition_issues("Anladım, peki neden?", "tr")


def test_candidate_answer_blocks_hiring_promises() -> None:
    assert candidate_answer_issues("İlanda hibrit çalışma belirtiliyor.", "tr") == []
    assert candidate_answer_issues("Tebrikler, işe alındınız!", "tr")


def test_internal_terms_are_blocked() -> None:
    assert candidate_answer_issues("İlan özetinde maaş bilgisi bulunmamaktadır.", "tr")
    assert question_issues("Job summary says Docker; how did you use it?", "en")
    assert candidate_answer_issues("Bu detay ilanda yer almıyor, İK size dönecek.", "tr")
    assert candidate_answer_issues("Bu bilgi mevcut verilerde yer almamaktadır.", "tr")
    assert candidate_answer_issues("The salary is not specified in the job description.", "en")


def test_mentions_cv() -> None:
    assert mentions_cv("CV'nizdeki projeyi anlatır mısınız?")
    assert mentions_cv("Özgeçmişinizde yazan stajdan bahseder misiniz?")
    assert not mentions_cv("En yakın projenizi anlatır mısınız?")
