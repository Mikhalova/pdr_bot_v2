"""Всі тексти інтерфейсу — лише українська."""

TEXTS = {
    "welcome": (
        "🚗 <b>Привіт! Я PDR Bot</b>\n\n"
        "Допоможу підготуватися до іспиту з правил дорожнього руху 🇺🇦\n\n"
        "Обирай режим:"
    ),
    "menu_title": "📋 <b>Головне меню</b>\n\nОбирай режим тестування:",
    "choose_topic": "📚 <b>Оберіть тему:</b>",
    "choose_ticket": "📋 <b>Оберіть білет:</b>",
    "loading": "⏳ Завантажую питання...",
    "no_questions": "❌ Питань не знайдено. Спробуй пізніше.",
    "question_header": "❓ <b>Питання {current}/{total}</b>",
    "correct": "✅ <b>Правильно!</b>",
    "wrong": "❌ <b>Неправильно!</b>\nПравильна відповідь: <b>{answer}</b>",
    "explanation_title": "💡 <b>Пояснення:</b>\n\n{text}",
    "no_explanation": "Пояснення відсутнє.",
    "answer_prompt": "\n\n<i>Обери відповідь:</i>",
    "test_result": (
        "🏁 <b>Тест завершено!</b>\n\n"
        "✅ Правильних: <b>{correct}</b> з {total}\n"
        "📊 Результат: <b>{percent}%</b>\n\n"
        "{verdict}"
    ),
    "verdict_pass": "🎉 Вітаю! Ти склав(ла) тест!",
    "verdict_fail": "😕 Не склав(ла). Ще трохи практики — і все вийде!",
    "exam_verdict_pass": "🎉 Вітаю! Іспит складено!",
    "exam_verdict_fail": "😕 Іспит не складено. Продовжуй тренуватись!",
    "no_mistakes": "🎉 Помилок немає! Так тримати!",
    "stats_title": "📊 <b>Твоя статистика</b>",
    "stats_body": (
        "📝 Пройдено тестів: <b>{tests}</b>\n"
        "✅ Правильних відповідей: <b>{correct}</b>\n"
        "❌ Неправильних: <b>{wrong}</b>\n"
        "📈 Загальний результат: <b>{percent}%</b>\n"
        "🔥 Серія правильних: <b>{streak}</b>"
    ),
    "stats_empty": "📊 Статистики поки немає. Пройди перший тест!",
    "exam_timer": "⏱ Залишилось: {minutes}:{seconds}",
    "exam_timeout": "⏰ <b>Час вийшов!</b>",
}


def t(key: str, **kwargs) -> str:
    text = TEXTS.get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text
