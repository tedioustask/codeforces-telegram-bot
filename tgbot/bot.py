#!/usr/bin/python3
# pylint: disable=unused-argument, wrong-import-position

import logging
import psycopg2
import psycopg2.extras
import json
import os

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

user_contests = {}

TOKEN = os.environ['BOT_TOKEN']
DB_HOST = os.environ['DB_HOST']
DB = os.environ['POSTGRES_DB']
USER = os.environ['POSTGRES_USER']
PWD = os.environ['POSTGRES_PASSWORD']

con = psycopg2.connect(database=DB, user=USER, password=PWD, host=DB_HOST)
cur = con.cursor()
cur.execute("SELECT distinct tag from Contests")
tags = cur.fetchall()
con.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    keyboard = [[InlineKeyboardButton("Select problem set", callback_data='start_select')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text='''
    Welcome to Codeforces Problemsets telegram bot! \n 
    You can search problems by sending problem name to bot or select problemsets by tag and rating with button below
    '''
    await update.message.reply_text(text=text, reply_markup=reply_markup)

async def select_tag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    keyboard = [[InlineKeyboardButton(f"{tag[0]}", callback_data=str(tag[0]))] for i, tag in enumerate(tags)]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("CHOOSE TAG", reply_markup=reply_markup)

async def start_over(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompt same text & keyboard as `start` does but not as new message"""
    # Get CallbackQuery from Update
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery

    # Instead of sending a new message, edit the message that
    # originated the CallbackQuery. This gives the feeling of an
    # interactive menu.
    keyboard = [[InlineKeyboardButton("Select problem set", callback_data='start_select')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text='''
    Welcome to Codeforces Problemsets telegram bot! \n 
    You can search problems by sending problem name to bot or select problemsets by tag and rating with button below
    '''
    await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
    #await update.callback_query.message.delete()

async def select_rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    print(query.data)
    selected_tag = query.data

    sql_query = '''
        select distinct rating
        from contests
        where tag = %s
		order by rating
    '''
    cur.execute(sql_query, (selected_tag,))
    ratings = cur.fetchall()
    con.commit()

    keyboard = [[InlineKeyboardButton(f"{rating[0]}", callback_data=f'{{"rating": {rating[0]}, "tag": "{selected_tag}"}}')] for i, rating in enumerate(ratings)]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="CHOOSE RATING", reply_markup=reply_markup
    )

async def select_contest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    def get_contests(tag, rating):
        sql_query = '''
        select JSON_AGG(ROW_TO_JSON(p))
        from Problems p
        INNER JOIN (
            select ProblemId, ContestId from contestinfo
            where ContestId in (
                select id from contests
                where tag = %s and rating = %s
            ) 
        ) AS t ON p.Id = t.ProblemId
        GROUP BY ContestId
          '''
        cur.execute(sql_query, (tag, rating))
        contests = cur.fetchall()
        contests = list(contests)
        con.commit()
        return contests
    current_category = query.data
    current_tag = json.loads(query.data)["tag"] 
    current_rating = json.loads(query.data)["rating"] 

    user_id = update.effective_chat.id

    if not user_contests.get(user_id):
        user_contests[user_id] = {} 

    if not user_contests[user_id].get(current_category):
        user_contests[user_id][current_category] = []

    if user_contests[user_id][current_category]:
        current_contests = user_contests[user_id][current_category]
    else:
        current_contests = get_contests(current_tag, current_rating)

    poped_contest = current_contests.pop()

    keyboard = [
        [InlineKeyboardButton(f"{contest['name']}", callback_data=f"{contest['name']}")] for contest in poped_contest[0]
    ] + [[InlineKeyboardButton("TO MENU", callback_data="start_over"),  
        InlineKeyboardButton("NEXT SET", callback_data=query.data)]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=f"Contest problems list ({len(current_contests)} remainig)", reply_markup=reply_markup
    )

    user_contests[user_id][current_category] = current_contests

async def show_contest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message:
        problem_name = update.message.text
    else:
        if update.callback_query:
            problem_name = update.callback_query.data
    sql_query = '''
    select *
    from Problems p
    where p.name = %s
    '''
    dcur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
    dcur.execute(sql_query, (problem_name,))
    problem_dict = dcur.fetchone()
    con.commit()

    if problem_dict:
        problem_message=f'''
        *{escape_markdown(problem_dict['name'], version=2)}*
        __Solved times:__ {problem_dict["solvedcount"]}
        __Rating:__ {problem_dict["rating"]}
        __Contest Id:__ {problem_dict["siteid"]}
        __Index:__ {problem_dict["siteindex"]}
        __Tags:__ _{escape_markdown(', '.join(problem_dict["tags"]), version=2)}_
        [Link](https://codeforces.com/problemset/problem/{problem_dict["siteid"]}/{problem_dict["siteindex"]})
        '''
    else:
        problem_message = "There is no such problem"
    
    if update.message:
        await update.message.reply_text(
            text=problem_message, parse_mode=ParseMode.MARKDOWN_V2
        )
    else:
        if update.callback_query:
            await update.callback_query.message.reply_text(
                text=problem_message, parse_mode=ParseMode.MARKDOWN_V2
            )

def main() -> None:

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(select_rating, pattern="^("+ '|'.join([tag[0].replace('*','\*') for tag in tags ]) +")$"))
    application.add_handler(CallbackQueryHandler(select_contest, pattern="^\{.*\}$"))
    application.add_handler(CallbackQueryHandler(select_tag, pattern="^start_select$"))
    application.add_handler(CallbackQueryHandler(start_over, pattern="^start_over$"))
    application.add_handler(CallbackQueryHandler(show_contest, pattern=".*"))
    application.add_handler(MessageHandler(filters.Regex(".*"), show_contest))

    application.run_polling()
    con.close()

if __name__ == "__main__":
    main()
