# backend/services/gis_processor.py
from shapely.geometry import shape, Point, LineString, Polygon
from shapely.wkt import dumps, loads # 用於處理 WKT 格式，QGIS 可能更常用
from pyproj import CRS, Transformer # 用於座標轉換

# 定義一個轉換器，從 WGS84 (EPSG:4326) 轉換到一個投影座標系 (例如，台灣地區使用 UTM Zone 51N, EPSG:32651)
# 這樣可以進行精確的面積和長度計算
# 在實際應用中，您可能需要根據您的專案區域選擇合適的 UTM Zone 或其他投影座標系
transformer_to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32651", always_xy=True)
transformer_from_utm = Transformer.from_crs("EPSG:32651", "EPSG:4326", always_xy=True)

def transform_geometry_to_utm(geojson_geometry):
    """將 GeoJSON 幾何從 WGS84 轉換到 UTM 座標系 (EPSG:32651)"""
    geom_shapely = shape(geojson_geometry)
    
    def transform_point(x, y):
        return transformer_to_utm.transform(x, y)

    if geom_shapely.geom_type == 'Point':
        return Point(transform_point(geom_shapely.x, geom_shapely.y))
    elif geom_shapely.geom_type == 'LineString':
        coords_utm = [transform_point(x, y) for x, y in geom_shapely.coords]
        return LineString(coords_utm)
    elif geom_shapely.geom_type == 'Polygon':
        exterior_utm = [transform_point(x, y) for x, y in geom_shapely.exterior.coords]
        interiors_utm = []
        for interior in geom_shapely.interiors:
            interiors_utm.append([transform_point(x, y) for x, y in interior.coords])
        return Polygon(exterior_utm, interiors_utm)
    # 處理其他類型或集合類型
    return geom_shapely # 返回未轉換的，或者拋出錯誤


def calculate_area_from_geom(geojson_geometry):
    """
    從 GeoJSON 幾何物件計算面積 (平方公尺)。
    先轉換到投影座標系再計算以提高精確度。
    """
    try:
        geom_utm = transform_geometry_to_utm(geojson_geometry)
        return geom_utm.area # 返回平方公尺
    except Exception as e:
        print(f"Error calculating area: {e}")
        return 0

def get_pipe_length_from_geom(geojson_geometry):
    """
    從 GeoJSON LineString 幾何物件計算長度 (公尺)。
    先轉換到投影座標系再計算以提高精確度。
    """
    try:
        geom_utm = transform_geometry_to_utm(geojson_geometry)
        return geom_utm.length # 返回公尺
    except Exception as e:
        print(f"Error calculating length: {e}")
        return 0