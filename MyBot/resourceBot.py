from dotenv import load_dotenv
import os,json
import telebot.types
import requests

env_path = os.path.join(os.getcwd(), "token2.env")
load_dotenv(env_path)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
FASTAPI_BASE_URL = os.environ.get("FASTAPI_BASE_URL")
print(f"BOT_TOKEN: {BOT_TOKEN}")
bot = telebot.TeleBot(BOT_TOKEN)

def get_resources(course_id: str, resource_type: str) -> dict:
    url = FASTAPI_BASE_URL
    params = {"course_id": course_id, "resource_type": resource_type}
    response = requests.get(url, params)
    return response.json()

@bot.message_handler(commands=["start"])
def welcome_message(message):
    bot.reply_to(
        message,
        "Hello🎓\nWelcome to the 300lvl CS Resource Bot!\n"
        "📚 Easily access and store academic resources.\n"
        "👉 Use /courses for a list of courses.\n"
        "✨ Enter /add to add resources or /get to access them.\n"
        "ℹ️ Enter /help for a list of commands"
    )

@bot.message_handler(commands=["help"])
def help_message(message):
    bot.reply_to(
        message,
        "ℹ️ *Help Section* \n\n"
        "Here are the commands you can use:\n\n"
        "/start - Start the bot and get a welcome message.\n"
        "/courses - List all available courses.\n"
        "/add - Add academic resources to a course.\n"
        "/get - Retrieve academic resources for a course.\n"
        "💡 Use /add or /get followed by the course code to add or retrieve resources.\n\n"
    )

@bot.message_handler(commands=["courses"])
def list_courses(message):
    response = requests.get(f"{FASTAPI_BASE_URL}/get-courses")
    if response.status_code == 200:
        courses = response.json()
        course_list = "\n".join([course['course_code'] for course in courses])
        bot.reply_to(message, f"📜 List of Courses:\n{course_list}")
    else:
        bot.reply_to(message, "❌ Failed to fetch courses.")

@bot.message_handler(commands=["add"])
def add_handler(message):
    sent_msg = bot.send_message(
        message.chat.id, "🔧 *Add Resource* \n\nEnter the course code:", parse_mode="Markdown"
    )
    bot.register_next_step_handler(sent_msg, process_course_code, action="add")

@bot.message_handler(commands=["get"])
def get_handler(message):
    sent_msg = bot.send_message(
        message.chat.id, "🔍 *Get Resource* \n\nEnter the course code:", parse_mode="Markdown"
    )
    bot.register_next_step_handler(sent_msg, process_course_code, action="get")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    action, course_code, resource_type = call.data.split("_")

    if action == "get":
        response = requests.get(f"{FASTAPI_BASE_URL}/get-resources/{course_code}/{resource_type}")

        if response.status_code == 200:
            resources = response.json()
            if not resources:
                bot.send_message(call.message.chat.id, "❌ No resources found.")
            else:
                for resource in resources:
                    file_ids = resource.get('resource_data', "[]")
                    try:
                        file_ids = json.loads(file_ids) if isinstance(file_ids, str) else file_ids
                    except json.JSONDecodeError:
                        file_ids = [] 

                    file_ids = resource.get('resource_data', "[]")  # Default to empty JSON list

                    # Ensure it's a list
                    if isinstance(file_ids, str):  
                        try:
                            file_ids = json.loads(file_ids)  # First decoding
                        except json.JSONDecodeError:
                            file_ids = []

                    if isinstance(file_ids, list) and len(file_ids) == 1 and isinstance(file_ids[0], str):
                        try:
                            file_ids = json.loads(file_ids[0])  # Second decoding
                        except json.JSONDecodeError:
                            pass  # Keep original list if decoding fails

                    if not isinstance(file_ids, list):  # Final safety check
                        file_ids = []

                    # Debugging: Print file_ids to verify
                    print(f"DEBUG: Fixed file_ids = {file_ids}")

                    # Send documents if valid
                    for file_id in file_ids:
                        if isinstance(file_id, str) and file_id.startswith("BQAC"):
                            bot.send_document(call.message.chat.id, file_id)
                        else:
                            bot.send_message(call.message.chat.id, "❌ Invalid file ID stored in database.")
        else:
            bot.send_message(call.message.chat.id, "❌ Failed to fetch resources.")

    elif action == "add":
        bot.send_message(call.message.chat.id, f"➕ Add {resource_type} for {course_code}. Please upload the file or paste a link.")
        bot.register_next_step_handler(call.message, save_resource, course_code, resource_type)

def process_course_code(message, action):
    course_code = message.text.upper()
    response = requests.get(f"{FASTAPI_BASE_URL}/get-courses")
    
    if response.status_code == 200:
        courses = response.json()
        course_list = [course['course_code'] for course in courses]

        if course_code not in course_list:
            sent_msg = bot.send_message(message.chat.id, "❌ Course does not exist. Enter a valid course:")
            return bot.register_next_step_handler(sent_msg, process_course_code, action)
        
        markup = telebot.types.InlineKeyboardMarkup()
        for option in ["Notes", "PQimages", "PQfiles", "Textbooks", "Code", "Others"]:
            markup.add(telebot.types.InlineKeyboardButton(option, callback_data=f"{action}_{course_code}_{option.lower()}"))

        bot.send_message(message.chat.id, f"{action.capitalize()} resources for {course_code}. Choose a category:", reply_markup=markup)

@bot.message_handler(content_types=['document', 'text'])
def save_resource(message, course_code, resource_type):
    resource_data = []

    if message.content_type == "text":
        resource_data.append(message.text.strip())

    elif message.content_type == "document":
        resource_data.append(message.document.file_id)
        file_id = message.document.file_id
    if file_id:
        print("Extracted file_id:", file_id)
    else:
        print("No file_id found!")
    response = requests.post(
        f"{FASTAPI_BASE_URL}/add-resources/{course_code}/{resource_type}/upload",
        json={"course_code": course_code, "resource_type": resource_type, "resource_data": file_id}
    )
    print(response.json())

    bot.send_message(message.chat.id, "✅ Resource saved successfully" if response.status_code == 200 else f"❌ Failed: {response.text}")

bot.infinity_polling()