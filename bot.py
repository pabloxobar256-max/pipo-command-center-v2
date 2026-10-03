# ============================================================
# ⚡ PIPO BOT - النسخة المطورة والاحترافية v5.0 PRO
# 🛡️ نظام أمان متكامل لحماية وإدارة مجموعات التليجرام
# 👑 برمجة وتطوير: @amirx_xpipo | Developer ID: 8050958688
# ============================================================

import asyncio, os, time, random, datetime, re, json, logging
from collections import defaultdict
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import EditBannedRequest, LeaveChannelRequest
from telethon.tl.types import ChatBannedRights, InputPhoto, InputDocument
from aiohttp import web

# إعداد التسجيل والمخرجات
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s: %(message)s'
)
logger = logging.getLogger("PIPO_BOT")

# ============================================================
#  البيانات الأساسية وتوكنات الاتصال
# ============================================================
API_ID = int(os.environ.get("API_ID", 33938821))
API_HASH = os.environ.get("API_HASH", '24a5e855b4cf3ce48e054c32ea725aa4')
BOT_TOKEN = os.environ.get("BOT_TOKEN", '8957362371:AAF_e-BbKcvFBw1cjzILba7bR2Sh8jS81fQ')
DEVELOPER_USERNAME = os.environ.get("DEVELOPER_USERNAME", 'amirx_xpipo')
DEVELOPER_ID = int(os.environ.get("DEVELOPER_ID", 8050958688))
API_TOKEN = os.environ.get("API_TOKEN", "pipomaster2026")
PORT = int(os.environ.get("PORT", 10000))

# ============================================================
#  إدارة تخزين البيانات بصيغة JSON
# ============================================================
def load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"خطأ تحميل {path}: {e}")
    return default

def save_json(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"خطأ حفظ {path}: {e}")

GROUPS_FILE = "groups.json"
BAD_WORDS_FILE = "bad_words.json"
GLOBAL_BAN_FILE = "global_bans.json"

active_groups = set(load_json(GROUPS_FILE, [-1003798077802]))
global_bans = set(load_json(GLOBAL_BAN_FILE, []))

def save_groups():
    save_json(GROUPS_FILE, list(active_groups))

def save_global_bans():
    save_json(GLOBAL_BAN_FILE, list(global_bans))

# ============================================================
#  إعدادات المجموعات الفردية
# ============================================================
def get_group_settings(chat_id):
    path = f"group_settings_{chat_id}.json"
    default = {
        "swear_protection": True,
        "link_protection": True,
        "forward_protection": True,
        "anti_porn_enabled": True,
        "bot_hunter_enabled": True,
        "anti_duplicate_enabled": True,
        "captcha_enabled": True,
        "auto_lock_enabled": False,
        "lock_start_hour": 0,
        "lock_end_hour": 9,
        "mute_duration": 300,
        "welcome_media": {"type": None, "media_id": None, "access_hash": None, "file_reference": ""},
        "welcome_text": "أهلاً بك في مجموعتنا! نتمنى لك إقامة ممتعة مع الالتزام بالقوانين.",
        "rules": "1. الاحترام المتبادل بين الأعضاء.\n2. يمنع نشر الروابط والإعلانات دون إذن الإدارة.\n3. يمنع الألفاظ البذيئة والشتائم بجميع أنواعها.\n4. يمنع المحتوى الإباحي.",
        "max_warnings": 3
    }
    return load_json(path, default)

def save_group_settings(chat_id, data):
    save_json(f"group_settings_{chat_id}.json", data)

# ============================================================
#  قائمة الكلمات الممنوعة
# ============================================================
DEFAULT_BAD_WORDS = [
    r'\b(كس|طيز|زب|نيك|شرموطة|قحبة|منيكة|منيوك|مسطي|مصطي|طحان|طيحان)\b',
    r'\b(zeb|zebi|zebbi|kahba|9ahba|9ahb|9hba|kess|kessou|tiz|tizi|3ass|3asska)\b',
    r'\b(nik|nikom|nikk|neek|nekk|nkk|n6k|9wd|9wad|9awd|gawd|goud|god|9od)\b',
    r'\b(كسمك|كسكم|طيزك|طيزكم|زبك|زبكم|نيكك|نيككم|شراميط|قحبات|منيوكة)\b',
    r'\b(ابن[\s]*القحبة|بنت[\s]*القحبة|ولد[\s]*القحبة|ابن[\s]*الحرام)\b',
    r'\b(انعل[\s]*ابوك|انعل[\s]*امك|انعل[\s]*دينك|انعل[\s]*ربك)\b',
    r'\b(يلعن[\s]*ابوك|يلعن[\s]*امك|يلعن[\s]*دينك|يلعن[\s]*ربك)\b',
]

BAD_WORDS = load_json(BAD_WORDS_FILE, DEFAULT_BAD_WORDS)

def save_bad_words(words):
    save_json(BAD_WORDS_FILE, words)

# ============================================================
#  المتغيرات التشغيلية
# ============================================================
client = TelegramClient('bot_session_pro', API_ID, API_HASH)
BOT_PHOTO = None
bot_locked = False
private_locked = False
mute_status = {}
warnings_data = defaultdict(list)
pending_users = {}
user_last_msg = defaultdict(lambda: defaultdict(float))

# ============================================================
#  الدوال المساعدة
# ============================================================
def is_developer(user_id):
    return user_id == DEVELOPER_ID

async def is_group_admin(chat_id, user_id):
    if user_id == DEVELOPER_ID:
        return True
    try:
        perms = await client.get_permissions(chat_id, user_id)
        return perms.is_admin or perms.is_creator
    except:
        return False

def contains_swear(text):
    if not text:
        return False
    normalized = re.sub(r'[\u064B-\u065F\s\._\*\-#@\~]', '', text).lower()
    for pattern in BAD_WORDS:
        if re.search(pattern, text, re.IGNORECASE) or re.search(pattern, normalized, re.IGNORECASE):
            return True
    return False

LINK_PATTERNS = [
    r'https?://[\w\d\.\-_/\?=&%]+',
    r't\.me/[\w\d_]+',
    r'telegram\.me/[\w\d_]+',
    r'www\.[\w\d\.\-_/]+'
]

def contains_link(text):
    if not text:
        return False
    return any(re.search(p, text, re.IGNORECASE) for p in LINK_PATTERNS)

PORN_KEYWORDS = [
    'sex', 'porn', 'xxx', 'nsfw', 'سكس', 'اباحية', 'جنس', 'porno', 'anal', 'بورن',
    'shemale', 'trans', 'gay', 'lesbian', 'cum', 'orgasm', 'nude', 'naked', 'fuck',
    'bitch', 'افلام اباحية', 'مقاطع للكبار', 'سكسي'
]

def contains_porn(text):
    if not text:
        return False
    t = text.lower()
    return any(w in t for w in PORN_KEYWORDS)

# ============================================================
#  دوال الكتم والحظر
# ============================================================
async def mute_user(chat, user, dur_seconds):
    try:
        until_date = datetime.datetime.fromtimestamp(time.time() + dur_seconds)
        await client(EditBannedRequest(chat, user, ChatBannedRights(
            until_date=until_date,
            send_messages=True,
            send_media=True,
            send_stickers=True,
            send_gifs=True,
            send_games=True,
            send_inline=True,
            embed_link_previews=True
        )))
        return True
    except Exception as e:
        logger.error(f"فشل الكتم في {chat} للمستخدم {user}: {e}")
        return False

async def unmute_user(chat, user):
    try:
        await client(EditBannedRequest(chat, user, ChatBannedRights(
            until_date=None,
            send_messages=False,
            send_media=False,
            send_stickers=False,
            send_gifs=False,
            send_games=False,
            send_inline=False,
            embed_link_previews=False
        )))
        return True
    except Exception as e:
        logger.error(f"فشل فك الكتم: {e}")
        return False

async def ban_user(chat, user):
    try:
        await client(EditBannedRequest(chat, user, ChatBannedRights(
            until_date=None,
            view_messages=True
        )))
        return True
    except Exception as e:
        logger.error(f"فشل الحظر: {e}")
        return False

# ============================================================
#  معالجات الأحداث الأمنية
# ============================================================

@client.on(events.NewMessage(func=lambda e: e.is_group and e.raw_text and ('بوت' in e.raw_text or 'bot' in e.raw_text.lower())))
async def reply_to_bot(event):
    if event.chat_id not in active_groups or bot_locked:
        return
    sender = await event.get_sender()
    if not sender or await is_group_admin(event.chat_id, sender.id):
        return
    await event.reply("يا خو ما دصرنيش حبب")

@client.on(events.NewMessage())
async def handle_swear(event):
    if not event.is_group or event.chat_id not in active_groups or bot_locked:
        return
    sender = await event.get_sender()
    if not sender or await is_group_admin(event.chat_id, sender.id):
        return

    settings = get_group_settings(event.chat_id)
    if not settings.get("swear_protection", True):
        return

    text = event.raw_text or ""
    if contains_swear(text):
        try:
            await event.delete()
        except:
            pass

        dur = settings.get("mute_duration", 300)
        await mute_user(event.chat_id, sender.id, dur)
        mute_status[sender.id] = {
            'until': time.time() + dur,
            'name': sender.first_name or 'عضو',
            'chat_id': event.chat_id
        }
        name = sender.first_name or "العضو"
        await event.respond(f"🚫 عذراً [{name}](tg://user?id={sender.id})، تم حذف رسالتك وكتمك {dur//60} دقيقة بسبب استخدام ألفاظ بذيئة.")

@client.on(events.NewMessage())
async def handle_links(event):
    if not event.is_group or event.chat_id not in active_groups or bot_locked:
        return
    sender = await event.get_sender()
    if not sender or await is_group_admin(event.chat_id, sender.id):
        return

    settings = get_group_settings(event.chat_id)
    if not settings.get("link_protection", True):
        return

    if contains_link(event.raw_text or ""):
        try:
            await event.delete()
        except:
            pass
        name = sender.first_name or "العضو"
        await event.respond(f"🔗 عفواً [{name}](tg://user?id={sender.id})، يمنع نشر الروابط والإعلانات في هذه المجموعة!")

@client.on(events.NewMessage())
async def handle_porn(event):
    if not event.is_group or event.chat_id not in active_groups or bot_locked:
        return
    sender = await event.get_sender()
    if not sender or await is_group_admin(event.chat_id, sender.id):
        return

    settings = get_group_settings(event.chat_id)
    if not settings.get("anti_porn_enabled", True):
        return

    if contains_porn(event.raw_text or ""):
        try:
            await event.delete()
        except:
            pass
        dur = 3600
        await mute_user(event.chat_id, sender.id, dur)
        mute_status[sender.id] = {'until': time.time() + dur, 'name': sender.first_name or 'عضو', 'chat_id': event.chat_id}
        name = sender.first_name or "العضو"
        await event.respond(f"🔞 تحذير أمني: [{name}](tg://user?id={sender.id}) تم كتمك لمدة ساعة لنشر محتوى إباحي ممنوع.")

@client.on(events.NewMessage())
async def handle_flood(event):
    if not event.is_group or event.chat_id not in active_groups or bot_locked:
        return
    sender = await event.get_sender()
    if not sender or await is_group_admin(event.chat_id, sender.id):
        return

    settings = get_group_settings(event.chat_id)
    if not settings.get("anti_duplicate_enabled", True):
        return

    text = (event.raw_text or "").strip()
    if not text:
        return
    now = time.time()
    user_msgs = user_last_msg[sender.id]
    if text in user_msgs and (now - user_msgs[text] < 4):
        try:
            await event.delete()
        except:
            pass
        return
    user_msgs[text] = now

@client.on(events.ChatAction(func=lambda e: e.user_joined or e.user_added))
async def handle_new_member(event):
    if event.chat_id not in active_groups:
        return
    settings = get_group_settings(event.chat_id)
    try:
        user = await event.get_user()
        if not user:
            return

        me = await client.get_me()
        if user.bot and user.id != me.id:
            if settings.get("bot_hunter_enabled", True):
                try:
                    await client.kick_participant(event.chat_id, user.id)
                    await event.respond(f"🤖🛡️ **البوت الحارس:** تم طرد البوت الدخيل ({user.first_name}) لحماية المجموعة.")
                except Exception as ex:
                    logger.error(f"فشل طرد البوت: {ex}")
            return

        if settings.get("captcha_enabled", True) and not user.bot:
            n1 = random.randint(2, 9)
            n2 = random.randint(1, 9)
            ans = n1 + n2
            pending_users[user.id] = {
                'answer': ans,
                'chat': event.chat_id,
                'attempts': 0,
                'created_at': time.time()
            }
            await mute_user(event.chat_id, user.id, 120)

            wrong1 = ans + random.choice([-2, 1, 2, 3])
            wrong2 = ans + random.choice([-3, -1, 4])
            choices = [ans, wrong1, wrong2]
            random.shuffle(choices)

            buttons = [
                [Button.inline(f"🔢 {c}", f"cap_{user.id}_{c}") for c in choices],
                [Button.inline("❌ أنا بوت", f"cap_bot_{user.id}")]
            ]

            await event.respond(
                f"👋 أهلاً بك يا [{user.first_name}](tg://user?id={user.id}) في مجموعتنا!\n\n"
                f"🛡️ **تحقق أمني:** الرجاء حل المسألة لتأكيد أنك إنسان وتفعيل الشات:\n"
                f"❓ **{n1} + {n2} = ؟**\n"
                f"⏳ اضغط على الزر الصحيح خلال دقيقة واحدة.",
                buttons=buttons
            )
            return

        welcome_text = settings.get("welcome_text", "أهلاً بك في مجموعتنا!")
        buttons = [
            [Button.inline("📜 قوانين المجموعة", "group_rules_btn")]
        ]
        await event.respond(f"🎉 مرحباً بك [{user.first_name}](tg://user?id={user.id})!\n{welcome_text}", buttons=buttons)

    except Exception as e:
        logger.error(f"خطأ ترحيب: {e}")

@client.on(events.CallbackQuery(pattern=r'^cap_'))
async def on_captcha_click(event):
    data = event.data.decode('utf-8')
    parts = data.split('_')

    if len(parts) >= 3 and parts[1] == "bot":
        uid = int(parts[2])
        if event.sender_id == uid:
            try:
                await client.kick_participant(event.chat_id, uid)
                await event.edit("🚫 تم طرد المستخدم بناءً على اختياره.")
            except:
                pass
        return

    if len(parts) >= 3:
        target_uid = int(parts[1])
        selected_val = int(parts[2])

        if event.sender_id != target_uid:
            await event.answer("⚠️ هذا الاختبار مخصص للعضو المنضم حديثاً فقط!", alert=True)
            return

        if target_uid in pending_users:
            correct = pending_users[target_uid]['answer']
            if selected_val == correct:
                del pending_users[target_uid]
                await unmute_user(event.chat_id, target_uid)
                await event.edit("✅ **تم التحقق بنجاح!**\nتم فك القيود ويمكنك الآن المشاركة في المجموعة بحرية. مرحباً بك! 🎉")
            else:
                pending_users[target_uid]['attempts'] += 1
                if pending_users[target_uid]['attempts'] >= 2:
                    del pending_users[target_uid]
                    try:
                        await client.kick_participant(event.chat_id, target_uid)
                    except:
                        pass
                    await event.edit("❌ فشل التحقق الأمني، تم طردك لحماية المجموعة.")
                else:
                    await event.answer("❌ إجابة خاطئة! لديك فرصة واحدة متبقية.", alert=True)

@client.on(events.CallbackQuery(pattern='^group_rules_btn$'))
async def on_rules_click(event):
    settings = get_group_settings(event.chat_id)
    rules = settings.get("rules", "لا توجد قوانين محددة حالياً.")
    await event.answer(f"📜 قوانين المجموعة:\n{rules}", alert=True)

@client.on(events.NewMessage(func=lambda e: e.is_private))
async def private_handler(event):
    if private_locked and event.sender_id != DEVELOPER_ID:
        await event.reply("🔒 تم قفل خاص البوت بواسطة المطور.")
        return

@client.on(events.NewMessage(pattern='^/غلق_الخاص$', from_users=DEVELOPER_ID))
async def lock_private(event):
    global private_locked
    private_locked = True
    await event.reply("🔒 تم قفل خاص البوت بنجاح.")

@client.on(events.NewMessage(pattern='^/فتح_الخاص$', from_users=DEVELOPER_ID))
async def unlock_private(event):
    global private_locked
    private_locked = False
    await event.reply("🔓 تم فتح خاص البوت بنجاح.")

# ============================================================
#  مهام الفحص الدورية
# ============================================================
async def background_tasks():
    while True:
        try:
            now = time.time()
            for uid, info in list(mute_status.items()):
                if info['until'] <= now:
                    chat_id = info.get('chat_id')
                    if chat_id:
                        await unmute_user(chat_id, uid)
                    else:
                        for gid in active_groups:
                            try: await unmute_user(gid, uid)
                            except: pass
                    del mute_status[uid]
        except Exception as e:
            logger.error(f"خطأ في المهام الدورية: {e}")
        await asyncio.sleep(25)

# ============================================================
#  خادم الويب API للوحة التحكم
# ============================================================
def cors_json_response(data, status=200):
    return web.json_response(data, status=status, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type, X-Bot-Token",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
    })

async def options_handler(request):
    return web.Response(headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type, X-Bot-Token",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
    })

async def api_handler(request):
    token = request.headers.get('X-Bot-Token', '')
    if token != API_TOKEN:
        return cors_json_response({'error': 'Unauthorized'}, status=403)
    path = request.path
    data = await request.json() if request.method == 'POST' else {}

    if path == '/api/stats':
        return cors_json_response({
            'totalGroups': len(active_groups),
            'totalMuted': len(mute_status),
            'totalBanned': len(global_bans),
            'totalWarnings': sum(len(w) for w in warnings_data.values()),
            'botLocked': bot_locked,
            'privateLocked': private_locked
        })

    if path == '/api/groups':
        res = []
        for gid in active_groups:
            try:
                ent = await client.get_entity(gid)
                title = ent.title
            except:
                title = f"مجموعة {gid}"
            res.append({
                'id': str(gid),
                'title': title,
                'settings': get_group_settings(gid)
            })
        return cors_json_response({'groups': res})

    if path == '/api/broadcast':
        msg = data.get('message', '')
        pin = data.get('pin', False)
        if not msg:
            return cors_json_response({'error': 'رسالة فارغة'}, status=400)
        cnt = 0
        for gid in active_groups:
            try:
                sent = await client.send_message(gid, f"📢 **إذاعة رسمية من الإدارة:**\n\n{msg}\n\n👑 @{DEVELOPER_USERNAME}")
                if pin:
                    await client.pin_admin(gid, sent.id)
                cnt += 1
            except Exception as e:
                logger.error(f"فشل الإرسال لـ {gid}: {e}")
        return cors_json_response({'success': True, 'count': cnt})

    if path == '/api/unmute':
        uid = data.get('uid')
        if uid:
            for gid in active_groups:
                try: await unmute_user(gid, uid)
                except: pass
            if uid in mute_status:
                del mute_status[uid]
            return cors_json_response({'success': True})

    return cors_json_response({'error': 'غير معروف'})

# ============================================================
#  ✅ دالة خدمة control.html
# ============================================================
async def serve_control(request):
    """يفتح control.html"""
    try:
        return web.FileResponse('control.html')
    except Exception as e:
        logger.error(f"خطأ في خدمة control.html: {e}")
        return web.Response(text=f"خطأ: {e}", status=500)

async def serve_root(request):
    """الصفحة الرئيسية تفتح اللوحة"""
    return await serve_control(request)

async def health(request):
    """health check بسيط"""
    return web.Response(text="OK")

# ============================================================
#  التشغيل الرئيسي
# ============================================================
async def main():
    logger.info("⚡ جاري تشغيل PIPO BOT v5.0...")
    await client.start(bot_token=BOT_TOKEN)
    me = await client.get_me()
    logger.info(f"✅ تم تسجيل الدخول بنجاح كـ: @{me.username} (ID: {me.id})")

    app = web.Application()

    # CORS preflight
    app.router.add_route('OPTIONS', '/{tail:.*}', options_handler)

    # API routes
    app.router.add_get('/api/stats', api_handler)
    app.router.add_get('/api/groups', api_handler)
    app.router.add_post('/api/broadcast', api_handler)
    app.router.add_post('/api/unmute', api_handler)

    # لوحة التحكم
    app.router.add_get('/', serve_root)
    app.router.add_get('/control.html', serve_control)

    # Health check
    app.router.add_get('/health', health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logger.info(f"🌐 خادم الويب يعمل على المنفذ {PORT}")
    logger.info(f"🎛️ لوحة التحكم: http://0.0.0.0:{PORT}/control.html")

    asyncio.create_task(background_tasks())
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
