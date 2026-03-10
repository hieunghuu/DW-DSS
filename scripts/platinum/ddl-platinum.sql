    -- platinum_promotion_effectiveness
    -- Purpose: Analyze ROI and effectiveness of each markdown type
    CREATE MATERIALIZED VIEW platinum.promotion_effectiveness AS
    SELECT 
        s.store_id,
        st.store_type,
        st.store_size,
        DATE_TRUNC('week', s.date) AS week_start,
        s.department_id,
        
        -- Sales metrics
        SUM(s.weekly_sales) AS total_sales,
        AVG(s.weekly_sales) AS avg_sales,
        
        -- Promotion metrics
        COALESCE(AVG(f.markdown1), 0) AS avg_markdown1,
        COALESCE(AVG(f.markdown2), 0) AS avg_markdown2,
        COALESCE(AVG(f.markdown3), 0) AS avg_markdown3,
        COALESCE(AVG(f.markdown4), 0) AS avg_markdown4,
        COALESCE(AVG(f.markdown5), 0) AS avg_markdown5,
        
        -- Promotion flags
        CASE WHEN AVG(f.markdown1) > 0 THEN TRUE ELSE FALSE END AS has_markdown1,
        CASE WHEN AVG(f.markdown2) > 0 THEN TRUE ELSE FALSE END AS has_markdown2,
        CASE WHEN AVG(f.markdown3) > 0 THEN TRUE ELSE FALSE END AS has_markdown3,
        CASE WHEN AVG(f.markdown4) > 0 THEN TRUE ELSE FALSE END AS has_markdown4,
        CASE WHEN AVG(f.markdown5) > 0 THEN TRUE ELSE FALSE END AS has_markdown5,
        
        -- Calculated KPIs
        SUM(s.weekly_sales) / NULLIF(
            COALESCE(SUM(f.markdown1), 0) + 
            COALESCE(SUM(f.markdown2), 0) + 
            COALESCE(SUM(f.markdown3), 0) + 
            COALESCE(SUM(f.markdown4), 0) + 
            COALESCE(SUM(f.markdown5), 0), 0
        ) AS promotion_roi,
        
        MAX((s.is_holiday)::int) AS has_holiday
        
    FROM silver.sales s
    LEFT JOIN silver.economic_features f ON s.store_id = f.store_id AND s.date = f.date
    LEFT JOIN silver.stores st ON s.store_id = st.store_id AND st.is_current = TRUE
    GROUP BY s.store_id, st.store_type, st.store_size, DATE_TRUNC('week', s.date), s.department_id;

    CREATE INDEX idx_plat_promo_week ON platinum.promotion_effectiveness (week_start);
    CREATE INDEX idx_plat_promo_store ON platinum.promotion_effectiveness (store_id);

    -- platinum_sales_trend_analysis
    -- Purpose: Pre-aggregate sales trends for faster dashboarding
    CREATE MATERIALIZED VIEW platinum.sales_trend_analysis AS
    SELECT 
        s.store_id,
        st.store_type,
        s.department_id,
        DATE_TRUNC('week', s.date) AS week_start,
        DATE_TRUNC('month', s.date) AS month_start,
        DATE_TRUNC('quarter', s.date) AS quarter_start,
        EXTRACT(YEAR FROM s.date) AS year,
        
        -- Sales aggregates
        SUM(s.weekly_sales) AS total_sales,
        AVG(s.weekly_sales) AS avg_sales,
        COUNT(*) AS num_records,
        
        -- YoY and MoM calculations
        LAG(SUM(s.weekly_sales), 52) OVER (
            PARTITION BY s.store_id, s.department_id 
            ORDER BY DATE_TRUNC('week', s.date)
        ) AS sales_52w_ago,
        
        LAG(SUM(s.weekly_sales), 1) OVER (
            PARTITION BY s.store_id, s.department_id 
            ORDER BY DATE_TRUNC('week', s.date)
        ) AS sales_1w_ago,
        
        -- Economic context
        AVG(f.cpi) AS avg_cpi,
        AVG(f.unemployment) AS avg_unemployment,
        AVG(f.temperature) AS avg_temperature
        
    FROM silver.sales s
    LEFT JOIN silver.stores st ON s.store_id = st.store_id AND st.is_current = TRUE
    LEFT JOIN silver.economic_features f ON s.store_id = f.store_id AND s.date = f.date
    GROUP BY s.store_id, st.store_type, s.department_id, 
            DATE_TRUNC('week', s.date), DATE_TRUNC('month', s.date), 
            DATE_TRUNC('quarter', s.date), EXTRACT(YEAR FROM s.date);

    CREATE INDEX idx_plat_trend_week ON platinum.sales_trend_analysis (week_start);
    CREATE INDEX idx_plat_trend_month ON platinum.sales_trend_analysis (month_start);