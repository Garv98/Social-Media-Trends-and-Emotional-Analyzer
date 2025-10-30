#!/usr/bin/env python3
"""Quick Database Viewer - View your Twitter data in a user-friendly format"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collector.database import PostgreSQLManager
import pandas as pd
from datetime import datetime

class DatabaseViewer:
    """Simple database viewer for tweet data"""
    
    def __init__(self):
        self.db = PostgreSQLManager()
        self.cursor = self.db.pg_connection.cursor()
    
    def show_summary(self):
        """Show database summary statistics"""
        print("📊 DATABASE SUMMARY")
        print("=" * 40)
        
        # Total tweets
        self.cursor.execute("SELECT COUNT(*) FROM tweets")
        total_tweets = self.cursor.fetchone()[0]
        print(f"📱 Total Tweets: {total_tweets:,}")
        
        # Total hashtags
        self.cursor.execute("SELECT COUNT(*) FROM hashtags")
        total_hashtags = self.cursor.fetchone()[0]
        print(f"🏷️  Total Hashtags: {total_hashtags}")
        
        # Date range
        self.cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM tweets")
        date_range = self.cursor.fetchone()
        if date_range[0]:
            print(f"📅 Date Range: {date_range[0].strftime('%Y-%m-%d')} to {date_range[1].strftime('%Y-%m-%d')}")
        
        # Processed tweets
        self.cursor.execute("SELECT COUNT(*) FROM tweets WHERE processed = true")
        processed = self.cursor.fetchone()[0]
        print(f"⚙️  Processed Tweets: {processed:,} ({(processed/total_tweets*100):.1f}%)")
    
    def show_recent_tweets(self, limit=5):
        """Show recent tweets"""
        print(f"\n📱 RECENT TWEETS (Last {limit})")
        print("=" * 60)
        
        self.cursor.execute("""
            SELECT id, original_text, author_username, created_at, like_count, retweet_count
            FROM tweets 
            ORDER BY created_at DESC 
            LIMIT %s
        """, (limit,))
        
        tweets = self.cursor.fetchall()
        
        for i, tweet in enumerate(tweets, 1):
            print(f"\n{i}. Tweet ID: {tweet[0]}")
            print(f"   Text: {tweet[1][:100]}...")
            print(f"   Author: @{tweet[2] or 'Unknown'}")
            print(f"   Date: {tweet[3].strftime('%Y-%m-%d %H:%M')}")
            print(f"   Engagement: {tweet[4]} likes, {tweet[5]} retweets")
    
    def show_top_hashtags(self, limit=10):
        """Show most popular hashtags"""
        print(f"\n🏷️  TOP HASHTAGS (Top {limit})")
        print("=" * 40)
        
        self.cursor.execute("""
            SELECT h.hashtag, COUNT(*) as tweet_count
            FROM hashtags h
            JOIN tweet_hashtags th ON h.id = th.hashtag_id
            GROUP BY h.hashtag
            ORDER BY tweet_count DESC
            LIMIT %s
        """, (limit,))
        
        hashtags = self.cursor.fetchall()
        
        for i, (hashtag, count) in enumerate(hashtags, 1):
            print(f"{i:2d}. {hashtag:<20} {count:>4} tweets")
    
    def show_daily_stats(self, days=7):
        """Show daily tweet statistics"""
        print(f"\n📈 DAILY STATISTICS (Last {days} days)")
        print("=" * 50)
        
        self.cursor.execute("""
            SELECT DATE(created_at) as date, 
                   COUNT(*) as tweets,
                   AVG(like_count) as avg_likes,
                   AVG(retweet_count) as avg_retweets
            FROM tweets
            WHERE created_at >= NOW() - INTERVAL '%s days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """, (days,))
        
        daily_stats = self.cursor.fetchall()
        
        print(f"{'Date':<12} {'Tweets':<8} {'Avg Likes':<10} {'Avg RTs':<10}")
        print("-" * 50)
        
        for date, tweets, avg_likes, avg_retweets in daily_stats:
            print(f"{date.strftime('%Y-%m-%d'):<12} {tweets:<8} {avg_likes or 0:<10.1f} {avg_retweets or 0:<10.1f}")
    
    def export_to_csv(self, filename="tweets_export.csv"):
        """Export all tweets to CSV"""
        print(f"\n💾 EXPORTING TO CSV: {filename}")
        
        try:
            df = pd.read_sql("""
                SELECT t.id, t.original_text, t.cleaned_text, t.created_at,
                       t.author_username, t.like_count, t.retweet_count,
                       t.reply_count, t.quote_count, t.processed
                FROM tweets t
                ORDER BY t.created_at DESC
            """, self.db.pg_connection)
            
            df.to_csv(filename, index=False)
            print(f"✅ Exported {len(df)} tweets to {filename}")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    def interactive_query(self):
        """Run custom SQL queries"""
        print("\n💻 INTERACTIVE SQL QUERY")
        print("=" * 30)
        print("Enter SQL query (or 'quit' to exit):")
        
        while True:
            query = input("\nSQL> ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            try:
                self.cursor.execute(query)
                
                if query.lower().startswith('select'):
                    results = self.cursor.fetchall()
                    if results:
                        # Show column names
                        cols = [desc[0] for desc in self.cursor.description]
                        print("\n" + " | ".join(cols))
                        print("-" * 60)
                        
                        # Show first 10 results
                        for row in results[:10]:
                            print(" | ".join(str(val) for val in row))
                        
                        if len(results) > 10:
                            print(f"... and {len(results) - 10} more rows")
                    else:
                        print("No results found.")
                else:
                    print("Query executed successfully.")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def close(self):
        """Close database connection"""
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'db') and self.db:
            self.db.close_connections()

def main():
    """Main function"""
    print("🌐 TWITTER DATABASE VIEWER")
    print("=" * 40)
    
    try:
        viewer = DatabaseViewer()
        
        # Show main menu
        while True:
            print("\n📋 MENU OPTIONS:")
            print("1. Database Summary")
            print("2. Recent Tweets")
            print("3. Top Hashtags")
            print("4. Daily Statistics")
            print("5. Export to CSV")
            print("6. Custom SQL Query")
            print("7. Exit")
            
            choice = input("\nSelect option (1-7): ").strip()
            
            if choice == '1':
                viewer.show_summary()
            elif choice == '2':
                limit = input("How many recent tweets? (default 5): ").strip()
                limit = int(limit) if limit.isdigit() else 5
                viewer.show_recent_tweets(limit)
            elif choice == '3':
                limit = input("How many top hashtags? (default 10): ").strip()
                limit = int(limit) if limit.isdigit() else 10
                viewer.show_top_hashtags(limit)
            elif choice == '4':
                days = input("How many days? (default 7): ").strip()
                days = int(days) if days.isdigit() else 7
                viewer.show_daily_stats(days)
            elif choice == '5':
                filename = input("CSV filename (default: tweets_export.csv): ").strip()
                filename = filename if filename else "tweets_export.csv"
                viewer.export_to_csv(filename)
            elif choice == '6':
                viewer.interactive_query()
            elif choice == '7':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid option. Please choose 1-7.")
        
        viewer.close()
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Make sure Docker containers are running: docker-compose up -d")

if __name__ == "__main__":
    main()
