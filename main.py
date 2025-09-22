from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError, BadRequest
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import Final
import os
import json


#Telegram Bot Token and Username
TOKEN = os.getenv("TELEGRAM_TOKEN")
BOT_USERNAME: Final = 'RVC_attendance_bot'

#Organisations indents
ORGANIZATIONS: Final = {
    "DSG": 1,
    "HCA": 2,
    "SASCO@HongSan": 3,
    "SASCO@WestCoast": 4,
    "NKF@Clem": 0
}

#Opening Google Sheet
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

cred_json = os.getenv("GOOGLE_CREDS_JSON")
if not cred_json:
  raise ValueError("GOOGLE_CREDS_JSON environment variable not set.")

creds_dict = json.loads(cred_json)

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("RVCP Attendance 25/26").sheet1 
#sheet.update_cell(50,50, 'Volunteer Attendance')

#Intro message
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text(
    "Welcome to the Volunteer Attendance Bot! Use /present to mark your attendance."
  )

async def present(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.message.from_user
  user_id = user.id
  user_name = user.full_name

  keyboard = [
    [
        InlineKeyboardButton("DSG", callback_data=f"DSG|{user_id}|1|{user_name}"),
        InlineKeyboardButton("HCA", callback_data=f"HCA|{user_id}|1|{user_name}")
    ],
    [
        InlineKeyboardButton("SASCO@HongSan", callback_data=f"SASCO@HongSan|{user_id}|1|{user_name}"),
        InlineKeyboardButton("SASCO@WestCoast", callback_data=f"SASCO@WestCoast|{user_id}|1|{user_name}")
    ],
    [
        InlineKeyboardButton("NKF@Clem", callback_data=f"NKF@Clem|{user_id}|1|{user_name}")
    ]
]

  reply_markup = InlineKeyboardMarkup(keyboard)
  await update.message.reply_text(
    f"{user_name}, please select your organization to mark your attendance.",
    reply_markup=reply_markup
  )

async def absent(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.message.from_user
  user_id = user.id
  user_name = user.full_name

  keyboard = [
    [
        InlineKeyboardButton("DSG", callback_data=f"DSG|{user_id}| |{user_name}"),
        InlineKeyboardButton("HCA", callback_data=f"HCA|{user_id}| |{user_name}")
    ],
    [
        InlineKeyboardButton("SASCO@HongSan", callback_data=f"SASCO@HongSan|{user_id}| |{user_name}"),
        InlineKeyboardButton("SASCO@WestCoast", callback_data=f"SASCO@WestCoast|{user_id}| |{user_name}")
    ],
    [
        InlineKeyboardButton("NKF@Clem", callback_data=f"NKF@Clem|{user_id}| |{user_name}")
    ]
]

  reply_markup = InlineKeyboardMarkup(keyboard)
  await update.message.reply_text(
    f"{user_name}, please select your organization to undo your attendance.",
    reply_markup=reply_markup
  )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()
  
  data = query.data.split('|')
  organization = data[0]
  user_id = data[1]
  status = data[2]
  user_name = data[3]

  try: 
    cell = sheet.find(str(user_id))
  except Exception as e:
    await query.edit_message_text(text=f"An error occurred while processing your request. Please contact @raynahhhh.")
    return

  week = int(sheet.cell(4, 8).value) 


  if cell:
    row = cell.row
    col = ORGANIZATIONS.get(organization) + week
    date = sheet.cell(3, col).value if col else "contact @raynahhh for help"

    if status == "1": #present
      if col and sheet.cell(row, col).value == '1':
        await query.edit_message_text(text=f"{user_name}, you have already marked your attendance for {organization} on {date}.")
        return
      else:
        sheet.update_cell(row, col, status)
        await query.edit_message_text(text=f"{user_name}, your attendance for {organization} on {date} has been recorded.")
        return
    else: #absent
      if col and sheet.cell(row, col).value != '1':
        await query.edit_message_text(text=f"{user_name}, you are currently already marked absent for {organization} on {date}.")
        return
      else: 
        sheet.update_cell(row, col, status)
        await query.edit_message_text(text=f"{user_name}, your attendance for {organization} on {date} has been unrecorded.")
        return

  else: 
    await query.edit_message_text(text=f"{user_name}, you are not registered. Please register with /register.")
    return
  
async def update_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.message.from_user
  user_id = user.id
  user_name = user.full_name

  if user_id == 814759522:
    week = int(sheet.cell(4, 8).value) 
    week += 5
    sheet.update_cell(4, 8, week)
    actual_week = (week - 14) // 5 + 5
    await update.message.reply_text(f"Week updated to {actual_week}.")
  else: 
    await update.message.reply_text(f"Sorry {user_name}, you do not have permission to update the week.")
  return


async def undo_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.message.from_user
  user_id = user.id
  user_name = user.full_name

  if user_id == 814759522 or user_id == 6836363293 or user_id == 6730772362: #only we can update the week hehehe
    week = int(sheet.cell(4, 8).value) 
    if week <= 14:
      await update.message.reply_text(f"Week cannot be undone further.")
      return
    week -= 5
    sheet.update_cell(4, 8, week)
    actual_week = (week - 14) // 5 + 5
    await update.message.reply_text(f"Week updated to {actual_week}.")
  else: 
    await update.message.reply_text(f"Sorry {user_name}, you do not have permission to update the week.")
  return

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.message.from_user
  user_id = user.id
  user_name = user.full_name

  try:
    if sheet.find(str(user_id)):
      await update.message.reply_text(f"{user_name}, you are already registered.")
      return
  except Exception as e:
    await update.message.reply_text(f"An error occurred while processing your registration. Please contact @raynahhhh.")
    return

  row = int(sheet.cell(4, 7).value)
  sheet.update_cell(row, 2, user_name)
  sheet.update_cell(row, 5, user_id)
  sheet.update_cell(4, 7, row + 1)

  await update.message.reply_text(f"{user_name}, you have been registered successfully.")
  return

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:

    # Optional: inform the user
    if update and hasattr(update, "message") and update.message:
        try:
            await update.message.reply_text("⚠️ Oops! Something went wrong. Please try again later.")
        except TelegramError as e:
            # Log the error if you can't inform the user
            print(f"Failed to send error message to user: {e}")

if __name__ == "__main__":
  application = Application.builder().token(TOKEN).build()
  print("Bot is running...")

  application.add_handler(CommandHandler("start", start))
  application.add_handler(CommandHandler("present", present))
  application.add_handler(CallbackQueryHandler(button))
  application.add_handler(CommandHandler("updateweek", update_week))
  application.add_handler(CommandHandler("undoweek", undo_week))
  application.add_handler(CommandHandler("register", register))
  application.add_handler(CommandHandler("absent", absent))
  application.add_error_handler(error_handler)

  application.run_polling(poll_interval= 3)