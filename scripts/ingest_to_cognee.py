import asyncio
import os
import sys
from pathlib import Path

# Add project root to path to import src
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.infrastructure.cognee import cognee_memory
from src.infrastructure.settings import settings

async def main():
    summary_dir = settings.summary_dir
    # Get only top-level txt files to avoid nested structures if any
    files = sorted(list(summary_dir.glob("*.txt")))
    
    if not files:
        print(f"No summary files found in {summary_dir}")
        return

    print(f"Found {len(files)} summary files. Starting ingestion...")

    # For large datasets, we should batch 'add' and then 'cognify' once
    for i, file_path in enumerate(files):
        print(f"[{i+1}/{len(files)}] Buffering {file_path.name}...")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
                # Extract simple metadata from filename
                # Example: 20251120_205733_summary.txt
                name_parts = file_path.stem.split("_")
                metadata = {"source_file": file_path.name}
                if len(name_parts) >= 1:
                    metadata["date_raw"] = name_parts[0]
                if len(name_parts) >= 2:
                    metadata["timestamp_raw"] = name_parts[1]

                await cognee_memory.add(content, metadata)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    print("Building knowledge graph (cognify)... This may take a while depending on LLM speed.")
    try:
        await cognee_memory.cognify()
        print("Cognification completed successfully.")
    except Exception as e:
        print(f"Error during cognify: {e}")
        return

    # Simple search test
    print("\n--- Verification Test ---")
    query = "VRChatで最近会った人や訪れた場所について教えて"
    print(f"Query: {query}")
    try:
        results = await cognee_memory.search(query)
        print("Search results:")
        for res in results:
            print(f"- {res}")
    except Exception as e:
        print(f"Search failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
