#!/usr/bin/env python
# pylint: disable=C0116,W0613
from datetime import datetime
import csv
import logging


from googleapiclient.discovery import build
from telegram import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, ConversationHandler, Filters, MessageHandler, Updater


# Enable logging
from helpers import add_new_item, get_and_update_next_id, get_spreadsheets_creds
from secret import ADMINS_GROUPCHAT, ADMINS_IDS, DUMP_GROUPCHAT, TOKEN, BOT_ID

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

userids_file = "./users"
submissions_file = "./submissions.csv".format()
fieldnames = [
    "filename",
    "title",
    "link",
    "nsfw",
    "at",
    "author",
]

# Connect to Google Sheets API
creds = get_spreadsheets_creds()
service = build("sheets", "v4", credentials=creds)


def start(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    with open(userids_file, "a") as f:
        f.write("{}\n".format(user.id))

    message = "Welcome to the ✨ Telegram Art Display Action ✨ (TADA) submission platform!\n"

    choices = [["Submit"]]
    message += '👉 You can click on "Submit" to submit your artwork.\n'

    if public_can_vote or user.id in ADMINS_IDS:
        choices.append(["{}Vote".format("(admin) " if user.id in ADMINS_IDS else "")])
        message += '👉 You can click on "Vote" to vote for artworks.\n'

    message += (
        "👉 You can use /cancel to cancel what you are doing at any time, and /start to start over.\n"
        "Any question? Simply directly send a message to that bot!"
    )

    update.message.reply_text(message, reply_markup=ReplyKeyboardMarkup(choices, one_time_keyboard=True))

    return MAIN_MENU


def accept_rules(update: Update, context: CallbackContext) -> int:
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
    update.message.reply_text("Alright, let's start again, then!\n" "Please give use the title of your artwork.\n")

    return SUBMIT_TITLE


def submit_title(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    photo_file = update.message.photo[-1].get_file()
    filename = "./works/{}_{}.jpg".format(user.id, datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    photo_file.download(filename)
    context.user_data[user.id]["filename"] = filename
    update.message.reply_text("Nice!\n" "Now please give use the title of your artwork.\n")

    return SUBMIT_TITLE


def submit_link(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
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
    context.user_data[user.id]["link"] = update.message.text
    update.message.reply_text(
        "You're getting there!\n"
        "Is your artwork NSFW (Not Safe For Work)? As a rule of thumb, if you would not show this artwork to your grandma or display it in an elementary school, it is probably NSFW."
        'As a more precise rule, artworks that contains "nudity, intense sexuality, political incorrectness, profanity, slurs, violence or other potentially disturbing subject matter" (https://en.wikipedia.org/wiki/Not_safe_for_work) must be marked as NSFW.\n'
        "So, do you want to mark your artwork as NSFW?\n",
        reply_markup=ReplyKeyboardMarkup([["My artwork is NSFW", "My artwork is safe"]], one_time_keyboard=True),
    )

    return NSFW


def is_nsfw(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Please explicitly list everything that is NSFW in your artwork.\n", reply_markup=ReplyKeyboardRemove()
    )

    return IS_NSFW


def store_nsfw(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
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
        "Now, we just need to know how we should reference you. You can either put a name, a nickname, or a Telegram @.\n"
    )

    return ENTER_AUTHOR


def confirmation(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    context.user_data[user.id]["author"] = update.message.text
    update.message.reply_text("And you are done! ✨\n")
    message = "Here's what you submitted:\n"

    message += "- Title: {}\n".format(context.user_data[user.id]["title"])
    message += "- Link: {}\n".format(context.user_data[user.id]["link"])
    message += "- NSFW?: {}\n".format(
        "Yes, {}".format(context.user_data[user.id]["nsfw"]) if context.user_data[user.id]["nsfw"] else "No"
    )
    message += "- Telegram: {}\n".format(context.user_data[user.id]["at"])
    message += "- Author: {}\n".format(context.user_data[user.id]["author"])
    update.message.reply_text(message)

    update.message.reply_text(
        "Are these information correct?\n", reply_markup=ReplyKeyboardMarkup([["Yes!", "Nah."]], one_time_keyboard=True)
    )

    return CONFIRMATION


def submission(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    pic_id = get_and_update_next_id(service)

    # Save locally
    with open(submissions_file, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow(context.user_data[user.id])

    # Save on Google sheet
    add_new_item(service, pic_id, user.id, context.user_data[user.id])

    # Send to DUMP
    message = "#{}\n".format(pic_id)
    message += "- User ID: {}\n".format(user.id)
    message += "- Title: {}\n".format(context.user_data[user.id]["title"])
    message += "- Link: {}\n".format(context.user_data[user.id]["link"])
    message += "- NSFW?: {}\n".format(
        "Yes, {}".format(context.user_data[user.id]["nsfw"]) if context.user_data[user.id]["nsfw"] else "No"
    )
    message += "- Telegram: {}\n".format(context.user_data[user.id]["at"])
    message += "- Author: {}\n".format(context.user_data[user.id]["author"])

    with open(context.user_data[user.id]["filename"], "rb") as file:
        context.bot.send_photo(chat_id=DUMP_GROUPCHAT, photo=file, caption=message)

    # We are done here
    update.message.reply_text(
        "These information, along with your artwork, have been submitted!\n"
        "Thank you so much for being part of that competition. We will get back to you in March to let you know about the results.\n"
        "Meanwhile, if you want to discuss with us, you can directly send a message here. You can submit a new artwork as well using /start.\n"
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
    update.message.forward(chat_id=ADMINS_GROUPCHAT)


def forward_to_user(update: Update, context: CallbackContext) -> None:
    # Stolen from https://github.com/ohld/telegram-support-bot
    if update.message.reply_to_message.from_user.id == BOT_ID:
        if update.message.reply_to_message.forward_from:
            user_id = update.message.reply_to_message.forward_from.id
        else:
            try:
                user_id = int(update.message.reply_to_message.text.split("\n")[0])
            except ValueError:
                user_id = None
        if user_id:
            context.bot.copy_message(
                message_id=update.message.message_id, chat_id=user_id, from_chat_id=update.message.chat_id
            )
        else:
            context.bot.send_message(
                chat_id=ADMINS_GROUPCHAT,
                text="User above don't allow forward his messages. You must reply to bot reply under user forwarded message.",
            )


def notify_all(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id in ADMINS_IDS:
        with open(userids_file, "r") as f:
            userids = [int(userid) for userid in set(f.readlines())]
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


def vote(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Vote does not do anything for now.")

    return ConversationHandler.END


def main() -> None:
    # Create files if not existing
    open(userids_file, "a").close()
    with open(submissions_file, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    updater = Updater(TOKEN)

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler(["start"], start)],
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
        fallbacks=[CommandHandler(["cancel"], cancel)],
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler(["notify", "notify_all"], notify_all))
    dispatcher.add_handler(MessageHandler(Filters.chat_type.private & ~Filters.command, forward_to_chat))
    dispatcher.add_handler(
        MessageHandler(Filters.chat(ADMINS_GROUPCHAT) & Filters.reply & ~Filters.command, forward_to_user)
    )

    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    main()
