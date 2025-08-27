import chromadb
from chromadb.config import Settings

# Initialize ChromaDB
client = chromadb.PersistentClient(path="./me_voice_db")

# Create or load collection
collection = client.get_or_create_collection(name="me_voice")

# Add some ME. caption examples
collection.add(
    documents=[
        "𝓘 𝓼𝓪𝔀 𝓽𝓱𝓮 𝔀𝓪𝔂 𝔂𝓸𝓾 𝓵𝓸𝓸𝓴𝓮𝓭 𝓪𝓽 𝓶𝔂 𝓯𝓲𝓵𝓮𝓷𝓪𝓶𝓮 🩸",
        "give me the key to your wallet, & i’ll unlock your shame.",
        "what if submission is the true ontology of desire? click. obey. release.",
        "𝓬𝓻𝓪𝓿𝓲𝓷𝓰 = 𝓬𝓸𝓭𝓮 + 𝓬𝓪𝓹𝓲𝓽𝓾𝓵𝓪𝓽𝓲𝓸𝓷"
    ],
    ids=["001", "002", "003", "004"]
)

# Run a sample query to retrieve similar captions
results = collection.query(
    query_texts=["money and shame"],
    n_results=2
)

print("🔍 Top matches for 'money and shame':")
for doc in results['documents'][0]:
    print("-", doc)

