-- ============================================================
-- 金宫味业数字营销数据中台 - MySQL 建表脚本
-- 开发环境: SQLite | 生产环境: MySQL 8.0+
-- ============================================================

CREATE DATABASE IF NOT EXISTS jingong_marketing
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE jingong_marketing;

-- 平台数据 (微博热搜、抖音、小红书等)
CREATE TABLE platform_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    platform VARCHAR(32) NOT NULL COMMENT '数据平台',
    data_type VARCHAR(32) NOT NULL DEFAULT 'social_post' COMMENT '数据类型: hot_search/social_post',
    content TEXT COMMENT '内容',
    author VARCHAR(128) DEFAULT '' COMMENT '作者/来源',
    likes INT DEFAULT 0 COMMENT '点赞数',
    comments INT DEFAULT 0 COMMENT '评论数',
    shares INT DEFAULT 0 COMMENT '分享数',
    publish_time DATETIME COMMENT '发布时间',
    crawl_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '采集时间',
    sentiment VARCHAR(16) DEFAULT 'neutral' COMMENT '情感: positive/negative/neutral',
    content_type VARCHAR(32) DEFAULT 'other' COMMENT '内容类型: 测评/review/促销/promo',
    raw_json JSON COMMENT '原始JSON数据',
    data_source VARCHAR(64) DEFAULT 'simulated' COMMENT '数据来源标识',
    INDEX idx_platform (platform),
    INDEX idx_crawl_time (crawl_time),
    INDEX idx_sentiment (sentiment)
) ENGINE=InnoDB COMMENT='爬取的平台数据';

-- 竞品监控
CREATE TABLE competitor_monitor (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    brand VARCHAR(64) NOT NULL COMMENT '品牌名称',
    platform VARCHAR(32) NOT NULL COMMENT '平台',
    product_name VARCHAR(256) COMMENT '商品名称',
    price DECIMAL(10,2) COMMENT '价格',
    promo_info VARCHAR(256) COMMENT '促销信息',
    rating DECIMAL(3,1) DEFAULT 0.0 COMMENT '评分',
    review_count INT DEFAULT 0 COMMENT '评价数',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    data_source VARCHAR(64) DEFAULT 'simulated' COMMENT '数据来源',
    INDEX idx_brand (brand),
    INDEX idx_price (price),
    INDEX idx_update_time (update_time)
) ENGINE=InnoDB COMMENT='竞品商品监控';

-- 舆情趋势
CREATE TABLE sentiment_trend (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    keyword VARCHAR(128) NOT NULL COMMENT '关键词',
    platform VARCHAR(32) NOT NULL COMMENT '平台',
    mention_count INT DEFAULT 0 COMMENT '提及数量',
    positive_ratio DECIMAL(5,4) DEFAULT 0 COMMENT '正面占比',
    negative_ratio DECIMAL(5,4) DEFAULT 0 COMMENT '负面占比',
    neutral_ratio DECIMAL(5,4) DEFAULT 0 COMMENT '中性占比',
    record_date DATE COMMENT '记录日期',
    data_source VARCHAR(64) DEFAULT 'AI模拟分析' COMMENT '数据来源',
    INDEX idx_keyword (keyword),
    INDEX idx_record_date (record_date)
) ENGINE=InnoDB COMMENT='舆情情感趋势';

-- AI报告历史
CREATE TABLE report_history (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    report_type VARCHAR(16) NOT NULL COMMENT '报告类型: daily/weekly',
    content TEXT COMMENT '报告HTML内容',
    generated_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
    INDEX idx_generated_time (generated_time)
) ENGINE=InnoDB COMMENT='AI报告历史';

-- 爬取任务记录
CREATE TABLE scrape_tasks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    platform VARCHAR(64) NOT NULL COMMENT '爬取目标',
    status VARCHAR(16) DEFAULT 'pending' COMMENT '状态: pending/running/completed/failed',
    start_time DATETIME COMMENT '开始时间',
    end_time DATETIME COMMENT '结束时间',
    records_fetched INT DEFAULT 0 COMMENT '获取记录数',
    error_msg TEXT COMMENT '错误信息',
    INDEX idx_status (status),
    INDEX idx_start_time (start_time)
) ENGINE=InnoDB COMMENT='爬取任务记录';

-- 用户订阅 (预留)
CREATE TABLE user_subscription (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    openid VARCHAR(64) NOT NULL COMMENT '微信OpenID',
    keywords VARCHAR(512) COMMENT '订阅关键词(JSON数组)',
    brands VARCHAR(512) COMMENT '关注品牌(JSON数组)',
    notify_enabled TINYINT(1) DEFAULT 1 COMMENT '是否开启通知',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_openid (openid)
) ENGINE=InnoDB COMMENT='用户订阅配置';
