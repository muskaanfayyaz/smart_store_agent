import chainlit as cl
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load .env
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Gemini setup
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

DB_FILE = "products.json"

# Load product DB from file
def load_db():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r") as f:
        return json.load(f)

# Save DB to file
def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Search the DB for a match
def find_product(problem: str, db: list):
    for item in db:
        if problem.lower() in item["problem"].lower():
            return item
    return None

# ✅ Gemini suggestion function
def generate_suggestion(problem: str):
    prompt = f"""A customer says: "{problem}". Suggest one over-the-counter product or medicine and explain why it's helpful."""
    response = model.generate_content([prompt])
    return response.text

# ✅ Display welcome message on chat start
@cl.on_chat_start
async def start():
    await cl.Message(content="""
👋 **Welcome to Smart Store Agent!**

Just tell me how you're feeling or what you're dealing with — like:
- "I have a headache"
- "I'm feeling nauseous"
- "My child has a fever"

I'll suggest a suitable **over-the-counter product or medicine**, and explain why it works.

Let's begin!
""").send()

# ✅ Main response handler
@cl.on_message
async def main(message: cl.Message):
    user_problem = message.content
    db = load_db()

    existing = find_product(user_problem, db)
    if existing:
        await cl.Message(content=f"**Suggested Product:** {existing['product']}\n\n{existing['description']}").send()
        return

    ai_response = generate_suggestion(user_problem)

    # Parse product name and description
    product_name = ai_response.split("\n")[0].replace("Suggested Product:", "").strip(" *:")
    description = "\n".join(ai_response.split("\n")[1:]).strip()

    # Save new entry
    new_entry = {
        "problem": user_problem,
        "product": product_name,
        "description": description
    }
    db.append(new_entry)
    save_db(db)

    await cl.Message(content=f"**Suggested Product:** {product_name}\n\n{description}").send()
