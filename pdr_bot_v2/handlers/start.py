from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from translations import t
from keyboards import kb_main_menu
import database as db

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    db.init_db()
    await message.answer(t("welcome"), reply_markup=kb_main_menu(), parse_mode="HTML")


@router.callback_query(lambda c: c.data == "menu:home")
async def cb_home(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(t("menu_title"), reply_markup=kb_main_menu(), parse_mode="HTML")
    await callback.answer()
