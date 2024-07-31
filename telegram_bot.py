import os

import pandas as pd
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

from utils import rate_candidates
from scrapers.robota_ua_scraper import RobotaUaScraper
from scrapers.work_ua_scraper import WorkUaScraper
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

(
    JOB_SITE,
    POSITION,
    EXPERIENCE,
    LOCATION,
    SALARY,
    TECHNOLOGIES,
    RESULTS,
    BACK,
    START_OVER,
) = range(9)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [KeyboardButton("Work.ua")],
        [KeyboardButton("Robota.ua")],
        [KeyboardButton("Both")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(
        "Please choose the job site:", reply_markup=reply_markup
    )
    return JOB_SITE


async def job_site(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_text = update.message.text
    if user_text.lower() in ["work.ua", "robota.ua", "both"]:
        context.user_data["job_site"] = user_text.lower().replace(".", "_")
    else:
        await update.message.reply_text(
            "Invalid site. Please choose one of the options:"
        )
        return JOB_SITE

    await update.message.reply_text(
        "You selected: {}. Now, please enter the job position:".format(user_text)
    )
    keyboard = [[KeyboardButton("Skip")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(
        "Please enter the job position:", reply_markup=reply_markup
    )
    return POSITION


async def position(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_text = update.message.text
    if user_text.lower() != "skip":
        context.user_data["position"] = user_text
    else:
        context.user_data["position"] = None

    keyboard = [[KeyboardButton("Skip")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(
        "Position recorded. Please enter the required experience:",
        reply_markup=reply_markup,
    )
    return EXPERIENCE


async def experience(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_text = update.message.text
    if user_text.lower() != "skip":
        try:
            context.user_data["experience"] = int(user_text)
        except ValueError:
            await update.message.reply_text(
                "Invalid input. Please enter a number or 'skip':"
            )
            return EXPERIENCE
    else:
        context.user_data["experience"] = None

    keyboard = [[KeyboardButton("Skip")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(
        "Please enter the location:", reply_markup=reply_markup
    )
    return LOCATION


async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_text = update.message.text
    if user_text.lower() != "skip":
        context.user_data["location"] = user_text
    else:
        context.user_data["location"] = None

    keyboard = [[KeyboardButton("Skip")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(
        "Please enter the salary expectations:", reply_markup=reply_markup
    )
    return SALARY


async def salary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_text = update.message.text
    if user_text.lower() != "skip":
        try:
            salary_expectation = list(map(int, user_text.split("-")))
            context.user_data["salary"] = salary_expectation
        except ValueError:
            await update.message.reply_text(
                "Invalid input. Please enter a valid salary range or 'skip':"
            )
            return SALARY
    else:
        context.user_data["salary"] = None

    keyboard = [[KeyboardButton("Enter Technologies")], [KeyboardButton("Start Over")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(
        "Please enter the technologies (comma-separated) or choose 'Start Over':",
        reply_markup=reply_markup,
    )
    return TECHNOLOGIES


async def technologies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_text = update.message.text
    if user_text.lower() == "start over":
        return await start(update, context)

    if user_text.lower() != "enter technologies":
        context.user_data["technologies"] = [
            tech.strip() for tech in user_text.split(",")
        ]
    else:
        await update.message.reply_text(
            "Please enter the technologies (comma-separated):"
        )
        return TECHNOLOGIES

    await update.message.reply_text(
        "Searching for candidates based on your criteria..."
    )
    links = await fetch_results(context.user_data)
    result_text = "\n".join(links)
    await update.message.reply_text(f"Here are the top 5 resumes:\n{result_text}")
    return ConversationHandler.END


async def fetch_results(user_data) -> list:
    job_position = user_data.get("position")
    experience = user_data.get("experience")
    location = user_data.get("location")
    salary_expectation = user_data.get("salary")
    technologies = user_data.get("technologies", [])

    scrapers = []
    if user_data["job_site"] in ["work_ua", "both"]:
        scrapers.append(
            WorkUaScraper(
                job_position,
                years_of_experience=experience,
                location=location,
                salary_expectation=salary_expectation,
            )
        )
    if user_data["job_site"] in ["robota_ua", "both"]:
        scrapers.append(
            RobotaUaScraper(
                job_position,
                years_of_experience=experience,
                location=location,
                salary_expectation=salary_expectation,
            )
        )

    for scraper in scrapers:
        scraper.scrape()
        scraper.close()

    rate_candidates("job_positions.csv", technologies, "sorted_resumes.csv")

    df = pd.read_csv("sorted_resumes.csv")
    links = df["resume"].head(5).tolist()

    return links


def main():
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            JOB_SITE: [MessageHandler(filters.TEXT & ~filters.COMMAND, job_site)],
            POSITION: [MessageHandler(filters.TEXT & ~filters.COMMAND, position)],
            EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, experience)],
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, location)],
            SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, salary)],
            TECHNOLOGIES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, technologies)
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
