"""
PDR Scraper — vodiy.ua з Playwright (headless Chrome)
======================================================
vodiy.ua використовує Vue.js, тому потрібен браузер.

Запуск:
    pip install playwright
    playwright install chromium
    python scraper.py

Результат: questions.json (~1700+ питань категорія B)
"""

import asyncio
import json
import re
import sys
from pathlib import Path

OUTPUT_FILE = "questions.json"
BASE_URL = "https://vodiy.ua"
COMPLECT = 6  # Нові 2026

# Теми категорії B (ID з vodiy.ua)
THEME_IDS = list(range(1, 36))   # теми 1-35
TICKET_IDS = list(range(1, 91))  # білети 1-90


async def parse_page(page, url: str, topic_id: int, topic_name: str, ticket_id) -> list:
    """Відкриваємо сторінку і парсимо питання через JS."""
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
    except Exception as e:
        print(f"    ❌ Не завантажилось: {e}")
        return []

    # Отримуємо питання через JavaScript прямо з Vue-компонента / DOM
    questions = await page.evaluate("""
    () => {
        const results = [];
        
        // Спроба 1: знайти питання в DOM
        const blocks = document.querySelectorAll(
            '.question, .test-question, [class*="question"], article'
        );
        
        for (const block of blocks) {
            const text = block.innerText || '';
            if (text.length < 10) continue;
            
            // Шукаємо текст питання
            const qEl = block.querySelector(
                '.question__text, .question-text, h2, h3, .title, p'
            );
            const qText = qEl ? qEl.innerText.trim() : '';
            if (!qText || qText.length < 5) continue;
            
            // Шукаємо варіанти відповідей
            const answerEls = block.querySelectorAll(
                '.answer, .option, li, [class*="answer"]'
            );
            const answers = [];
            let correct = 0;
            
            answerEls.forEach((el, i) => {
                const t = el.innerText.trim().replace(/^[1-4АБВГABCDabcd]\\.\\s*/, '');
                if (t && t.length > 0) {
                    answers.push(t);
                    const cls = el.className || '';
                    if (/correct|right|true|active/i.test(cls)) correct = i;
                }
            });
            
            if (answers.length >= 2) {
                const img = block.querySelector('img');
                results.push({
                    question: qText,
                    answers: answers,
                    correct: correct,
                    image_url: img ? (img.src || img.dataset.src || null) : null
                });
            }
        }
        
        // Спроба 2: знайти дані у window.__vue__ або у Vue-інстансах
        if (results.length === 0) {
            try {
                const vueApp = document.querySelector('#app')?.__vue__;
                if (vueApp) {
                    const store = vueApp.$store;
                    if (store) {
                        const state = store.state;
                        // Шукаємо масиви питань у стані Vuex
                        for (const key of Object.keys(state)) {
                            const val = state[key];
                            if (Array.isArray(val) && val.length > 0) {
                                const first = val[0];
                                if (first && (first.question || first.text || first.title)) {
                                    return val;
                                }
                            }
                        }
                    }
                }
            } catch(e) {}
        }
        
        return results;
    }
    """)

    if not questions:
        # Спроба 3: перехопити через мережу — дивимось XHR відповіді
        return []

    results = []
    keys = ["a", "b", "c", "d"]

    for i, q in enumerate(questions):
        # Нормалізуємо структуру
        if isinstance(q, dict):
            if "question" in q and "answers" in q:
                # Наша структура з DOM
                answers_list = q.get("answers", [])
                correct_idx = q.get("correct", 0)
                correct_key = keys[correct_idx] if correct_idx < 4 else "a"
                results.append({
                    "id": None,
                    "topic_id": topic_id,
                    "topic_name": topic_name,
                    "ticket_id": ticket_id,
                    "question": q["question"],
                    "image_url": q.get("image_url"),
                    "answer_a": answers_list[0] if len(answers_list) > 0 else None,
                    "answer_b": answers_list[1] if len(answers_list) > 1 else None,
                    "answer_c": answers_list[2] if len(answers_list) > 2 else None,
                    "answer_d": answers_list[3] if len(answers_list) > 3 else None,
                    "correct": correct_key,
                    "explanation": q.get("explanation"),
                    "source_url": url,
                })
            else:
                # Структура з Vuex store
                raw_q = q.get("question") or q.get("text") or q.get("title", "")
                raw_answers = q.get("answers") or q.get("options") or []
                if isinstance(raw_answers, list) and raw_q:
                    correct_raw = q.get("correct") or q.get("right") or q.get("correct_answer", 0)
                    if isinstance(correct_raw, int):
                        correct_key = keys[correct_raw] if correct_raw < 4 else "a"
                    else:
                        correct_key = str(correct_raw).lower()
                    
                    results.append({
                        "id": q.get("id"),
                        "topic_id": topic_id,
                        "topic_name": topic_name,
                        "ticket_id": ticket_id,
                        "question": raw_q,
                        "image_url": q.get("image") or q.get("image_url"),
                        "answer_a": raw_answers[0] if len(raw_answers) > 0 else None,
                        "answer_b": raw_answers[1] if len(raw_answers) > 1 else None,
                        "answer_c": raw_answers[2] if len(raw_answers) > 2 else None,
                        "answer_d": raw_answers[3] if len(raw_answers) > 3 else None,
                        "correct": correct_key,
                        "explanation": q.get("explanation") or q.get("comment"),
                        "source_url": url,
                    })

    return results


async def get_themes(page) -> list:
    """Отримати список тем."""
    await page.goto(f"{BASE_URL}/pdr/test/?complect={COMPLECT}", wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(2000)

    # Шукаємо посилання на теми
    links = await page.query_selector_all("a[href*='theme='], a[href*='tema=']")
    themes = []
    for link in links:
        href = await link.get_attribute("href")
        text = (await link.inner_text()).strip()
        m = re.search(r"theme=(\d+)|tema=(\d+)", href or "")
        if m and text:
            tid = int(m.group(1) or m.group(2))
            full_url = BASE_URL + href if not href.startswith("http") else href
            if not any(t["id"] == tid for t in themes):
                themes.append({"id": tid, "name": text, "url": full_url})

    if not themes:
        # Fallback: використовуємо відомі ID
        for i in THEME_IDS:
            themes.append({
                "id": i,
                "name": f"Тема {i}",
                "url": f"{BASE_URL}/pdr/test/?complect={COMPLECT}&theme={i}"
            })

    return themes


async def main():
    print("=" * 55)
    print("  PDR Scraper — vodiy.ua (Playwright)")
    print("  Офіційна база ПДР України, ~1700 питань")
    print("=" * 55)

    from playwright.async_api import async_playwright

    all_questions = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="uk-UA",
        )
        page = await context.new_page()

        # Перехоплення мережевих запитів (для API)
        api_responses = []

        async def on_response(response):
            if response.status == 200:
                ct = response.headers.get("content-type", "")
                if "json" in ct and any(k in response.url for k in ["question", "test", "bilet", "theme", "ticket"]):
                    try:
                        body = await response.json()
                        api_responses.append((response.url, body))
                    except Exception:
                        pass

        page.on("response", on_response)

        # Отримуємо теми
        print("\n📋 Отримую список тем...")
        themes = await get_themes(page)
        print(f"   Знайдено: {len(themes)} тем")

        # Парсинг по темах
        print(f"\n📚 Парсинг по темах:")
        for theme in themes:
            print(f"  [{theme['id']:2d}] {theme['name'][:40]}", end=" ... ", flush=True)
            api_responses.clear()

            qs = await parse_page(page, theme["url"], theme["id"], theme["name"], None)

            # Якщо DOM не дав результату — перевіряємо API
            if not qs and api_responses:
                for url, body in api_responses:
                    if isinstance(body, list):
                        for item in body:
                            if isinstance(item, dict) and ("question" in item or "text" in item):
                                raw_q = item.get("question") or item.get("text", "")
                                answers = item.get("answers") or item.get("options") or []
                                correct_raw = item.get("correct", 0)
                                if isinstance(correct_raw, int):
                                    correct_key = ["a","b","c","d"][correct_raw] if correct_raw < 4 else "a"
                                else:
                                    correct_key = str(correct_raw).lower()
                                qs.append({
                                    "id": item.get("id"),
                                    "topic_id": theme["id"],
                                    "topic_name": theme["name"],
                                    "ticket_id": None,
                                    "question": raw_q,
                                    "image_url": item.get("image") or item.get("image_url"),
                                    "answer_a": answers[0] if len(answers) > 0 else None,
                                    "answer_b": answers[1] if len(answers) > 1 else None,
                                    "answer_c": answers[2] if len(answers) > 2 else None,
                                    "answer_d": answers[3] if len(answers) > 3 else None,
                                    "correct": correct_key,
                                    "explanation": item.get("explanation"),
                                    "source_url": url,
                                })

            print(f"{len(qs)} питань")
            all_questions.extend(qs)
            await asyncio.sleep(0.5)

        # Парсинг по білетах
        print(f"\n📋 Парсинг по білетах (1-90):")
        for tid in TICKET_IDS:
            url = f"{BASE_URL}/pdr/test/?complect={COMPLECT}&bilet={tid}"
            print(f"  Білет {tid:2d}", end=" ... ", flush=True)
            api_responses.clear()

            qs = await parse_page(page, url, 0, "", tid)
            print(f"{len(qs)} питань")
            all_questions.extend(qs)
            await asyncio.sleep(0.4)

        page.remove_listener("response", on_response)
        await browser.close()

    # Дедублікація
    seen, unique = set(), []
    for q in all_questions:
        key = (q.get("question") or "")[:80]
        if key and key not in seen:
            seen.add(key)
            unique.append(q)

    # Нумерація
    for i, q in enumerate(unique):
        if not q.get("id"):
            q["id"] = i + 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*55}")
    print(f"✅ Збережено {len(unique)} питань → {OUTPUT_FILE}")

    if len(unique) < 50:
        print("\n⚠️  Мало питань! Запусти з --debug для діагностики:")
        print("   python scraper.py --debug")
    print(f"{'='*55}")


async def debug():
    """Показати структуру сторінки."""
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = f"{BASE_URL}/pdr/test/?complect={COMPLECT}&theme=1"
        print(f"Завантажую: {url}")
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)

        # Виводимо структуру DOM
        structure = await page.evaluate("""
        () => {
            const info = {
                classes_with_question: [],
                sample_text: document.body.innerText.substring(0, 2000),
                links_count: document.querySelectorAll('a').length,
                vue_detected: !!document.querySelector('#app')?.__vue__,
            };
            
            // Знаходимо всі унікальні класи
            document.querySelectorAll('*').forEach(el => {
                const cls = el.className;
                if (typeof cls === 'string' && 
                    (cls.includes('question') || cls.includes('answer') || cls.includes('test'))) {
                    if (!info.classes_with_question.includes(cls)) {
                        info.classes_with_question.push(cls);
                    }
                }
            });
            
            return info;
        }
        """)

        print("\n=== СТРУКТУРА DOM ===")
        print(f"Vue.js: {structure['vue_detected']}")
        print(f"Класи з 'question/answer/test': {structure['classes_with_question'][:20]}")
        print("\n=== ТЕКСТ СТОРІНКИ ===")
        print(structure['sample_text'])

        await browser.close()


if __name__ == "__main__":
    if "--debug" in sys.argv:
        asyncio.run(debug())
    else:
        asyncio.run(main())
