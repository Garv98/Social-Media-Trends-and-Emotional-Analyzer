#!/usr/bin/env python3
"""Universal Hashtag Collection Strategy"""

class UniversalHashtagProvider:
    """Provides diverse hashtags across multiple categories for comprehensive data collection"""
    
    @staticmethod
    def get_trending_hashtags():
        """Popular trending hashtags that typically have high volume"""
        return [
            # General trending
            '#trending', '#viral', '#popular', '#news', '#breaking',
            # Social & lifestyle  
            '#life', '#love', '#happy', '#motivation', '#inspiration',
            # Technology (broad)
            '#tech', '#innovation', '#digital', '#future', '#app',
            # Business & finance
            '#business', '#money', '#success', '#entrepreneur', '#startup',
            # Entertainment
            '#music', '#art', '#culture', '#entertainment', '#fun'
        ]
    
    @staticmethod
    def get_category_hashtags():
        """Hashtags organized by major categories"""
        return {
            'technology': [
                '#tech', '#AI', '#MachineLearning', '#DataScience', '#programming',
                '#coding', '#software', '#hardware', '#cloud', '#cybersecurity'
            ],
            'business': [
                '#business', '#entrepreneur', '#startup', '#marketing', '#finance',
                '#investment', '#economy', '#leadership', '#productivity', '#growth'
            ],
            'lifestyle': [
                '#lifestyle', '#health', '#fitness', '#food', '#travel',
                '#fashion', '#beauty', '#wellness', '#mindfulness', '#selfcare'
            ],
            'education': [
                '#education', '#learning', '#study', '#university', '#knowledge',
                '#skills', '#training', '#career', '#development', '#research'
            ],
            'social': [
                '#social', '#community', '#people', '#culture', '#society',
                '#politics', '#news', '#opinion', '#discussion', '#debate'
            ],
            'entertainment': [
                '#entertainment', '#music', '#movies', '#sports', '#gaming',
                '#art', '#photography', '#books', '#tv', '#comedy'
            ],
            'science': [
                '#science', '#research', '#discovery', '#medicine', '#space',
                '#environment', '#climate', '#nature', '#biology', '#physics'
            ]
        }
    
    @staticmethod
    def get_universal_set(max_hashtags=50):
        """Get a balanced universal set of hashtags across all categories"""
        categories = UniversalHashtagProvider.get_category_hashtags()
        trending = UniversalHashtagProvider.get_trending_hashtags()
        
        # Take top hashtags from each category
        universal_set = []
        hashtags_per_category = max_hashtags // len(categories)
        
        for category, hashtags in categories.items():
            universal_set.extend(hashtags[:hashtags_per_category])
        
        # Add trending hashtags
        remaining_slots = max_hashtags - len(universal_set)
        universal_set.extend(trending[:remaining_slots])
        
        return universal_set[:max_hashtags]
    
    @staticmethod
    def get_high_volume_hashtags():
        """Hashtags known for high tweet volumes"""
        return [
            '#news', '#breaking', '#today', '#update', '#live',
            '#trending', '#viral', '#popular', '#hot', '#now',
            '#love', '#life', '#happy', '#good', '#great',
            '#work', '#business', '#money', '#success', '#win',
            '#tech', '#new', '#best', '#top', '#amazing'
        ]
    
    @staticmethod
    def get_balanced_collection_set():
        """Get a balanced set optimized for diverse sentiment collection"""
        return {
            'high_volume': [
                '#news', '#trending', '#today', '#life', '#work',
                '#business', '#tech', '#love', '#happy', '#success'
            ],
            'positive_sentiment': [
                '#inspiration', '#motivation', '#success', '#achievement', '#victory',
                '#celebration', '#grateful', '#blessed', '#amazing', '#wonderful'
            ],
            'neutral_topics': [
                '#technology', '#business', '#education', '#research', '#development',
                '#innovation', '#science', '#culture', '#society', '#economy'
            ],
            'negative_sentiment': [
                '#disappointed', '#frustrated', '#concerned', '#worried', '#problem',
                '#issue', '#challenge', '#difficulty', '#struggle', '#failure'
            ],
            'diverse_domains': [
                '#health', '#environment', '#politics', '#sports', '#entertainment',
                '#travel', '#food', '#music', '#art', '#fashion'
            ]
        }

if __name__ == "__main__":
    provider = UniversalHashtagProvider()
    
    print("🌐 UNIVERSAL HASHTAG COLLECTION STRATEGIES")
    print("=" * 60)
    
    print("\n📈 High Volume Hashtags (25):")
    high_volume = provider.get_high_volume_hashtags()
    for i, tag in enumerate(high_volume, 1):
        print(f"{i:2d}. {tag}")
    
    print(f"\n🎯 Universal Set (50 hashtags):")
    universal = provider.get_universal_set(50)
    for i, tag in enumerate(universal, 1):
        print(f"{i:2d}. {tag}")
    
    print(f"\n⚖️ Balanced Collection Set:")
    balanced = provider.get_balanced_collection_set()
    for category, hashtags in balanced.items():
        print(f"  {category}: {hashtags[:5]}...")
