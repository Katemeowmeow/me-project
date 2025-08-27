import pandas as pd
import chromadb

# Load your styled captions
df = pd.read_excel("ME. Coded Text - Captions.xlsx")

# Extract each column of text with style tags
long_form = df.iloc[2:, 0].dropna().tolist()
short_form = df.iloc[2:, 1].dropna().tolist()
code_phrases = df.iloc[2:, 2].dropna().tolist()
instagram = df.iloc[2:, 4].dropna().tolist()

# Combine into a caption data list
caption_data = []

for i, text in enumerate(long_form):
    caption_data.append({"id": f"long_{i}", "text": text, "style": "long_form_philosophical"})

for i, text in enumerate(short_form):
    caption_data.append({"id": f"short_{i}", "text": text, "style": "short_form_demands"})

for i, text in enumerate(code_phrases):
    caption_data.append({"id": f"code_{i}", "text": text, "style": "code_phrases"})

for i, text in enumerate(instagram):
    caption_data.append({"id": f"insta_{i}", "text": text, "style": "instagram_captions"})

# Connect to Chroma
client = chromadb.PersistentClient(path="./me_voice_db")
collection = client.get_or_create_collection(name="me_voice")

# Write to Chroma
for item in caption_data:
    collection.add(
        documents=[item["text"]],
        metadatas=[{"style": item["style"]}],
        ids=[item["id"]]
    )

print(f"✅ Added {len(caption_data)} ME. captions to memory.")

