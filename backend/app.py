# D:\00_Project\my-hydro-app\backend\app.py

from shapely.geometry import shape
from shapely.wkt import dumps as wkt_dumps
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry, Geography, functions
from flask_cors import CORS
import json
import os
import math
import traceback

app = Flask(__name__)
CORS(app)

# 資料庫配置
# 請替換 'your_username' 和 'your_password' 為您的 PostgreSQL 實際用戶名和密碼
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
    geom = db.Column(Geometry('POINT', srid=4326))
    top_elevation = db.Column(db.Float, default=0.0)
    bottom_elevation = db.Column(db.Float, default=-5.0)
    design_flow_limit = db.Column(db.Float, default=0.1)
    overflow_elevation = db.Column(db.Float, default=-0.5)
    inflow = db.Column(db.Float, default=0.0)
    downstream_capacity = db.Column(db.Float, default=0.0)
    calculated_water_level = db.Column(db.Float)
    is_overflow = db.Column(db.Boolean)

    def to_dict(self):
        geojson_str = db.session.scalar(db.func.ST_AsGeoJSON(self.geom))
        geojson_dict = json.loads(geojson_str) if geojson_str else None
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
    geom = db.Column(Geometry('LINESTRING', srid=4326))
    diameter = db.Column(db.Float, default=0.5)
    slope = db.Column(db.Float, default=0.001)
    material = db.Column(db.String(50), default='混凝土')
    design_flow = db.Column(db.Float, default=0.1)
    calculated_flow = db.Column(db.Float)
    full_capacity_ratio = db.Column(db.Float)
    calculated_length_m = db.Column(db.Float) # 新增長度欄位

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
            'full_capacity_ratio': self.full_capacity_ratio,
            'calculated_length_m': self.calculated_length_m # 返回長度資訊
        }

class CatchmentArea(db.Model):
    __tablename__ = 'catchment_areas'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    geom = db.Column(Geography('POLYGON', srid=4326))
    runoff_coefficient = db.Column(db.Float, default=0.5)
    rainfall_intensity = db.Column(db.Float, default=50.0)
    calculated_peak_flow = db.Column(db.Float)
    calculated_area_sq_m = db.Column(db.Float) # 新增面積欄位

    def to_dict(self):
        geojson_str = db.session.scalar(db.func.ST_AsGeoJSON(self.geom))
        geojson_dict = json.loads(geojson_str) if geojson_str else None
        return {
            'id': self.id,
            'name': self.name,
            'geom': geojson_dict,
            'runoff_coefficient': self.runoff_coefficient,
            'rainfall_intensity': self.rainfall_intensity,
            'calculated_peak_flow': self.calculated_peak_flow,
            'calculated_area_sq_m': self.calculated_area_sq_m # 返回面積資訊
        }

# ==============================================================================
# API Routes
# ==============================================================================
# ... (這裡的 API Routes 保持不變，因為它們會自動處理新的欄位)
@app.route('/api/manholes', methods=['GET'])
def get_manholes():
    manholes = Manhole.query.all()
    return jsonify([mh.to_dict() for mh in manholes])

@app.route('/api/manholes', methods=['POST'])
def add_manhole():
    data = request.get_json()
    geojson_dict = data['geom']
    shapely_geom = shape(geojson_dict)
    wkt_geom = wkt_dumps(shapely_geom)

    new_manhole = Manhole(
        name=data.get('name', '新建人孔'),
        geom=wkt_geom,
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
    if 'geom' in data:
        geojson_dict = data['geom']
        shapely_geom = shape(geojson_dict)
        manhole.geom = wkt_dumps(shapely_geom)
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
    geojson_dict = data['geom']
    shapely_geom = shape(geojson_dict)
    wkt_geom = wkt_dumps(shapely_geom)

    new_pipeline = Pipeline(
        name=data.get('name', '新建管線'),
        geom=wkt_geom,
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
    if 'geom' in data:
        geojson_dict = data['geom']
        shapely_geom = shape(geojson_dict)
        pipeline.geom = wkt_dumps(shapely_geom)
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
    geojson_dict = data['geom']
    shapely_geom = shape(geojson_dict)
    wkt_geom = wkt_dumps(shapely_geom)

    new_area = CatchmentArea(
        name=data.get('name', '新建集水區'),
        geom=wkt_geom,
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
    if 'geom' in data:
        geojson_dict = data['geom']
        shapely_geom = shape(geojson_dict)
        area.geom = wkt_dumps(shapely_geom)
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
# 模擬端點 - 修正後的版本
# ==============================================================================

@app.route('/api/simulate', methods=['POST'])
def simulate_hydraulics():
    try:
        manholes = Manhole.query.all()
        pipelines = Pipeline.query.all()
        catchment_areas = CatchmentArea.query.all()

        # 1. 計算集水區洪峰流量 (Q = C * I * A) 和面積
        for area in catchment_areas:
            geom_transformed = db.func.ST_Transform(area.geom, 3857)
            area_sq_m = db.session.scalar(db.func.ST_Area(geom_transformed))
            
            calculated_flow = (area.runoff_coefficient * area.rainfall_intensity * area_sq_m) / 3600000
            area.calculated_peak_flow = max(0, calculated_flow)
            area.calculated_area_sq_m = area_sq_m # 儲存計算出的面積
            
            db.session.add(area) 

        # 2. 管道水理計算和長度
        for pipeline in pipelines:
            n = 0.013 
            if pipeline.material == '鑄鐵':
                n = 0.014
            elif pipeline.material == 'PVC':
                n = 0.009
            
            # 計算管線長度
            # 由於 geom 欄位是 Geometry('LINESTRING', srid=4326)，我們也需要進行投影轉換以獲得公尺單位
            geom_transformed_len = db.func.ST_Transform(pipeline.geom, 3857)
            pipeline.calculated_length_m = db.session.scalar(db.func.ST_Length(geom_transformed_len))

            A_full = math.pi * (pipeline.diameter / 2)**2
            R_full = pipeline.diameter / 4

            Q_full = (1/n) * A_full * (R_full**(2/3)) * (pipeline.slope**0.5)

            pipeline.calculated_flow = pipeline.design_flow
            
            if Q_full > 0:
                pipeline.full_capacity_ratio = (pipeline.calculated_flow / Q_full) * 100
            else:
                pipeline.full_capacity_ratio = 0
            
            db.session.add(pipeline) 

        # 3. 人孔水位和溢流判斷
        for manhole in manholes:
            if manhole.design_flow_limit > 0:
                water_level_ratio = manhole.inflow / manhole.design_flow_limit
                manhole.calculated_water_level = manhole.bottom_elevation + \
                                                 water_level_ratio * (manhole.overflow_elevation - manhole.bottom_elevation)
                manhole.calculated_water_level = min(manhole.calculated_water_level, manhole.top_elevation)
            else:
                manhole.calculated_water_level = manhole.bottom_elevation

            manhole.is_overflow = manhole.calculated_water_level > manhole.overflow_elevation
            
            db.session.add(manhole) 

        db.session.commit()

        updated_manholes = Manhole.query.all()
        updated_pipelines = Pipeline.query.all()
        updated_catchment_areas = CatchmentArea.query.all()

        return jsonify({
            "message": "模擬執行成功！",
            "manholes": [mh.to_dict() for mh in updated_manholes],
            "pipelines": [pl.to_dict() for pl in updated_pipelines],
            "catchment_areas": [ca.to_dict() for ca in updated_catchment_areas]
        })

    except Exception as e:
        db.session.rollback()
        print("模擬執行失敗:")
        traceback.print_exc() 
        return jsonify({"message": f"模擬執行失敗: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)