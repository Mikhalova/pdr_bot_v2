"""Хендлери тестів. Підтримка 2-5 варіантів відповідей."""

import random
from typing import Optional
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from translations import t
from keyboards import (
    kb_main_menu, kb_topics, kb_tickets,
    kb_answer_buttons, kb_after_answer, kb_end_test,
    format_answers_text,
)
import database as db

router = Router()

ANSWER_KEYS = ["a", "b", "c", "d", "e"]


class TestState(StatesGroup):
    in_test = State()
    in_exam = State()


def get_answers(q: dict) -> dict:
    return {k: q.get(f"answer_{k}") for k in ANSWER_KEYS if q.get(f"answer_{k}")}


async def send_question(bot: Bot, chat_id: int, state: FSMContext):
    data = await state.get_data()
    questions = data["questions"]
    idx = data["current_idx"]

    if idx >= len(questions):
        await finish_test(bot, chat_id, state)
        return

    q = questions[idx]
    answers = get_answers(q)
    answers_text = format_answers_text(answers)

    header = t("question_header", current=idx + 1, total=len(questions))
    full_text = (
        f"{header}\n\n"
        f"<b>{q['question']}</b>\n\n"
        f"{answers_text}"
        f"\n\n<i>Обери відповідь:</i>"
    )
    kb = kb_answer_buttons(q["id"], answers)

    if q.get("image_url"):
        try:
            await bot.send_photo(chat_id, photo=q["image_url"],
                                 caption=full_text, reply_markup=kb, parse_mode="HTML")
            return
        except Exception:
            pass
    await bot.send_message(chat_id, full_text, reply_markup=kb, parse_mode="HTML")


async def finish_test(bot: Bot, chat_id: int, state: FSMContext):
    data = await state.get_data()
    correct = data.get("correct_count", 0)
    total = len(data.get("questions", []))
    user_id = data.get("user_id")
    exam_mode = data.get("exam_mode", False)
    mode = data.get("mode", "random")

    percent = round(correct / total * 100) if total else 0
    passed = percent >= 75

    if exam_mode:
        verdict = t("exam_verdict_pass") if passed else t("exam_verdict_fail")
    else:
        verdict = t("verdict_pass") if passed else t("verdict_fail")

    text = t("test_result", correct=correct, total=total, percent=percent, verdict=verdict)

    if user_id:
        db.increment_tests(user_id)

    await state.clear()
    await bot.send_message(chat_id, text, reply_markup=kb_end_test(mode), parse_mode="HTML")


# ── Меню ─────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "menu:random")
async def cb_random(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    questions = db.get_random_questions(20)
    if not questions:
        await callback.message.answer(t("no_questions"))
        await callback.answer()
        return
    await state.set_state(TestState.in_test)
    await state.set_data({"questions": questions, "current_idx": 0,
                          "correct_count": 0, "exam_mode": False,
                          "mode": "random", "user_id": callback.from_user.id})
    await callback.answer()
    await send_question(callback.bot, callback.message.chat.id, state)


@router.callback_query(F.data == "menu:topics")
async def cb_menu_topics(callback: CallbackQuery):
    topics = db.get_topics()
    if not topics:
        await callback.message.answer(t("no_questions"))
        await callback.answer()
        return
    await callback.message.answer(t("choose_topic"),
                                  reply_markup=kb_topics(topics), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("topic:"))
async def cb_topic_selected(callback: CallbackQuery, state: FSMContext):
    topic_id = int(callback.data.split(":")[1])
    questions = db.get_questions_by_topic(topic_id)
    if not questions:
        await callback.message.answer(t("no_questions"))
        await callback.answer()
        return
    await state.set_state(TestState.in_test)
    await state.set_data({"questions": questions, "current_idx": 0,
                          "correct_count": 0, "exam_mode": False,
                          "mode": "topic", "user_id": callback.from_user.id})
    await callback.answer()
    await send_question(callback.bot, callback.message.chat.id, state)


@router.callback_query(F.data == "menu:tickets")
async def cb_menu_tickets(callback: CallbackQuery):
    ticket_ids = db.get_tickets()
    if not ticket_ids:
        await callback.message.answer(t("no_questions"))
        await callback.answer()
        return
    await callback.message.answer(t("choose_ticket"),
                                  reply_markup=kb_tickets(ticket_ids), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("ticket:"))
async def cb_ticket_selected(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":")[1]

    # Випадковий білет
    if val == "random":
        ticket_ids = db.get_tickets()
        if not ticket_ids:
            await callback.message.answer(t("no_questions"))
            await callback.answer()
            return
        ticket_id = random.choice(ticket_ids)
    else:
        ticket_id = int(val)

    questions = db.get_questions_by_ticket(ticket_id)
    if not questions:
        await callback.message.answer(t("no_questions"))
        await callback.answer()
        return

    await state.set_state(TestState.in_test)
    await state.set_data({"questions": questions, "current_idx": 0,
                          "correct_count": 0, "exam_mode": False,
                          "mode": "ticket", "user_id": callback.from_user.id,
                          "ticket_id": ticket_id})
    await callback.answer()

    label = f"Білет №{ticket_id}" if val != "random" else f"🎲 Випадковий білет №{ticket_id}"
    await callback.message.answer(
        f"📋 <b>{label}</b> — {len(questions)} питань\n\nПочинаємо!",
        parse_mode="HTML"
    )
    await send_question(callback.bot, callback.message.chat.id, state)


@router.callback_query(F.data == "menu:mistakes")
async def cb_mistakes(callback: CallbackQuery, state: FSMContext):
    questions = db.get_mistake_questions(callback.from_user.id)
    if not questions:
        await callback.message.answer(t("no_mistakes"), reply_markup=kb_main_menu(),
                                      parse_mode="HTML")
        await callback.answer()
        return
    await state.set_state(TestState.in_test)
    await state.set_data({"questions": questions, "current_idx": 0,
                          "correct_count": 0, "exam_mode": False,
                          "mode": "random", "user_id": callback.from_user.id})
    await callback.answer()
    await send_question(callback.bot, callback.message.chat.id, state)


@router.callback_query(F.data == "menu:exam")
async def cb_exam(callback: CallbackQuery, state: FSMContext):
    questions = db.get_random_questions(20)
    if not questions:
        await callback.message.answer(t("no_questions"))
        await callback.answer()
        return
    await state.set_state(TestState.in_exam)
    await state.set_data({"questions": questions, "current_idx": 0,
                          "correct_count": 0, "exam_mode": True,
                          "mode": "exam", "user_id": callback.from_user.id})
    await callback.answer()
    await send_question(callback.bot, callback.message.chat.id, state)


# ── Відповідь ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("answer:"))
async def cb_answer(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    q_id = int(parts[1])
    user_answer = parts[2]

    data = await state.get_data()
    if not data:
        await callback.answer("Сесія закінчилась. Почни новий тест /start")
        return

    questions = data["questions"]
    idx = data["current_idx"]
    exam_mode = data.get("exam_mode", False)
    user_id = data.get("user_id")

    q = next((x for x in questions if x["id"] == q_id), None)
    if not q:
        q = questions[idx] if idx < len(questions) else None
    if not q:
        await callback.answer()
        return

    correct_key = q.get("correct", "a").lower()
    is_correct = user_answer == correct_key

    if user_id:
        db.update_stats(user_id, is_correct, q["id"])

    if is_correct:
        await state.update_data(correct_count=data.get("correct_count", 0) + 1)
        result_text = t("correct")
    else:
        labels = {"a": "1", "b": "2", "c": "3", "d": "4", "e": "5"}
        right_label = labels.get(correct_key, correct_key)
        right_text = q.get(f"answer_{correct_key}", "")
        result_text = t("wrong", answer=f"{right_label}. {right_text}")

    has_explanation = bool(q.get("explanation")) and not exam_mode

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await callback.message.answer(
        result_text,
        reply_markup=kb_after_answer(q["id"], has_explanation),
        parse_mode="HTML"
    )
    await callback.answer()


# ── Пояснення ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("expl:"))
async def cb_explanation(callback: CallbackQuery, state: FSMContext):
    q_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    q = None
    if data:
        q = next((x for x in data.get("questions", []) if x["id"] == q_id), None)

    if q and q.get("explanation"):
        await callback.message.answer(
            t("explanation_title", text=q["explanation"]), parse_mode="HTML"
        )
    else:
        await callback.answer(t("no_explanation"), show_alert=True)
        return
    await callback.answer()


# ── Наступне питання ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "next:question")
async def cb_next_question(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data:
        await callback.answer("Сесія закінчилась. Почни новий тест /start")
        return

    idx = data["current_idx"] + 1
    await state.update_data(current_idx=idx)

    if idx >= len(data["questions"]):
        await finish_test(callback.bot, callback.message.chat.id, state)
    else:
        await send_question(callback.bot, callback.message.chat.id, state)

    await callback.answer()
