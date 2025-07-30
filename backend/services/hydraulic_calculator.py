# backend/services/hydraulic_calculator.py
import math

# 曼寧糙度係數表 (簡化，實際應用可能更複雜)
MANNING_N_VALUES = {
    'concrete': 0.013,
    'ductile_iron': 0.012,
    'pvc': 0.009,
    'earth': 0.025
}

def get_manning_n(material):
    return MANNING_N_VALUES.get(material.lower(), 0.013) # 預設值

def calculate_pipe_hydraulics(diameter, slope, manning_n, design_flow):
    """
    計算圓管的曼寧公式水力特性。
    根據設計流量計算實際流量、流速和水深。
    這裡的水深計算使用簡化迭代法或查表，實際精確解法更複雜。
    """
    if diameter <= 0 or slope < 0 or manning_n <= 0:
        return 0, 0, 0, 0 # 無效輸入

    radius = diameter / 2
    area_full = math.pi * radius**2
    perimeter_full = math.pi * diameter
    rh_full = area_full / perimeter_full # 滿管時的水力半徑

    v_full = (1 / manning_n) * (rh_full**(2/3)) * (slope**(1/2)) if slope > 0 else 0
    q_full = area_full * v_full

    calculated_flow = design_flow # 假設設計流量即為期望的實際流量

    # --- 簡化的水深和流速計算 (實際應用中應使用更精確的數值解法) ---
    # 對於重力流下的部分滿管，水深 d 的計算是一個非線性問題，通常需要迭代
    # 這裡為 MVP 目的，進行簡化處理：
    calculated_depth = diameter # 預設為滿管水深
    calculated_velocity = v_full # 預設為滿管流速
    
    if design_flow <= q_full and q_full > 0: # 僅在未滿管且滿管流量大於0時進行近似
        # 非常簡化的流量-水深關係近似，僅作示意
        # 實際工程會使用如 "Trapezoidal/Circular Culvert Flow" 查表或迭代計算
        flow_ratio_simplified = design_flow / q_full
        if flow_ratio_simplified <= 0.5: # 流量小於一半時，水深可能約為流量比乘以管徑
            calculated_depth = diameter * (flow_ratio_simplified ** 0.5) * 0.8
        else: # 流量大於一半時，水深會逐漸接近管徑
             calculated_depth = diameter * (0.5 + (flow_ratio_simplified - 0.5) * 0.8)

        if calculated_depth < 0.01: calculated_depth = 0.01 # 避免水深過小
        
        # 重新計算部分滿管的面積和水力半徑，然後計算流速
        if calculated_depth > 0:
            theta = 2 * math.acos(1 - (2 * calculated_depth / diameter))
            area_partial = (radius**2 / 2) * (theta - math.sin(theta))
            perimeter_partial = radius * theta
            if perimeter_partial > 0:
                rh_partial = area_partial / perimeter_partial
                calculated_velocity = (1 / manning_n) * (rh_partial**(2/3)) * (slope**(1/2)) if slope > 0 else 0
            else:
                calculated_velocity = 0 # 無水流
        else:
            calculated_velocity = 0

    elif design_flow > q_full:
        # 如果設計流量超過滿管容量，則認為是超載，水深為滿管或更高（壓力流），
        # 但這裡暫時只用滿管水深表示。
        # 流速則按流量/滿管面積估算，以反映流量增大
        calculated_depth = diameter
        calculated_velocity = design_flow / area_full if area_full > 0 else 0
    # --- 簡化結束 ---

    flow_ratio = design_flow / q_full if q_full > 0 else 0 # 滿管度

    return calculated_flow, calculated_velocity, calculated_depth, flow_ratio

def calculate_rational_formula_peak_flow(area_sqm, runoff_coefficient, rainfall_intensity_mmhr):
    """
    使用合理化公式計算洪峰流量。
    Qp = 1/360 * C * I * A
    Qp: CMS (立方公尺/秒)
    C: 逕流係數 (無因次)
    I: 降雨強度 (mm/hr)
    A: 集水面積 (公頃)
    這裡輸入面積為平方米，轉換為公頃： area_sqm / 10000
    """
    area_hectares = area_sqm / 10000.0
    if runoff_coefficient < 0 or runoff_coefficient > 1 or rainfall_intensity_mmhr < 0 or area_hectares < 0:
        return 0 # 無效輸入
    
    return (1.0 / 360.0) * runoff_coefficient * rainfall_intensity_mmhr * area_hectares

def check_manhole_overflow(manhole_elevation_invert, manhole_overflow_point_elevation, inflow_to_manhole, downstream_pipe_capacity):
    """
    檢查人孔是否溢流。
    簡化邏輯：如果流入人孔的流量超過下游管線容量，或理論水位高於溢流點。
    這裡僅比較流量是否超過下游管線承載力。
    更精確的方法會根據流入流量計算人孔內的水位。
    """
    is_overflow = False
    current_water_level = manhole_elevation_invert # 簡化：初始假設水位在底部

    if inflow_to_manhole > downstream_pipe_capacity:
        is_overflow = True
        # 如果溢流，假設水位到達溢流點或更高
        current_water_level = manhole_overflow_point_elevation + (inflow_to_manhole - downstream_pipe_capacity) * 0.1 # 簡化水位上升
    else:
        # 如果沒有溢流，水位則在底部與溢流點之間，簡化為設計流量比例
        level_ratio = inflow_to_manhole / downstream_pipe_capacity if downstream_pipe_capacity > 0 else 0
        current_water_level = manhole_elevation_invert + (manhole_overflow_point_elevation - manhole_elevation_invert) * level_ratio

    return is_overflow, current_water_level