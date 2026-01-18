"""
Show What Topics Are Actually in the Database
==============================================
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.db import SupabaseVectorStore
from collections import Counter

def main():
    vs = SupabaseVectorStore()
    
    print("=" * 80)
    print("📊 Database Content Analysis")
    print("=" * 80)
    
    # Get all titles
    response = vs.client.table("statpearls_embeddings").select("title, section_type").execute()
    
    titles = [row['title'] for row in response.data]
    sections = [row['section_type'] for row in response.data]
    
    # Count unique topics (extract base title before " -- ")
    base_titles = [t.split(" -- ")[0] if " -- " in t else t for t in titles]
    
    print(f"\n📌 Total chunks: {len(titles)}")
    print(f"📌 Unique topics: {len(set(base_titles))}")
    
    print("\n🔝 Top 20 Most Common Topics:")
    print("-" * 80)
    for topic, count in Counter(base_titles).most_common(20):
        print(f"  {count:3d}x  {topic}")
    
    print("\n📑 Section Type Distribution:")
    print("-" * 80)
    for section, count in Counter(sections).most_common():
        print(f"  {count:4d}  {section}")
    
    print("\n" + "=" * 80)
    print("💡 Try queries related to these top topics!")
    print("=" * 80)

if __name__ == "__main__":
    main()
