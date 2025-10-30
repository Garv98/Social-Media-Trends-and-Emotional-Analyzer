#!/usr/bin/env python3
"""Comprehensive EDA Dashboard Generator"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Any
import logging
from wordcloud import WordCloud
import textwrap

class EDADashboardGenerator:
    """Generate comprehensive EDA dashboards and visualizations"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = self._setup_logger()
        
        # Set styling
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
    def _setup_logger(self):
        logger = logging.getLogger('EDADashboard')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        if not logger.handlers:
            logger.addHandler(handler)
        return logger
    
    def generate_comprehensive_dashboard(self, days_back: int = 7) -> str:
        """
        Generate comprehensive EDA dashboard
        """
        self.logger.info(f"📊 Generating comprehensive EDA dashboard for last {days_back} days...")
        
        # Load data
        df = self._load_tweet_data(days_back)
        
        if df.empty:
            self.logger.warning("⚠️ No data available for dashboard generation")
            return None
        
        # Create output directory
        output_dir = f"logs/eda_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate all visualizations
        dashboard_components = {
            'overview': self._create_overview_dashboard(df, output_dir),
            'temporal_analysis': self._create_temporal_analysis(df, output_dir),
            'engagement_analysis': self._create_engagement_analysis(df, output_dir),
            'text_analysis': self._create_text_analysis(df, output_dir),
            'hashtag_analysis': self._create_hashtag_analysis(df, output_dir),
            'author_analysis': self._create_author_analysis(df, output_dir),
            'interactive_dashboard': self._create_interactive_dashboard(df, output_dir)
        }
        
        # Generate summary report
        summary_path = self._generate_summary_report(df, dashboard_components, output_dir)
        
        self.logger.info(f"✅ EDA dashboard generated in: {output_dir}")
        return output_dir
    
    def _load_tweet_data(self, days_back: int) -> pd.DataFrame:
        """Load real tweet data from PostgreSQL database"""
        query = f"""
        SELECT 
            t.id,
            t.original_text,
            t.cleaned_text,
            t.created_at,
            t.author_id,
            t.author_username,
            t.like_count,
            t.retweet_count,
            t.reply_count,
            t.quote_count,
            t.char_count,
            t.word_count,
            t.hashtag_count,
            t.mention_count,
            t.url_count,
            t.processed,
            STRING_AGG(h.hashtag, ',') as hashtags
        FROM tweets t
        LEFT JOIN tweet_hashtags th ON t.id = th.tweet_id
        LEFT JOIN hashtags h ON th.hashtag_id = h.id
        WHERE t.created_at >= NOW() - INTERVAL '{days_back} days'
        GROUP BY t.id, t.original_text, t.cleaned_text, t.created_at, 
                 t.author_id, t.author_username, t.like_count, t.retweet_count,
                 t.reply_count, t.quote_count, t.char_count, t.word_count,
                 t.hashtag_count, t.mention_count, t.url_count, t.processed
        ORDER BY t.created_at DESC
        """
        
        try:
            df = pd.read_sql(query, self.db_manager.pg_connection)
            
            if df.empty:
                self.logger.warning("⚠️ No tweets found in database")
                return df
            
            # Convert datetime
            df['created_at'] = pd.to_datetime(df['created_at'])
            
            # Process hashtags column
            df['hashtags_list'] = df['hashtags'].fillna('').apply(
                lambda x: [tag.strip() for tag in x.split(',') if tag.strip()] if x else []
            )
            
            # Fill NaN values with 0 for numeric columns
            numeric_cols = ['like_count', 'retweet_count', 'reply_count', 'quote_count', 
                          'char_count', 'word_count', 'hashtag_count', 'mention_count', 'url_count']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = df[col].fillna(0)
            
            self.logger.info(f"📊 Loaded {len(df)} tweets for analysis")
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            return pd.DataFrame()
    
    def _create_overview_dashboard(self, df: pd.DataFrame, output_dir: str) -> str:
        """Create overview dashboard"""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Twitter Data Collection - Overview Dashboard', fontsize=16, fontweight='bold')
        
        # 1. Tweet volume over time
        daily_tweets = df.groupby(df['created_at'].dt.date).size()
        axes[0, 0].plot(daily_tweets.index, daily_tweets.values, marker='o', linewidth=2)
        axes[0, 0].set_title('Daily Tweet Volume', fontweight='bold')
        axes[0, 0].set_xlabel('Date')
        axes[0, 0].set_ylabel('Number of Tweets')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # 2. Tweet length distribution
        axes[0, 1].hist(df['char_count'].dropna(), bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        axes[0, 1].set_title('Tweet Length Distribution', fontweight='bold')
        axes[0, 1].set_xlabel('Character Count')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].axvline(df['char_count'].mean(), color='red', linestyle='--', label=f'Mean: {df["char_count"].mean():.1f}')
        axes[0, 1].legend()
        
        # 3. Engagement metrics
        if 'like_count' in df.columns:
            engagement_data = df[['like_count', 'retweet_count', 'reply_count']].mean()
            bars = axes[0, 2].bar(engagement_data.index, engagement_data.values, color=['#ff6b6b', '#4ecdc4', '#45b7d1'])
            axes[0, 2].set_title('Average Engagement Metrics', fontweight='bold')
            axes[0, 2].set_ylabel('Average Count')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                axes[0, 2].text(bar.get_x() + bar.get_width()/2., height,
                               f'{height:.1f}', ha='center', va='bottom')
        
        # 4. Hourly tweet pattern
        hourly_tweets = df.groupby(df['created_at'].dt.hour).size()
        axes[1, 0].bar(hourly_tweets.index, hourly_tweets.values, color='lightgreen', alpha=0.7)
        axes[1, 0].set_title('Tweets by Hour of Day', fontweight='bold')
        axes[1, 0].set_xlabel('Hour')
        axes[1, 0].set_ylabel('Number of Tweets')
        axes[1, 0].set_xticks(range(0, 24, 2))
        
        # 5. Top authors
        top_authors = df['author_username'].value_counts().head(10)
        axes[1, 1].barh(range(len(top_authors)), top_authors.values, color='coral')
        axes[1, 1].set_title('Top 10 Most Active Authors', fontweight='bold')
        axes[1, 1].set_yticks(range(len(top_authors)))
        axes[1, 1].set_yticklabels([textwrap.shorten(author, width=15) for author in top_authors.index])
        axes[1, 1].set_xlabel('Number of Tweets')
        
        # 6. Data quality indicators
        quality_metrics = {
            'Complete Tweets': len(df[df['original_text'].notna()]),
            'Processed Tweets': len(df[df['processed'] == True]),
            'With Hashtags': len(df[df['hashtag_count'] > 0]),
            'With Mentions': len(df[df['mention_count'] > 0])
        }
        
        bars = axes[1, 2].bar(quality_metrics.keys(), quality_metrics.values(), color='mediumpurple', alpha=0.7)
        axes[1, 2].set_title('Data Quality Metrics', fontweight='bold')
        axes[1, 2].set_ylabel('Count')
        axes[1, 2].tick_params(axis='x', rotation=45)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            axes[1, 2].text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(height)}', ha='center', va='bottom')
        
        plt.tight_layout()
        overview_path = os.path.join(output_dir, 'overview_dashboard.png')
        plt.savefig(overview_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return overview_path
    
    def _create_temporal_analysis(self, df: pd.DataFrame, output_dir: str) -> str:
        """Create temporal analysis visualizations"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Temporal Analysis Dashboard', fontsize=16, fontweight='bold')
        
        # 1. Time series with trend
        daily_tweets = df.groupby(df['created_at'].dt.date).size()
        axes[0, 0].plot(daily_tweets.index, daily_tweets.values, marker='o', linewidth=2, markersize=6)
        
        # Add trend line
        x_numeric = np.arange(len(daily_tweets))
        z = np.polyfit(x_numeric, daily_tweets.values, 1)
        p = np.poly1d(z)
        axes[0, 0].plot(daily_tweets.index, p(x_numeric), "r--", alpha=0.8, linewidth=2, label='Trend')
        
        axes[0, 0].set_title('Tweet Volume Trend Over Time', fontweight='bold')
        axes[0, 0].set_xlabel('Date')
        axes[0, 0].set_ylabel('Number of Tweets')
        axes[0, 0].legend()
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # 2. Day of week pattern
        df['day_of_week'] = df['created_at'].dt.day_name()
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_tweets = df['day_of_week'].value_counts().reindex(day_order)
        
        bars = axes[0, 1].bar(day_tweets.index, day_tweets.values, color='lightblue', alpha=0.8)
        axes[0, 1].set_title('Tweet Distribution by Day of Week', fontweight='bold')
        axes[0, 1].set_ylabel('Number of Tweets')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            axes[0, 1].text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(height)}', ha='center', va='bottom')
        
        # 3. Hourly heatmap
        df['hour'] = df['created_at'].dt.hour
        df['day'] = df['created_at'].dt.day_name()
        
        heatmap_data = df.groupby(['day', 'hour']).size().unstack(fill_value=0)
        heatmap_data = heatmap_data.reindex(day_order)
        
        im = axes[1, 0].imshow(heatmap_data.values, cmap='YlOrRd', aspect='auto')
        axes[1, 0].set_title('Tweet Activity Heatmap (Day vs Hour)', fontweight='bold')
        axes[1, 0].set_xticks(range(0, 24, 2))
        axes[1, 0].set_xticklabels(range(0, 24, 2))
        axes[1, 0].set_yticks(range(len(day_order)))
        axes[1, 0].set_yticklabels(day_order)
        axes[1, 0].set_xlabel('Hour of Day')
        axes[1, 0].set_ylabel('Day of Week')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=axes[1, 0])
        cbar.set_label('Number of Tweets')
        
        # 4. Peak activity analysis
        peak_hours = df.groupby('hour').size().nlargest(5)
        axes[1, 1].bar(peak_hours.index, peak_hours.values, color='orange', alpha=0.8)
        axes[1, 1].set_title('Top 5 Peak Activity Hours', fontweight='bold')
        axes[1, 1].set_xlabel('Hour of Day')
        axes[1, 1].set_ylabel('Number of Tweets')
        
        # Add value labels
        for i, (hour, count) in enumerate(peak_hours.items()):
            axes[1, 1].text(hour, count, f'{int(count)}', ha='center', va='bottom')
        
        plt.tight_layout()
        temporal_path = os.path.join(output_dir, 'temporal_analysis.png')
        plt.savefig(temporal_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return temporal_path
    
    def _create_engagement_analysis(self, df: pd.DataFrame, output_dir: str) -> str:
        """Create engagement analysis visualizations"""
        if 'like_count' not in df.columns:
            return None
            
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Engagement Analysis Dashboard', fontsize=16, fontweight='bold')
        
        # 1. Engagement distribution
        engagement_metrics = ['like_count', 'retweet_count', 'reply_count', 'quote_count']
        available_metrics = [col for col in engagement_metrics if col in df.columns]
        
        for i, metric in enumerate(available_metrics[:4]):
            color = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4'][i]
            axes[0, 0].hist(df[metric].dropna(), bins=30, alpha=0.7, label=metric.replace('_count', ''), color=color)
        
        axes[0, 0].set_title('Engagement Metrics Distribution', fontweight='bold')
        axes[0, 0].set_xlabel('Count')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].legend()
        axes[0, 0].set_yscale('log')
        
        # 2. Engagement correlation
        if len(available_metrics) > 1:
            corr_data = df[available_metrics].corr()
            im = axes[0, 1].imshow(corr_data.values, cmap='coolwarm', vmin=-1, vmax=1)
            axes[0, 1].set_title('Engagement Metrics Correlation', fontweight='bold')
            axes[0, 1].set_xticks(range(len(available_metrics)))
            axes[0, 1].set_yticks(range(len(available_metrics)))
            axes[0, 1].set_xticklabels([m.replace('_count', '') for m in available_metrics], rotation=45)
            axes[0, 1].set_yticklabels([m.replace('_count', '') for m in available_metrics])
            
            # Add correlation values
            for i in range(len(available_metrics)):
                for j in range(len(available_metrics)):
                    axes[0, 1].text(j, i, f'{corr_data.iloc[i, j]:.2f}', 
                                   ha='center', va='center', fontweight='bold')
            
            plt.colorbar(im, ax=axes[0, 1])
        
        # 3. Top engaged tweets
        df['total_engagement'] = df[available_metrics].sum(axis=1)
        top_engaged = df.nlargest(10, 'total_engagement')
        
        axes[1, 0].barh(range(len(top_engaged)), top_engaged['total_engagement'], color='gold', alpha=0.8)
        axes[1, 0].set_title('Top 10 Most Engaged Tweets', fontweight='bold')
        axes[1, 0].set_xlabel('Total Engagement')
        axes[1, 0].set_yticks(range(len(top_engaged)))
        axes[1, 0].set_yticklabels([f"Tweet {i+1}" for i in range(len(top_engaged))])
        
        # 4. Engagement vs time of day
        hourly_engagement = df.groupby('hour')[available_metrics].mean()
        
        for metric in available_metrics:
            axes[1, 1].plot(hourly_engagement.index, hourly_engagement[metric], 
                           marker='o', label=metric.replace('_count', ''), linewidth=2)
        
        axes[1, 1].set_title('Average Engagement by Hour', fontweight='bold')
        axes[1, 1].set_xlabel('Hour of Day')
        axes[1, 1].set_ylabel('Average Count')
        axes[1, 1].legend()
        axes[1, 1].set_xticks(range(0, 24, 2))
        
        plt.tight_layout()
        engagement_path = os.path.join(output_dir, 'engagement_analysis.png')
        plt.savefig(engagement_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return engagement_path
    
    def _create_text_analysis(self, df: pd.DataFrame, output_dir: str) -> str:
        """Create text analysis visualizations"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Text Analysis Dashboard', fontsize=16, fontweight='bold')
        
        # 1. Text length vs engagement
        if 'like_count' in df.columns:
            try:
                scatter = axes[0, 0].scatter(df['char_count'], df['like_count'], alpha=0.6, c='blue')
                axes[0, 0].set_title('Text Length vs Likes', fontweight='bold')
                axes[0, 0].set_xlabel('Character Count')
                axes[0, 0].set_ylabel('Like Count')
                
                # Add trend line with error handling
                valid_data = df[['char_count', 'like_count']].dropna()
                if len(valid_data) > 10 and valid_data['char_count'].std() > 0:
                    try:
                        z = np.polyfit(valid_data['char_count'], valid_data['like_count'], 1)
                        p = np.poly1d(z)
                        axes[0, 0].plot(valid_data['char_count'], p(valid_data['char_count']), "r--", alpha=0.8)
                    except np.linalg.LinAlgError:
                        # Skip trend line if linear algebra fails
                        pass
            except Exception as e:
                axes[0, 0].text(0.5, 0.5, f'Error in scatter plot: {str(e)[:50]}...', 
                               ha='center', va='center', transform=axes[0, 0].transAxes)
        
        # 2. Hashtag count distribution
        hashtag_counts = df['hashtag_count'].value_counts().sort_index()
        axes[0, 1].bar(hashtag_counts.index, hashtag_counts.values, color='lightgreen', alpha=0.8)
        axes[0, 1].set_title('Distribution of Hashtag Counts', fontweight='bold')
        axes[0, 1].set_xlabel('Number of Hashtags')
        axes[0, 1].set_ylabel('Number of Tweets')
        
        # 3. Mention count distribution
        mention_counts = df['mention_count'].value_counts().sort_index()
        axes[1, 0].bar(mention_counts.index, mention_counts.values, color='lightsalmon', alpha=0.8)
        axes[1, 0].set_title('Distribution of Mention Counts', fontweight='bold')
        axes[1, 0].set_xlabel('Number of Mentions')
        axes[1, 0].set_ylabel('Number of Tweets')
        
        # 4. Word count vs character count
        if 'word_count' in df.columns:
            try:
                axes[1, 1].scatter(df['word_count'], df['char_count'], alpha=0.6, c='purple')
                axes[1, 1].set_title('Word Count vs Character Count', fontweight='bold')
                axes[1, 1].set_xlabel('Word Count')
                axes[1, 1].set_ylabel('Character Count')
                
                # Add trend line with error handling
                valid_data = df[['word_count', 'char_count']].dropna()
                if len(valid_data) > 10 and valid_data['word_count'].std() > 0:
                    try:
                        z = np.polyfit(valid_data['word_count'], valid_data['char_count'], 1)
                        p = np.poly1d(z)
                        axes[1, 1].plot(valid_data['word_count'], p(valid_data['word_count']), "r--", alpha=0.8)
                    except np.linalg.LinAlgError:
                        # Skip trend line if linear algebra fails
                        pass
            except Exception as e:
                axes[1, 1].text(0.5, 0.5, f'Error in plot: {str(e)[:50]}...', 
                               ha='center', va='center', transform=axes[1, 1].transAxes)
        
        plt.tight_layout()
        text_path = os.path.join(output_dir, 'text_analysis.png')
        plt.savefig(text_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Generate word cloud
        self._create_wordcloud(df, output_dir)
        
        return text_path
    
    def _create_wordcloud(self, df: pd.DataFrame, output_dir: str):
        """Create word cloud from tweet text"""
        try:
            # Combine all tweet text
            text_series = df['cleaned_text'].dropna().astype(str)
            if len(text_series) == 0:
                self.logger.warning("No text data available for word cloud")
                return
                
            text = ' '.join(text_series)
            
            if text.strip() and len(text.strip()) > 10:
                wordcloud = WordCloud(width=800, height=400, 
                                    background_color='white',
                                    max_words=100,
                                    colormap='viridis',
                                    relative_scaling=0.5,
                                    min_font_size=10).generate(text)
                
                plt.figure(figsize=(12, 6))
                plt.imshow(wordcloud, interpolation='bilinear')
                plt.axis('off')
                plt.title('Tweet Text Word Cloud', fontsize=16, fontweight='bold')
                
                wordcloud_path = os.path.join(output_dir, 'wordcloud.png')
                plt.savefig(wordcloud_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                self.logger.info(f"📊 Word cloud saved to: {wordcloud_path}")
            else:
                self.logger.warning("Insufficient text data for word cloud generation")
                
        except Exception as e:
            self.logger.warning(f"Could not generate word cloud: {str(e)}")
    
    def _create_hashtag_analysis(self, df: pd.DataFrame, output_dir: str) -> str:
        """Create hashtag analysis visualizations"""
        # Extract hashtags from the hashtags_list column
        all_hashtags = []
        for hashtags_list in df['hashtags_list'].dropna():
            if hashtags_list and hashtags_list != [None]:
                all_hashtags.extend([h for h in hashtags_list if h])
        
        if not all_hashtags:
            self.logger.warning("No hashtags found for analysis")
            return None
            
        hashtag_counts = pd.Series(all_hashtags).value_counts()
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Hashtag Analysis Dashboard', fontsize=16, fontweight='bold')
        
        # 1. Top hashtags
        top_hashtags = hashtag_counts.head(15)
        axes[0, 0].barh(range(len(top_hashtags)), top_hashtags.values, color='skyblue')
        axes[0, 0].set_title('Top 15 Most Used Hashtags', fontweight='bold')
        axes[0, 0].set_yticks(range(len(top_hashtags)))
        axes[0, 0].set_yticklabels([textwrap.shorten(tag, width=20) for tag in top_hashtags.index])
        axes[0, 0].set_xlabel('Frequency')
        
        # 2. Hashtag frequency distribution
        freq_dist = hashtag_counts.value_counts().sort_index()
        axes[0, 1].bar(freq_dist.index, freq_dist.values, color='lightcoral', alpha=0.8)
        axes[0, 1].set_title('Hashtag Frequency Distribution', fontweight='bold')
        axes[0, 1].set_xlabel('Number of Uses')
        axes[0, 1].set_ylabel('Number of Hashtags')
        axes[0, 1].set_yscale('log')
        
        # 3. Hashtag co-occurrence (for tweets with multiple hashtags)
        multi_hashtag_tweets = df[df['hashtag_count'] > 1]
        cooccurrence_pairs = []
        
        for hashtags_list in multi_hashtag_tweets['hashtags_list'].dropna():
            if hashtags_list and len(hashtags_list) > 1:
                hashtags = [h for h in hashtags_list if h]
                for i in range(len(hashtags)):
                    for j in range(i+1, len(hashtags)):
                        pair = tuple(sorted([hashtags[i], hashtags[j]]))
                        cooccurrence_pairs.append(pair)
        
        if cooccurrence_pairs:
            cooccurrence_counts = pd.Series(cooccurrence_pairs).value_counts().head(10)
            pair_labels = [f"{pair[0]} + {pair[1]}" for pair in cooccurrence_counts.index]
            
            axes[1, 0].barh(range(len(cooccurrence_counts)), cooccurrence_counts.values, color='lightgreen')
            axes[1, 0].set_title('Top 10 Hashtag Co-occurrences', fontweight='bold')
            axes[1, 0].set_yticks(range(len(cooccurrence_counts)))
            axes[1, 0].set_yticklabels([textwrap.shorten(label, width=25) for label in pair_labels])
            axes[1, 0].set_xlabel('Frequency')
        
        # 4. Hashtag trend over time (for top hashtags)
        top_5_hashtags = hashtag_counts.head(5).index
        
        for hashtag in top_5_hashtags:
            hashtag_tweets = df[df['hashtags_list'].apply(
                lambda x: hashtag in x if x and x != [None] else False
            )]
            
            if not hashtag_tweets.empty:
                daily_counts = hashtag_tweets.groupby(hashtag_tweets['created_at'].dt.date).size()
                axes[1, 1].plot(daily_counts.index, daily_counts.values, 
                               marker='o', label=textwrap.shorten(hashtag, width=15), linewidth=2)
        
        axes[1, 1].set_title('Top 5 Hashtags Trend Over Time', fontweight='bold')
        axes[1, 1].set_xlabel('Date')
        axes[1, 1].set_ylabel('Number of Tweets')
        axes[1, 1].legend()
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        hashtag_path = os.path.join(output_dir, 'hashtag_analysis.png')
        plt.savefig(hashtag_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return hashtag_path
    
    def _create_author_analysis(self, df: pd.DataFrame, output_dir: str) -> str:
        """Create author analysis visualizations"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Author Analysis Dashboard', fontsize=16, fontweight='bold')
        
        # 1. Author activity distribution
        author_tweet_counts = df['author_username'].value_counts()
        
        # Distribution of how many tweets each author has
        activity_dist = author_tweet_counts.value_counts().sort_index()
        axes[0, 0].bar(activity_dist.index, activity_dist.values, color='lightblue', alpha=0.8)
        axes[0, 0].set_title('Author Activity Distribution', fontweight='bold')
        axes[0, 0].set_xlabel('Number of Tweets per Author')
        axes[0, 0].set_ylabel('Number of Authors')
        axes[0, 0].set_yscale('log')
        
        # 2. Top authors by engagement
        if 'like_count' in df.columns:
            author_engagement = df.groupby('author_username')[['like_count', 'retweet_count']].sum()
            author_engagement['total_engagement'] = author_engagement.sum(axis=1)
            top_engaged_authors = author_engagement.nlargest(10, 'total_engagement')
            
            axes[0, 1].barh(range(len(top_engaged_authors)), top_engaged_authors['total_engagement'], 
                           color='gold', alpha=0.8)
            axes[0, 1].set_title('Top 10 Authors by Total Engagement', fontweight='bold')
            axes[0, 1].set_yticks(range(len(top_engaged_authors)))
            axes[0, 1].set_yticklabels([textwrap.shorten(author, width=15) 
                                       for author in top_engaged_authors.index])
            axes[0, 1].set_xlabel('Total Engagement')
        
        # 3. Author posting patterns
        author_hour_pattern = df.groupby(['author_username', df['created_at'].dt.hour]).size().unstack(fill_value=0)
        
        # Get top 5 most active authors for pattern analysis
        top_authors = author_tweet_counts.head(5).index
        
        for author in top_authors:
            if author in author_hour_pattern.index:
                pattern = author_hour_pattern.loc[author]
                axes[1, 0].plot(pattern.index, pattern.values, 
                               marker='o', label=textwrap.shorten(author, width=15), linewidth=2)
        
        axes[1, 0].set_title('Posting Patterns of Top 5 Authors', fontweight='bold')
        axes[1, 0].set_xlabel('Hour of Day')
        axes[1, 0].set_ylabel('Number of Tweets')
        axes[1, 0].legend()
        axes[1, 0].set_xticks(range(0, 24, 2))
        
        # 4. Unique vs repeat authors over time
        daily_authors = df.groupby(df['created_at'].dt.date)['author_username'].agg(['count', 'nunique'])
        daily_authors['repeat_ratio'] = (daily_authors['count'] - daily_authors['nunique']) / daily_authors['count']
        
        ax2 = axes[1, 1].twinx()
        
        line1 = axes[1, 1].plot(daily_authors.index, daily_authors['nunique'], 
                               color='blue', marker='o', label='Unique Authors', linewidth=2)
        line2 = ax2.plot(daily_authors.index, daily_authors['repeat_ratio'], 
                        color='red', marker='s', label='Repeat Ratio', linewidth=2)
        
        axes[1, 1].set_title('Author Diversity Over Time', fontweight='bold')
        axes[1, 1].set_xlabel('Date')
        axes[1, 1].set_ylabel('Unique Authors', color='blue')
        ax2.set_ylabel('Repeat Author Ratio', color='red')
        
        # Combine legends
        lines1, labels1 = axes[1, 1].get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        axes[1, 1].legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        author_path = os.path.join(output_dir, 'author_analysis.png')
        plt.savefig(author_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return author_path
    
    def _create_interactive_dashboard(self, df: pd.DataFrame, output_dir: str) -> str:
        """Create interactive Plotly dashboard"""
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['Tweet Volume Over Time', 'Engagement Metrics', 
                           'Hourly Activity Pattern', 'Top Hashtags'],
            specs=[[{"secondary_y": False}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        # 1. Tweet volume over time
        daily_tweets = df.groupby(df['created_at'].dt.date).size().reset_index()
        daily_tweets.columns = ['date', 'count']
        
        fig.add_trace(
            go.Scatter(x=daily_tweets['date'], y=daily_tweets['count'],
                      mode='lines+markers', name='Daily Tweets',
                      line=dict(color='blue', width=3)),
            row=1, col=1
        )
        
        # 2. Engagement metrics (if available)
        if 'like_count' in df.columns:
            engagement_avg = df[['like_count', 'retweet_count', 'reply_count']].mean()
            
            fig.add_trace(
                go.Bar(x=engagement_avg.index, y=engagement_avg.values,
                      name='Avg Engagement', marker_color='lightcoral'),
                row=1, col=2
            )
        
        # 3. Hourly activity pattern
        hourly_tweets = df.groupby(df['created_at'].dt.hour).size()
        
        fig.add_trace(
            go.Bar(x=hourly_tweets.index, y=hourly_tweets.values,
                  name='Hourly Tweets', marker_color='lightgreen'),
            row=2, col=1
        )
        
        # 4. Top hashtags
        all_hashtags = []
        for hashtags_list in df['hashtags_list'].dropna():
            if hashtags_list and hashtags_list != [None]:
                all_hashtags.extend([h for h in hashtags_list if h])
        
        if all_hashtags:
            hashtag_counts = pd.Series(all_hashtags).value_counts().head(10)
            
            fig.add_trace(
                go.Bar(x=hashtag_counts.values, y=hashtag_counts.index,
                      orientation='h', name='Top Hashtags', 
                      marker_color='skyblue'),
                row=2, col=2
            )
        
        # Update layout
        fig.update_layout(
            title_text="Interactive Twitter Data Analysis Dashboard",
            title_x=0.5,
            height=800,
            showlegend=False
        )
        
        # Save interactive dashboard
        dashboard_path = os.path.join(output_dir, 'interactive_dashboard.html')
        pyo.plot(fig, filename=dashboard_path, auto_open=False)
        
        return dashboard_path
    
    def _generate_summary_report(self, df: pd.DataFrame, components: Dict[str, str], output_dir: str) -> str:
        """Generate summary report"""
        report = {
            'generation_time': datetime.now().isoformat(),
            'data_summary': {
                'total_tweets': len(df),
                'date_range': {
                    'start': df['created_at'].min().isoformat(),
                    'end': df['created_at'].max().isoformat()
                },
                'unique_authors': df['author_username'].nunique(),
                'avg_engagement': df[['like_count', 'retweet_count']].mean().to_dict() if 'like_count' in df.columns else None,
                'top_hashtags': [],
                'data_quality_score': self._calculate_dashboard_quality_score(df)
            },
            'dashboard_components': components,
            'insights': self._generate_key_insights(df)
        }
        
        # Extract top hashtags
        all_hashtags = []
        for hashtags_list in df['hashtags_list'].dropna():
            if hashtags_list and hashtags_list != [None]:
                all_hashtags.extend([h for h in hashtags_list if h])
        
        if all_hashtags:
            report['data_summary']['top_hashtags'] = pd.Series(all_hashtags).value_counts().head(5).to_dict()
        
        # Save report
        report_path = os.path.join(output_dir, 'dashboard_summary.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Generate HTML summary
        self._generate_html_summary(report, output_dir)
        
        return report_path
    
    def _calculate_dashboard_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate a quality score for the dashboard data"""
        score = 0
        
        # Data volume score (30%)
        if len(df) > 1000:
            score += 30
        elif len(df) > 500:
            score += 20
        elif len(df) > 100:
            score += 10
        
        # Data completeness score (25%)
        complete_fields = ['original_text', 'author_username', 'created_at']
        completeness = df[complete_fields].notna().all(axis=1).mean()
        score += completeness * 25
        
        # Data diversity score (25%)
        author_diversity = df['author_username'].nunique() / len(df)
        score += min(author_diversity * 100, 25)
        
        # Time coverage score (20%)
        time_span = (df['created_at'].max() - df['created_at'].min()).days
        if time_span >= 7:
            score += 20
        elif time_span >= 3:
            score += 15
        elif time_span >= 1:
            score += 10
        
        return min(score, 100)
    
    def _generate_key_insights(self, df: pd.DataFrame) -> List[str]:
        """Generate key insights from the data"""
        insights = []
        
        # Volume insights
        daily_tweets = df.groupby(df['created_at'].dt.date).size()
        if len(daily_tweets) > 1:
            trend = "increasing" if daily_tweets.iloc[-1] > daily_tweets.iloc[0] else "decreasing"
            insights.append(f"Tweet volume shows a {trend} trend over the analysis period")
        
        # Peak activity insights
        hourly_activity = df.groupby(df['created_at'].dt.hour).size()
        peak_hour = hourly_activity.idxmax()
        insights.append(f"Peak activity occurs at {peak_hour}:00 with {hourly_activity.max()} tweets")
        
        # Author insights
        author_counts = df['author_username'].value_counts()
        top_author_ratio = author_counts.iloc[0] / len(df) if len(author_counts) > 0 else 0
        if top_author_ratio > 0.1:
            insights.append(f"Content is concentrated: top author contributes {top_author_ratio:.1%} of tweets")
        else:
            insights.append("Content shows good author diversity")
        
        # Engagement insights (if available)
        if 'like_count' in df.columns:
            avg_engagement = df['like_count'].mean()
            high_engagement_tweets = len(df[df['like_count'] > avg_engagement * 2])
            insights.append(f"Average engagement is {avg_engagement:.1f} likes, with {high_engagement_tweets} high-performing tweets")
        
        # Hashtag insights
        hashtag_tweets = df[df['hashtag_count'] > 0]
        hashtag_ratio = len(hashtag_tweets) / len(df)
        insights.append(f"{hashtag_ratio:.1%} of tweets contain hashtags")
        
        return insights
    
    def _generate_html_summary(self, report: Dict[str, Any], output_dir: str):
        """Generate HTML summary page"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Twitter Data Analysis Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #1da1f2; color: white; padding: 20px; border-radius: 10px; }}
                .summary {{ background-color: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 10px; }}
                .insights {{ background-color: #e8f5e8; padding: 20px; margin: 20px 0; border-radius: 10px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 15px; background-color: white; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .component {{ margin: 10px 0; }}
                ul {{ list-style-type: none; padding-left: 0; }}
                li {{ margin: 5px 0; padding: 5px; background-color: rgba(255,255,255,0.8); border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Twitter Data Analysis Dashboard</h1>
                <p>Generated on: {report['generation_time']}</p>
            </div>
            
            <div class="summary">
                <h2>📈 Data Summary</h2>
                <div class="metric">
                    <strong>Total Tweets:</strong> {report['data_summary']['total_tweets']:,}
                </div>
                <div class="metric">
                    <strong>Unique Authors:</strong> {report['data_summary']['unique_authors']:,}
                </div>
                <div class="metric">
                    <strong>Data Quality Score:</strong> {report['data_summary']['data_quality_score']:.1f}/100
                </div>
                <div class="metric">
                    <strong>Date Range:</strong> {report['data_summary']['date_range']['start'][:10]} to {report['data_summary']['date_range']['end'][:10]}
                </div>
            </div>
            
            <div class="insights">
                <h2>💡 Key Insights</h2>
                <ul>
        """
        
        for insight in report['insights']:
            html_content += f"<li>• {insight}</li>"
        
        html_content += """
                </ul>
            </div>
            
            <div class="summary">
                <h2>📊 Dashboard Components</h2>
        """
        
        for component_name, component_path in report['dashboard_components'].items():
            if component_path:
                filename = os.path.basename(component_path)
                html_content += f'<div class="component">📈 <a href="{filename}">{component_name.replace("_", " ").title()}</a></div>'
        
        html_content += """
            </div>
            
            <div class="summary">
                <h2>🏷️ Top Hashtags</h2>
        """
        
        if report['data_summary']['top_hashtags']:
            for hashtag, count in report['data_summary']['top_hashtags'].items():
                html_content += f'<div class="metric"><strong>{hashtag}:</strong> {count} tweets</div>'
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        html_path = os.path.join(output_dir, 'dashboard_summary.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)


if __name__ == "__main__":
    import sys
    import os
    
    # Add parent directory to path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from data_collector.database import PostgreSQLManager
    
    print("📊 Generating comprehensive EDA dashboard...")
    
    # Initialize
    db_manager = PostgreSQLManager()
    dashboard_generator = EDADashboardGenerator(db_manager)
    
    # Generate dashboard
    output_dir = dashboard_generator.generate_comprehensive_dashboard(days_back=7)
    
    if output_dir:
        print(f"✅ Dashboard generated successfully in: {output_dir}")
        print(f"🌐 Open dashboard_summary.html to view the results")
    else:
        print("❌ Failed to generate dashboard")
