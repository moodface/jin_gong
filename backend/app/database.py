import sqlite3
from .config import DB_PATH


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS platform_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            data_type TEXT NOT NULL,
            content TEXT,
            author TEXT,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            publish_time TEXT,
            crawl_time TEXT DEFAULT (datetime('now','localtime')),
            sentiment TEXT DEFAULT 'neutral',
            content_type TEXT DEFAULT 'other',
            raw_json TEXT,
            data_source TEXT DEFAULT 'simulated'
        );

        CREATE TABLE IF NOT EXISTS competitor_monitor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            platform TEXT NOT NULL,
            product_name TEXT,
            price REAL,
            promo_info TEXT,
            rating REAL,
            review_count INTEGER DEFAULT 0,
            update_time TEXT DEFAULT (datetime('now','localtime')),
            data_source TEXT DEFAULT 'simulated'
        );

        CREATE TABLE IF NOT EXISTS sentiment_trend (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            platform TEXT NOT NULL,
            mention_count INTEGER DEFAULT 0,
            positive_ratio REAL DEFAULT 0,
            negative_ratio REAL DEFAULT 0,
            neutral_ratio REAL DEFAULT 0,
            record_date TEXT DEFAULT (date('now','localtime')),
            data_source TEXT DEFAULT 'simulated'
        );

        CREATE TABLE IF NOT EXISTS report_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_type TEXT NOT NULL,
            content TEXT,
            sections_json TEXT,
            generated_time TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS scrape_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            start_time TEXT,
            end_time TEXT,
            records_fetched INTEGER DEFAULT 0,
            error_msg TEXT
        );

        CREATE TABLE IF NOT EXISTS user_subscription (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            openid TEXT NOT NULL,
            keywords TEXT,
            brands TEXT,
            notify_enabled INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(openid)
        );
    """)
    conn.commit()
    conn.close()
