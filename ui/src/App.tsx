import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import {
  Activity, ArrowUpRight, MessageSquare, Sun, Moon,
  TrendingUp, BarChart3, List
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { supabase } from './supabaseClient';

// Helper for tailwind-like class merging
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Interfaces
interface EmotionScores {
  joy: number;
  sadness: number;
  anger: number;
  fear: number;
  love: number;
  unknown: number;
}

interface EmotionPrediction {
  label: string;
  score: number;
  raw_scores: EmotionScores;
}

interface RedditPost {
  id: string;
  text: string;
  raw_text: string;
  timestamp: string;
  platform: string;
  engagement: {
    score: number;
    num_comments: number;
  };
  meta: {
    subreddit: string;
  };
  emotion_prediction: EmotionPrediction;
}

const EMOTION_COLORS: Record<string, string> = {
  joy: '#d4af37',
  anger: '#ef4444',
  fear: '#8b5cf6',
  sadness: '#3b82f6',
  love: '#ec4899',
  unknown: '#6b7280',
};

export default function App() {
  const [data, setData] = useState<RedditPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const [lastUpdate, setLastUpdate] = useState<string>('');

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      // Fetch latest 500 posts from Supabase
      const { data: posts, error } = await supabase
        .from('reddit_posts')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(500);

      if (error) throw error;

      if (posts) {
        // Map data back to our preferred structure if needed
        const parsedData = posts.map(p => ({
          ...p.raw_data,
          // Ensure values from flat columns take precedence or match
          emotion_prediction: {
            label: p.emotion_label,
            score: p.emotion_score,
            raw_scores: p.raw_data.emotion_prediction.raw_scores
          }
        })) as RedditPost[];

        setData(parsedData);
        setLastUpdate(new Date().toLocaleTimeString());
      }
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data from Supabase:', error);
      setLoading(false);
    }
  };

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  // Analytics Helpers
  const emotionDistribution = data.reduce((acc, post) => {
    const label = post.emotion_prediction.label;
    acc[label] = (acc[label] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const pieData = Object.entries(emotionDistribution)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);

  const subredditStats = data.reduce((acc, post) => {
    const sub = post.meta.subreddit;
    if (!acc[sub]) acc[sub] = { sub, count: 0, joy: 0, anger: 0, sadness: 0, fear: 0, love: 0 };
    acc[sub].count++;
    const emotion = post.emotion_prediction.label;
    if (acc[sub][emotion as keyof typeof acc[typeof sub]] !== undefined) {
      (acc[sub][emotion as keyof typeof acc[typeof sub]])++;
    }
    return acc;
  }, {} as Record<string, any>);

  const barData = Object.values(subredditStats).sort((a: any, b: any) => b.count - a.count).slice(0, 8);

  if (loading && data.length === 0) {
    return (
      <div className="loader-container">
        <div className="spinner"></div>
        <p className="metric-label">Connecting to Supabase...</p>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      {/* Header */}
      <header className="header">
        <div className="brand">
          <div className="logo-icon">
            <TrendingUp size={24} />
          </div>
          <div className="title-group">
            <h1>Reddit Emotional Analyzer</h1>
            <div className="status-badge">
              <div className="pulse"></div>
              Cloud Database Active
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <p className="metric-label">Last updated: {lastUpdate}</p>
          <button className="theme-toggle" onClick={toggleTheme}>
            {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
          </button>
        </div>
      </header>

      {/* Hero Stats */}
      <section className="grid grid-cols-4">
        <div className="glass-card metric-card">
          <span className="metric-label">Total Analyzed</span>
          <span className="metric-value">{data.length}</span>
        </div>
        <div className="glass-card metric-card">
          <span className="metric-label">Active Subreddits</span>
          <span className="metric-value">{Object.keys(subredditStats).length}</span>
        </div>
        <div className="glass-card metric-card">
          <span className="metric-label">Dominant Emotion</span>
          <span className="metric-value" style={{ color: EMOTION_COLORS[pieData[0]?.name] || 'var(--reddit-orange)', textTransform: 'capitalize' }}>
            {pieData[0]?.name || 'N/A'}
          </span>
        </div>
        <div className="glass-card metric-card">
          <span className="metric-label">DB Status</span>
          <span className="metric-value" style={{ color: '#22c55e' }}>Online</span>
        </div>
      </section>

      {/* Analytics Section */}
      <section className="grid grid-cols-2">
        <div className="glass-card">
          <h2><Activity size={20} color="var(--reddit-orange)" /> Overall Emotion Distribution</h2>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={EMOTION_COLORS[entry.name] || '#ccc'} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    borderRadius: '12px',
                    border: 'none',
                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
                    backgroundColor: 'var(--reddit-card-bg)',
                    color: 'var(--reddit-text)'
                  }}
                />
                <Legend verticalAlign="bottom" height={36} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card">
          <h2><BarChart3 size={20} color="var(--reddit-orange)" /> Top Subreddits by Sentiment</h2>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData}>
                <XAxis dataKey="sub" stroke="var(--reddit-text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip
                  cursor={{ fill: 'rgba(0,0,0,0.05)' }}
                  contentStyle={{
                    borderRadius: '12px',
                    border: 'none',
                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
                    backgroundColor: 'var(--reddit-card-bg)'
                  }}
                />
                <Bar dataKey="joy" stackId="a" fill={EMOTION_COLORS.joy} radius={[0, 0, 0, 0]} />
                <Bar dataKey="anger" stackId="a" fill={EMOTION_COLORS.anger} />
                <Bar dataKey="fear" stackId="a" fill={EMOTION_COLORS.fear} />
                <Bar dataKey="sadness" stackId="a" fill={EMOTION_COLORS.sadness} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      {/* Feed Section */}
      <section>
        <h2><List size={20} color="var(--reddit-orange)" /> Recent Social Trends</h2>
        <div className="grid">
          {data.slice(0, 10).map((post) => (
            <div key={post.id} className="glass-card post-card">
              <div className="post-header">
                <span className="subreddit-name">r/{post.meta.subreddit}</span>
                <span className={cn("emotion-tag", `tag-${post.emotion_prediction.label}`)}>
                  {post.emotion_prediction.label}
                </span>
              </div>
              <p className="post-content">{post.text}</p>
              <div className="post-footer">
                <div className="interaction-item">
                  <ArrowUpRight size={16} />
                  {post.engagement.score?.toLocaleString() || 0}
                </div>
                <div className="interaction-item">
                  <MessageSquare size={16} />
                  {post.engagement.num_comments?.toLocaleString() || 0}
                </div>
                <div className="interaction-item" style={{ marginLeft: 'auto' }}>
                  {new Date(post.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
