-- 初始化資料庫腳本
-- Database Initialization Script

-- 創建監控記錄表
CREATE TABLE IF NOT EXISTS monitoring_records (
    id BIGSERIAL PRIMARY KEY,
    request_id VARCHAR(50) NOT NULL,
    member_code VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 品質指標
    overall_score FLOAT NOT NULL,
    relevance_score FLOAT NOT NULL,
    novelty_score FLOAT NOT NULL,
    explainability_score FLOAT NOT NULL,
    diversity_score FLOAT NOT NULL,
    
    -- 性能指標
    total_time_ms FLOAT NOT NULL,
    feature_loading_ms FLOAT DEFAULT 0,
    model_inference_ms FLOAT DEFAULT 0,
    reason_generation_ms FLOAT DEFAULT 0,
    quality_evaluation_ms FLOAT DEFAULT 0,
    
    -- 元資料
    recommendation_count INTEGER NOT NULL,
    strategy_used VARCHAR(50) NOT NULL,
    is_degraded BOOLEAN DEFAULT FALSE,
    
    -- 索引
    CONSTRAINT monitoring_records_request_id_key UNIQUE (request_id)
);

-- 創建索引
CREATE INDEX IF NOT EXISTS idx_monitoring_records_timestamp ON monitoring_records(timestamp);
CREATE INDEX IF NOT EXISTS idx_monitoring_records_member_code ON monitoring_records(member_code);
CREATE INDEX IF NOT EXISTS idx_monitoring_records_overall_score ON monitoring_records(overall_score);
CREATE INDEX IF NOT EXISTS idx_monitoring_records_is_degraded ON monitoring_records(is_degraded);

-- 創建告警記錄表
CREATE TABLE IF NOT EXISTS alert_records (
    id BIGSERIAL PRIMARY KEY,
    alert_level VARCHAR(20) NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    current_value FLOAT NOT NULL,
    threshold_value FLOAT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(50)
);

-- 創建索引
CREATE INDEX IF NOT EXISTS idx_alert_records_timestamp ON alert_records(timestamp);
CREATE INDEX IF NOT EXISTS idx_alert_records_alert_level ON alert_records(alert_level);
CREATE INDEX IF NOT EXISTS idx_alert_records_is_resolved ON alert_records(is_resolved);
CREATE INDEX IF NOT EXISTS idx_alert_records_metric_name ON alert_records(metric_name);

-- 創建 A/B 測試記錄表
CREATE TABLE IF NOT EXISTS ab_test_records (
    id BIGSERIAL PRIMARY KEY,
    test_id VARCHAR(50) NOT NULL,
    member_code VARCHAR(20) NOT NULL,
    group_name VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 推薦結果
    recommendations JSONB,
    
    -- 品質指標
    overall_score FLOAT,
    relevance_score FLOAT,
    novelty_score FLOAT,
    explainability_score FLOAT,
    diversity_score FLOAT,
    
    -- 性能指標
    total_time_ms FLOAT,
    
    -- 用戶行為（可選）
    clicked_products JSONB,
    purchased_products JSONB,
    
    CONSTRAINT ab_test_records_unique_key UNIQUE (test_id, member_code)
);

-- 創建索引
CREATE INDEX IF NOT EXISTS idx_ab_test_records_test_id ON ab_test_records(test_id);
CREATE INDEX IF NOT EXISTS idx_ab_test_records_member_code ON ab_test_records(member_code);
CREATE INDEX IF NOT EXISTS idx_ab_test_records_group_name ON ab_test_records(group_name);
CREATE INDEX IF NOT EXISTS idx_ab_test_records_timestamp ON ab_test_records(timestamp);

-- 創建會員特徵快取表（可選）
CREATE TABLE IF NOT EXISTS member_features_cache (
    member_code VARCHAR(20) PRIMARY KEY,
    features JSONB NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

-- 創建索引
CREATE INDEX IF NOT EXISTS idx_member_features_cache_expires_at ON member_features_cache(expires_at);

-- 創建產品資訊快取表（可選）
CREATE TABLE IF NOT EXISTS product_info_cache (
    product_id VARCHAR(20) PRIMARY KEY,
    product_info JSONB NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

-- 創建索引
CREATE INDEX IF NOT EXISTS idx_product_info_cache_expires_at ON product_info_cache(expires_at);

-- 創建系統配置表
CREATE TABLE IF NOT EXISTS system_config (
    config_key VARCHAR(100) PRIMARY KEY,
    config_value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

-- 插入預設配置
INSERT INTO system_config (config_key, config_value, description) VALUES
    ('quality_thresholds', '{"overall_score": {"critical": 40, "warning": 50, "target": 60}}', '品質閾值配置'),
    ('performance_thresholds', '{"total_time_ms": {"p50": 200, "p95": 500, "p99": 1000}}', '性能閾值配置'),
    ('strategy_weights', '{"collaborative_filtering": 0.4, "content_based": 0.3, "popularity": 0.2, "diversity": 0.1}', '推薦策略權重')
ON CONFLICT (config_key) DO NOTHING;

-- 創建清理過期記錄的函數
CREATE OR REPLACE FUNCTION cleanup_expired_records()
RETURNS void AS $$
BEGIN
    -- 清理 7 天前的監控記錄
    DELETE FROM monitoring_records
    WHERE timestamp < NOW() - INTERVAL '7 days';
    
    -- 清理 90 天前的告警記錄
    DELETE FROM alert_records
    WHERE timestamp < NOW() - INTERVAL '90 days';
    
    -- 清理過期的快取
    DELETE FROM member_features_cache
    WHERE expires_at < NOW();
    
    DELETE FROM product_info_cache
    WHERE expires_at < NOW();
    
    RAISE NOTICE '過期記錄清理完成';
END;
$$ LANGUAGE plpgsql;

-- 創建定時任務（需要 pg_cron 擴展）
-- CREATE EXTENSION IF NOT EXISTS pg_cron;
-- SELECT cron.schedule('cleanup-expired-records', '0 2 * * *', 'SELECT cleanup_expired_records()');

-- 創建視圖：每日品質統計
CREATE OR REPLACE VIEW daily_quality_stats AS
SELECT
    DATE(timestamp) as date,
    COUNT(*) as total_recommendations,
    COUNT(DISTINCT member_code) as unique_members,
    AVG(overall_score) as avg_overall_score,
    AVG(relevance_score) as avg_relevance_score,
    AVG(novelty_score) as avg_novelty_score,
    AVG(explainability_score) as avg_explainability_score,
    AVG(diversity_score) as avg_diversity_score,
    AVG(total_time_ms) as avg_response_time_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_time_ms) as p50_response_time_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_time_ms) as p95_response_time_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY total_time_ms) as p99_response_time_ms,
    SUM(CASE WHEN is_degraded THEN 1 ELSE 0 END) as degradation_count
FROM monitoring_records
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- 創建視圖：每小時品質統計
CREATE OR REPLACE VIEW hourly_quality_stats AS
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as total_recommendations,
    COUNT(DISTINCT member_code) as unique_members,
    AVG(overall_score) as avg_overall_score,
    AVG(relevance_score) as avg_relevance_score,
    AVG(novelty_score) as avg_novelty_score,
    AVG(explainability_score) as avg_explainability_score,
    AVG(diversity_score) as avg_diversity_score,
    AVG(total_time_ms) as avg_response_time_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_time_ms) as p50_response_time_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_time_ms) as p95_response_time_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY total_time_ms) as p99_response_time_ms,
    SUM(CASE WHEN is_degraded THEN 1 ELSE 0 END) as degradation_count
FROM monitoring_records
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC;

-- 授予權限（根據實際用戶調整）
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO recommendation_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO recommendation_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO recommendation_readonly;

-- 完成
SELECT 'Database initialization completed successfully!' as status;
