"""Клавіатури бота. Підтримка 2-5 варіантів відповідей."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ── Головне меню ──────────────────────────────────────────────────────────────

def kb_main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📋 Білети", callback_data="menu:tickets"))
    builder.row(InlineKeyboardButton(text="📚 Теми", callback_data="menu:topics"))
    builder.row(InlineKeyboardButton(text="🎲 20 випадкових", callback_data="menu:random"))
    builder.row(InlineKeyboardButton(text="❌ Робота над помилками", callback_data="menu:mistakes"))
    builder.row(InlineKeyboardButton(text="⏱ Режим іспиту", callback_data="menu:exam"))
    builder.row(InlineKeyboardButton(text="📊 Статистика", callback_data="menu:stats"))
    return builder.as_markup()


# ── Список тем ────────────────────────────────────────────────────────────────

def kb_topics(topics: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for topic in topics:
        builder.row(InlineKeyboardButton(
            text=topic["name"],
            callback_data=f"topic:{topic['id']}"
        ))
    builder.row(InlineKeyboardButton(text="🏠 Головне меню", callback_data="menu:home"))
    return builder.as_markup()


def kb_tickets(ticket_ids: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # Кнопка випадкового білету зверху
    builder.row(InlineKeyboardButton(text="🎲 Випадковий білет", callback_data="ticket:random"))
    # Всі білети по 6 в рядку
    buttons = [
        InlineKeyboardButton(text=f"№{tid}", callback_data=f"ticket:{tid}")
        for tid in ticket_ids
    ]
    builder.add(*buttons)
    builder.adjust(6)
    builder.row(InlineKeyboardButton(text="🏠 Головне меню", callback_data="menu:home"))
    return builder.as_markup()


# ── Відповідь: нумерований список у тексті, кнопки — тільки цифри ─────────────

def kb_answer_buttons(question_id: int, answers: dict) -> InlineKeyboardMarkup:
    """
    answers = {"a": "...", "b": "...", "c": "...", "d": "...", "e": "..." (опц.)}
    Кнопки: 1 / 2 / 3 / 4 / 5 — скільки є варіантів.
    """
    builder = InlineKeyboardBuilder()
    labels = {"a": "1", "b": "2", "c": "3", "d": "4", "e": "5"}
    keys_present = [k for k in ["a", "b", "c", "d", "e"] if answers.get(k)]
    buttons = [
        InlineKeyboardButton(
            text=labels[k],
            callback_data=f"answer:{question_id}:{k}"
        )
        for k in keys_present
    ]
    builder.row(*buttons)
    return builder.as_markup()


def format_answers_text(answers: dict) -> str:
    """Варіанти відповідей як нумерований список у тексті питання."""
    labels = {"a": "1", "b": "2", "c": "3", "d": "4", "e": "5"}
    lines = []
    for k in ["a", "b", "c", "d", "e"]:
        text = answers.get(k)
        if text:
            lines.append(f"{labels[k]}. {text}")
    return "\n".join(lines)


# ── Після відповіді ───────────────────────────────────────────────────────────

def kb_after_answer(question_id: int, has_explanation: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_explanation:
        builder.row(InlineKeyboardButton(text="💡 Пояснення", callback_data=f"expl:{question_id}"))
    builder.row(InlineKeyboardButton(text="➡️ Далі", callback_data="next:question"))
    return builder.as_markup()


# ── Кінець тесту ─────────────────────────────────────────────────────────────

def kb_end_test(mode: str = "random") -> InlineKeyboardMarkup:
    """mode: 'random' | 'ticket' | 'topic' | 'exam'"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔄 Ще тест", callback_data="menu:random"))
    if mode == "ticket":
        builder.row(InlineKeyboardButton(text="◀️ До білетів", callback_data="menu:tickets"))
    elif mode == "topic":
        builder.row(InlineKeyboardButton(text="◀️ До тем", callback_data="menu:topics"))
    builder.row(InlineKeyboardButton(text="🏠 Головне меню", callback_data="menu:home"))
    return builder.as_markup()


# ── Статистика ────────────────────────────────────────────────────────────────

def kb_stats() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏠 Головне меню", callback_data="menu:home"))
    return builder.as_markup()
