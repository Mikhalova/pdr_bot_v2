import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

QUESTIONS_PER_TEST = 20
PASS_SCORE = 75
EXAM_TIME_SECONDS = 1200  # 20 хвилин

DB_PATH = "pdr_bot.db"
QUESTIONS_CACHE = "questions.json"

BASE_URL = "https://pdrtest.com"
