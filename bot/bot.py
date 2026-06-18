import asyncio
import os

import httpx
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

TOKEN = os.getenv("BOT_TOKEN")
API = os.getenv("API_URL", "http://backend:8000/api")

active = {}  # uid -> state


def kb_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пройти тест", callback_data="tests")],
        [InlineKeyboardButton(text="Мои результаты", callback_data="results")],
    ])


def kb_tests(tests):
    btns = []
    for t in tests:
        btns.append([InlineKeyboardButton(text=t["title"], callback_data="go:" + str(t["id"]))])
    btns.append([InlineKeyboardButton(text="← Назад", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=btns)


def kb_answers(q):
    btns = []
    for a in q["answers"]:
        btns.append([InlineKeyboardButton(
            text=a["text"],
            callback_data="a:%s:%s" % (q["id"], a["id"]),
        )])
    return InlineKeyboardMarkup(inline_keyboard=btns)


async def req(method, path, **kw):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await getattr(client, method)(API + path, **kw)
        r.raise_for_status()
        return r.json()


async def show_tests(msg, edit=False):
    tests = await req("get", "/tests")
    if not tests:
        txt = "Сейчас нет доступных тестов. Загляни позже."
        kb = kb_menu()
    else:
        lines = []
        for t in tests:
            line = "• %s — %s вопр." % (t["title"], t["questions_count"])
            if t.get("description"):
                line += "\n  %s" % t["description"]
            lines.append(line)
        txt = "Выбери тест:\n\n" + "\n".join(lines)
        kb = kb_tests(tests)

    if edit:
        await msg.edit_text(txt, reply_markup=kb)
    else:
        await msg.answer(txt, reply_markup=kb)


async def show_results(msg, tg_id, edit=False):
    try:
        rows = await req("get", "/users/%s/attempts" % tg_id)
    except httpx.HTTPError:
        rows = []

    if not rows:
        txt = "Ты ещё не проходил тесты.\nНажми «Пройти тест», чтобы начать."
    else:
        txt = "Твои последние результаты:\n\n"
        for r in rows[:10]:
            txt += "• %s — %s из %s (%s%%)\n" % (
                r["test_title"], r["score"], r["total"], r["percentage"],
            )

    if edit:
        await msg.edit_text(txt, reply_markup=kb_menu())
    else:
        await msg.answer(txt, reply_markup=kb_menu())


async def step(msg, uid):
    s = active[uid]
    i = s["i"]
    qs = s["qs"]

    if i >= len(qs):
        payload = {
            "telegram_id": s["tg"],
            "username": s.get("un"),
            "first_name": s.get("fn"),
            "answers": s["picked"],
        }
        try:
            res = await req("post", "/tests/%s/submit" % s["tid"], json=payload)
        except httpx.HTTPError:
            await msg.answer(
                "Не удалось сохранить результат.\nПопробуй пройти тест ещё раз.",
                reply_markup=kb_menu(),
            )
            del active[uid]
            return

        p = res["percentage"]
        if p >= 80:
            comment = "Отличный результат!"
        elif p >= 50:
            comment = "Неплохо, но есть над чем поработать."
        else:
            comment = "Попробуй пройти тест ещё раз — получится лучше."

        await msg.answer(
            "Тест завершён.\n\n"
            "Правильных ответов: %s из %s (%s%%)\n\n"
            "%s" % (res["score"], res["total"], p, comment),
            reply_markup=kb_menu(),
        )
        del active[uid]
        return

    q = qs[i]
    await msg.answer(
        "%s\n\n"
        "Вопрос %s из %s\n"
        "%s" % (s["title"], i + 1, len(qs), q["text"]),
        reply_markup=kb_answers(q),
    )


async def on_start(msg):
    name = msg.from_user.first_name or "друг"
    await msg.answer(
        "Привет, %s!\n\n"
        "Здесь можно проходить тесты и смотреть свои результаты.\n"
        "Выбери, что хочешь сделать:" % name,
        reply_markup=kb_menu(),
    )


async def on_tests(msg):
    await show_tests(msg)


async def on_results(msg):
    await show_results(msg, msg.from_user.id)


async def on_click(cb: CallbackQuery):
    uid = cb.from_user.id
    d = cb.data

    if d == "menu":
        await cb.message.edit_text("Главное меню", reply_markup=kb_menu())
        await cb.answer()
        return

    if d == "tests":
        await show_tests(cb.message, edit=True)
        await cb.answer()
        return

    if d == "results":
        await show_results(cb.message, uid, edit=True)
        await cb.answer()
        return

    if d.startswith("go:"):
        tid = int(d.split(":")[1])
        test = await req("get", "/tests/%s/public" % tid)
        active[uid] = {
            "tid": tid,
            "title": test["title"],
            "qs": test["questions"],
            "i": 0,
            "picked": [],
            "tg": cb.from_user.id,
            "un": cb.from_user.username,
            "fn": cb.from_user.first_name,
        }
        await cb.message.delete()
        await step(cb.message, uid)
        await cb.answer()
        return

    if d.startswith("a:"):
        parts = d.split(":")
        qid, aid = int(parts[1]), int(parts[2])
        if uid not in active:
            await cb.answer("Сессия истекла. Начни тест заново.", show_alert=True)
            return
        s = active[uid]
        s["picked"].append({"question_id": qid, "answer_id": aid})
        s["i"] += 1
        await cb.message.delete()
        await step(cb.message, uid)
        await cb.answer()
        return

    await cb.answer()


async def wait_backend():
    for _ in range(30):
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                if (await c.get(API + "/tests")).status_code == 200:
                    return
        except Exception:
            pass
        await asyncio.sleep(2)
    raise SystemExit("backend down")


async def run():
    if not TOKEN:
        raise SystemExit("BOT_TOKEN?")

    await wait_backend()

    bot = Bot(TOKEN)
    dp = Dispatcher()
    dp.message.register(on_start, CommandStart())
    dp.message.register(on_tests, Command("tests"))
    dp.message.register(on_results, Command("results"))
    dp.callback_query.register(on_click)

    print("bot up")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run())
