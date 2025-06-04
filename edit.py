import asyncio
import logging
import time
import json
import os
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ChatMemberAdministrator, ChatMemberOwner
)
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)

# --- Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- Globals ---
authorized_users = {}
deletion_delay = {}
CHANNEL_USERNAME = "@federation_of_shadows"
SUPPORT_LINK = "https://t.me/federation_of_shadows"
global_bans = set()
global_mutes = set()
stats_data = {"groups": set(), "users": set()}
sudo_users = {
    "lord": 7819315360,
    "substitute_lords": {8162803790, 6138142369},
    "descendants": set(),
}
ALL_COMMANDS = [
    "auth", "setdelay", "gban", "ungban", "gmute", "ungmute",
    "addsudouser", "rmsudouser", "sudousers", "stats"
]
ALL_COMMANDS = sorted(set(ALL_COMMANDS))
MODULES_COUNT = len(ALL_COMMANDS)
bot_start_time = time.time()

# --- Utility Functions ---

def is_admin_member(member):
    try:
        return isinstance(member, ChatMemberAdministrator) or isinstance(member, ChatMemberOwner)
    except Exception as e:
        logging.error(f"is_admin_member error: {e}")
        return False

def is_sudo(user_id):
    try:
        return (
            user_id == sudo_users["lord"] or
            user_id in sudo_users.get("substitute_lords", set()) or
            user_id in sudo_users.get("descendants", set())
        )
    except Exception as e:
        logging.error(f"is_sudo error: {e}")
        return False
def is_owner(user_id):
    try:
        return user_id == sudo_users["lord"]
    except Exception as e:
        logging.error(f"is_owner error: {e}")
        return False
async def get_stats():
    try:
        groups = stats_data.get("groups", set())
        users = stats_data.get("users", set())
        total_groups = len(groups)
        total_users = len(users)
        return {
            "total_groups": total_groups,
            "total_users": total_users,
            "uptime": int(time.time() - bot_start_time),
            "modules_count": MODULES_COUNT
        }
    except Exception as e:
        logging.error(f"get_stats error: {e}")
        return {"error": str(e)}
    
    
async def get_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        if update.message.reply_to_message and update.message.reply_to_message.from_user:
            return update.message.reply_to_message.from_user
        if context.args and context.args[0]:
            arg = context.args[0]
            if arg.isdigit():
                try:
                    member = await context.bot.get_chat_member(chat_id, int(arg))
                    return member.user
                except Exception as e:
                    logging.debug(f"get_target_user: user_id lookup failed: {e}")
            username = arg.lstrip("@")
            try:
                user_obj = await context.bot.get_chat("@" + username)
                return user_obj
            except Exception as e:
                logging.debug(f"get_target_user: get_chat failed: {e}")
        await update.message.reply_text(
            "❌ <b>Couldn't find the user. Please reply or provide a valid user ID/username.</b>",
            parse_mode="HTML"
        )
        return None
    except Exception as e:
        logging.error(f"get_target_user error: {e}")
        try:
            await update.message.reply_text("❌ <b>Unexpected error in user lookup.</b>", parse_mode="HTML")
        except Exception:
            pass
        return None

async def is_user_in_channel(user_id, bot):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception as e:
        logging.info(f"User {user_id} is not a member of the channel or error occurred: {e}")
        return False

async def is_admin(update: Update, user_id: int) -> bool:
    """
    Checks if the given user_id is an admin or owner in the chat.
    Returns True if admin/owner, False otherwise.
    """
    try:
        chat = update.effective_chat
        if chat is None:
            return False
        member = await chat.get_member(user_id)
        return member.status in ("administrator", "creator", "owner")
    except Exception as e:
        logging.error(f"is_admin: error checking admin status for user {user_id}: {e}")
        return False

# --- Handlers ---

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        try:
            is_member = await is_user_in_channel(user.id, context.bot)
        except Exception as e:
            logging.error(f"start_handler: channel check failed: {e}")
            is_member = True
        if is_member:
            try:
                bot_me = await context.bot.get_me()
                processing_msg = await update.message.reply_text(
                    "<b>⏳ Please wait while we process your request...</b>\n"
                    "<i>Step 1: Initializing system modules...</i>",
                    parse_mode="HTML"
                )
                await asyncio.sleep(0.8)
                steps = [
                    "<i>Step 2: Verifying channel membership...</i>",
                    "<i>Step 3: Preparing your personalized welcome...</i>",
                    "<i>Step 4: Finalizing setup...</i>"
                ]
                for step in steps:
                    try:
                        await processing_msg.edit_text(
                            "<b>⏳ Please wait while we process your request...</b>\n" + step,
                            parse_mode="HTML"
                        )
                    except Exception:
                        pass
                    await asyncio.sleep(0.8)
                welcome_text = (
                    f"• Hello {user.mention_html()}\n\n"
                    "• I'm the most advanced Telegram text copyright protector bot.\n"
                    "• I safeguard your groups by automatically detecting and deleting edited messages after a set delay.\n\n"
                    "⚙️ <b>Key Highlights:</b>\n"
                    "• Delayed message deletion system\n"
                    "• Copyright protection\n"
                    "• Permit trusted users\n"
                    "• Fully customizable deletion timer\n\n"
                    "➜ <b>Add me to your group to get started.</b>"
                )
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{bot_me.username}?startgroup=true")],
                    [
                        InlineKeyboardButton("👑 Owner", url="https://t.me/FOS_FOUNDER"),
                        InlineKeyboardButton("💬 Support", url=SUPPORT_LINK),
                    ]
                ])
                try:
                    with open("C:/Users/Anirudh/Desktop/edit.jpg", "rb") as photo_file:
                        await processing_msg.delete()
                        await update.message.reply_photo(
                            photo=photo_file,
                            caption=welcome_text,
                            parse_mode="HTML",
                            reply_markup=kb
                        )
                except Exception as e:
                    logging.warning(f"start_handler: photo send failed: {e}")
                    try:
                        await processing_msg.edit_text(
                            welcome_text,
                            parse_mode="HTML",
                            reply_markup=kb
                        )
                    except Exception:
                        pass
            except Exception as e:
                logging.error(f"start_handler: welcome flow failed: {e}")
        else:
            try:
                keyboard = [
                    [InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"<b>Access Restricted</b>\n"
                    f"Hello {user.mention_html()},\n\n"
                    "To access the full features of this bot, please join our official channel first.\n"
                    "Once you have joined, use /start again.",
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
            except Exception as e:
                logging.error(f"start_handler: restricted message failed: {e}")
    except Exception as e:
        logging.error(f"start_handler error: {e}")
        try:
            await update.message.reply_text("❌ <b>Unexpected error in /start.</b>", parse_mode="HTML")
        except Exception:
            pass

async def auth_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not (await is_admin(update, update.effective_user.id) or is_sudo(update.effective_user.id)):
            await update.message.reply_text("❌ Only admins, owners, or sudo users can authorize users.")
            return

        chat_id = update.effective_chat.id
        user_id = None
        mention = None
        if update.message.reply_to_message and update.message.reply_to_message.from_user:
            user_id = update.message.reply_to_message.from_user.id
            mention = update.message.reply_to_message.from_user.mention_html()
        elif context.args and len(context.args) == 1:
            try:
                user_id = int(context.args[0])
                if user_id <= 0:
                    raise ValueError
            except ValueError:
                await update.message.reply_text("Invalid user ID. Please provide a valid positive integer.")
                return
        else:
            await update.message.reply_text("Usage: /auth <user_id>\nOr reply to a user's message with /auth")
            return

        authorized_users.setdefault(chat_id, set()).add(user_id)

        if not mention:
            try:
                user = await context.bot.get_chat_member(chat_id, user_id)
                mention = user.user.mention_html()
            except Exception:
                mention = f"<code>{user_id}</code>"

        keyboard = [
            [InlineKeyboardButton("Support Channel", url=SUPPORT_LINK)],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"✅ <b>User {mention} has been authorized successfully!</b>\n\n"
            "They can now edit messages without automatic deletion.",
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    except Exception as e:
        logging.error(f"auth_user error: {e}")
        try:
            await update.message.reply_text("An unexpected error occurred while authorizing the user.")
        except Exception:
            pass

async def set_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_admin(update, update.effective_user.id):
            await update.message.reply_text("❌ Only admins or owners can set the deletion delay.")
            return
        if not context.args or len(context.args) == 0:
            keyboard = [
                [
                    InlineKeyboardButton("Seconds", callback_data="setdelay_unit_seconds"),
                    InlineKeyboardButton("Minutes", callback_data="setdelay_unit_minutes"),
                    InlineKeyboardButton("Hours", callback_data="setdelay_unit_hours"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "Choose the time unit for the deletion delay:",
                reply_markup=reply_markup
            )
            return
        if len(context.args) == 1:
            unit = context.args[0].lower()
            if unit not in ["seconds", "minutes", "hours"]:
                await update.message.reply_text("Invalid unit. Please choose from seconds, minutes, or hours.")
                return
            values = [5, 10, 30, 60, 120, 300, 600, 1800, 3600] if unit == "seconds" else [1, 5, 10, 15, 30, 60] if unit == "minutes" else [1]
            keyboard = [
                [InlineKeyboardButton(str(v), callback_data=f"setdelay_value_{unit}_{v}")]
                for v in values
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"How many {unit} should the deletion delay be? Choose below or send a number.",
                reply_markup=reply_markup
            )
            context.user_data["setdelay_unit"] = unit
            return
        if len(context.args) == 2:
            unit = context.args[0].lower()
            try:
                value = int(context.args[1])
            except ValueError:
                await update.message.reply_text("Please provide a valid number for the delay.")
                return
            if unit == "seconds":
                if not (1 <= value <= 3600):
                    await update.message.reply_text("Seconds must be between 1 and 3600.")
                    return
                delay = value
            elif unit == "minutes":
                if not (1 <= value <= 60):
                    await update.message.reply_text("Minutes must be between 1 and 60.")
                    return
                delay = value * 60
            elif unit == "hours":
                if value != 1:
                    await update.message.reply_text("Hours can only be set to 1 (3600 seconds).")
                    return
                delay = 3600
            else:
                await update.message.reply_text("Invalid unit. Please choose from seconds, minutes, or hours.")
                return
            chat_id = update.effective_chat.id
            deletion_delay[chat_id] = delay
            await update.message.reply_text(
                f"✅ Deletion delay has been set to <b>{delay} seconds</b> for this chat.",
                parse_mode="HTML"
            )
            return
        await update.message.reply_text("Usage: /setdelay [seconds|minutes|hours] [amount]")
    except Exception as e:
        logging.error(f"set_delay error: {e}")
        try:
            await update.message.reply_text("An unexpected error occurred while setting the delay.")
        except Exception:
            pass

async def set_delay_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        if query is None:
            return
        await query.answer()
        data = query.data
        if not data:
            await query.edit_message_text("No callback data received. Please try again.")
            return
        if data.startswith("setdelay_unit_"):
            unit = data.split("_")[-1]
            if unit not in ["seconds", "minutes", "hours"]:
                await query.edit_message_text("Invalid unit selected. Please try again.")
                return
            values = [5, 10, 30, 60, 120, 300, 600, 1800, 3600] if unit == "seconds" else [1, 5, 10, 15, 30, 60] if unit == "minutes" else [1]
            keyboard = [
                [InlineKeyboardButton(str(v), callback_data=f"setdelay_value_{unit}_{v}")]
                for v in values
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"How many {unit} should the deletion delay be? Choose below or send a number.",
                reply_markup=reply_markup
            )
            context.user_data["setdelay_unit"] = unit
        elif data.startswith("setdelay_value_"):
            parts = data.split("_")
            if len(parts) < 4:
                await query.edit_message_text("Invalid callback data format. Please try again.")
                return
            unit = parts[2]
            value_str = "_".join(parts[3:])  # In case value contains underscores
            try:
                value = int(value_str)
            except ValueError:
                await query.edit_message_text("Invalid value for delay. Please select a valid number.")
                return
            if unit == "seconds":
                if not (1 <= value <= 3600):
                    await query.edit_message_text("Seconds must be between 1 and 3600.")
                    return
                delay = value
            elif unit == "minutes":
                if not (1 <= value <= 60):
                    await query.edit_message_text("Minutes must be between 1 and 60.")
                    return
                delay = value * 60
            elif unit == "hours":
                if value != 1:
                    await query.edit_message_text("Hours can only be set to 1 (3600 seconds).")
                    return
                delay = 3600
            else:
                await query.edit_message_text("Invalid unit. Please try again.")
                return
            chat_id = query.message.chat_id if query.message else None
            if chat_id is None:
                await query.edit_message_text("Could not determine chat ID. Please try again.")
                return
            deletion_delay[chat_id] = delay
            await query.edit_message_text(
                f"✅ Deletion delay has been set to <b>{delay} seconds</b> for this chat.",
                parse_mode="HTML"
            )
        else:
            await query.edit_message_text("Unknown callback data. Please try again.")
    except Exception as e:
        logging.error(f"set_delay_callback error: {e}")
        try:
            if update.callback_query:
                await update.callback_query.edit_message_text("An unexpected error occurred in set_delay_callback.")
        except Exception:
            pass

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        help_text = (
            "<b>🛡️ Edit Saviour Bot Help</b>\n\n"
            "This bot protects your group by deleting edited messages after a set delay.\n\n"
            "<b>🛠️ Available Commands:</b>\n"
            "<b>/start</b> — Start the bot and get a welcome message.\n"
            "<b>/help</b> — Show this help message.\n\n"
            "<b>Admin & User Commands:</b>\n"
            "<b>/auth &lt;user_id&gt;</b> — Authorize a user to edit messages without auto-deletion.\n"
            "<b>/unauth &lt;user_id&gt;</b> — Remove a user's authorization.\n"
            "<b>/setdelay</b> — Set the deletion delay for edited messages.\n"
            "<b>/stats</b> — Show bot statistics.\n"
            "<b>/uptime</b> — Show bot uptime.\n"
        )
        keyboard = [
            [
                InlineKeyboardButton(
                    "➕ Add to Group",
                    url=f"https://t.me/{(await context.bot.get_me()).username}?startgroup=true"
                ),
                InlineKeyboardButton("💬 Support", url=SUPPORT_LINK)
            ],
            [
                InlineKeyboardButton("🔔 Channel", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            help_text,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    except Exception as e:
        logging.error(f"help_command error: {e}")
        try:
            await update.message.reply_text("An error occurred while displaying help.")
        except Exception:
            pass

async def gban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not is_sudo(update.effective_user.id):
            await update.message.reply_text("❌ Only sudo users can use this command.")
            return
        target = await get_target_user(update, context)
        if not target:
            return
        if target.id in global_bans:
            await update.message.reply_text("User is already globally banned.")
            return
        global_bans.add(target.id)
        failed_groups = []
        success_groups = []
        for group_id in stats_data.get("groups", set()):
            try:
                await context.bot.ban_chat_member(group_id, target.id)
                success_groups.append(group_id)
            except Exception as e:
                logging.debug(f"gban: failed to ban in group {group_id}: {e}")
                failed_groups.append(group_id)
        total_groups = len(stats_data.get("groups", set()))
        banned_count = len(success_groups)
        failed_count = len(failed_groups)
        await update.message.reply_text(
            f"🚫 <b>{target.mention_html()}</b> has been <b>globally banned</b>.\n"
            f"Banned in <b>{banned_count}</b> out of <b>{total_groups}</b> group(s) where the bot is present.",
            parse_mode="HTML"
        )
        if failed_groups:
            await update.message.reply_text(
                f"⚠️ Could not ban user in {failed_count} group(s) (bot may lack permissions).",
                parse_mode="HTML"
            )
    except Exception as e:
        logging.error(f"gban error: {e}")
        try:
            await update.message.reply_text("An error occurred while globally banning the user.")
        except Exception:
            pass

async def ungban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not is_sudo(update.effective_user.id):
            await update.message.reply_text("❌ Only sudo users can use this command.")
            return
        target = await get_target_user(update, context)
        if not target:
            return
        if target.id not in global_bans:
            await update.message.reply_text("User is not globally banned.")
            return
        global_bans.discard(target.id)
        failed_groups = []
        success_groups = []
        for group_id in stats_data.get("groups", set()):
            try:
                await context.bot.unban_chat_member(group_id, target.id)
                success_groups.append(group_id)
            except Exception as e:
                logging.debug(f"ungban: failed to unban in group {group_id}: {e}")
                failed_groups.append(group_id)
        total_groups = len(stats_data.get("groups", set()))
        unbanned_count = len(success_groups)
        failed_count = len(failed_groups)
        await update.message.reply_text(
            f"✅ <b>{target.mention_html()}</b> has been <b>globally unbanned</b>.\n"
            f"Unbanned in <b>{unbanned_count}</b> out of <b>{total_groups}</b> group(s) where the bot is present.",
            parse_mode="HTML"
        )
        if failed_groups:
            await update.message.reply_text(
                f"⚠️ Could not unban user in {failed_count} group(s) (bot may lack permissions).",
                parse_mode="HTML"
            )
    except Exception as e:
        logging.error(f"ungban error: {e}")
        try:
            await update.message.reply_text("An error occurred while unbanning the user.")
        except Exception:
            pass

async def gmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not is_sudo(update.effective_user.id):
            await update.message.reply_text("❌ Only sudo users can use this command.")
            return
        target = await get_target_user(update, context)
        if not target:
            return
        if target.id in global_mutes:
            await update.message.reply_text("User is already globally muted.")
            return
        global_mutes.add(target.id)
        # Try to delete all recent messages from the user in all groups (if possible)
        failed_groups = []
        for group_id in stats_data.get("groups", set()):
            try:
                # Optionally, restrict user from sending messages (if bot is admin)
                await context.bot.restrict_chat_member(
                    group_id, target.id,
                    permissions={"can_send_messages": False}
                )
            except Exception as e:
                logging.debug(f"gmute: failed to restrict in group {group_id}: {e}")
                failed_groups.append(group_id)
        await update.message.reply_text(
            f"🔇 <b>{target.mention_html()}</b> has been <b>globally muted</b>.\n"
            "All messages from this user will be deleted.",
            parse_mode="HTML"
        )
        if failed_groups:
            await update.message.reply_text(
                f"⚠️ Could not restrict user in {len(failed_groups)} group(s) (bot may lack permissions).",
                parse_mode="HTML"
            )
    except Exception as e:
        logging.error(f"gmute error: {e}")
        try:
            await update.message.reply_text("An error occurred while muting the user.")
        except Exception:
            pass

async def enforce_global_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        msg = getattr(update, "message", None)
        if not msg or not getattr(msg, "from_user", None):
            return
        user_id = msg.from_user.id
        if user_id in global_mutes:
            try:
                await msg.delete()
            except Exception as e:
                logging.debug(f"enforce_global_mute: failed to delete muted user's message: {e}")
    except Exception as e:
        logging.error(f"enforce_global_mute error: {e}")

async def ungmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not is_sudo(update.effective_user.id):
            await update.message.reply_text("❌ Only sudo users can use this command.")
            return
        target = await get_target_user(update, context)
        if not target:
            return
        if target.id not in global_mutes:
            await update.message.reply_text("User is not globally muted.")
            return
        global_mutes.discard(target.id)
        failed_groups = []
        for group_id in stats_data.get("groups", set()):
            try:
                # Remove restrictions (allow sending messages)
                await context.bot.restrict_chat_member(
                    group_id, target.id,
                    permissions={
                        "can_send_messages": True,
                        "can_send_media_messages": True,
                        "can_send_polls": True,
                        "can_send_other_messages": True,
                        "can_add_web_page_previews": True,
                        "can_change_info": False,
                        "can_invite_users": True,
                        "can_pin_messages": False,
                    }
                )
            except Exception as e:
                logging.debug(f"ungmute: failed to unrestrict in group {group_id}: {e}")
                failed_groups.append(group_id)
        await update.message.reply_text(
            f"✅ <b>{target.mention_html()}</b> has been <b>globally unmuted</b>.\n"
            "The user will be allowed to send messages.",
            parse_mode="HTML"
        )
        if failed_groups:
            await update.message.reply_text(
                f"⚠️ Could not unrestrict user in {len(failed_groups)} group(s) (bot may lack permissions).",
                parse_mode="HTML"
            )
    except Exception as e:
        logging.error(f"ungmute error: {e}")
        try:
            await update.message.reply_text("An error occurred while unmuting the user.")
        except Exception:
            pass

async def addsudouser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id != sudo_users["lord"]:
            await update.message.reply_text("❌ Only the bot owner can add sudo users.")
            return
        if not context.args or len(context.args) < 2 or not context.args[0].isdigit():
            await update.message.reply_text(
                "🚦 <b>Usage:</b> <code>/addsudouser &lt;user_id&gt; &lt;type:sub|desc&gt;</code>\n"
                "• <b>sub</b> — Assign as <b>Substitute Lord</b> (full sudo powers)\n"
                "• <b>desc</b> — Assign as <b>Descendant</b> (limited sudo powers)",
                parse_mode="HTML"
            )
            return
        user_id = int(context.args[0])
        user_type = context.args[1].lower()
        if user_id == sudo_users["lord"]:
            await update.message.reply_text("❌ The owner is already a sudo user.")
            return
        if user_type == "sub":
            if user_id in sudo_users["substitute_lords"]:
                await update.message.reply_text(
                    f"User <code>{user_id}</code> is already a Substitute Lord.",
                    parse_mode="HTML"
                )
                return
            sudo_users["substitute_lords"].add(user_id)
            await update.message.reply_text(
                f"👑 <b>Substitute Lord Ascends!</b>\n"
                f"<code>{user_id}</code> now wields the power of a <b>Substitute Lord</b>.\n"
                "The shadows salute their new commander!",
                parse_mode="HTML"
            )
        elif user_type == "desc":
            if user_id in sudo_users["descendants"]:
                await update.message.reply_text(
                    f"User <code>{user_id}</code> is already a Descendant.",
                    parse_mode="HTML"
                )
                return
            sudo_users["descendants"].add(user_id)
            await update.message.reply_text(
                f"🧬 <b>Descendant Initiated!</b>\n"
                f"<code>{user_id}</code> is now a <b>Descendant</b> of the Lord.\n"
                "A new legacy emerges from the darkness!",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                "❌ <b>Invalid type.</b> Use <code>sub</code> for Substitute Lord or <code>desc</code> for Descendant.",
                parse_mode="HTML"
            )
    except Exception as e:
        logging.error(f"addsudouser error: {e}")
        try:
            await update.message.reply_text("An error occurred while adding sudo user.")
        except Exception:
            pass

async def rmsudouser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id != sudo_users["lord"]:
            await update.message.reply_text("❌ Only the bot owner can remove sudo users.")
            return
        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text(
                "🚦 <b>Usage:</b> <code>/rmsudouser &lt;user_id&gt;</code>",
                parse_mode="HTML"
            )
            return
        user_id = int(context.args[0])
        if user_id == sudo_users["lord"]:
            await update.message.reply_text("❌ You cannot remove the owner from sudo users.")
            return
        removed = False
        if user_id in sudo_users.get("substitute_lords", set()):
            sudo_users["substitute_lords"].discard(user_id)
            removed = True
        if user_id in sudo_users.get("descendants", set()):
            sudo_users["descendants"].discard(user_id)
            removed = True
        if removed:
            await update.message.reply_text(
                f"✅ User <code>{user_id}</code> removed from sudo users.",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                f"User <code>{user_id}</code> is not a sudo user.",
                parse_mode="HTML"
            )
    except Exception as e:
        logging.error(f"rmsudouser error: {e}")
        try:
            await update.message.reply_text("An error occurred while removing sudo user.")
        except Exception:
            pass
async def authusers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        users = authorized_users.get(chat_id, set())
        if not users:
            await update.message.reply_text("No users are authorized in this chat.")
            return

        mentions = []
        for user_id in users:
            try:
                user = await context.bot.get_chat_member(chat_id, user_id)
                mentions.append(user.user.mention_html())
            except Exception:
                mentions.append(f"<code>{user_id}</code>")

        text = "<b>✅ Authorized Users in this chat:</b>\n" + "\n".join(f"• {m}" for m in mentions)
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"authusers error: {e}")
        try:
            await update.message.reply_text("An error occurred while listing authorized users.")
        except Exception:
            pass
async def sudousers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        lord = sudo_users["lord"]
        substitutes = sudo_users.get("substitute_lords", set())
        descendants = sudo_users.get("descendants", set())

        async def get_mention(user_id):
            try:
                user = await context.bot.get_chat(user_id)
                return user.mention_html()
            except Exception:
                return f"<code>{user_id}</code>"

        processing_msg = await update.message.reply_text(
            "<b>⏳ Fetching sudo users...</b>\n<i>Step 1: Gathering Lord info...</i>",
            parse_mode="HTML"
        )
        await asyncio.sleep(0.7)

        lines = [
            "👑 <b>Sudo Users Control Panel</b> 👑",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]
        # Step 2: Lord
        await processing_msg.edit_text(
            "<b>⏳ Fetching sudo users...</b>\n<i>Step 2: Fetching Lord...</i>",
            parse_mode="HTML"
        )
        lord_mention = await get_mention(lord)
        lines.append(f"👑 <b>Lord:</b> {lord_mention}")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        await asyncio.sleep(0.7)

        # Step 3: Substitute Lords
        await processing_msg.edit_text(
            "<b>⏳ Fetching sudo users...</b>\n<i>Step 3: Fetching Substitute Lords...</i>",
            parse_mode="HTML"
        )
        if substitutes:
            lines.append("🦸 <b>Substitute Lords:</b>")
            for uid in substitutes:
                lines.append(f"   └ {await get_mention(uid)}")
                await asyncio.sleep(0.2)
        else:
            lines.append("🦸 <b>Substitute Lords:</b>\n   └ None")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        await asyncio.sleep(0.7)

        # Step 4: Descendants
        await processing_msg.edit_text(
            "<b>⏳ Fetching sudo users...</b>\n<i>Step 4: Fetching Descendants...</i>",
            parse_mode="HTML"
        )
        if descendants:
            lines.append("🧬 <b>Descendants:</b>")
            for uid in descendants:
                lines.append(f"   └ {await get_mention(uid)}")
                await asyncio.sleep(0.2)
        else:
            lines.append("🧬 <b>Descendants:</b>\n   └ None")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("Only the Lord and Substitute Lords can manage sudo users.")
        lines.append("⚡️ Sudo powers are reserved for the elite. Use them wisely! ⚡️")

        await processing_msg.edit_text("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        logging.error(f"sudousers error: {e}")
        try:
            await update.message.reply_text("An error occurred while listing sudo users.")
        except Exception:
            pass

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        groups = len(stats_data["groups"])
        users = len(stats_data["users"])
        bans = len(global_bans)
        mutes = len(global_mutes)
        sudos = 1 + len(sudo_users.get("substitute_lords", set())) + len(sudo_users.get("descendants", set()))
        text = (
            "<b>📊 Bot Statistics:</b>\n"
            f"• <b>Groups:</b> {groups}\n"
            f"• <b>Users:</b> {users}\n"
            f"• <b>Global Bans:</b> {bans}\n"
            f"• <b>Global Mutes:</b> {mutes}\n"
            f"• <b>Sudo Users:</b> {sudos}\n"
            f"• <b>Modules:</b> {MODULES_COUNT}\n"
        )
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"stats error: {e}")
        try:
            await update.message.reply_text("An error occurred while fetching stats.")
        except Exception:
            pass
async def unauth_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_admin(update, update.effective_user.id):
            await update.message.reply_text("❌ Only admins or owners can unauthorize users.")
            return

        chat_id = update.effective_chat.id
        user_id = None
        mention = None

        if update.message.reply_to_message and update.message.reply_to_message.from_user:
            user_id = update.message.reply_to_message.from_user.id
            mention = update.message.reply_to_message.from_user.mention_html()
        elif context.args and len(context.args) == 1:
            try:
                user_id = int(context.args[0])
                if user_id <= 0:
                    raise ValueError
            except ValueError:
                await update.message.reply_text("Invalid user ID. Please provide a valid positive integer.")
                return
        else:
            await update.message.reply_text("Usage: /unauth <user_id>\nOr reply to a user's message with /unauth")
            return

        if chat_id in authorized_users and user_id in authorized_users[chat_id]:
            authorized_users[chat_id].discard(user_id)
            if not mention:
                try:
                    user = await context.bot.get_chat_member(chat_id, user_id)
                    mention = user.user.mention_html()
                except Exception:
                    mention = f"<code>{user_id}</code>"
            await update.message.reply_text(
                f"🚫 <b>User {mention} has been unauthorized successfully!</b>\n\n"
                "They will now be subject to automatic deletion of edited messages.",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text("User is not authorized in this chat.")
    except Exception as e:
        logging.error(f"unauth_user error: {e}")
        try:
            await update.message.reply_text("An unexpected error occurred while unauthorizing the user.")
        except Exception:
            pass
async def edited_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        msg = getattr(update, "edited_message", None) or getattr(update, "message", None)
        if not msg:
            return
        chat_id = msg.chat_id
        user_id = msg.from_user.id

        # Enforce global mute if needed
        if user_id in global_mutes:
            try:
                await msg.delete()
            except Exception as e:
                logging.debug(f"edited_message: failed to delete globally muted user's message: {e}")
            return

        # Allow authorized users to edit without deletion
        if chat_id in authorized_users and user_id in authorized_users[chat_id]:
            return

        delay = deletion_delay.get(chat_id, 10)
        await asyncio.sleep(delay)

        try:
            await msg.delete()
            mention = msg.from_user.mention_html()
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"✏️ {mention} edited a message and it was deleted by the bot after the saved time.",
                parse_mode="HTML"
            )
        except Exception as e:
            logging.debug(f"edited_message: failed to delete message or send mention: {e}")
    except Exception as e:
        logging.error(f"edited_message error: {e}")

async def uptime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        now = time.time()
        uptime_seconds = int(now - bot_start_time)
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        uptime_str = " ".join(parts)
        await update.message.reply_text(
            f"⏱️ <b>Bot Uptime</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<b>🟢 Online for:</b> <code>{uptime_str}</code>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<i>Stay Safe with Edit Saviour !</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"uptime error: {e}")
        try:
            await update.message.reply_text("An error occurred while fetching uptime.")
        except Exception:
            pass
DATA_FILE = "bot_data.json"

def save_data():
                try:
                    data = {
                        "authorized_users": {str(k): list(v) for k, v in authorized_users.items()},
                        "deletion_delay": {str(k): v for k, v in deletion_delay.items()},
                        "global_bans": list(global_bans),
                        "global_mutes": list(global_mutes),
                        "stats_data": {
                            "groups": list(stats_data["groups"]),
                            "users": list(stats_data["users"])
                        },
                        "sudo_users": {
                            "lord": sudo_users["lord"],
                            "substitute_lords": list(sudo_users.get("substitute_lords", set())),
                            "descendants": list(sudo_users.get("descendants", set()))
                        }
                    }
                    with open(DATA_FILE, "w", encoding="utf-8") as f:
                        json.dump(data, f)
                except Exception as e:
                    logging.error(f"Failed to save data: {e}")

def load_data():
                if not os.path.exists(DATA_FILE):
                    return
                try:
                    with open(DATA_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    authorized_users.clear()
                    for k, v in data.get("authorized_users", {}).items():
                        authorized_users[int(k)] = set(v)
                    deletion_delay.clear()
                    for k, v in data.get("deletion_delay", {}).items():
                        deletion_delay[int(k)] = v
                    global_bans.clear()
                    global_bans.update(data.get("global_bans", []))
                    global_mutes.clear()
                    global_mutes.update(data.get("global_mutes", []))
                    stats_data["groups"] = set(data.get("stats_data", {}).get("groups", []))
                    stats_data["users"] = set(data.get("stats_data", {}).get("users", []))
                    sudo_users["lord"] = data.get("sudo_users", {}).get("lord", sudo_users["lord"])
                    sudo_users["substitute_lords"] = set(data.get("sudo_users", {}).get("substitute_lords", []))
                    sudo_users["descendants"] = set(data.get("sudo_users", {}).get("descendants", []))
                except Exception as e:
                    logging.error(f"Failed to load data: {e}")

            # Save data after every change to critical structures
def save_after(func):
                async def wrapper(*args, **kwargs):
                    result = await func(*args, **kwargs)
                    save_data()
                    return result
                return wrapper

            # Patch handlers that modify data
auth_user = save_after(auth_user)
unauth_user = save_after(unauth_user)
set_delay = save_after(set_delay)
set_delay_callback = save_after(set_delay_callback)
gban = save_after(gban)
ungban = save_after(ungban)
gmute = save_after(gmute)
ungmute = save_after(ungmute)
addsudouser = save_after(addsudouser)
rmsudouser = save_after(rmsudouser)

            # Load data at startup
load_data()
if __name__ == "__main__":
    try:
        app = ApplicationBuilder().token("7272212814:AAE7WLE7S6pflh8xMtRgX3bms0a_vPo2XjY").build()
        app.add_handler(CommandHandler("start", start_handler))
        app.add_handler(CommandHandler("auth", auth_user))
        app.add_handler(CommandHandler("unauth", unauth_user))
        app.add_handler(CommandHandler("authusers", authusers))
        app.add_handler(CommandHandler("setdelay", set_delay))
        app.add_handler(CallbackQueryHandler(set_delay_callback))
        app.add_handler(CommandHandler("gban", gban))
        app.add_handler(CommandHandler("ungban", ungban))
        app.add_handler(CommandHandler("gmute", gmute))
        app.add_handler(CommandHandler("ungmute", ungmute))
        app.add_handler(CommandHandler("addsudouser", addsudouser))
        app.add_handler(CommandHandler("rmsudouser", rmsudouser))
        app.add_handler(CommandHandler("sudousers", sudousers))
        app.add_handler(CommandHandler("stats", stats))
        app.add_handler(CommandHandler("uptime", uptime))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE, edited_message))
        app.add_handler(MessageHandler(filters.ALL & ~filters.UpdateType.EDITED_MESSAGE, enforce_global_mute))
        app.add_error_handler(lambda update, context: logging.error(f"Update {update} caused error {context.error}"))
        logging.info("Bot is starting...")

        print("Bot started.")
        app.run_polling()
    except Exception as e:
        logging.critical(f"Bot failed to start: {e}")
