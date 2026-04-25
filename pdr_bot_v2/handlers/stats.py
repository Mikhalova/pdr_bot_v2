from aiogram import Router, F
from aiogram.types import CallbackQuery

from translations import t
from keyboards import kb_stats
import database as db

router = Router()


@router.callback_query(F.data == "menu:stats")
async def cb_stats(callback: CallbackQuery):
    user_id = callback.from_user.id
    stats   = db.get_stats(user_id)

    if stats["tests"] == 0:
        text = t("stats_empty")
    else:
        text = (
            f"{t('stats_title')}\n\n"
            f"📝 Пройдено тестів: <b>{stats['tests']}</b>\n"
            f"✅ Правильних відповідей: <b>{stats['correct']}</b>\n"
            f"❌ Неправильних: <b>{stats['wrong']}</b>\n"
            f"📈 Загальний результат: <b>{stats.get('percent', 0)}%</b>\n"
            f"🔥 Серія правильних: <b>{stats['streak']}</b>"
        )

    await callback.message.answer(text, reply_markup=kb_stats(), parse_mode="HTML")
    await callback.answer()
