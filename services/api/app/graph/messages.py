"""Sabit mülakatçı metinleri (LLM gerektirmez, hata durumunda da çalışır)."""

from app.graph.state import EndReason, Language

GREETING = {
    "tr": (
        "Merhaba, hoş geldiniz! {role} pozisyonu için yaklaşık {minutes} dakikalık bir "
        "mülakat yapacağız. Hazırsanız başlayalım."
    ),
    "en": (
        "Hi, welcome! We'll have an interview of about {minutes} minutes for the {role} "
        "position. If you're ready, let's begin."
    ),
}

CLOSING: dict[EndReason, dict[Language, str]] = {
    "completed": {
        "tr": "Sorularım bu kadardı. Katıldığınız için teşekkür ederim, başarılar dilerim!",
        "en": "That's all my questions. Thank you for your time, and best of luck!",
    },
    "timeout": {
        "tr": "Süremiz doldu, mülakatı burada bitiriyoruz. Katıldığınız için teşekkür ederim!",
        "en": "We're out of time, so we'll stop here. Thank you for joining!",
    },
    "user_ended": {
        "tr": "Peki, mülakatı burada sonlandırıyoruz. Katıldığınız için teşekkürler!",
        "en": "Alright, we'll end the interview here. Thanks for joining!",
    },
}
