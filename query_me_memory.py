import chromadb

client = chromadb.PersistentClient(path="./me_voice_db")
collection = client.get_or_create_collection(name="me_voice")

search_prompt = "glitch + worship"
target_style = "short_form_demands"
n_results = 3

results = collection.query(
    query_texts=[search_prompt],
    n_results=n_results,
    where={"style": target_style}
)

print(f"\n🔍 Top {n_results} results in style: {target_style}\n")
for doc in results["documents"][0]:
    print("—", doc)

