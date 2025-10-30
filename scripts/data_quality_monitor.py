#!/usr/bin/env python3
"""Data Quality Monitoring and Validation"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import logging
import json
import os

class DataQualityMonitor:
    """Monitor and validate data quality for tweet collection"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        logger = logging.getLogger('DataQualityMonitor')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        if not logger.handlers:
            logger.addHandler(handler)
        return logger
    
    def comprehensive_quality_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive data quality checks
        """
        self.logger.info("🔍 Starting comprehensive data quality check...")
        
        quality_report = {
            'timestamp': datetime.now().isoformat(),
            'completeness_check': self._check_data_completeness(),
            'consistency_check': self._check_data_consistency(),
            'accuracy_check': self._check_data_accuracy(),
            'uniqueness_check': self._check_data_uniqueness(),
            'timeliness_check': self._check_data_timeliness(),
            'validity_check': self._check_data_validity(),
            'anomaly_detection': self._detect_anomalies(),
            'overall_score': 0.0,
            'recommendations': []
        }
        
        # Calculate overall quality score
        quality_report['overall_score'] = self._calculate_overall_score(quality_report)
        
        # Generate recommendations
        quality_report['recommendations'] = self._generate_recommendations(quality_report)
        
        # Save report
        self._save_quality_report(quality_report)
        
        # Print summary
        self._print_quality_summary(quality_report)
        
        return quality_report
    
    def _check_data_completeness(self) -> Dict[str, Any]:
        """Check for missing or null values"""
        query = """
        SELECT 
            COUNT(*) as total_tweets,
            COUNT(CASE WHEN original_text IS NULL OR original_text = '' THEN 1 END) as missing_text,
            COUNT(CASE WHEN author_id IS NULL THEN 1 END) as missing_author,
            COUNT(CASE WHEN created_at IS NULL THEN 1 END) as missing_timestamp,
            COUNT(CASE WHEN processed = FALSE THEN 1 END) as unprocessed_tweets
        FROM tweets
        WHERE created_at >= NOW() - INTERVAL '7 days'
        """
        
        with self.db_manager.pg_connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result:
                total, missing_text, missing_author, missing_timestamp, unprocessed = result
                
                completeness_score = 100.0
                if total > 0:
                    completeness_score = max(0, 100 - (
                        (missing_text + missing_author + missing_timestamp) / total * 100
                    ))
                
                return {
                    'score': completeness_score,
                    'total_tweets': total,
                    'missing_text_count': missing_text,
                    'missing_author_count': missing_author,
                    'missing_timestamp_count': missing_timestamp,
                    'unprocessed_count': unprocessed,
                    'completeness_percentage': completeness_score
                }
        
        return {'score': 0, 'error': 'Could not check data completeness'}
    
    def _check_data_consistency(self) -> Dict[str, Any]:
        """Check for data consistency issues"""
        consistency_checks = {}
        
        # Check timestamp consistency
        query = """
        SELECT COUNT(*) as future_tweets
        FROM tweets 
        WHERE created_at > NOW()
        """
        
        with self.db_manager.pg_connection.cursor() as cursor:
            cursor.execute(query)
            future_tweets = cursor.fetchone()[0]
            
            # Check for duplicate processing
            cursor.execute("""
                SELECT COUNT(*) as total, COUNT(DISTINCT id) as unique_ids
                FROM tweets
                WHERE created_at >= NOW() - INTERVAL '7 days'
            """)
            
            total, unique_ids = cursor.fetchone()
            duplicates = total - unique_ids
            
            # Check character count consistency
            cursor.execute("""
                SELECT COUNT(*) as inconsistent_char_count
                FROM tweets 
                WHERE char_count != LENGTH(original_text)
                AND char_count IS NOT NULL
                AND original_text IS NOT NULL
            """)
            
            inconsistent_chars = cursor.fetchone()[0]
            
            # Calculate consistency score
            total_issues = future_tweets + duplicates + inconsistent_chars
            consistency_score = max(0, 100 - (total_issues / max(total, 1) * 100))
            
            return {
                'score': consistency_score,
                'future_tweets': future_tweets,
                'duplicate_tweets': duplicates,
                'inconsistent_char_counts': inconsistent_chars,
                'total_consistency_issues': total_issues
            }
    
    def _check_data_accuracy(self) -> Dict[str, Any]:
        """Check data accuracy against expected patterns"""
        query = """
        SELECT 
            COUNT(*) as total_tweets,
            COUNT(CASE WHEN char_count < 1 OR char_count > 280 THEN 1 END) as invalid_length,
            COUNT(CASE WHEN hashtag_count < 0 THEN 1 END) as negative_hashtags,
            COUNT(CASE WHEN mention_count < 0 THEN 1 END) as negative_mentions,
            COUNT(CASE WHEN like_count < 0 OR retweet_count < 0 THEN 1 END) as negative_engagement
        FROM tweets 
        WHERE created_at >= NOW() - INTERVAL '7 days'
        """
        
        with self.db_manager.pg_connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result:
                total, invalid_length, neg_hashtags, neg_mentions, neg_engagement = result
                
                total_accuracy_issues = invalid_length + neg_hashtags + neg_mentions + neg_engagement
                accuracy_score = max(0, 100 - (total_accuracy_issues / max(total, 1) * 100))
                
                return {
                    'score': accuracy_score,
                    'total_tweets': total,
                    'invalid_length_count': invalid_length,
                    'negative_hashtag_count': neg_hashtags,
                    'negative_mention_count': neg_mentions,
                    'negative_engagement_count': neg_engagement,
                    'total_accuracy_issues': total_accuracy_issues
                }
        
        return {'score': 0, 'error': 'Could not check data accuracy'}
    
    def _check_data_uniqueness(self) -> Dict[str, Any]:
        """Check for duplicate data"""
        query = """
        SELECT 
            COUNT(*) as total_tweets,
            COUNT(DISTINCT id) as unique_tweets,
            COUNT(*) - COUNT(DISTINCT id) as duplicate_count
        FROM tweets 
        WHERE created_at >= NOW() - INTERVAL '7 days'
        """
        
        with self.db_manager.pg_connection.cursor() as cursor:
            cursor.execute(query)
            total, unique, duplicates = cursor.fetchone()
            
            uniqueness_score = (unique / max(total, 1)) * 100
            
            return {
                'score': uniqueness_score,
                'total_tweets': total,
                'unique_tweets': unique,
                'duplicate_count': duplicates,
                'uniqueness_percentage': uniqueness_score
            }
    
    def _check_data_timeliness(self) -> Dict[str, Any]:
        """Check data freshness and collection patterns"""
        query = """
        SELECT 
            COUNT(*) as total_tweets,
            COUNT(CASE WHEN created_at >= NOW() - INTERVAL '1 hour' THEN 1 END) as last_hour,
            COUNT(CASE WHEN created_at >= NOW() - INTERVAL '24 hours' THEN 1 END) as last_24_hours,
            MAX(created_at) as latest_tweet,
            MIN(created_at) as oldest_tweet
        FROM tweets
        """
        
        with self.db_manager.pg_connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result:
                total, last_hour, last_24_hours, latest, oldest = result
                
                # Calculate timeliness score based on recent activity
                now = datetime.now()
                if latest:
                    hours_since_latest = (now - latest).total_seconds() / 3600
                    timeliness_score = max(0, 100 - (hours_since_latest * 2))  # Penalty for old data
                else:
                    timeliness_score = 0
                
                return {
                    'score': timeliness_score,
                    'total_tweets': total,
                    'tweets_last_hour': last_hour,
                    'tweets_last_24_hours': last_24_hours,
                    'latest_tweet_time': latest.isoformat() if latest else None,
                    'oldest_tweet_time': oldest.isoformat() if oldest else None,
                    'hours_since_latest': hours_since_latest if latest else None
                }
        
        return {'score': 0, 'error': 'Could not check data timeliness'}
    
    def _check_data_validity(self) -> Dict[str, Any]:
        """Check data format validity"""
        query = """
        SELECT 
            COUNT(*) as total_tweets,
            COUNT(CASE WHEN CAST(author_id AS TEXT) ~ '^[0-9]+$' THEN 1 ELSE 0 END) as valid_author_ids,
            COUNT(CASE WHEN original_text ~ '[a-zA-Z]' THEN 1 ELSE 0 END) as tweets_with_text,
            COUNT(CASE WHEN hashtag_count >= 0 AND hashtag_count <= 50 THEN 1 ELSE 0 END) as valid_hashtag_counts
        FROM tweets 
        WHERE created_at >= NOW() - INTERVAL '7 days'
        AND original_text IS NOT NULL
        """
        
        with self.db_manager.pg_connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result:
                total, valid_authors, valid_text, valid_hashtags = result
                
                validity_score = 0
                if total > 0:
                    validity_score = (
                        (valid_authors + valid_text + valid_hashtags) / (total * 3)
                    ) * 100
                
                return {
                    'score': validity_score,
                    'total_tweets': total,
                    'valid_author_ids': valid_authors,
                    'tweets_with_text': valid_text,
                    'valid_hashtag_counts': valid_hashtags,
                    'validity_percentage': validity_score
                }
        
        return {'score': 0, 'error': 'Could not check data validity'}
    
    def _detect_anomalies(self) -> Dict[str, Any]:
        """Detect anomalies in the data"""
        # Get recent tweet volumes by hour
        query = """
        SELECT 
            DATE_TRUNC('hour', created_at) as hour,
            COUNT(*) as tweet_count,
            AVG(char_count) as avg_length,
            AVG(like_count) as avg_likes
        FROM tweets 
        WHERE created_at >= NOW() - INTERVAL '7 days'
        GROUP BY DATE_TRUNC('hour', created_at)
        ORDER BY hour
        """
        
        anomalies = {
            'volume_anomalies': [],
            'engagement_anomalies': [],
            'length_anomalies': [],
            'anomaly_score': 100
        }
        
        with self.db_manager.pg_connection.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            
            if len(results) > 24:  # Need at least 24 hours of data
                volumes = [row[1] for row in results]
                lengths = [row[2] for row in results if row[2]]
                likes = [row[3] for row in results if row[3]]
                
                # Simple anomaly detection using z-score
                if volumes:
                    volume_mean = np.mean(volumes)
                    volume_std = np.std(volumes)
                    
                    for i, (hour, count, length, like_avg) in enumerate(results):
                        if volume_std > 0:
                            z_score = abs((count - volume_mean) / volume_std)
                            if z_score > 3:  # Anomaly threshold
                                anomalies['volume_anomalies'].append({
                                    'hour': hour.isoformat(),
                                    'tweet_count': count,
                                    'z_score': z_score,
                                    'type': 'high' if count > volume_mean else 'low'
                                })
                
                # Calculate anomaly score (fewer anomalies = higher score)
                total_anomalies = len(anomalies['volume_anomalies'])
                anomalies['anomaly_score'] = max(0, 100 - (total_anomalies * 5))
        
        return anomalies
    
    def _calculate_overall_score(self, quality_report: Dict[str, Any]) -> float:
        """Calculate overall data quality score"""
        scores = []
        weights = {
            'completeness_check': 0.25,
            'consistency_check': 0.20,
            'accuracy_check': 0.20,
            'uniqueness_check': 0.15,
            'timeliness_check': 0.10,
            'validity_check': 0.10
        }
        
        for check_name, weight in weights.items():
            check_result = quality_report.get(check_name, {})
            score = check_result.get('score', 0)
            scores.append(score * weight)
        
        return sum(scores)
    
    def _generate_recommendations(self, quality_report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on quality issues"""
        recommendations = []
        
        # Completeness recommendations
        completeness = quality_report.get('completeness_check', {})
        if completeness.get('score', 100) < 90:
            recommendations.append("🔧 Improve data collection to reduce missing values")
            if completeness.get('unprocessed_count', 0) > 0:
                recommendations.append("⚡ Process pending tweets to improve completeness")
        
        # Consistency recommendations
        consistency = quality_report.get('consistency_check', {})
        if consistency.get('future_tweets', 0) > 0:
            recommendations.append("🕐 Fix timestamp handling to prevent future dates")
        if consistency.get('duplicate_tweets', 0) > 0:
            recommendations.append("🔄 Implement deduplication logic")
        
        # Timeliness recommendations
        timeliness = quality_report.get('timeliness_check', {})
        if timeliness.get('score', 100) < 80:
            recommendations.append("⏰ Increase collection frequency for fresher data")
        
        # Anomaly recommendations
        anomalies = quality_report.get('anomaly_detection', {})
        if len(anomalies.get('volume_anomalies', [])) > 3:
            recommendations.append("📊 Investigate volume anomalies in data collection")
        
        # Overall score recommendations
        overall_score = quality_report.get('overall_score', 0)
        if overall_score < 70:
            recommendations.append("🚨 Data quality needs immediate attention")
        elif overall_score < 85:
            recommendations.append("⚠️ Consider implementing additional quality controls")
        else:
            recommendations.append("✅ Data quality is good, maintain current practices")
        
        return recommendations
    
    def _save_quality_report(self, quality_report: Dict[str, Any]):
        """Save quality report to file"""
        os.makedirs('logs', exist_ok=True)
        filename = f"logs/data_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(quality_report, f, indent=2, default=str)
        
        self.logger.info(f"📊 Data quality report saved to: {filename}")
    
    def _print_quality_summary(self, quality_report: Dict[str, Any]):
        """Print quality summary"""
        print("\n" + "="*60)
        print("🔍 DATA QUALITY ASSESSMENT SUMMARY")
        print("="*60)
        
        overall_score = quality_report.get('overall_score', 0)
        print(f"📊 Overall Quality Score: {overall_score:.1f}/100")
        
        # Score interpretation
        if overall_score >= 90:
            print("✅ Excellent data quality")
        elif overall_score >= 80:
            print("👍 Good data quality")
        elif overall_score >= 70:
            print("⚠️  Acceptable data quality")
        else:
            print("🚨 Poor data quality - needs attention")
        
        print(f"\n📈 DETAILED SCORES:")
        
        checks = [
            ('completeness_check', 'Completeness'),
            ('consistency_check', 'Consistency'),
            ('accuracy_check', 'Accuracy'),
            ('uniqueness_check', 'Uniqueness'),
            ('timeliness_check', 'Timeliness'),
            ('validity_check', 'Validity')
        ]
        
        for check_key, check_name in checks:
            check_result = quality_report.get(check_key, {})
            score = check_result.get('score', 0)
            print(f"  {check_name}: {score:.1f}/100")
        
        # Key metrics
        completeness = quality_report.get('completeness_check', {})
        print(f"\n📋 KEY METRICS:")
        print(f"  Total Tweets (7 days): {completeness.get('total_tweets', 0)}")
        print(f"  Missing Data Issues: {completeness.get('missing_text_count', 0) + completeness.get('missing_author_count', 0)}")
        
        # Recommendations
        recommendations = quality_report.get('recommendations', [])
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"  {i}. {rec}")
        
        print("="*60)


if __name__ == "__main__":
    import sys
    import os
    
    # Add parent directory to path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from data_collector.database import PostgreSQLManager
    
    print("🔍 Starting Data Quality Assessment...")
    
    # Initialize
    db_manager = PostgreSQLManager()
    monitor = DataQualityMonitor(db_manager)
    
    # Run comprehensive quality check
    quality_report = monitor.comprehensive_quality_check()
    
    print("✅ Data quality assessment completed!")
