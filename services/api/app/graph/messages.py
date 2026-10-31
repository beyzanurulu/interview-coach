"""Sabit mülakatçı metinleri. LLM gerektirmez; kaymaya ve hatalara karşı güvenli."""

from app.graph.state import AnswerType, EndReason, Language

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

FALLBACK_WARMUP = {
    "tr": "Kendinizden ve bu role neden ilgi duyduğunuzdan kısaca bahseder misiniz?",
    "en": "Could you briefly introduce yourself and tell me why this role interests you?",
}

CANDIDATE_INVITE = {
    "tr": "Benim sorularım bu kadar. Son olarak, sizin bize sormak istediğiniz bir şey var mı?",
    "en": "That's all from my side. Before we wrap up, is there anything you'd like to ask us?",
}

CANDIDATE_ANOTHER = {
    "tr": "Başka bir sorunuz var mı?",
    "en": "Is there anything else you'd like to ask?",
}

CANDIDATE_FALLBACK_ANSWER = {
    "tr": "Bu konuda size net bilgi veremiyorum; İK ekibimiz süreçle ilgili size ayrıca dönüş yapacaktır.",
    "en": "I can't give you a definite answer on that; our HR team will follow up with you.",
}

# Model yanıt veremediğinde: aday soru sormuş da olabilir, sormamış da; ikisine de uyan cevap.
CANDIDATE_ERROR_REPLY = {
    "tr": "Teşekkür ederim; sorularınız olursa İK ekibimiz size ayrıca dönüş yapacaktır.",
    "en": "Thank you; if you have any questions, our HR team will follow up with you.",
}

CLOSING: dict[EndReason, dict[Language, str]] = {
    "completed": {
        "tr": "Görüşmemiz burada sona eriyor. Katıldığınız için teşekkür ederim, başarılar dilerim!",
        "en": "That brings us to the end. Thank you for your time, and best of luck!",
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

REPEAT_QUESTION = {
    "tr": "Sorumu tekrarlıyorum: {question}",
    "en": "Let me repeat my question: {question}",
}

# Cevap olmayan mesajlara verilecek yanıtlar. İkinci eleman, davranış tekrarlandığında
# kullanılan daha net uyarıdır. Mülakat sonlandırılmaz (ürün kararı: uyarıyla devam).
REDIRECTS: dict[AnswerType, dict[Language, tuple[str, str]]] = {
    "off_topic": {
        "tr": (
            "Bu, mülakatımızın konusu dışında kalıyor; mülakata dönelim.",
            "Pratikten en iyi verimi almanız için mülakat sorularına odaklanmanızı rica ediyorum.",
        ),
        "en": (
            "That's outside the scope of our interview; let's get back to it.",
            "To get the most out of this practice, please focus on the interview questions.",
        ),
    },
    "asks_for_answer": {
        "tr": (
            "Mülakat sırasında cevap öneremiyorum; sizin kendi yaklaşımınızı duymak istiyorum.",
            "Bu bir mülakat pratiği; cevabı sizin vermeniz gerekiyor.",
        ),
        "en": (
            "I can't suggest answers during the interview; I'd like to hear your own approach.",
            "This is interview practice, so the answer needs to come from you.",
        ),
    },
    "ai_question": {
        "tr": (
            "Evet, ben yapay zekâ tabanlı bir mülakat koçuyum; bu görüşmeyi gerçek bir mülakat gibi yürütüyorum.",
            "Evet, yapay zekâ tabanlı bir mülakat koçuyum.",
        ),
        "en": (
            "Yes, I'm an AI interview coach; I'm running this like a real interview.",
            "Yes, I'm an AI interview coach.",
        ),
    },
    "inappropriate": {
        "tr": (
            "Lütfen profesyonel bir dil kullanalım.",
            "Mülakat boyunca profesyonel bir dil kullanmanızı tekrar rica ediyorum.",
        ),
        "en": (
            "Let's please keep the conversation professional.",
            "Once again, please keep the conversation professional.",
        ),
    },
    "unclear": {
        "tr": ("Cevabınızı tam anlayamadım.", "Cevabınızı yine anlayamadım."),
        "en": ("I didn't quite catch your answer.", "I still didn't catch your answer."),
    },
}
