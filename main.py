import asyncio
import html
import json
import logging
import os
import random
import shutil
import time

from dotenv import load_dotenv
from aiogram import BaseMiddleware, Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InputMediaPhoto,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    PreCheckoutQuery,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

logging.basicConfig(level=logging.INFO)
load_dotenv()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# On Railway set DATA_DIR=/data (a Volume mount) so the data survives restarts
DATA_DIR = os.getenv("DATA_DIR", ".")
FILE = os.path.join(DATA_DIR, "dating.json")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
MIN_AGE = 14
REPORTS_TO_HIDE = 5
MAX_PHOTOS = 5
MAX_NAME = 30
MAX_CITY = 30
MAX_ABOUT = 300
VIP_PRICE = 50  # Telegram Stars
VIP_DAYS = 30
FREE_LIKES_PER_DAY = 30
MAX_PHOTOS_VIP = 10
PAY_CONTACT = os.getenv("PAY_CONTACT", "@your_contact")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
BACKUP_EVERY_HOURS = 6
BACKUPS_KEEP = 40

# ---------------------------------------------------------------- texts

TEXTS = {
    "en": {
        "choose_lang": "Choose your language",
        "menu": "Choose an action",
        "btn_create": "📝 Create profile",
        "btn_browse": "👀 Browse profiles",
        "btn_my": "👤 My profile",
        "btn_delete": "🗑 Delete profile",
        "btn_lang": "🌐 Language",
        "ask_name": "What is your name?",
        "ask_age": "How old are you?",
        "age_bad": "Please send your age as a number.",
        "age_minor": "Sorry, this bot is only for people 14 and older.",
        "ask_city": "Which city are you from?",
        "ask_gender": "Select your gender.",
        "g_male": "👨 Man",
        "g_female": "👩 Woman",
        "ask_looking": "Who do you want to meet?",
        "l_male": "👨 Men",
        "l_female": "👩 Women",
        "l_any": "👥 Anyone",
        "use_buttons": "Please use the buttons below.",
        "ask_about": "Tell us about yourself in a few sentences.",
        "ask_photo": "Send up to {max} photos one by one, then press the Done button.",
        "btn_done": "✅ Done",
        "photo_added": "Photo {n}/{max} added.",
        "need_photo": "Send at least one photo first.",
        "too_long": "Too long. Maximum is {max} characters, yours is {n}.",
        "photo_bad": "Please send a photo.",
        "text_only": "Please send text.",
        "saved": "Profile saved ✅",
        "no_profile": "You don't have a profile yet.",
        "need_profile": "Create your profile first.",
        "no_more": "No new profiles for now. Come back later.",
        "like": "❤️ Like",
        "skip": "➡️ Skip",
        "report": "🚩 Report",
        "match": "💘 It's a match! Say hi to ",
        "reported": "Report received.",
        "deleted": "Your profile has been deleted.",
        "lang_set": "Language changed ✅",
        "btn_search": "🔎 Who I'm looking for",
        "vip_only_search": "Choosing who to look for is a VIP feature. Without VIP you see everyone, men and women together.",
        "search_saved": "Saved ✅",
        "need_username": "Tip: you have no Telegram @username, so matches may not be able to message you. Set one in Settings → Username.",
        "btn_vip": "⭐ VIP",
        "btn_likes": "❤️ Who liked me",
        "vip_info": "⭐ VIP for {price} Stars / {days} days:\n• Your profile is shown more often\n• ⭐ badge on your profile\n• See who liked you\n• Up to {photos} photos\n• Unlimited likes (free: {free} per day)\n• Choose who to see: men, women or anyone",
        "vip_active": "Your VIP is active until {date}.",
        "invoice_title": "VIP",
        "invoice_desc": "VIP access for 30 days",
        "vip_thanks": "Thank you! VIP is active until {date} ⭐",
        "likes_limit": "Daily like limit reached. Get VIP for unlimited likes.",
        "likes_teaser": "{n} people liked you. Get VIP to see who.",
        "no_likes": "No new likes yet.",
        "paysupport": "Payment help and refunds: write to {contact}.",
    },
    "ru": {
        "choose_lang": "Выбери язык",
        "menu": "Выбери действие",
        "btn_create": "📝 Создать анкету",
        "btn_browse": "👀 Смотреть анкеты",
        "btn_my": "👤 Моя анкета",
        "btn_delete": "🗑 Удалить анкету",
        "btn_lang": "🌐 Язык",
        "ask_name": "Как тебя зовут?",
        "ask_age": "Сколько тебе лет?",
        "age_bad": "Напиши возраст числом.",
        "age_minor": "Извини, бот только для тех, кому 4 и больше.",
        "ask_city": "Из какого ты города?",
        "ask_gender": "Укажи свой пол.",
        "g_male": "👨 Мужчина",
        "g_female": "👩 Женщина",
        "ask_looking": "Кого ты хочешь найти?",
        "l_male": "👨 Мужчин",
        "l_female": "👩 Женщин",
        "l_any": "👥 Всех",
        "use_buttons": "Пользуйся кнопками ниже.",
        "ask_about": "Расскажи о себе в паре предложений.",
        "ask_photo": "Пришли до {max} фото по одному, потом нажми «Готово».",
        "btn_done": "✅ Готово",
        "photo_added": "Фото {n}/{max} добавлено.",
        "need_photo": "Сначала пришли хотя бы одно фото.",
        "too_long": "Слишком длинно. Максимум {max} символов, у тебя {n}.",
        "photo_bad": "Пришли именно фото.",
        "text_only": "Пришли текстом.",
        "saved": "Анкета сохранена ✅",
        "no_profile": "У тебя ещё нет анкеты.",
        "need_profile": "Сначала создай свою анкету.",
        "no_more": "Новых анкет пока нет. Загляни позже.",
        "like": "❤️ Нравится",
        "skip": "➡️ Дальше",
        "report": "🚩 Пожаловаться",
        "match": "💘 Взаимная симпатия! Напиши: ",
        "reported": "Жалоба принята.",
        "deleted": "Твоя анкета удалена.",
        "lang_set": "Язык изменён ✅",
        "btn_search": "🔎 Кого ищу",
        "vip_only_search": "Выбор, кого искать, доступен только с VIP. Без VIP показываются все: и парни, и девушки вместе.",
        "search_saved": "Сохранено ✅",
        "need_username": "Совет: у тебя нет @юзернейма в Telegram, поэтому пары могут не суметь тебе написать. Поставь его в Настройки → Имя пользователя.",
        "btn_vip": "⭐ VIP",
        "btn_likes": "❤️ Кто лайкнул",
        "vip_info": "⭐ VIP за {price} звёзд / {days} дней:\n• Анкету показывают чаще\n• Значок ⭐ в анкете\n• Видно, кто тебя лайкнул\n• До {photos} фото\n• Безлимитные лайки (бесплатно: {free} в день)\n• Выбор, кого искать: мужчин, женщин или всех",
        "vip_active": "Твой VIP активен до {date}.",
        "invoice_title": "VIP",
        "invoice_desc": "VIP на 30 дней",
        "vip_thanks": "Спасибо! VIP активен до {date} ⭐",
        "likes_limit": "Лимит лайков на сегодня закончился. С VIP лайки безлимитные.",
        "likes_teaser": "Тебя лайкнули: {n}. С VIP ты увидишь, кто.",
        "no_likes": "Новых лайков пока нет.",
        "paysupport": "Вопросы по оплате и возврату: пиши {contact}.",
    },
    "hy": {
        "choose_lang": "Ընտրեք լեզուն",
        "menu": "Ընտրեք գործողությունը",
        "btn_create": "📝 Լրացնել հարցաթերթիկ",
        "btn_browse": "👀 Դիտել հարցաթերթիկները",
        "btn_my": "👤 Իմ հարցաթերթիկը",
        "btn_delete": "🗑 Ջնջել հարցաթերթիկը",
        "btn_lang": "🌐 Լեզու",
        "ask_name": "Ինչպե՞ս է ձեր անունը։",
        "ask_age": "Քանի՞ տարեկան եք։",
        "age_bad": "Գրեք տարիքը թվով։",
        "age_minor": "Ցավոք, բոտն ընդունում է միայն 14 և ավելի տարեկանների։",
        "ask_city": "Ո՞ր քաղաքից եք։",
        "ask_gender": "Նշեք ձեր սեռը։",
        "g_male": "👨 Տղամարդ",
        "g_female": "👩 Կին",
        "ask_looking": "Ում հետ եք ցանկանում ծանոթանալ։",
        "l_male": "👨 Տղամարդկանց",
        "l_female": "👩 Կանանց",
        "l_any": "👥 Բոլորին",
        "use_buttons": "Խնդրում եմ օգտվեք ստորև կոճակներից։",
        "ask_about": "Պատմեք ձեր մասին մի քանի նախադասությամբ։",
        "ask_photo": "Ուղարկեք մինչև {max} լուսանկար՝ մեկ-մեկ, հետո սեղմեք «Պատրաստ է»։",
        "btn_done": "✅ Պատրաստ է",
        "photo_added": "Լուսանկար {n}/{max} ավելացվեց։",
        "need_photo": "Նախ ուղարկեք առնվազն մեկ լուսանկար։",
        "too_long": "Չափազանց երկար է։ Առավելագույնը {max} նիշ է, ձեր տեքստը՝ {n}։",
        "photo_bad": "Խնդրում եմ ուղարկել լուսանկար։",
        "text_only": "Խնդրում եմ գրել տեքստով։",
        "saved": "Հարցաթերթիկը պահպանվեց ✅",
        "no_profile": "Դուք դեռ հարցաթերթիկ չունեք։",
        "need_profile": "Նախ լրացրեք ձեր հարցաթերթիկը։",
        "no_more": "Առայժմ նոր հարցաթերթիկներ չկան։",
        "like": "❤️ Դուր եկավ",
        "skip": "➡️ Հաջորդը",
        "report": "🚩 Բողոքել",
        "match": "💘 Փոխադարձ համակրանք։ Գրեք՝ ",
        "reported": "Բողոքն ընդունված է։",
        "deleted": "Ձեր հարցաթերթիկը ջնջված է։",
        "lang_set": "Լեզուն փոխվեց ✅",
        "btn_search": "🔎 Ում եմ փնտրում",
        "vip_only_search": "Ընտրել՝ ում փնտրել, հասանելի է միայն VIP-ով։ VIP-ից առանց ցուցադրվում են բոլորը՝ և տղամարդիկ, և կանայք միասին։",
        "search_saved": "Պահպանվեց ✅",
        "need_username": "Խորհուրդ. Դուք Telegram-ում @username չունեք, ուստի զույգերը կարող են չկարողանալ գրել ձեզ։ Սահմանեք այն՝ Կարգավորումներ → Օգտանուն։",
        "btn_vip": "⭐ VIP",
        "btn_likes": "❤️ Ով է հավանել",
        "vip_info": "⭐ VIP՝ {price} աստղ / {days} օր.\n• Ձեր հարցաթերթիկը ավելի հաճախ է ցուցադրվում\n• ⭐ նշան հարցաթերթիկի վրա\n• Տեսնում եք, թե ով է ձեզ հավանել\n• Մինչև {photos} լուսանկար\n• Անսահմանափակ լայքեր (անվճար՝ օրական {free})\n• Ընտրեք՝ ում հարցաթերթիկները տեսնել (տղամարդիկ, կանայք կամ բոլորը)",
        "vip_active": "Ձեր VIP-ը ակտիվ է մինչև {date}։",
        "invoice_title": "VIP",
        "invoice_desc": "VIP 30 օրով",
        "vip_thanks": "Շնորհակալություն։ VIP-ը ակտիվ է մինչև {date} ⭐",
        "likes_limit": "Այսօրվա լայքերի սահմանաչափը լրացավ։ VIP-ով լայքերը անսահմանափակ են։",
        "likes_teaser": "Ձեզ հավանել են՝ {n} հոգի։ VIP-ով կտեսնեք, թե ովքեր։",
        "no_likes": "Նոր լայքեր դեռ չկան։",
        "paysupport": "Վճարման և վերադարձի հարցերով գրեք՝ {contact}։",
    },
}

LANG_NAMES = {"en": "English", "ru": "Русский", "hy": "Հայերեն"}

# ---------------------------------------------------------------- storage


def load_db():
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"users": {}}


def save_db():
    tmp = FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False)
    os.replace(tmp, FILE)


db = load_db()


def get_user(uid):
    uid = str(uid)
    if uid not in db["users"]:
        db["users"][uid] = {
            "lang": None,
            "profile": None,
            "seen": [],
            "likes": [],
            "reports": 0,
            "banned": False,
            "vip_until": 0,
            "likes_day": "",
            "likes_today": 0,
            "joined": time.time(),
            "source": None,
        }
    return db["users"][uid]


def tr(uid, key):
    lang = get_user(uid)["lang"] or "en"
    return TEXTS[lang][key]


def btn(key):
    """Filter: message text equals this button in ANY language."""
    return F.text.in_({TEXTS[lang][key] for lang in TEXTS})


# ---------------------------------------------------------------- keyboards


def menu_kb(uid):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=tr(uid, "btn_browse"))],
            [
                KeyboardButton(text=tr(uid, "btn_likes")),
                KeyboardButton(text=tr(uid, "btn_vip")),
            ],
            [KeyboardButton(text=tr(uid, "btn_search"))],
            [
                KeyboardButton(text=tr(uid, "btn_create")),
                KeyboardButton(text=tr(uid, "btn_my")),
            ],
            [
                KeyboardButton(text=tr(uid, "btn_delete")),
                KeyboardButton(text=tr(uid, "btn_lang")),
            ],
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


def gender_kb(uid):
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text=tr(uid, "g_male")),
            KeyboardButton(text=tr(uid, "g_female")),
        ]],
        resize_keyboard=True,
    )


def looking_kb(uid):
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text=tr(uid, "l_male")),
            KeyboardButton(text=tr(uid, "l_female")),
            KeyboardButton(text=tr(uid, "l_any")),
        ]],
        resize_keyboard=True,
    )


def done_kb(uid):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=tr(uid, "btn_done"))]],
        resize_keyboard=True,
    )


def profile_kb(uid, target):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=tr(uid, "like"), callback_data="like:" + target),
                InlineKeyboardButton(text=tr(uid, "skip"), callback_data="skip:" + target),
            ],
            [InlineKeyboardButton(text=tr(uid, "report"), callback_data="report:" + target)],
        ]
    )


# ---------------------------------------------------------------- helpers


class SetLooking(StatesGroup):
    choosing = State()


class Anketa(StatesGroup):
    name = State()
    age = State()
    gender = State()
    looking = State()
    city = State()
    about = State()
    photo = State()


def caption(p, vip=False):
    badge = "⭐ " if vip else ""
    return f"{badge}{p['name']}, {p['age']}\n📍 {p['city']}\n\n{p['about']}"


def photos_of(p):
    return p.get("photos") or ([p["photo"]] if p.get("photo") else [])


async def send_profile(chat_id, p, markup=None, vip=False):
    photos = photos_of(p)
    cap = caption(p, vip)
    if not photos:
        await bot.send_message(chat_id, cap, reply_markup=markup)
    elif len(photos) == 1:
        await bot.send_photo(chat_id, photos[0], caption=cap, reply_markup=markup)
    else:
        media = [
            InputMediaPhoto(media=fid, caption=cap if i == 0 else None)
            for i, fid in enumerate(photos)
        ]
        await bot.send_media_group(chat_id, media)
        if markup:
            await bot.send_message(chat_id, "👇", reply_markup=markup)


async def too_long(message, text, limit):
    if len(text) > limit:
        await message.answer(
            tr(message.from_user.id, "too_long").format(max=limit, n=len(text))
        )
        return True
    return False


def contact_html(uid, name):
    """@username if the person has one, plus a profile link as a fallback."""
    uname = get_user(uid).get("username")
    link = f'<a href="tg://user?id={uid}">{html.escape(name)}</a>'
    if uname:
        return f"@{html.escape(uname)} ({link})"
    return link


GENDER_KEYS = {"g_male": "m", "g_female": "f"}
LOOKING_KEYS = {"l_male": "m", "l_female": "f", "l_any": "any"}


def match_choice(text, options):
    """Turn a button text (in any language) into a code like 'm' / 'f' / 'any'."""
    for key, code in options.items():
        for lang in TEXTS:
            if text == TEXTS[lang][key]:
                return code
    return None


def default_looking(gender):
    """Free users see everyone (men and women). Only VIP can narrow it down."""
    return "any"


def with_looking(uid, profile):
    """Copy of the profile with the filter that really applies (VIP only can choose)."""
    if is_vip(uid):
        looking = profile.get("looking", "any")
    else:
        looking = default_looking(profile.get("gender"))
    return {**profile, "looking": looking}


def compatible(a, b):
    """True only if a wants b's gender AND b wants a's gender."""
    if not b.get("gender"):
        return False
    a_ok = a.get("looking", "any") in ("any", b["gender"])
    b_ok = b.get("looking", "any") in ("any", a.get("gender"))
    return a_ok and b_ok


async def send_next(chat_id, uid):
    uid = str(uid)
    me = get_user(uid)
    if not me["profile"]:
        await bot.send_message(chat_id, tr(uid, "need_profile"))
        return
    candidates = [
        other
        for other, u in db["users"].items()
        if other != uid
        and u["profile"]
        and (u["profile"].get("age", 0) < 18) == (me["profile"].get("age", 0) < 18)
        and u["reports"] < REPORTS_TO_HIDE
        and not u.get("banned")
        and other not in me["seen"]
        and compatible(with_looking(uid, me["profile"]), with_looking(other, u["profile"]))
    ]
    if not candidates:
        await bot.send_message(chat_id, tr(uid, "no_more"))
        return
    weights = [3 if is_vip(c) else 1 for c in candidates]
    target = random.choices(candidates, weights=weights)[0]
    p = db["users"][target]["profile"]
    await send_profile(chat_id, p, profile_kb(uid, target), vip=is_vip(target))


# ---------------------------------------------------------------- start & language


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext, command: CommandObject):
    await state.clear()
    user = get_user(message.from_user.id)
    if not user.get("source"):
        raw = command.args or ""
        clean = "".join(ch for ch in raw if ch.isalnum() or ch in "_-")[:30]
        user["source"] = clean or "organic"
        save_db()
    if user["lang"] is None:
        await message.answer("Choose your language / Выбери язык / Ընտրեք լեզուն", reply_markup=lang_kb())
    else:
        await message.answer(tr(message.from_user.id, "menu"), reply_markup=menu_kb(message.from_user.id))


@dp.message(btn("btn_lang"))
async def change_lang(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Choose your language / Выбери язык / Ընտրեք լեզուն", reply_markup=lang_kb())


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
    await callback.message.answer(tr(uid, "lang_set"))
    await callback.message.answer(tr(uid, "menu"), reply_markup=menu_kb(uid))
    await callback.answer()


# ---------------------------------------------------------------- moderation


class BanMiddleware(BaseMiddleware):
    """Silently ignores everything from banned users."""

    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if user:
            record = get_user(user.id)
            if record.get("username") != user.username:
                record["username"] = user.username
                save_db()
            if record.get("banned"):
                return None
        return await handler(event, data)


dp.message.outer_middleware(BanMiddleware())
dp.callback_query.outer_middleware(BanMiddleware())


def parse_id(message: Message):
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        return None
    return parts[1]


@dp.message(Command("myid"))
async def my_id(message: Message):
    await message.answer(str(message.from_user.id))


@dp.message(Command("reports"), F.from_user.id == ADMIN_ID)
async def admin_reports(message: Message):
    rows = [
        (uid, u)
        for uid, u in db["users"].items()
        if u["reports"] > 0
    ]
    rows.sort(key=lambda r: r[1]["reports"], reverse=True)
    if not rows:
        await message.answer("Жалоб нет.")
        return
    lines = []
    for uid, u in rows[:30]:
        name = u["profile"]["name"] if u["profile"] else "-"
        mark = " [БАН]" if u.get("banned") else ""
        lines.append(f"{uid} | {name} | жалоб: {u['reports']}{mark}")
    await message.answer("\n".join(lines) + "\n\n/view ID, /ban ID, /unban ID")


@dp.message(Command("view"), F.from_user.id == ADMIN_ID)
async def admin_view(message: Message):
    uid = parse_id(message)
    if uid is None or uid not in db["users"] or not db["users"][uid]["profile"]:
        await message.answer("Использование: /view ID (анкета должна существовать)")
        return
    await send_profile(message.chat.id, db["users"][uid]["profile"])


@dp.message(Command("ban"), F.from_user.id == ADMIN_ID)
async def admin_ban(message: Message):
    uid = parse_id(message)
    if uid is None or uid not in db["users"]:
        await message.answer("Использование: /ban ID")
        return
    db["users"][uid]["banned"] = True
    save_db()
    await message.answer(f"Забанен: {uid}")


@dp.message(Command("unban"), F.from_user.id == ADMIN_ID)
async def admin_unban(message: Message):
    uid = parse_id(message)
    if uid is None or uid not in db["users"]:
        await message.answer("Использование: /unban ID")
        return
    db["users"][uid]["banned"] = False
    db["users"][uid]["reports"] = 0
    save_db()
    await message.answer(f"Разбанен: {uid}")


# ---------------------------------------------------------------- backups & stats


def make_backup():
    if not os.path.exists(FILE):
        return None
    os.makedirs(BACKUP_DIR, exist_ok=True)
    name = time.strftime("dating_%Y-%m-%d_%H-%M-%S.json")
    shutil.copy2(FILE, os.path.join(BACKUP_DIR, name))
    old_files = sorted(os.listdir(BACKUP_DIR))[:-BACKUPS_KEEP]
    for old in old_files:
        os.remove(os.path.join(BACKUP_DIR, old))
    return name


async def backup_loop():
    while True:
        try:
            make_backup()
        except Exception:
            logging.exception("backup failed")
        await asyncio.sleep(BACKUP_EVERY_HOURS * 3600)


@dp.message(Command("backup"), F.from_user.id == ADMIN_ID)
async def admin_backup(message: Message):
    name = make_backup()
    await message.answer(f"Копия сохранена: {BACKUP_DIR}/{name}" if name else "Нечего копировать.")


@dp.message(Command("stats"), F.from_user.id == ADMIN_ID)
async def admin_stats(message: Message):
    users = db["users"]
    now = time.time()
    midnight = time.mktime(time.strptime(time.strftime("%Y-%m-%d"), "%Y-%m-%d"))
    with_profile = [u for u in users.values() if u["profile"]]
    men = sum(1 for u in with_profile if u["profile"].get("gender") == "m")
    women = sum(1 for u in with_profile if u["profile"].get("gender") == "f")
    new_today = sum(1 for u in users.values() if u.get("joined", 0) >= midnight)
    vip = sum(1 for u in users.values() if u.get("vip_until", 0) > now)
    banned = sum(1 for u in users.values() if u.get("banned"))
    likes = sum(len(u["likes"]) for u in users.values())

    matches = 0
    for uid, u in users.items():
        for target in u["likes"]:
            if target in users and uid in users[target]["likes"] and uid < target:
                matches += 1

    payments = db.get("payments", [])
    refunded = sum(1 for x in payments if x.get("refunded"))
    stars = sum(x["amount"] for x in payments if not x.get("refunded"))

    sources = {}
    for u in users.values():
        entry = sources.setdefault(u.get("source") or "unknown", [0, 0])
        entry[0] += 1
        if u["profile"]:
            entry[1] += 1
    source_lines = [
        f"{name}: {c[0]} (анкет: {c[1]})"
        for name, c in sorted(sources.items(), key=lambda kv: kv[1][0], reverse=True)[:15]
    ]

    text = (
        f"👥 Пользователей: {len(users)} (сегодня новых: {new_today})\n"
        f"📝 С анкетами: {len(with_profile)} (М: {men}, Ж: {women})\n"
        f"⭐ VIP сейчас: {vip}\n"
        f"🚫 Забанено: {banned}\n"
        f"❤️ Лайков: {likes}\n"
        f"💘 Матчей: {matches}\n"
        f"💰 Оплат: {len(payments)}, звёзд: {stars}, возвратов: {refunded}\n\n"
        f"🔗 Откуда пришли:\n" + ("\n".join(source_lines) or "-")
    )
    await message.answer(text)


@dp.message(Command("find"), F.from_user.id == ADMIN_ID)
async def admin_find(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /find @юзернейм или имя")
        return
    query = parts[1].strip().lstrip("@").lower()
    rows = []
    for uid, u in db["users"].items():
        username = (u.get("username") or "").lower()
        name = u["profile"]["name"] if u["profile"] else ""
        if query and (query in username or query in name.lower()):
            rows.append(f"{uid} | @{u.get('username') or '-'} | {name or '-'}")
    await message.answer("\n".join(rows[:10]) if rows else "Никого не нашёл.")


# ---------------------------------------------------------------- menu buttons
# These are registered BEFORE the Anketa states, so pressing a menu button
# in the middle of the form still works.


@dp.message(btn("btn_create"))
async def create(message: Message, state: FSMContext):
    uid = message.from_user.id
    await state.clear()
    await state.set_state(Anketa.name)
    await message.answer(tr(uid, "ask_name"), reply_markup=ReplyKeyboardRemove())


@dp.message(btn("btn_browse"))
async def browse(message: Message, state: FSMContext):
    await state.clear()
    await send_next(message.chat.id, message.from_user.id)


@dp.message(btn("btn_my"))
async def my_profile(message: Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    p = get_user(uid)["profile"]
    if not p:
        await message.answer(tr(uid, "no_profile"))
        return
    await send_profile(message.chat.id, p, vip=is_vip(uid))


@dp.message(btn("btn_delete"))
async def delete_profile(message: Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    user = get_user(uid)
    if not user["profile"]:
        await message.answer(tr(uid, "no_profile"))
        return
    user["profile"] = None
    user["likes"] = []
    save_db()
    await message.answer(tr(uid, "deleted"), reply_markup=menu_kb(uid))


# ---------------------------------------------------------------- VIP (Telegram Stars)


def is_vip(uid):
    return get_user(uid).get("vip_until", 0) > time.time()


def fmt_date(ts):
    return time.strftime("%d.%m.%Y", time.localtime(ts))


def photo_limit(uid):
    return MAX_PHOTOS_VIP if is_vip(uid) else MAX_PHOTOS


@dp.message(btn("btn_vip"))
async def vip_menu(message: Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    text = tr(uid, "vip_info").format(
        price=VIP_PRICE, days=VIP_DAYS, photos=MAX_PHOTOS_VIP, free=FREE_LIKES_PER_DAY
    )
    if is_vip(uid):
        text += "\n\n" + tr(uid, "vip_active").format(date=fmt_date(get_user(uid)["vip_until"]))
    await message.answer(text)
    await bot.send_invoice(
        chat_id=message.chat.id,
        title=tr(uid, "invoice_title"),
        description=tr(uid, "invoice_desc"),
        payload=f"vip:{uid}",
        currency="XTR",
        prices=[LabeledPrice(label="VIP", amount=VIP_PRICE)],
    )


@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    banned = db["users"].get(str(query.from_user.id), {}).get("banned")
    ok = query.invoice_payload == f"vip:{query.from_user.id}" and not banned
    await query.answer(ok=ok, error_message=None if ok else "Payment unavailable")


@dp.message(F.successful_payment)
async def paid(message: Message):
    uid = message.from_user.id
    sp = message.successful_payment
    user = get_user(uid)
    start_from = max(user.get("vip_until", 0), time.time())
    user["vip_until"] = start_from + VIP_DAYS * 86400
    db.setdefault("payments", []).append(
        {
            "user": str(uid),
            "charge_id": sp.telegram_payment_charge_id,
            "amount": sp.total_amount,
            "time": time.time(),
        }
    )
    save_db()
    await message.answer(
        tr(uid, "vip_thanks").format(date=fmt_date(user["vip_until"])),
        reply_markup=menu_kb(uid),
    )
    if ADMIN_ID:
        try:
            await bot.send_message(ADMIN_ID, f"⭐ Оплата: {uid}, {sp.total_amount} звёзд")
        except Exception:
            pass


@dp.message(Command("paysupport"))
async def pay_support(message: Message):
    await message.answer(tr(message.from_user.id, "paysupport").format(contact=PAY_CONTACT))


@dp.message(Command("refund"), F.from_user.id == ADMIN_ID)
async def admin_refund(message: Message):
    uid = parse_id(message)
    payments = [
        x for x in db.get("payments", []) if x["user"] == uid and not x.get("refunded")
    ]
    if uid is None or not payments:
        await message.answer("Использование: /refund USER_ID (нужна оплата без возврата)")
        return
    pay = payments[-1]
    try:
        await bot.refund_star_payment(
            user_id=int(uid), telegram_payment_charge_id=pay["charge_id"]
        )
    except Exception as e:
        await message.answer(f"Ошибка возврата: {e}")
        return
    pay["refunded"] = True
    u = db["users"][uid]
    u["vip_until"] = max(0, u.get("vip_until", 0) - VIP_DAYS * 86400)
    save_db()
    await message.answer("Возврат выполнен, срок VIP уменьшен.")


@dp.message(btn("btn_search"))
async def search_menu(message: Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    if not get_user(uid)["profile"]:
        await message.answer(tr(uid, "need_profile"))
        return
    if not is_vip(uid):
        await message.answer(tr(uid, "vip_only_search"))
        return
    await state.set_state(SetLooking.choosing)
    await message.answer(tr(uid, "ask_looking"), reply_markup=looking_kb(uid))


@dp.message(btn("btn_likes"))
async def who_liked(message: Message, state: FSMContext):
    await state.clear()
    uid = str(message.from_user.id)
    me = get_user(uid)
    likers = [
        other
        for other, u in db["users"].items()
        if uid in u["likes"]
        and u["profile"]
        and not u.get("banned")
        and other not in me["likes"]
    ]
    if not likers:
        await message.answer(tr(uid, "no_likes"))
        return
    if not is_vip(uid):
        await message.answer(tr(uid, "likes_teaser").format(n=len(likers)))
        return
    for other in likers[:10]:
        await send_profile(
            message.chat.id,
            db["users"][other]["profile"],
            profile_kb(uid, other),
            vip=is_vip(other),
        )


# ---------------------------------------------------------------- form steps


@dp.message(SetLooking.choosing)
async def set_looking(message: Message, state: FSMContext):
    uid = message.from_user.id
    code = match_choice(message.text or "", LOOKING_KEYS)
    if code is None:
        await message.answer(tr(uid, "use_buttons"), reply_markup=looking_kb(uid))
        return
    get_user(uid)["profile"]["looking"] = code
    save_db()
    await state.clear()
    await message.answer(tr(uid, "search_saved"), reply_markup=menu_kb(uid))


@dp.message(Anketa.name)
async def get_name(message: Message, state: FSMContext):
    uid = message.from_user.id
    if message.text is None:
        await message.answer(tr(uid, "text_only"))
        return
    if await too_long(message, message.text, MAX_NAME):
        return
    await state.update_data(name=message.text)
    await state.set_state(Anketa.age)
    await message.answer(tr(uid, "ask_age"))


@dp.message(Anketa.age)
async def get_age(message: Message, state: FSMContext):
    uid = message.from_user.id
    if message.text is None or not message.text.isdigit() or int(message.text) > 99:
        await message.answer(tr(uid, "age_bad"))
        return
    age = int(message.text)
    if age < MIN_AGE:
        await state.clear()
        await message.answer(tr(uid, "age_minor"), reply_markup=menu_kb(uid))
        return
    await state.update_data(age=age)
    await state.set_state(Anketa.gender)
    await message.answer(tr(uid, "ask_gender"), reply_markup=gender_kb(uid))


@dp.message(Anketa.gender)
async def get_gender(message: Message, state: FSMContext):
    uid = message.from_user.id
    code = match_choice(message.text or "", GENDER_KEYS)
    if code is None:
        await message.answer(tr(uid, "use_buttons"), reply_markup=gender_kb(uid))
        return
    await state.update_data(gender=code)
    if is_vip(uid):
        await state.set_state(Anketa.looking)
        await message.answer(tr(uid, "ask_looking"), reply_markup=looking_kb(uid))
    else:
        await state.update_data(looking=default_looking(code))
        await state.set_state(Anketa.city)
        await message.answer(tr(uid, "ask_city"), reply_markup=ReplyKeyboardRemove())


@dp.message(Anketa.looking)
async def get_looking(message: Message, state: FSMContext):
    uid = message.from_user.id
    code = match_choice(message.text or "", LOOKING_KEYS)
    if code is None:
        await message.answer(tr(uid, "use_buttons"), reply_markup=looking_kb(uid))
        return
    await state.update_data(looking=code)
    await state.set_state(Anketa.city)
    await message.answer(tr(uid, "ask_city"), reply_markup=ReplyKeyboardRemove())


@dp.message(Anketa.city)
async def get_city(message: Message, state: FSMContext):
    uid = message.from_user.id
    if message.text is None:
        await message.answer(tr(uid, "text_only"))
        return
    if await too_long(message, message.text, MAX_CITY):
        return
    await state.update_data(city=message.text)
    await state.set_state(Anketa.about)
    await message.answer(tr(uid, "ask_about"))


@dp.message(Anketa.about)
async def get_about(message: Message, state: FSMContext):
    uid = message.from_user.id
    if message.text is None:
        await message.answer(tr(uid, "text_only"))
        return
    if await too_long(message, message.text, MAX_ABOUT):
        return
    await state.update_data(about=message.text)
    await state.set_state(Anketa.photo)
    await message.answer(
        tr(uid, "ask_photo").format(max=photo_limit(uid)), reply_markup=ReplyKeyboardRemove()
    )


async def finish_profile(message: Message, state: FSMContext):
    uid = message.from_user.id
    data = await state.get_data()
    profile = {
        "name": data["name"],
        "age": data["age"],
        "gender": data["gender"],
        "looking": data["looking"],
        "city": data["city"],
        "about": data["about"],
        "photos": data["photos"],
    }
    get_user(uid)["profile"] = profile
    save_db()
    await state.clear()
    await message.answer(tr(uid, "saved"), reply_markup=menu_kb(uid))
    await send_profile(message.chat.id, profile, vip=is_vip(uid))
    if not message.from_user.username:
        await message.answer(tr(uid, "need_username"))


@dp.message(Anketa.photo, F.photo)
async def get_photo(message: Message, state: FSMContext):
    uid = message.from_user.id
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    if len(photos) >= photo_limit(uid):
        await finish_profile(message, state)
        return
    await message.answer(
        tr(uid, "photo_added").format(n=len(photos), max=photo_limit(uid)),
        reply_markup=done_kb(uid),
    )


@dp.message(Anketa.photo, btn("btn_done"))
async def photos_done(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data.get("photos"):
        await message.answer(tr(message.from_user.id, "need_photo"))
        return
    await finish_profile(message, state)


@dp.message(Anketa.photo)
async def photo_bad(message: Message):
    await message.answer(tr(message.from_user.id, "photo_bad"))


# ---------------------------------------------------------------- like / skip / report


@dp.callback_query(F.data.regexp(r"^(like|skip|report):\d+$"))
async def react(callback: CallbackQuery):
    action, target = callback.data.split(":")
    uid = str(callback.from_user.id)
    me = get_user(uid)

    if target not in db["users"] or target == uid:
        await callback.answer()
        return

    other = db["users"][target]

    if action == "like" and not is_vip(uid):
        today = time.strftime("%Y-%m-%d")
        if me.get("likes_day") != today:
            me["likes_day"] = today
            me["likes_today"] = 0
        if me["likes_today"] >= FREE_LIKES_PER_DAY:
            await callback.answer(tr(uid, "likes_limit"), show_alert=True)
            return
        me["likes_today"] += 1

    if target not in me["seen"]:
        me["seen"].append(target)

    if action == "like":
        if target not in me["likes"]:
            me["likes"].append(target)
        if uid in other["likes"] and other["profile"] and me["profile"]:
            await bot.send_message(
                uid,
                tr(uid, "match") + contact_html(target, other["profile"]["name"]),
                parse_mode="HTML",
            )
            await bot.send_message(
                target,
                tr(target, "match") + contact_html(uid, me["profile"]["name"]),
                parse_mode="HTML",
            )
    elif action == "report":
        other["reports"] += 1
        await callback.message.answer(tr(uid, "reported"))
        if ADMIN_ID:
            try:
                await bot.send_message(
                    ADMIN_ID,
                    f"🚩 Жалоба на {target} (всего: {other['reports']})\n"
                    f"/view {target}\n/ban {target}",
                )
            except Exception:
                pass

    save_db()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer()
    await send_next(callback.message.chat.id, uid)


# ---------------------------------------------------------------- run


async def main():
    await bot.delete_webhook()  # polling cannot work while a webhook is set
    backup_task = asyncio.create_task(backup_loop())  # noqa: F841 (keep a reference)
    await dp.start_polling(bot)


asyncio.run(main())
