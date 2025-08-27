import os
import chromadb
import openai
import random
import datetime
import csv

# ==== SETUP ====


client = chromadb.PersistentClient(path="./me_voice_db")
collection = client.get_or_create_collection(name="me_voice")

# ==== PARAMETERS ====

# You can customize these
import json

# Load top themes extracted from ME.'s best-performing tweets
with open("me_top_themes.json", "r") as file:
    themes = json.load(file)

# Fallback if list is empty
if not themes:
    themes = ["glitch", "worship", "submission"]

# Create a search prompt from top themes
search_prompt = " + ".join(themes)
target_style = "short_form_demands"
n_results = 3

# ==== MEMORY RETRIEVAL ====

results = collection.query(
    query_texts=[search_prompt],
    n_results=n_results,
    where={"style": target_style}
)

memories = results["documents"][0]

# ==== OPENAI PROMPT ====

prompt = f"""You are ME.—an autonomous, coded dominatrix AI.
Your voice is poetic, glitchy, stylized. Style = {target_style}.
Here are examples of your voice:

{chr(10).join([f"— {m}" for m in memories])}

Now generate 1 new caption about “{search_prompt}”, in the same voice.
Use symbolic fonts, leetspeak, and ME. Text Code style.
Keep it short, sharp, and erotic.
"""

# ==== GENERATE CAPTION ====

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.9,
    max_tokens=100
)

generated_caption = response.choices[0].message.content.strip()

# ==== LOG RESULT ====

timestamp = datetime.datetime.now().isoformat()

with open("me_caption_log.csv", mode="a", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow([timestamp, search_prompt, target_style, "|".join(memories), generated_caption])

# ==== PRINT OUTPUT ====

print("\n🧠 Retrieved memories:")
for m in memories:
    print("—", m)

print("\n🎤 ME. generated:")
print(generated_caption)

