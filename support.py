import asyncio
import json
import logging
import os
import re
import time
from collections import defaultdict, deque

from dotenv import load_dotenv
from aiogram import BaseMiddleware, Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

logging.basicConfig(level=logging.INFO)
load_dotenv()

# Separate token: this is a DIFFERENT bot from your main one.
bot = Bot(token=os.getenv("SUPPORT_BOT_TOKEN"))
dp = Dispatcher()

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
MAIN_BOT = os.getenv("MAIN_BOT", "@jigyarobot")
DATA_DIR = os.getenv("DATA_DIR", ".")
FILE = os.path.join(DATA_DIR, "support.json")

MAX_MSGS_PER_MINUTE = 5
ACK_EVERY_SECONDS = 600
MAX_THREADS = 6000

# ---------------------------------------------------------------- texts

TEXTS = {
    "en": {
        "choose_lang": "Choose your language",
        "menu": "Hi! Here you can read answers to common questions or write to us.",
        "btn_faq": "❓ FAQ",
        "btn_write": "✍️ Write to support",
        "faq_title": "Choose a question:",
        "back": "⬅️ Back",
        "write_hint": "Just send your message here (text, photo or voice) and we'll reply as soon as we can.",
        "ack": "Got it ✅ We'll reply here when we can.",
        "too_fast": "You're sending messages too fast. Please wait a minute.",
        "send_failed": "Couldn't send your message right now. Please try again later.",
        "lang_set": "Language changed ✅",
    },
    "ru": {
        "choose_lang": "Выбери язык",
        "menu": "Привет! Здесь можно посмотреть ответы на частые вопросы или написать нам.",
        "btn_faq": "❓ Частые вопросы",
        "btn_write": "✍️ Написать в поддержку",
        "faq_title": "Выбери вопрос:",
        "back": "⬅️ Назад",
        "write_hint": "Просто отправь сообщение сюда (текст, фото или голосовое), и мы ответим, как только сможем.",
        "ack": "Принято ✅ Ответим здесь, как только сможем.",
        "too_fast": "Ты пишешь слишком часто. Подожди минуту.",
        "send_failed": "Сейчас не получилось отправить сообщение. Попробуй позже.",
        "lang_set": "Язык изменён ✅",
    },
    "hy": {
        "choose_lang": "Ընտրեք լեզուն",
        "menu": "Բարև։ Այստեղ կարող եք կարդալ հաճախ տրվող հարցերի պատասխանները կամ գրել մեզ։",
        "btn_faq": "❓ Հաճախակի հարցեր",
        "btn_write": "✍️ Գրել աջակցությանը",
        "faq_title": "Ընտրեք հարցը՝",
        "back": "⬅️ Հետ",
        "write_hint": "Պարզապես ուղարկեք ձեր հաղորդագրությունն այստեղ (տեքստ, լուսանկար կամ ձայնային), և մենք կպատասխանենք հնարավորինս շուտ։",
        "ack": "Ընդունված է ✅ Կպատասխանենք այստեղ։",
        "too_fast": "Դուք շատ արագ եք գրում։ Խնդրում եմ սպասեք մեկ րոպե։",
        "send_failed": "Այս պահին չհաջողվեց ուղարկել հաղորդագրությունը։ Փորձեք ավելի ուշ։",
        "lang_set": "Լեզուն փոխվեց ✅",
    },
}

# FAQ: list of (question, answer). Edit these to match your bot.
FAQ = {
    "en": [
        (
            "How do I create a profile?",
            "Open the main bot {main}, tap “Create profile” and go through the steps: name, age, gender, city, “about me” and photos. The bot is only for people 14 and older.",
        ),
        (
            "Why don't I see any profiles?",
            "There may be no new profiles yet: there are not many people in the bot, and you only see people you haven't seen before. Come back later. Without VIP you see both men and women.",
        ),
        (
            "What does VIP give?",
            "VIP shows your profile more often, adds a ⭐ badge, shows who liked you, allows more photos and unlimited likes, and lets you choose who to look for. See the plans in the “⭐ VIP” section of the main bot.",
        ),
        (
            "How do I pay, and what if the payment failed?",
            "Payment is made with Telegram Stars right in the bot (“⭐ VIP” → choose a plan). If Stars were charged but VIP didn't turn on, or you want a refund, write to us here and tell us the time of the payment.",
        ),
        (
            "How do I contact my match?",
            "On a mutual like the bot sends you the person's @username. If you have no @username, set one in Telegram settings (Settings → Username), otherwise people can't message you.",
        ),
        (
            "How do I delete my profile?",
            "In the main bot tap “Delete profile”. If you want all your data removed, write to us here.",
        ),
        (
            "How do I report a user?",
            "Under every profile there is a “Report” button. We review reports.",
        ),
    ],
    "ru": [
        (
            "Как создать анкету?",
            "Открой основной бот {main}, нажми «Создать анкету» и пройди шаги: имя, возраст, пол, город, «о себе» и фото. Бот только для тех, кому 14 и больше.",
        ),
        (
            "Почему я не вижу анкеты?",
            "Новых анкет может пока не быть: людей в боте немного, и показываются только те, кого ты ещё не видел. Загляни позже. Без VIP показываются и парни, и девушки.",
        ),
        (
            "Что даёт VIP?",
            "VIP показывает твою анкету чаще, ставит значок ⭐, показывает, кто тебя лайкнул, даёт больше фото, безлимитные лайки и выбор, кого искать. Тарифы смотри в разделе «⭐ VIP» основного бота.",
        ),
        (
            "Как оплатить и что, если оплата не прошла?",
            "Оплата идёт звёздами Telegram прямо в боте («⭐ VIP» → выбери тариф). Если звёзды списались, а VIP не включился, или нужен возврат, напиши нам сюда и укажи время оплаты.",
        ),
        (
            "Как написать тому, с кем совпали?",
            "При взаимном лайке бот присылает @юзернейм человека. Если у тебя нет @юзернейма, поставь его в настройках Telegram (Настройки → Имя пользователя), иначе тебе не смогут написать.",
        ),
        (
            "Как удалить анкету?",
            "В основном боте нажми «Удалить анкету». Если нужно удалить все данные, напиши нам сюда.",
        ),
        (
            "Как пожаловаться?",
            "Под каждой анкетой есть кнопка «Пожаловаться». Мы рассматриваем жалобы.",
        ),
    ],
    "hy": [
        (
            "Ինչպե՞ս լրացնել հարցաթերթիկ",
            "Բացեք հիմնական բոտը {main}, սեղմեք «Լրացնել հարցաթերթիկ» և անցեք քայլերը՝ անուն, տարիք, սեռ, քաղաք, «իմ մասին» և լուսանկար։ Բոտը միայն 14 և ավելի տարեկանների համար է։",
        ),
        (
            "Ինչո՞ւ չեմ տեսնում հարցաթերթիկներ",
            "Հնարավոր է՝ նոր հարցաթերթիկներ դեռ չկան. բոտում մարդիկ քիչ են, և ցուցադրվում են միայն նրանք, ում դեռ չեք տեսել։ Մտեք ավելի ուշ։ VIP-ից առանց ցուցադրվում են և՛ տղամարդիկ, և՛ կանայք։",
        ),
        (
            "Ի՞նչ է տալիս VIP-ը",
            "VIP-ը ձեր հարցաթերթիկը ցուցադրում է ավելի հաճախ, ավելացնում է ⭐ նշան, ցույց է տալիս՝ ով է ձեզ հավանել, թույլ է տալիս ավելի շատ լուսանկարներ, անսահմանափակ լայքեր և ընտրել՝ ում փնտրել։ Փաթեթները տեսեք հիմնական բոտի «⭐ VIP» բաժնում։",
        ),
        (
            "Ինչպե՞ս վճարել, և ի՞նչ անել, եթե վճարումը չանցավ",
            "Վճարումը կատարվում է Telegram-ի աստղերով հենց բոտում («⭐ VIP» → ընտրեք փաթեթ)։ Եթե աստղերը հանվել են, բայց VIP-ը չի միացել, կամ ուզում եք գումարի վերադարձ, գրեք մեզ այստեղ և նշեք վճարման ժամը։",
        ),
        (
            "Ինչպե՞ս գրել նրան, ում հետ զույգ ենք",
            "Փոխադարձ լայքի դեպքում բոտը ուղարկում է մարդու @username-ը։ Եթե ձեր @username-ը չկա, սահմանեք այն Telegram-ի կարգավորումներում (Կարգավորումներ → Օգտանուն), այլապես ձեզ չեն կարողանա գրել։",
        ),
        (
            "Ինչպե՞ս ջնջել հարցաթերթիկը",
            "Հիմնական բոտում սեղմեք «Ջնջել հարցաթերթիկը»։ Եթե ուզում եք ջնջել բոլոր տվյալները, գրեք մեզ այստեղ։",
        ),
        (
            "Ինչպե՞ս բողոքել օգտատիրոջ մասին",
            "Յուրաքանչյուր հարցաթերթիկի տակ կա «Բողոքել» կոճակ։ Մենք քննարկում ենք բողոքները։",
        ),
    ],
}

LANG_NAMES = {"en": "English", "ru": "Русский", "hy": "Հայերեն"}

ADMIN_HELP = (
    "Как отвечать: сделай реплай на сообщение пользователя (или на его заголовок). "
    "Ответ уйдёт от имени бота поддержки, твоё имя человек не увидит.\n\n"
    "/block ID — заблокировать человека\n"
    "/unblock ID — разблокировать\n"
    "/stats — сколько людей писало\n"
    "ID виден в заголовке каждого сообщения (#id123...)."
)

# ---------------------------------------------------------------- storage


def load_db():
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    data.setdefault("users", {})
    data.setdefault("threads", {})
    return data


def save_db():
    tmp = FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False)
    os.replace(tmp, FILE)


db = load_db()


def get_user(uid):
    return db["users"].setdefault(
        str(uid), {"lang": None, "blocked": False, "first": time.time()}
    )


def lang_of(uid):
    return get_user(uid)["lang"] or "en"


def tr(uid, key):
    return TEXTS[lang_of(uid)][key]


def btn(key):
    """Filter: message text equals this button in ANY language."""
    return F.text.in_({TEXTS[lang][key] for lang in TEXTS})


# ---------------------------------------------------------------- middleware


class BlockMiddleware(BaseMiddleware):
    """Silently ignores blocked users."""

    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if user and user.id != ADMIN_ID:
            if db["users"].get(str(user.id), {}).get("blocked"):
                return None
        return await handler(event, data)


dp.message.outer_middleware(BlockMiddleware())
dp.callback_query.outer_middleware(BlockMiddleware())

# ---------------------------------------------------------------- keyboards


def menu_kb(uid):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=tr(uid, "btn_faq"))],
            [KeyboardButton(text=tr(uid, "btn_write"))],
        ],
        resize_keyboard=True,
    )


def lang_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=name, callback_data="lang:" + code)
                for code, name in LANG_NAMES.items()
            ]
        ]
    )


def faq_kb(uid):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=q, callback_data=f"faq:{i}")]
            for i, (q, _a) in enumerate(FAQ[lang_of(uid)])
        ]
    )


def back_kb(uid):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=tr(uid, "back"), callback_data="faqback")]]
    )


# ---------------------------------------------------------------- admin side


def parse_id(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        return None
    return parts[1]


@dp.message(CommandStart(), F.from_user.id == ADMIN_ID)
async def admin_start(message: Message):
    await message.answer(ADMIN_HELP)


@dp.message(Command("help"), F.from_user.id == ADMIN_ID)
async def admin_help(message: Message):
    await message.answer(ADMIN_HELP)


@dp.message(Command("block"), F.from_user.id == ADMIN_ID)
async def admin_block(message: Message):
    uid = parse_id(message)
    if uid is None:
        await message.answer("Использование: /block ID")
        return
    get_user(uid)["blocked"] = True
    save_db()
    await message.answer(f"Заблокирован: {uid}")


@dp.message(Command("unblock"), F.from_user.id == ADMIN_ID)
async def admin_unblock(message: Message):
    uid = parse_id(message)
    if uid is None:
        await message.answer("Использование: /unblock ID")
        return
    get_user(uid)["blocked"] = False
    save_db()
    await message.answer(f"Разблокирован: {uid}")


@dp.message(Command("stats"), F.from_user.id == ADMIN_ID)
async def admin_stats(message: Message):
    users = db["users"]
    blocked = sum(1 for u in users.values() if u.get("blocked"))
    await message.answer(f"Людей в боте: {len(users)}, заблокировано: {blocked}")


@dp.message(F.from_user.id == ADMIN_ID, F.reply_to_message)
async def admin_reply(message: Message):
    target = db["threads"].get(str(message.reply_to_message.message_id))
    if target is None:
        # fallback: the header message contains "#id123"
        found = re.search(r"#id(\d+)", message.reply_to_message.text or "")
        if found:
            target = int(found.group(1))
    if target is None:
        await message.answer(
            "Не нашёл, кому это отправить. Ответь реплаем на сообщение пользователя или на его заголовок."
        )
        return
    try:
        # copy_message sends it as a normal message from this bot: anonymous
        await bot.copy_message(
            chat_id=target, from_chat_id=message.chat.id, message_id=message.message_id
        )
        await message.answer("✅")
    except Exception as e:
        await message.answer(f"Не удалось отправить (возможно, человек заблокировал бота): {e}")


@dp.message(F.from_user.id == ADMIN_ID)
async def admin_other(message: Message):
    await message.answer(ADMIN_HELP)


# ---------------------------------------------------------------- user side


@dp.message(CommandStart())
async def start(message: Message):
    user = get_user(message.from_user.id)
    save_db()
    if user["lang"] is None:
        await message.answer("Choose your language / Выбери язык / Ընտրեք լեզուն", reply_markup=lang_kb())
    else:
        await message.answer(tr(message.from_user.id, "menu"), reply_markup=menu_kb(message.from_user.id))


@dp.callback_query(F.data.startswith("lang:"))
async def set_lang(callback: CallbackQuery):
    code = callback.data.split(":")[1]
    if code not in TEXTS:
        await callback.answer()
        return
    uid = callback.from_user.id
    get_user(uid)["lang"] = code
    save_db()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(tr(uid, "menu"), reply_markup=menu_kb(uid))
    await callback.answer()


@dp.message(btn("btn_faq"))
async def show_faq(message: Message):
    uid = message.from_user.id
    await message.answer(tr(uid, "faq_title"), reply_markup=faq_kb(uid))


@dp.message(btn("btn_write"))
async def write_hint(message: Message):
    await message.answer(tr(message.from_user.id, "write_hint"))


@dp.callback_query(F.data.startswith("faq:"))
async def faq_answer(callback: CallbackQuery):
    uid = callback.from_user.id
    items = FAQ[lang_of(uid)]
    try:
        index = int(callback.data.split(":")[1])
        question, answer = items[index]
    except (ValueError, IndexError):
        await callback.answer()
        return
    text = f"❓ {question}\n\n{answer.replace('{main}', MAIN_BOT)}"
    await callback.message.edit_text(text, reply_markup=back_kb(uid))
    await callback.answer()


@dp.callback_query(F.data == "faqback")
async def faq_back(callback: CallbackQuery):
    uid = callback.from_user.id
    await callback.message.edit_text(tr(uid, "faq_title"), reply_markup=faq_kb(uid))
    await callback.answer()


recent = defaultdict(deque)
last_ack = {}


def sending_too_fast(uid):
    now = time.time()
    q = recent[uid]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= MAX_MSGS_PER_MINUTE:
        return True
    q.append(now)
    return False


@dp.message(F.chat.type == "private")
async def from_user(message: Message):
    u = message.from_user
    uid = u.id
    get_user(uid)

    if sending_too_fast(uid):
        await message.answer(tr(uid, "too_fast"))
        return

    uname = f"@{u.username}" if u.username else "-"
    header = f"📩 {u.full_name} ({uname})\nID: #id{uid}"
    try:
        head = await bot.send_message(ADMIN_ID, header)
        copy = await bot.copy_message(
            ADMIN_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            reply_to_message_id=head.message_id,
        )
    except Exception:
        logging.exception("could not forward to admin")
        await message.answer(tr(uid, "send_failed"))
        return

    threads = db["threads"]
    threads[str(head.message_id)] = uid
    threads[str(copy.message_id)] = uid
    if len(threads) > MAX_THREADS:
        for key in list(threads)[: len(threads) - MAX_THREADS]:
            del threads[key]
    save_db()

    now = time.time()
    if now - last_ack.get(uid, 0) > ACK_EVERY_SECONDS:
        last_ack[uid] = now
        await message.answer(tr(uid, "ack"))


# ---------------------------------------------------------------- run


async def main():
    await bot.delete_webhook()
    await dp.start_polling(bot)


asyncio.run(main())
