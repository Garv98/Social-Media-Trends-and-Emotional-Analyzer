import re
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import string
from typing import Dict, Any, List
import logging
from datetime import datetime

class TweetPreprocessor:
    """Tweet preprocessing and cleaning pipeline"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self._download_nltk_data()
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
    
    def _setup_logger(self):
        logger = logging.getLogger('TweetProcessor')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        if not logger.handlers:
            logger.addHandler(handler)
        return logger
    
    def _download_nltk_data(self):
        """Download required NLTK data"""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            self.logger.info("Downloading NLTK punkt tokenizer...")
            nltk.download('punkt', quiet=True)
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            self.logger.info("Downloading NLTK stopwords...")
            nltk.download('stopwords', quiet=True)
        
        try:
            nltk.data.find('corpora/wordnet')
        except LookupError:
            self.logger.info("Downloading NLTK wordnet...")
            nltk.download('wordnet', quiet=True)
        
        try:
            nltk.data.find('corpora/omw-1.4')
        except LookupError:
            self.logger.info("Downloading NLTK omw-1.4...")
            nltk.download('omw-1.4', quiet=True)
    
    def clean_tweet_text(self, text: str) -> str:
        """
        Clean and preprocess tweet text
        
        Args:
            text: Raw tweet text
            
        Returns:
            Cleaned tweet text
        """
        if not isinstance(text, str):
            return ""
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove user mentions and hashtags for cleaning (keep original for hashtag extraction)
        text = re.sub(r'@\w+', '', text)
        
        # Remove retweet indicators
        text = re.sub(r'^RT\s+', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep some punctuation
        text = re.sub(r'[^\w\s#@.,!?-]', '', text)
        
        # Convert to lowercase
        text = text.lower().strip()
        
        return text
    
    def advanced_clean_text(self, text: str) -> str:
        """
        Advanced text cleaning for ML processing
        
        Args:
            text: Raw tweet text
            
        Returns:
            Heavily cleaned text for ML models
        """
        if not isinstance(text, str):
            return ""
        
        # Basic cleaning
        text = self.clean_tweet_text(text)
        
        # Remove hashtags and mentions completely
        text = re.sub(r'#\w+|@\w+', '', text)
        
        # Remove numbers
        text = re.sub(r'\d+', '', text)
        
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and short words
        tokens = [word for word in tokens if word not in self.stop_words and len(word) > 2]
        
        # Lemmatize
        tokens = [self.lemmatizer.lemmatize(word) for word in tokens]
        
        return ' '.join(tokens)
    
    def extract_features(self, text: str) -> Dict[str, Any]:
        """
        Extract various features from tweet text
        
        Args:
            text: Tweet text
            
        Returns:
            Dictionary of extracted features
        """
        if not isinstance(text, str):
            text = ""
        
        features = {
            'char_count': len(text),
            'word_count': len(text.split()),
            'hashtag_count': len(re.findall(r'#\w+', text)),
            'mention_count': len(re.findall(r'@\w+', text)),
            'url_count': len(re.findall(r'http\S+|www\S+|https\S+', text)),
            'exclamation_count': text.count('!'),
            'question_count': text.count('?'),
            'uppercase_count': sum(1 for c in text if c.isupper()),
            'has_emoji': bool(re.search(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', text)),
            'avg_word_length': sum(len(word) for word in text.split()) / max(len(text.split()), 1)
        }
        
        return features
    
    def preprocess_tweet(self, tweet_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete preprocessing pipeline for a tweet
        
        Args:
            tweet_data: Raw tweet data dictionary
            
        Returns:
            Processed tweet data dictionary
        """
        try:
            # Extract original text
            original_text = tweet_data.get('text', '')
            
            # Clean the text (basic cleaning)
            cleaned_text = self.clean_tweet_text(original_text)
            
            # Advanced cleaning for ML
            ml_text = self.advanced_clean_text(original_text)
            
            # Extract features
            features = self.extract_features(original_text)
            
            # Tokenize cleaned text
            tokens = word_tokenize(cleaned_text)
            filtered_tokens = [word for word in tokens if word not in self.stop_words and len(word) > 2]
            
            # Update tweet data with processed fields
            tweet_data.update({
                'original_text': original_text,
                'cleaned_text': cleaned_text,
                'ml_text': ml_text,
                'tokens': filtered_tokens,
                'token_count': len(filtered_tokens),
                'processed_at': datetime.now().isoformat(),
                **features  # Unpack all features
            })
            
            # Ensure hashtags, mentions, urls are extracted if not already
            if 'hashtags' not in tweet_data:
                tweet_data['hashtags'] = self._extract_hashtags(original_text)
            if 'mentions' not in tweet_data:
                tweet_data['mentions'] = self._extract_mentions(original_text)
            if 'urls' not in tweet_data:
                tweet_data['urls'] = self._extract_urls(original_text)
            
            return tweet_data
            
        except Exception as e:
            self.logger.error(f"Error preprocessing tweet: {str(e)}")
            return tweet_data
    
    def batch_preprocess(self, tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Preprocess a batch of tweets
        
        Args:
            tweets: List of tweet dictionaries
            
        Returns:
            List of processed tweet dictionaries
        """
        processed_tweets = []
        
        for i, tweet in enumerate(tweets):
            try:
                processed_tweet = self.preprocess_tweet(tweet)
                processed_tweets.append(processed_tweet)
                
                # Progress logging
                if (i + 1) % 100 == 0:
                    self.logger.info(f"Processed {i + 1}/{len(tweets)} tweets")
                    
            except Exception as e:
                self.logger.error(f"Error processing tweet {i}: {str(e)}")
                continue
        
        self.logger.info(f"Successfully processed {len(processed_tweets)}/{len(tweets)} tweets")
        return processed_tweets
    
    def create_dataframe(self, tweets: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert processed tweets to pandas DataFrame
        
        Args:
            tweets: List of processed tweet dictionaries
            
        Returns:
            pandas DataFrame
        """
        try:
            df = pd.DataFrame(tweets)
            
            # Convert datetime columns
            if 'created_at' in df.columns:
                df['created_at'] = pd.to_datetime(df['created_at'])
            if 'processed_at' in df.columns:
                df['processed_at'] = pd.to_datetime(df['processed_at'])
            
            # Extract public metrics if nested
            if 'public_metrics' in df.columns:
                metrics_df = pd.json_normalize(df['public_metrics'])
                df = pd.concat([df.drop('public_metrics', axis=1), metrics_df], axis=1)
            
            self.logger.info(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")
            return df
            
        except Exception as e:
            self.logger.error(f"Error creating DataFrame: {str(e)}")
            return pd.DataFrame()
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text"""
        return re.findall(r'#\w+', text.lower())
    
    def _extract_mentions(self, text: str) -> List[str]:
        """Extract user mentions from text"""
        return re.findall(r'@\w+', text.lower())
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        return re.findall(r'http\S+|www\S+|https\S+', text)
    
    def get_processing_stats(self, tweets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about processed tweets
        
        Args:
            tweets: List of processed tweet dictionaries
            
        Returns:
            Dictionary of processing statistics
        """
        if not tweets:
            return {}
        
        df = self.create_dataframe(tweets)
        
        stats = {
            'total_tweets': len(tweets),
            'avg_char_count': df['char_count'].mean() if 'char_count' in df.columns else 0,
            'avg_word_count': df['word_count'].mean() if 'word_count' in df.columns else 0,
            'total_hashtags': df['hashtag_count'].sum() if 'hashtag_count' in df.columns else 0,
            'total_mentions': df['mention_count'].sum() if 'mention_count' in df.columns else 0,
            'tweets_with_urls': df['url_count'].gt(0).sum() if 'url_count' in df.columns else 0,
            'tweets_with_hashtags': df['hashtag_count'].gt(0).sum() if 'hashtag_count' in df.columns else 0,
            'tweets_with_mentions': df['mention_count'].gt(0).sum() if 'mention_count' in df.columns else 0,
        }
        
        return stats


# Example usage and testing
if __name__ == "__main__":
    # Test the preprocessor
    processor = TweetPreprocessor()
    
    # Sample tweet data
    sample_tweets = [
        {
            'id': 1,
            'text': "Just loving the new #AI advancements! Check out this link: https://example.com @OpenAI is doing amazing work! 🚀",
            'created_at': '2023-10-27T10:00:00Z'
        },
        {
            'id': 2,
            'text': "RT @user: Machine Learning is the future! #MachineLearning #DataScience #AI",
            'created_at': '2023-10-27T11:00:00Z'
        }
    ]
    
    # Process tweets
    processed_tweets = processor.batch_preprocess(sample_tweets)
    
    # Show results
    for tweet in processed_tweets:
        print(f"Original: {tweet['text'][:50]}...")
        print(f"Cleaned: {tweet['cleaned_text']}")
        print(f"ML Text: {tweet['ml_text']}")
        print(f"Features: {tweet['char_count']} chars, {tweet['hashtag_count']} hashtags")
        print("---")
    
    # Get stats
    stats = processor.get_processing_stats(processed_tweets)
    print(f"Processing stats: {stats}")
