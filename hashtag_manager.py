#!/usr/bin/env python3
"""Hashtag Collection Mode Manager"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from universal_hashtags import UniversalHashtagProvider

def show_available_modes():
    """Show all available hashtag collection modes"""
    provider = UniversalHashtagProvider()
    
    print("🌐 AVAILABLE HASHTAG COLLECTION MODES")
    print("=" * 50)
    
    print("\n1️⃣ UNIVERSAL MODE (High Volume)")
    print("   • Broad range of trending hashtags")
    print("   • High tweet volume guaranteed")
    high_volume = provider.get_high_volume_hashtags()
    print(f"   • Sample: {high_volume[:5]}")
    print(f"   • Total hashtags: {len(high_volume)}")
    
    print("\n2️⃣ BALANCED MODE (Diverse)")
    print("   • Balanced across sentiment types")
    print("   • Multiple domain coverage")
    balanced = provider.get_balanced_collection_set()
    all_balanced = []
    for hashtags in balanced.values():
        all_balanced.extend(hashtags)
    print(f"   • Sample: {all_balanced[:5]}")
    print(f"   • Total hashtags: {len(set(all_balanced))}")
    
    print("\n3️⃣ CATEGORY MODE (Organized)")
    print("   • Hashtags organized by categories")
    print("   • Technology, Business, Lifestyle, etc.")
    categories = provider.get_category_hashtags()
    print(f"   • Categories: {list(categories.keys())[:4]}...")
    total_category = sum(len(tags) for tags in categories.values())
    print(f"   • Total hashtags: {total_category}")
    
    print("\n4️⃣ CUSTOM MODE")
    print("   • Use your own hashtags")
    print("   • Set via TARGET_HASHTAGS in .env")
    print("   • Example: #AI,#MachineLearning,#DataScience")

def collect_with_mode(mode):
    """Start collection with specified mode"""
    os.environ['HASHTAG_MODE'] = mode
    
    from scripts.run_collector import TweetCollectionPipeline
    
    print(f"\n🚀 Starting collection with {mode.upper()} mode...")
    pipeline = TweetCollectionPipeline()
    
    print(f"📊 Collecting from {len(pipeline.target_hashtags)} hashtags:")
    for i, tag in enumerate(pipeline.target_hashtags[:10], 1):
        print(f"   {i:2d}. {tag}")
    if len(pipeline.target_hashtags) > 10:
        print(f"   ... and {len(pipeline.target_hashtags) - 10} more")
    
    # Run one collection cycle
    pipeline.run_one_time_collection()

def main():
    """Main hashtag mode manager"""
    if len(sys.argv) < 2:
        show_available_modes()
        print("\n💡 USAGE:")
        print("   python hashtag_manager.py [mode]")
        print("   python hashtag_manager.py universal")
        print("   python hashtag_manager.py balanced")
        print("   python hashtag_manager.py category")
        print("   python hashtag_manager.py custom")
        return
    
    mode = sys.argv[1].lower()
    
    if mode == 'show':
        show_available_modes()
    elif mode in ['universal', 'balanced', 'category', 'custom']:
        try:
            collect_with_mode(mode)
        except KeyboardInterrupt:
            print("\n🛑 Collection stopped by user")
        except Exception as e:
            print(f"\n❌ Collection failed: {e}")
    else:
        print(f"❌ Unknown mode: {mode}")
        print("Available modes: universal, balanced, category, custom")

if __name__ == "__main__":
    main()
