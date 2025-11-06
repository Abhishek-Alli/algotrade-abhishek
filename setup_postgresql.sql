-- PostgreSQL Database Setup Script
-- Run this script to create the database and user

-- Create database
CREATE DATABASE trading_db;

-- Create user (optional, can use existing postgres user)
-- CREATE USER trading_user WITH PASSWORD 'your_password';
-- GRANT ALL PRIVILEGES ON DATABASE trading_db TO trading_user;

-- Connect to trading_db and run:
-- \c trading_db

-- Tables will be created automatically by the application
-- But you can also create them manually:

CREATE TABLE IF NOT EXISTS ohlcv_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(20, 8),
    high DECIMAL(20, 8),
    low DECIMAL(20, 8),
    close DECIMAL(20, 8),
    volume DECIMAL(20, 8),
    timeframe VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timestamp, timeframe)
);

CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_timeframe 
ON ohlcv_data(symbol, timeframe, timestamp DESC);

CREATE TABLE IF NOT EXISTS news_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50),
    headline TEXT,
    source VARCHAR(100),
    published_at TIMESTAMP,
    sentiment_score DECIMAL(5, 3),
    content TEXT,
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_news_symbol_published 
ON news_data(symbol, published_at DESC);

CREATE TABLE IF NOT EXISTS sentiment_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50),
    platform VARCHAR(50),
    text TEXT,
    timestamp TIMESTAMP,
    sentiment_score DECIMAL(5, 3),
    engagement_score DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


