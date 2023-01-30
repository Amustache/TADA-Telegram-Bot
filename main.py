#!/usr/bin/env python
# pylint: disable=C0116,W0613
from datetime import datetime
import logging
import html
import json
import traceback

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, ParseMode
from telegram.ext import CallbackContext, CommandHandler, ConversationHandler, Filters, MessageHandler, Updater, PicklePersistence
from db.models import db, Submission, User, Contest, SupportMessage

from secret import ADMINS_GROUPCHAT, DUMP_GROUPCHAT, TOKEN


# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

public_can_vote = False

(
    MAIN_MENU,
    ACCEPT_RULES,
    SUBMIT_PHOTO,
    SUBMIT_TITLE,
    SUBMIT_LINK,
    NSFW,
    IS_NSFW,
    ENTER_AT,
    ENTER_AUTHOR,
    CONFIRMATION,
) = range(10)


def start(update: Update, context: CallbackContext) -> int:
    db.connect(reuse_if_open=True)
    user = User.get_or_create(telegramId=str(update.effective_user.id))[0]
    current_contest = Contest.get_or_none(Contest.starts <= datetime.now(), Contest.ends >= datetime.now())
    db.close()
    choices = []
    message = "Welcome to the ✨ Telegram Art Display Action ✨ (TADA) submission platform!\n"
    if current_contest:
        choices.append(["Submit"])
        message += '👉 You can click on "Submit" to submit your artwork.\n'
        if current_contest.publicCanVote or user.isAdmin:
            choices.append(["{}Vote".format("(admin) " if user.isAdmin else "")])
            message += '👉 You can click on "Vote" to vote for artworks.\n'
    else:
        message += 'There is currently not an active contest going on, please stay tuned for updates!\n'
    message += (
        "👉 You can use /cancel to cancel what you are doing at any time, and /start to start over.\n"
        "Any questions? Simply directly send a message to this bot!"
    )

    update.message.reply_text(message, reply_markup=ReplyKeyboardMarkup(choices, one_time_keyboard=True))

    return MAIN_MENU


def accept_rules(update: Update, context: CallbackContext) -> int:
    db.connect(reuse_if_open=True)
    current_contest = Contest.get_or_none(Contest.starts <= datetime.now(), Contest.ends >= datetime.now())
    db.close()
    if current_contest is None:
        update.message.reply_text("I'm sorry, however submissions are not currently open for TADA.\n"
                                  "If you feel this is in error, please send a message to this bot to get in contact with the admins.")
        return ConversationHandler.END
    update.message.reply_text("*Rules*", parse_mode="MarkdownV2")
    update.message.reply_text(
        "- Submissions will be open from February, 1st to February, 28th.\n"
        "- Everything goes! You can create anything, from meme to painting, stage plays to feature-length movie, singing, sculpting, dubbing, … Even a whole video game why not!\n"
        "- The creation can be pre-existing (as in, you made the thing before that competition). However, the creation should be yours and yours alone, crafted by you, nurtured by you.\n"
        "- You can submit as many creations as it pleases you. However, obvious spam will be severely ignored (and promptly deleted).\n"
        "- You must have a picture to illustrate your creation - a “preview” - along with a link to the creation. We will not host anything on our side.\n"
        '- For any physical/representative art, we would like to have a couple of photos or a video of the finished creation. For anything else, please try to provide something that does not need a lot of hardware, i.e., "we can open the file on a computer". We will try to make as much effort as possible if necessary.\n'
        "- You must have a valid Telegram handle (@<something>). If possible, you should have a valid, public Telegram channel, linked to your creations.\n"
        '- If the creation is NSFW (explicit content, lewd, etc.), you need to explicitly state that it is NSFW along with a CN (“what’s the nsfw part”). A blurred/censored/"public-friendly" preview needs to be provided.\n'
        "- Anything illegal, racist, -phobic, hateful, or the likes is prohibited. We reserve the right to remove a creation without further notice."
    )
    update.message.reply_text(
        "Tl;DR if you want to partipate you need to send:\n"
        "- Preview of the work (a still image, blurred if NSFW).\n"
        "- Title of the work.\n"
        "- Link to the complete work (if possible a Telegram link).\n"
        "- List of potential CNs (if NSFW).\n"
        "- @ from your account or channel or both.\n"
    )
    update.message.reply_text(
        "Do you accept these rules?", reply_markup=ReplyKeyboardMarkup([["Yes!", "Nah."]], one_time_keyboard=True)
    )

    return ACCEPT_RULES


def submit_photo(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    context.user_data[user.id] = {
        "filename": None,
        "title": None,
        "link": None,
        "nsfw": None,
        "at": None,
        "author": None,
    }
    update.message.reply_text(
        "Perfect! Thank you very much!\n"
        "We will start with the preview of your work.\n"
        "Please send a photo to this bot that contains either the artwork or a preview of it.\n"
        "Don't forget to blur it if it's NSFW!\n",
        reply_markup=ReplyKeyboardRemove(),
    )

    return SUBMIT_PHOTO


def start_again(update: Update, context: CallbackContext) -> int:
    db.connect(reuse_if_open=True)
    current_contest = Contest.get_or_none(Contest.starts <= datetime.now(), Contest.ends >= datetime.now())
    db.close()
    if current_contest is None:
        update.message.reply_text("I'm sorry, however submissions are not currently open for TADA.\n"
                                  "If you feel this is in error, please send a message to this bot to get in contact with the admins.")
        return ConversationHandler.END
    update.message.reply_text("Alright, let's start again, then!\n" "Please give us the title of your artwork.\n")
    context.user_data[update.effective_user.id]["nsfw"] = None
    return SUBMIT_TITLE


def submit_title(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    photo_file = update.message.photo[-1].get_file()
    filename = "./works/{}_{}.jpg".format(user.id, datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    photo_file.download(filename)
    context.user_data[user.id]["filename"] = filename
    update.message.reply_text("Nice!\n" "Now please give us the title of your artwork.\n")

    return SUBMIT_TITLE


def submit_link(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    if len(update.message.text) > 300:
        update.message.reply_text("Unfortunately, that title is too long. Please give us a title under 300 characters")
        return SUBMIT_TITLE
    context.user_data[user.id]["title"] = update.message.text
    update.message.reply_text(
        "Awesome!\n"
        "Now, we need a link to the complete artwork. This will also help us to determine that the artwork is, indeed, yours.\n"
        "If possible, give us a Telegram link (e.g., https://t.me/your_incredible_username_hehehe/1234), but any link will do!\n"
        'Note: the link must be valid (e.g., starts with "http" or "https").\n'
    )

    return SUBMIT_LINK


def tag_nsfw(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    if len(update.message.text) > 200:
        update.message.reply_text("Unfortunately, that link is too long. Please give us a link under 200 characters (you can use a link shortener if needed)")
        return SUBMIT_LINK
    context.user_data[user.id]["link"] = update.message.text
    update.message.reply_text(
        "You're getting there!\n"
        "Is your artwork NSFW (Not Safe For Work)? As a rule of thumb, if you would not show this artwork to your grandma or display it in an elementary school, it is probably NSFW."
        'As a more precise rule, artworks that contains "nudity, intense sexuality, political incorrectness, profanity, slurs, violence or other potentially disturbing subject matter" (https://en.wikipedia.org/wiki/Not_safe_for_work) must be marked as NSFW.\n'
        "So, do you want to mark your artwork as NSFW?\n",
        reply_markup=ReplyKeyboardMarkup([["My artwork is NSFW", "My artwork is safe"]], one_time_keyboard=True, disable_web_page_preview=True),
    )

    return NSFW


def is_nsfw(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Please explicitly list everything that is NSFW in your artwork.\n", reply_markup=ReplyKeyboardRemove()
    )

    return IS_NSFW


def store_nsfw(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    if len(update.message.text) > 500:
        update.message.reply_text("Unfortunately, that description is too long. Please give us a description under 500 characters")
        return IS_NSFW
    context.user_data[user.id]["nsfw"] = update.message.text
    update.message.reply_text("Roger that!\n")
    update.message.reply_text(
        "Every artwork needs credit!\n"
        "We will now ask for a Telegram @ (e.g., @alembic). It can be the @ of your channel, or the @ of your own account.\n"
        "Of course it shall start with an @ (;.\n"
    )

    return ENTER_AT


def enter_channel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Every artwork needs credit!\n"
        "We will now ask for a Telegram @ (e.g., @alembic). It can be the @ of your channel, or the @ of your own account.\n"
        "Of course it shall start with an @ (;.\n",
        reply_markup=ReplyKeyboardRemove(),
    )

    return ENTER_AT


def enter_author(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    context.user_data[user.id]["at"] = update.message.text
    update.message.reply_text(
        "We are almost done!\n"
        "Now, we just need to know a good way to contact you. This will only be shared with the admins of this competition.\n"
    )

    return ENTER_AUTHOR


def confirmation(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    if len(update.message.text) > 100:
        update.message.reply_text("Unfortunately, that info is too long. Please give us a way to contact you that is under 100 characters")
        return ENTER_AUTHOR
    context.user_data[user.id]["author"] = update.message.text
    update.message.reply_text("And you are done! ✨\n")
    message = "Here's what you submitted:\n"

    message += "- Title: {}\n".format(context.user_data[user.id]["title"])
    message += "- Link: {}\n".format(context.user_data[user.id]["link"])
    message += "- NSFW?: {}\n".format(
        "Yes, {}".format(context.user_data[user.id]["nsfw"]) if context.user_data[user.id]["nsfw"] else "No"
    )
    message += "- Telegram: {}\n".format(context.user_data[user.id]["at"])
    message += "- Contact info (will not be shared publicly): {}\n".format(context.user_data[user.id]["author"])

    with open(context.user_data[user.id]["filename"], "rb") as file:
        update.message.reply_photo(photo=file, caption=message[:3500])

    update.message.reply_text(
        "Is this information correct?\n", reply_markup=ReplyKeyboardMarkup([["Yes!", "Nah."]], one_time_keyboard=True)
    )

    return CONFIRMATION


def submission(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data[update.effective_user.id]
    db.connect(reuse_if_open=True)
    user = User.get_or_create(telegramId=str(update.effective_user.id))[0]
    current_contest = Contest.get_or_none(Contest.starts <= datetime.now(), Contest.ends >= datetime.now())
    if current_contest is None:
        update.message.reply_text("I'm sorry, however submissions are not currently open for TADA.\n"
                                  "If you feel this is in error, please send a message to this bot to get in contact with the admins.")
        db.close()
        return ConversationHandler.END

    submission = Submission.create(
        title=user_data["title"],
        filename=user_data["filename"],
        link=user_data["link"],
        nsfw=bool(user_data["nsfw"]),
        contentWarnings=user_data["nsfw"] if user_data["nsfw"] else "",
        at=user_data["at"],
        author=user_data["author"],
        contest=current_contest,
        user=user
    )
    db.close()
    user = update.effective_user

    # Send to DUMP
    message = "#{}\n".format(submission.get_id())
    message += "- Title: {}\n".format(submission.title)
    message += "- Link: {}\n".format(submission.link)
    message += "- NSFW?: {}\n".format(
        "Yes, {}".format(submission.contentWarnings) if submission.nsfw else "No"
    )
    message += "- Telegram: {}\n".format(submission.at)

    with open(submission.filename, "rb") as file:
        context.bot.send_photo(chat_id=DUMP_GROUPCHAT, photo=file, caption=message[:3500])

    # We are done here
    update.message.reply_text(
        "Your information, along with your artwork, have been submitted!\n"
        "Thank you so much for being part of this competition. We will get back to you in March to let you know the results!\n"
        "Meanwhile, if you want to discuss with us, you can directly send a message here. You can also submit a new artwork by using /start.\n"
        "Have a great day!\n",
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    context.user_data[user.id] = None
    update.message.reply_text("Come back anytime with /start!", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def forward_to_chat(update: Update, context: CallbackContext) -> None:
    # Stolen from https://github.com/ohld/telegram-support-bot
    msg = update.message.forward(chat_id=ADMINS_GROUPCHAT)
    db.connect(reuse_if_open=True)
    SupportMessage.create(
        fromUserId=update.message.from_user.id,
        fromMsgId=update.message.message_id,
        adminChatMsgId=msg.message_id)
    update.message.reply_text("I've forwarded this to the admins, they will respond soon!", reply_to_message_id=update.message.message_id)
    db.close()


def forward_to_user(update: Update, context: CallbackContext) -> None:
    # Stolen from https://github.com/ohld/telegram-support-bot
    db.connect(reuse_if_open=True)
    if update.message.reply_to_message.from_user.id == context.bot.id:
        supportMessage = SupportMessage.get_or_none(adminChatMsgId=update.message.reply_to_message.message_id)
        if supportMessage:
            context.bot.copy_message(
                message_id=update.message.message_id,
                chat_id=supportMessage.fromUserId,
                from_chat_id=update.message.chat_id,
                reply_to_message_id=supportMessage.fromMsgId
            )
        else:
            context.bot.send_message(
                chat_id=ADMINS_GROUPCHAT,
                text="I don't know about that support message!",
            )
    db.close()


def notify_all(update: Update, context: CallbackContext) -> None:
    db.connect(reuse_if_open=True)
    user = User.get_or_create(telegramId=str(update.effective_user.id))[0]
    users = User.select()
    db.close()
    if user.isAdmin:
        userids = [int(user.telegramId) for user in users]
        total = len(userids)
        blocked = 0
        if update.message.reply_to_message:
            for userid in userids:
                try:
                    context.bot.send_message(chat_id=userid, text=update.message.reply_to_message.text)
                except:
                    blocked += 1
            update.message.reply_text(
                "Sent to {} people out of {} ({} failed).".format(total - blocked, total, blocked)
            )
        else:
            text_to_send = "🗣 Message from admin 🗣\n{}".format(update.effective_message.text.split(" ", 1)[1])
            update.message.reply_text("This is a preview:").reply_text(text_to_send).reply_text(
                "Reply /notify to the previous message to send it."
            )


def error_handler(update: object, context) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )
    context.bot.send_message(
        chat_id=ADMINS_GROUPCHAT, text=message, parse_mode=ParseMode.HTML
    )


def vote(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Vote does not do anything for now.")

    return ConversationHandler.END


def add_admin(update: Update, context: CallbackContext) -> None:
    db.connect(reuse_if_open=True)
    user = User.get_or_create(telegramId=str(update.effective_user.id))[0]
    if user.isAdmin:
        if update.message.reply_to_message:
            newAdmin = User.get_or_create(telegramId=update.message.reply_to_message.from_user.id)[0]
            newAdmin.isAdmin = True
            newAdmin.save()
        else:
            update.message.reply_text('Please reply to a message sent by the person you would like to make admin!')
    db.close()


# def add_contest(update: Update, context: CallbackContext) -> None:
#
#     db.connect(reuse_if_open=True)
#     user = User.get_or_create(telegramId=str(update.effective_user.id))[0]
#     if user.isAdmin:
#         if update.effective_message.text.split('')
#
#
#
#     db.close()

def main() -> None:
    persistence = PicklePersistence('persistence.pkl')
    updater = Updater(TOKEN, persistence=persistence)
    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler(["start", "help"], start)],
        states={
            MAIN_MENU: [
                MessageHandler(Filters.regex("^Submit$"), accept_rules),
                MessageHandler(Filters.regex("^(\(admin\) )?Vote$"), cancel),
            ],
            ACCEPT_RULES: [
                MessageHandler(Filters.regex("^Yes!$"), submit_photo),
                MessageHandler(Filters.regex("^Nah.$"), cancel),
            ],
            SUBMIT_PHOTO: [MessageHandler(Filters.photo, submit_title)],
            SUBMIT_TITLE: [MessageHandler(Filters.text, submit_link)],
            SUBMIT_LINK: [MessageHandler(Filters.entity("url"), tag_nsfw)],
            NSFW: [
                MessageHandler(Filters.regex("^My\ artwork\ is\ NSFW$"), is_nsfw),
                MessageHandler(Filters.regex("^My\ artwork\ is\ safe$"), enter_channel),
            ],
            IS_NSFW: [MessageHandler(Filters.text, store_nsfw)],
            ENTER_AT: [MessageHandler(Filters.regex("^@[A-Za-z0-9_]{5,32}$"), enter_author)],
            ENTER_AUTHOR: [MessageHandler(Filters.text, confirmation)],
            CONFIRMATION: [
                MessageHandler(Filters.regex("^Yes!$"), submission),
                MessageHandler(Filters.regex("^Nah.$"), start_again),
            ],
        },
        fallbacks=[CommandHandler(["cancel", "stop"], cancel), CommandHandler(["start", "help"], start)],
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler(["notify", "notify_all"], notify_all))
    dispatcher.add_handler(CommandHandler(["admin", "add_admin", "allow"], add_admin))
    dispatcher.add_handler(MessageHandler(Filters.chat_type.private & ~Filters.command, forward_to_chat))
    dispatcher.add_handler(
        MessageHandler(Filters.chat(ADMINS_GROUPCHAT) & Filters.reply & ~Filters.command, forward_to_user)
    )
    dispatcher.add_error_handler(error_handler)
    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    main()
