# D:\00_Project\my-hydro-app\backend\app.py

from shapely.geometry import shape
from shapely.wkt import dumps as wkt_dumps # 需要將 shapely 物件轉換為 WKT
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry, Geography # 確保導入 Geography
from flask_cors import CORS
import json
import os
import math

app = Flask(__name__)
CORS(app)  # 啟用 CORS，允許前端應用程式訪問

# 資料庫配置
# 請替換 'your_username' 和 'your_password' 為您的 PostgreSQL 實際用戶名和密碼
# 如果您在安裝 PostgreSQL 時沒有特別設定，預設的用戶名通常是 'postgres'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:admin@localhost:5432/hydro_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==============================================================================
# 資料庫模型定義
# ==============================================================================

class Manhole(db.Model):
    __tablename__ = 'manholes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    geom = db.Column(Geometry('POINT', srid=4326))  # 人孔是點，指定 SRID
    top_elevation = db.Column(db.Float, default=0.0) # 頂蓋標高 (m)
    bottom_elevation = db.Column(db.Float, default=-5.0) # 底部標高 (m)
    design_flow_limit = db.Column(db.Float, default=0.1) # 設計流量上限 (CMS)
    overflow_elevation = db.Column(db.Float, default=-0.5) # 溢流點標高 (m)
    inflow = db.Column(db.Float, default=0.0) # 流入流量 (CMS)
    downstream_capacity = db.Column(db.Float, default=0.0) # 下游管道容量 (CMS)

    # 模擬結果
    calculated_water_level = db.Column(db.Float) # 計算水位 (m)
    is_overflow = db.Column(db.Boolean) # 是否溢流

    def to_dict(self):
        # 從資料庫獲取 GeoJSON 字串，然後解析成 Python 字典
        geojson_str = db.session.scalar(db.func.ST_AsGeoJSON(self.geom))
        geojson_dict = json.loads(geojson_str) if geojson_str else None # 如果是空，則為 None

        return {
            'id': self.id,
            'name': self.name,
            'geom': geojson_dict,
            'top_elevation': self.top_elevation,
            'bottom_elevation': self.bottom_elevation,
            'design_flow_limit': self.design_flow_limit,
            'overflow_elevation': self.overflow_elevation,
            'inflow': self.inflow,
            'downstream_capacity': self.downstream_capacity,
            'calculated_water_level': self.calculated_water_level,
            'is_overflow': self.is_overflow
        }

class Pipeline(db.Model):
    __tablename__ = 'pipelines'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    geom = db.Column(Geometry('LINESTRING', srid=4326)) # 管線是線，指定 SRID
    diameter = db.Column(db.Float, default=0.5) # 管徑 (m)
    slope = db.Column(db.Float, default=0.001) # 坡度
    material = db.Column(db.String(50), default='混凝土') # 管材
    design_flow = db.Column(db.Float, default=0.1) # 設計流量 (CMS)

    # 模擬結果
    calculated_flow = db.Column(db.Float) # 計算流量 (CMS)
    full_capacity_ratio = db.Column(db.Float) # 滿管度 (%)

    def to_dict(self):
        geojson_str = db.session.scalar(db.func.ST_AsGeoJSON(self.geom))
        geojson_dict = json.loads(geojson_str) if geojson_str else None
        return {
            'id': self.id,
            'name': self.name,
            'geom': geojson_dict,
            'diameter': self.diameter,
            'slope': self.slope,
            'material': self.material,
            'design_flow': self.design_flow,
            'calculated_flow': self.calculated_flow,
            'full_capacity_ratio': self.full_capacity_ratio
        }

class CatchmentArea(db.Model):
    __tablename__ = 'catchment_areas'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    geom = db.Column(Geometry('POLYGON', srid=4326)) # 集水區是面，指定 SRID
    runoff_coefficient = db.Column(db.Float, default=0.5) # 逕流係數 (C)
    rainfall_intensity = db.Column(db.Float, default=50.0) # 降雨強度 (mm/hr)

    # 模擬結果
    calculated_peak_flow = db.Column(db.Float) # 洪峰流量 (CMS)

    def to_dict(self):
        geojson_str = db.session.scalar(db.func.ST_AsGeoJSON(self.geom))
        geojson_dict = json.loads(geojson_str) if geojson_str else None
        return {
            'id': self.id,
            'name': self.name,
            'geom': geojson_dict,
            'runoff_coefficient': self.runoff_coefficient,
            'rainfall_intensity': self.rainfall_intensity,
            'calculated_peak_flow': self.calculated_peak_flow
        }

# ==============================================================================
# API Routes
# ==============================================================================


# --- Manholes ---
@app.route('/api/manholes', methods=['GET'])
def get_manholes():
    manholes = Manhole.query.all()
    return jsonify([mh.to_dict() for mh in manholes])

@app.route('/api/manholes', methods=['POST'])
def add_manhole():
    data = request.get_json()
    # 將 GeoJSON 字典轉換為 Shapely 幾何物件，然後再轉換為 WKT 字串
    geojson_dict = data['geom']
    shapely_geom = shape(geojson_dict)
    wkt_geom = wkt_dumps(shapely_geom) # 將 Shapely 物件轉換為 WKT 字串

    new_manhole = Manhole(
        name=data.get('name', '新建人孔'),
        geom=wkt_geom, # 將 WKT 字串傳遞給 geom
        top_elevation=data.get('top_elevation'),
        bottom_elevation=data.get('bottom_elevation'),
        design_flow_limit=data.get('design_flow_limit'),
        overflow_elevation=data.get('overflow_elevation'),
        inflow=data.get('inflow'),
        downstream_capacity=data.get('downstream_capacity')
    )
    db.session.add(new_manhole)
    db.session.commit()
    return jsonify(new_manhole.to_dict()), 201

@app.route('/api/manholes/<int:id>', methods=['PUT'])
def update_manhole(id):
    manhole = Manhole.query.get_or_404(id)
    data = request.get_json()
    print(f"Received data: {data}")
    print(f"Type of data: {type(data)}")
    if 'geom' in data:
        geojson_dict = data['geom']
        shapely_geom = shape(geojson_dict)
        manhole.geom = wkt_dumps(shapely_geom) # 將 WKT 字串傳遞給 geom
    manhole.name = data.get('name', manhole.name)
    manhole.top_elevation = data.get('top_elevation', manhole.top_elevation)
    manhole.bottom_elevation = data.get('bottom_elevation', manhole.bottom_elevation)
    manhole.design_flow_limit = data.get('design_flow_limit', manhole.design_flow_limit)
    manhole.overflow_elevation = data.get('overflow_elevation', manhole.overflow_elevation)
    manhole.inflow = data.get('inflow', manhole.inflow)
    manhole.downstream_capacity = data.get('downstream_capacity', manhole.downstream_capacity)

    db.session.commit()
    return jsonify(manhole.to_dict())

@app.route('/api/manholes/<int:id>', methods=['DELETE'])
def delete_manhole(id):
    manhole = Manhole.query.get_or_404(id)
    db.session.delete(manhole)
    db.session.commit()
    return '', 204

# --- Pipelines ---
@app.route('/api/pipelines', methods=['GET'])
def get_pipelines():
    pipelines = Pipeline.query.all()
    return jsonify([pl.to_dict() for pl in pipelines])

@app.route('/api/pipelines', methods=['POST'])
def add_pipeline():
    data = request.get_json()
    # 將 GeoJSON 字典轉換為 Shapely 幾何物件，然後再轉換為 WKT 字串
    geojson_dict = data['geom']
    shapely_geom = shape(geojson_dict)
    wkt_geom = wkt_dumps(shapely_geom) # 將 Shapely 物件轉換為 WKT 字串

    new_pipeline = Pipeline(
        name=data.get('name', '新建管線'),
        geom=wkt_geom, # 將 WKT 字串傳遞給 geom
        diameter=data.get('diameter'),
        slope=data.get('slope'),
        material=data.get('material'),
        design_flow=data.get('design_flow')
    )
    db.session.add(new_pipeline)
    db.session.commit()
    return jsonify(new_pipeline.to_dict()), 201

@app.route('/api/pipelines/<int:id>', methods=['PUT'])
def update_pipeline(id):
    pipeline = Pipeline.query.get_or_404(id)
    data = request.get_json()
    print(f"Received data: {data}")
    print(f"Type of data: {type(data)}")
    if 'geom' in data:
        geojson_dict = data['geom']
        shapely_geom = shape(geojson_dict)
        pipeline.geom = wkt_dumps(shapely_geom) # 將 WKT 字串傳遞給 geom
    pipeline.name = data.get('name', pipeline.name)
    pipeline.diameter = data.get('diameter', pipeline.diameter)
    pipeline.slope = data.get('slope', pipeline.slope)
    pipeline.material = data.get('material', pipeline.material)
    pipeline.design_flow = data.get('design_flow', pipeline.design_flow)
    db.session.commit()
    return jsonify(pipeline.to_dict())

@app.route('/api/pipelines/<int:id>', methods=['DELETE'])
def delete_pipeline(id):
    pipeline = Pipeline.query.get_or_404(id)
    db.session.delete(pipeline)
    db.session.commit()
    return '', 204

# --- Catchment Areas ---
@app.route('/api/catchment_areas', methods=['GET'])
def get_catchment_areas():
    catchment_areas = CatchmentArea.query.all()
    return jsonify([ca.to_dict() for ca in catchment_areas])

@app.route('/api/catchment_areas', methods=['POST'])
def add_catchment_area():
    data = request.get_json()
    # 將 GeoJSON 字典轉換為 Shapely 幾何物件，然後再轉換為 WKT 字串
    geojson_dict = data['geom']
    shapely_geom = shape(geojson_dict)
    wkt_geom = wkt_dumps(shapely_geom) # 將 Shapely 物件轉換為 WKT 字串

    new_area = CatchmentArea(
        name=data.get('name', '新建集水區'),
        geom=wkt_geom, # 將 WKT 字串傳遞給 geom
        runoff_coefficient=data.get('runoff_coefficient'),
        rainfall_intensity=data.get('rainfall_intensity')
    )
    db.session.add(new_area)
    db.session.commit()
    return jsonify(new_area.to_dict()), 201

@app.route('/api/catchment_areas/<int:id>', methods=['PUT'])
def update_catchment_area(id):
    area = CatchmentArea.query.get_or_404(id)
    data = request.get_json()
    print(f"Received data: {data}")
    print(f"Type of data: {type(data)}")
    if 'geom' in data:
        geojson_dict = data['geom']
        shapely_geom = shape(geojson_dict)
        area.geom = wkt_dumps(shapely_geom) # 將 WKT 字串傳遞給 geom
    area.name = data.get('name', area.name)
    area.runoff_coefficient = data.get('runoff_coefficient', area.runoff_coefficient)
    area.rainfall_intensity = data.get('rainfall_intensity', area.rainfall_intensity)
    db.session.commit()
    return jsonify(area.to_dict())

@app.route('/api/catchment_areas/<int:id>', methods=['DELETE'])
def delete_catchment_area(id):
    area = CatchmentArea.query.get_or_404(id)
    db.session.delete(area)
    db.session.commit()
    return '', 204


# ==============================================================================
# 模擬端點
# ==============================================================================

@app.route('/api/simulate', methods=['POST'])
def simulate_hydraulics():
    # 重新獲取最新數據
    manholes = Manhole.query.all()
    pipelines = Pipeline.query.all()
    catchment_areas = CatchmentArea.query.all()

    # 1. 計算集水區洪峰流量 (簡化合理化公式 Q = C I A)
    for area in catchment_areas:
        # 使用 PostGIS 的 ST_Area(geom::geography) 獲取以平方米為單位的面積
        # 需要確保 geom 欄位在模型中是 Geometry 類型，並且 PostGIS 已啟用
        area_sq_m = db.session.scalar(db.func.ST_Area(area.geom))
        
        # 合理化公式: Q (CMS) = C * I * A / 3600 (I: mm/hr, A: m^2)
        # 轉換單位：I (mm/hr) -> m/s (1mm/hr = 1/(1000*3600) m/s)
        # Q = C * (I / 3600000) * A (m^3/s = CMS)
        area.calculated_peak_flow = area.runoff_coefficient * area.rainfall_intensity * area_sq_m / (3600 * 1000) # 1000 for mm to m
        
        db.session.add(area) # 更新模型
    db.session.commit()

    # 2. 管道水理計算 (簡化曼寧公式 V = (1/n) * R^(2/3) * S^(1/2) 接著 Q = V * A)
    for pipeline in pipelines:
        n = 0.013 # 簡化：假設所有管材糙率係數為混凝土
        if pipeline.material == '鑄鐵':
            n = 0.014
        elif pipeline.material == 'PVC':
            n = 0.009
            
        A_full = math.pi * (pipeline.diameter / 2)**2 # 滿管斷面積
        R_full = pipeline.diameter / 4 # 滿管水力半徑

        # 曼寧公式計算滿管流量 (CMS)
        Q_full = (1/n) * A_full * (R_full**(2/3)) * (pipeline.slope**0.5)

        # 簡化：假設管線的計算流量就是其設計流量
        pipeline.calculated_flow = pipeline.design_flow
        
        if Q_full > 0:
            pipeline.full_capacity_ratio = (pipeline.calculated_flow / Q_full) * 100
        else:
            pipeline.full_capacity_ratio = 0 # 避免除以零

        db.session.add(pipeline)
    db.session.commit()

    # 3. 人孔水位和溢流判斷
    for manhole in manholes:
        if manhole.design_flow_limit > 0:
            # 計算一個基於流量的水位比例
            water_level_ratio = manhole.inflow / manhole.design_flow_limit
            # 簡化水位計算：底部標高 + 比例 * (溢流點標高 - 底部標高)
            manhole.calculated_water_level = manhole.bottom_elevation + \
                                             water_level_ratio * (manhole.overflow_elevation - manhole.bottom_elevation)
            
            # 將水位限制在合理範圍內 (不超過頂蓋標高)
            manhole.calculated_water_level = min(manhole.calculated_water_level, manhole.top_elevation)
        else:
            manhole.calculated_water_level = manhole.bottom_elevation # 無流量上限時，水位在底部

        # 溢流判斷：計算水位是否超過溢流點標高
        manhole.is_overflow = manhole.calculated_water_level > manhole.overflow_elevation
        
        db.session.add(manhole)
    db.session.commit()

    return jsonify({"message": "模擬執行成功！", "manholes": [mh.to_dict() for mh in Manhole.query.all()],
                    "pipelines": [pl.to_dict() for pl in Pipeline.query.all()],
                    "catchment_areas": [ca.to_dict() for ca in CatchmentArea.query.all()]})


if __name__ == '__main__':
#    with app.app_context(): # 確保在應用程式上下文中執行
#        db.create_all() # 確保資料庫表存在
    app.run(debug=True, port=5000)