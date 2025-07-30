-- database/init_db.sql

-- 1. 檢查並刪除舊的資料表 (如果存在)，確保每次初始化都是乾淨的狀態
DROP TABLE IF EXISTS manholes CASCADE;
DROP TABLE IF EXISTS pipelines CASCADE;
DROP TABLE IF EXISTS catchment_areas CASCADE;

-- 2. 啟用 PostGIS 擴展 (必須在您要使用的資料庫中執行)
-- 這會讓您的資料庫具備處理地理空間資料的能力
CREATE EXTENSION IF NOT EXISTS postgis;

-- 3. 創建 'manholes' 資料表 (人孔)
-- 儲存人孔的點狀地理資訊及相關屬性
CREATE TABLE manholes (
    id SERIAL PRIMARY KEY,              -- 唯一識別碼，自動遞增
    name VARCHAR(255) NOT NULL,         -- 人孔名稱
    top_elevation NUMERIC(10, 3),       -- 頂蓋標高 (公尺)
    bottom_elevation NUMERIC(10, 3),    -- 底部標高 (公尺)
    design_flow_limit NUMERIC(10, 3),   -- 設計流量上限 (CMS, 立方公尺/秒)
    overflow_elevation NUMERIC(10, 3),  -- 溢流點標高 (公尺)
    geom GEOMETRY(Point, 4326),         -- 人孔的地理位置 (點)，使用 WGS84 座標系 (EPSG:4326)

    -- 以下欄位用於儲存模擬結果，初始化時可為空
    calculated_water_level NUMERIC(10, 3), -- 模擬後的計算水位
    is_overflow BOOLEAN DEFAULT FALSE,     -- 模擬後是否溢流
    simulation_notes TEXT                  -- 模擬相關筆記或訊息
);

-- 4. 創建 'pipelines' 資料表 (管線)
-- 儲存管線的線狀地理資訊及相關屬性
CREATE TABLE pipelines (
    id SERIAL PRIMARY KEY,              -- 唯一識別碼，自動遞增
    name VARCHAR(255) NOT NULL,         -- 管線名稱
    from_manhole_id INTEGER REFERENCES manholes(id), -- 起點人孔 ID
    to_manhole_id INTEGER REFERENCES manholes(id),   -- 終點人孔 ID
    diameter NUMERIC(10, 3),            -- 管徑 (公尺)
    slope NUMERIC(10, 5),               -- 坡度 (無單位)
    material VARCHAR(100),              -- 管材 (如: Concrete, PVC, HDPE)
    design_flow NUMERIC(10, 3),         -- 設計流量 (CMS)
    geom GEOMETRY(LineString, 4326),    -- 管線的地理位置 (線)，使用 WGS84 座標系 (EPSG:4326)

    -- 以下欄位用於儲存模擬結果，初始化時可為空
    calculated_flow NUMERIC(10, 3),       -- 模擬後的計算流量
    calculated_velocity NUMERIC(10, 3),   -- 模擬後的計算流速
    calculated_depth NUMERIC(10, 3),      -- 模擬後的計算水深
    full_capacity_ratio NUMERIC(5, 2),    -- 模擬後的滿管度百分比 (0-100)
    simulation_notes TEXT                 -- 模擬相關筆記或訊息
);

-- 5. 創建 'catchment_areas' 資料表 (集水區)
-- 儲存集水區的多邊形地理資訊及相關屬性
CREATE TABLE catchment_areas (
    id SERIAL PRIMARY KEY,               -- 唯一識別碼，自動遞增
    name VARCHAR(255) NOT NULL,          -- 集水區名稱
    runoff_coefficient NUMERIC(5, 3),    -- 逕流係數 (0-1)
    rainfall_intensity NUMERIC(10, 3),   -- 降雨強度 (mm/hr)
    geom GEOMETRY(Polygon, 4326),        -- 集水區的地理位置 (多邊形)，使用 WGS84 座標系 (EPSG:4326)

    -- 以下欄位用於儲存模擬結果，初始化時可為空
    calculated_peak_flow NUMERIC(10, 3), -- 模擬後的計算洪峰流量
    simulation_notes TEXT                -- 模擬相關筆記或訊息
);

-- 6. 為地理空間欄位創建空間索引 (可選，但強烈推薦以提高查詢速度)
CREATE INDEX idx_manholes_geom ON manholes USING GIST (geom);
CREATE INDEX idx_pipelines_geom ON pipelines USING GIST (geom);
CREATE INDEX idx_catchment_areas_geom ON catchment_areas USING GIST (geom);

-- 7. 允許 from_manhole_id 和 to_manhole_id 欄位可以為 NULL
-- (在前端繪製時，可能先建立管線，再連結人孔)
ALTER TABLE pipelines ALTER COLUMN from_manhole_id DROP NOT NULL;
ALTER TABLE pipelines ALTER COLUMN to_manhole_id DROP NOT NULL;