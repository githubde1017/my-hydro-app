<template>
  <div class="home-container">
    <aside class="sidebar">
      <h2>智慧水務管網水理檢核模擬</h2>
      <button @click="loadAllData" class="sidebar-button">載入所有數據</button>
      <button @click="executeSimulation" class="sidebar-button">執行模擬</button>

      <div class="data-lists">
        <details open>
          <summary>人孔 (Manholes)</summary>
          <input type="text" v-model="manholeSearchQuery" placeholder="搜尋人孔..." class="search-input" />
          <ul>
            <li v-for="manhole in filteredManholes" :key="manhole.id" @click="panToFeature(manhole)">
              {{ manhole.name }}
              <span>
                - 水位: {{ manhole.calculated_water_level !== null && manhole.calculated_water_level !== undefined ? manhole.calculated_water_level.toFixed(2) + ' m' : 'N/A' }} (溢流: {{ manhole.is_overflow ? '是' : '否' }})
              </span>
              <div class="item-actions">
                <button @click.stop="editFeature('manhole', manhole)">編輯</button>
                <button @click.stop="deleteFeature('manhole', manhole.id)">刪除</button>
              </div>
            </li>
          </ul>
        </details>

        <details open>
          <summary>管線 (Pipelines)</summary>
          <input type="text" v-model="pipelineSearchQuery" placeholder="搜尋管線..." class="search-input" />
          <ul>
            <li v-for="pipeline in filteredPipelines" :key="pipeline.id" @click="panToFeature(pipeline)">
              {{ pipeline.name }}
              <span>
                - 長度: {{ formatLength(pipeline.calculated_length_m) }}
                - 流量: {{ pipeline.calculated_flow !== null && pipeline.calculated_flow !== undefined ? pipeline.calculated_flow.toFixed(3) + ' CMS' : 'N/A' }} (滿管度: {{ pipeline.full_capacity_ratio !== null && pipeline.full_capacity_ratio !== undefined ? pipeline.full_capacity_ratio.toFixed(1) + '%' : 'N/A' }})
              </span>
              <div class="item-actions">
                <button @click.stop="editFeature('pipeline', pipeline)">編輯</button>
                <button @click.stop="deleteFeature('pipeline', pipeline.id)">刪除</button>
              </div>
            </li>
          </ul>
        </details>

        <details open>
          <summary>集水區 (Catchment Areas)</summary>
          <input type="text" v-model="catchmentAreaSearchQuery" placeholder="搜尋集水區..." class="search-input" />
          <ul>
            <li v-for="area in filteredCatchmentAreas" :key="area.id" @click="panToFeature(area)">
              {{ area.name }}
              <span>
                - 面積: {{ formatArea(area.calculated_area_sq_m) }}
                - 洪峰流量: {{ formatPeakFlow(area.calculated_peak_flow) }} CMS
              </span>
              <div class="item-actions">
                <button @click.stop="editFeature('catchment_area', area)">編輯</button>
                <button @click.stop="deleteFeature('catchment_area', area.id)">刪除</button>
              </div>
            </li>
          </ul>
        </details>
      </div>
    </aside>

    <div id="map-container"></div>

    <div v-if="showAddModal" class="modal-overlay">
      <div class="modal-content">
        <h3>新增 {{ getFeatureName(currentFeatureType) }} 屬性</h3>
        <form @submit.prevent="saveFeature">
          <div class="form-group">
            <label for="name">名稱:</label>
            <input type="text" id="name" v-model="form.name" required>
          </div>

          <div v-if="currentFeatureType === 'manhole'">
            <div class="form-group"><label>頂蓋標高 (m):</label><input type="number" step="0.001" v-model.number="form.top_elevation"></div>
            <div class="form-group"><label>底部標高 (m):</label><input type="number" step="0.001" v-model.number="form.bottom_elevation"></div>
            <div class="form-group"><label>設計流量上限 (CMS):</label><input type="number" step="0.001" v-model.number="form.design_flow_limit"></div>
            <div class="form-group"><label>溢流點標高 (m):</label><input type="number" step="0.001" v-model.number="form.overflow_elevation"></div>
            <div class="form-group"><label>流入流量 (CMS):</label><input type="number" step="0.001" v-model.number="form.inflow"></div>
            <div class="form-group"><label>下游管道容量 (CMS):</label><input type="number" step="0.001" v-model.number="form.downstream_capacity"></div>
          </div>

          <div v-if="currentFeatureType === 'pipeline'">
            <div class="form-group"><label>管徑 (m):</label><input type="number" step="0.001" v-model.number="form.diameter"></div>
            <div class="form-group"><label>坡度:</label><input type="number" step="0.00001" v-model.number="form.slope"></div>
            <div class="form-group"><label>管材:</label><input type="text" v-model="form.material"></div>
            <div class="form-group"><label>設計流量 (CMS):</label><input type="number" step="0.001" v-model.number="form.design_flow"></div>
          </div>

          <div v-if="currentFeatureType === 'catchment_area'">
            <div class="form-group"><label>逕流係數:</label><input type="number" step="0.001" min="0" max="1" v-model.number="form.runoff_coefficient"></div>
            <div class="form-group"><label>降雨強度 (mm/hr):</label><input type="number" step="0.001" v-model.number="form.rainfall_intensity"></div>
          </div>

          <div class="modal-actions">
            <button type="submit" class="button-primary">新增要素</button>
            <button type="button" @click="cancelAdd" class="button-secondary">取消</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showEditModal" class="modal-overlay">
      <div class="modal-content">
        <h3>編輯 {{ getFeatureName(currentFeatureType) }} 屬性</h3>
        <form @submit.prevent="updateFeatureAttributes">
          <div class="form-group">
            <label for="edit_name">名稱:</label>
            <input type="text" id="edit_name" v-model="editForm.name" required>
          </div>

          <div v-if="currentFeatureType === 'manhole'">
            <div class="form-group"><label>頂蓋標高 (m):</label><input type="number" step="0.001" v-model.number="editForm.top_elevation"></div>
            <div class="form-group"><label>底部標高 (m):</label><input type="number" step="0.001" v-model.number="editForm.bottom_elevation"></div>
            <div class="form-group"><label>設計流量上限 (CMS):</label><input type="number" step="0.001" v-model.number="editForm.design_flow_limit"></div>
            <div class="form-group"><label>溢流點標高 (m):</label><input type="number" step="0.001" v-model.number="editForm.overflow_elevation"></div>
            <div class="form-group"><label>流入流量 (CMS):</label><input type="number" step="0.001" v-model.number="editForm.inflow"></div>
            <div class="form-group"><label>下游管道容量 (CMS):</label><input type="number" step="0.001" v-model.number="editForm.downstream_capacity"></div>
          </div>

          <div v-if="currentFeatureType === 'pipeline'">
            <div class="form-group"><label>管線長度:</label><input type="text" :value="formatLength(editForm.calculated_length_m)" disabled></div>
            <div class="form-group"><label>管徑 (m):</label><input type="number" step="0.001" v-model.number="editForm.diameter"></div>
            <div class="form-group"><label>坡度:</label><input type="number" step="0.00001" v-model.number="editForm.slope"></div>
            <div class="form-group"><label>管材:</label><input type="text" v-model="editForm.material"></div>
            <div class="form-group"><label>設計流量 (CMS):</label><input type="number" step="0.001" v-model.number="editForm.design_flow"></div>
          </div>

          <div v-if="currentFeatureType === 'catchment_area'">
            <div class="form-group"><label>集水區面積:</label><input type="text" :value="formatArea(editForm.calculated_area_sq_m)" disabled></div>
            <div class="form-group"><label>逕流係數:</label><input type="number" step="0.001" min="0" max="1" v-model.number="editForm.runoff_coefficient"></div>
            <div class="form-group"><label>降雨強度 (mm/hr):</label><input type="number" step="0.001" v-model.number="editForm.rainfall_intensity"></div>
          </div>

          <div class="modal-actions">
            <button type="submit" class="button-primary">更新屬性</button>
            <button type="button" @click="cancelEdit" class="button-secondary">取消</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import L from 'leaflet';
import 'leaflet-draw';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import axios from 'axios';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const API_BASE_URL = 'http://127.0.0.1:5000/api';

export default {
  name: 'HomeView',
  data() {
    return {
      manholes: [],
      pipelines: [],
      catchmentAreas: [],
      showAddModal: false,
      showEditModal: false,
      currentFeatureType: '',
      form: {},
      editForm: {},
      tempGeometry: null,
      editingFeatureId: null,
      drawnLayer: null,
      // 新增搜尋框的 data 屬性
      manholeSearchQuery: '',
      pipelineSearchQuery: '',
      catchmentAreaSearchQuery: '',
    };
  },
  created() {
    this.map = null;
    this.drawControl = null;
    this.drawnItems = null;
    this.drawCreatedHandler = this.handleDrawCreated.bind(this);
    this.drawEditedHandler = this.handleDrawEdited.bind(this);
    this.drawDeletedHandler = this.handleDrawDeleted.bind(this);
  },
  async mounted() {
    this.initMap();
    await this.loadAllData();
  },
  beforeUnmount() {
    if (this.map) {
      this.map.off(L.Draw.Event.CREATED, this.drawCreatedHandler);
      this.map.off(L.Draw.Event.EDITED, this.drawEditedHandler);
      this.map.off(L.Draw.Event.DELETED, this.drawDeletedHandler);
      this.map.remove();
      this.map = null;
      this.drawControl = null;
      this.drawnItems = null;
    }
  },
  methods: {
    initMap() {
      if (this.map) {
        return;
      }
      this.map = L.map('map-container').setView([24.156, 120.645], 13);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      }).addTo(this.map);

      this.drawnItems = new L.FeatureGroup();
      this.map.addLayer(this.drawnItems);

      this.drawControl = new L.Control.Draw({
        edit: {
          featureGroup: this.drawnItems,
          poly: {
            allowIntersection: false
          }
        },
        draw: {
          polygon: {
            allowIntersection: false,
            showArea: true
          },
          polyline: true,
          marker: true,
          circle: false,
          circlemarker: false,
          rectangle: false
        }
      });
      this.map.addControl(this.drawControl);

      this.map.on(L.Draw.Event.CREATED, this.drawCreatedHandler);
      this.map.on(L.Draw.Event.EDITED, this.drawEditedHandler);
      this.map.on(L.Draw.Event.DELETED, this.drawDeletedHandler);
    },
    disableMapInteractions() {
      if (this.map) {
        this.map.dragging.disable();
        this.map.touchZoom.disable();
        this.map.doubleClickZoom.disable();
        this.map.scrollWheelZoom.disable();
        this.map.boxZoom.disable();
        this.map.keyboard.disable();
      }
    },
    enableMapInteractions() {
      if (this.map) {
        this.map.dragging.enable();
        this.map.touchZoom.enable();
        this.map.doubleClickZoom.enable();
        this.map.scrollWheelZoom.enable();
        this.map.boxZoom.enable();
        this.map.keyboard.enable();
      }
    },
    getFeatureName(type) {
      switch (type) {
        case 'manhole': return '人孔';
        case 'pipeline': return '管線';
        case 'catchment_area': return '集水區';
        default: return '';
      }
    },
    handleDrawCreated(e) {
      const type = e.layerType;
      const layer = e.layer;
      
      this.drawnLayer = layer;
      
      this.currentFeatureType = type === 'marker' ? 'manhole' : type === 'polyline' ? 'pipeline' : 'catchment_area';
      this.tempGeometry = layer.toGeoJSON().geometry;
      
      this.form = this.getInitialFormData(this.currentFeatureType);
      this.showAddModal = true;
      
      this.disableMapInteractions();
    },
    getInitialFormData(type) {
      switch (type) {
        case 'manhole':
          return { name: '新建人孔', top_elevation: 0, bottom_elevation: -5, design_flow_limit: 0.1, overflow_elevation: -0.5, inflow: 0, downstream_capacity: 0 };
        case 'pipeline':
          return { name: '新建管線', diameter: 0.5, slope: 0.001, material: '混凝土', design_flow: 0.1 };
        case 'catchment_area':
          return { name: '新建集水區', runoff_coefficient: 0.5, rainfall_intensity: 50 };
        default:
          return {};
      }
    },
    async saveFeature() {
      const apiEndpointMap = {
        'manhole': 'manholes',
        'pipeline': 'pipelines',
        'catchment_area': 'catchment_areas'
      };
      const apiEndpoint = apiEndpointMap[this.currentFeatureType];

      if (!apiEndpoint || !this.tempGeometry) {
        alert('無效的要素類型或幾何數據。');
        this.enableMapInteractions();
        return;
      }
      
      const featureData = {
        ...this.form,
        geom: this.tempGeometry
      };

      try {
        await axios.post(`${API_BASE_URL}/${apiEndpoint}`, featureData);
        console.log('要素新增成功');
        this.showAddModal = false;
        this.tempGeometry = null;

        if (this.drawnLayer && this.map) {
          this.map.removeLayer(this.drawnLayer);
          this.drawnLayer = null;
        }
        
        this.enableMapInteractions();
        await this.loadAllData();
      } catch (error) {
        console.error('新增要素失敗:', error);
        alert('新增要素失敗！');
        this.enableMapInteractions();
      }
    },
    cancelAdd() {
      this.showAddModal = false;
      this.tempGeometry = null;
      if (this.drawnLayer && this.map) {
        this.map.removeLayer(this.drawnLayer);
        this.drawnLayer = null;
      }
      this.enableMapInteractions();
    },
    editFeature(type, feature) {
      this.currentFeatureType = type;
      this.editingFeatureId = feature.id;
      this.editForm = { ...feature };
      this.showEditModal = true;
    },
    async updateFeatureAttributes() {
      const apiEndpointMap = {
        'manhole': 'manholes',
        'pipeline': 'pipelines',
        'catchment_area': 'catchment_areas'
      };
      const apiEndpoint = apiEndpointMap[this.currentFeatureType];
      
      try {
        await axios.put(`${API_BASE_URL}/${apiEndpoint}/${this.editingFeatureId}`, this.editForm);
        console.log('要素屬性更新成功。');
        this.showEditModal = false;
        await this.loadAllData();
      } catch (error) {
        console.error('更新要素屬性失敗:', error);
        alert('更新要素屬性失敗！');
      }
    },
    cancelEdit() {
      this.showEditModal = false;
      this.editingFeatureId = null;
      this.editForm = {};
    },
    async handleDrawEdited(e) {
      for (const layer of Object.values(e.layers._layers)) {
        const geojson = layer.toGeoJSON();
        const featureId = geojson.properties.id;
        const featureType = geojson.properties.type;

        const apiEndpointMap = {
          'manhole': 'manholes',
          'pipeline': 'pipelines',
          'area': 'catchment_areas'
        };
        const apiEndpoint = apiEndpointMap[featureType];
        
        if (apiEndpoint && featureId) {
          try {
            await axios.put(`${API_BASE_URL}/${apiEndpoint}/${featureId}`, { geom: geojson.geometry });
            console.log('要素幾何形狀更新成功。');
            await this.loadAllData();
          } catch (error) {
            console.error('更新幾何形狀失敗:', error);
            alert('更新幾何形狀失敗！');
          }
        }
      }
    },
    async handleDrawDeleted(e) {
      for (const layer of Object.values(e.layers._layers)) {
        const geojson = layer.toGeoJSON();
        const featureId = geojson.properties.id;
        const featureType = geojson.properties.type;

        const apiEndpointMap = {
          'manhole': 'manholes',
          'pipeline': 'pipelines',
          'area': 'catchment_areas'
        };
        const apiEndpoint = apiEndpointMap[featureType];
        
        if (apiEndpoint && featureId) {
          try {
            await axios.delete(`${API_BASE_URL}/${apiEndpoint}/${featureId}`);
            console.log('要素刪除成功:', featureId);
          } catch (error) {
            console.error('刪除要素失敗:', error);
            alert('刪除要素失敗！');
          }
        }
      }
    },
    async deleteFeature(type, id) {
      if (!confirm('確定要刪除此要素嗎？')) {
        return;
      }
      
      const apiEndpointMap = {
        'manhole': 'manholes',
        'pipeline': 'pipelines',
        'catchment_area': 'catchment_areas'
      };
      const apiEndpoint = apiEndpointMap[type];

      try {
        await axios.delete(`${API_BASE_URL}/${apiEndpoint}/${id}`);
        console.log('要素刪除成功:', id);
        await this.loadAllData();
      } catch (error) {
        console.error('刪除要素失敗:', error);
        alert('刪除要素失敗！');
      }
    },
    async loadAllData() {
      try {
        const [manholesRes, pipelinesRes, catchmentAreasRes] = await Promise.all([
          axios.get(`${API_BASE_URL}/manholes`),
          axios.get(`${API_BASE_URL}/pipelines`),
          axios.get(`${API_BASE_URL}/catchment_areas`)
        ]);

        this.manholes = manholesRes.data;
        this.pipelines = pipelinesRes.data;
        this.catchmentAreas = catchmentAreasRes.data;

        this.updateMapLayers();
        console.log('數據載入成功！');
      } catch (error) {
        console.error('載入數據失敗:', error);
        alert('載入數據失敗！請確認後端服務是否運行正常。');
      }
    },
    updateMapLayers() {
      if (!this.drawnItems) {
        return;
      }
      this.drawnItems.clearLayers();

      const manholeStyle = (feature) => {
        const isOverflow = feature.properties.is_overflow;
        return {
          radius: 8,
          fillColor: isOverflow ? 'red' : 'green',
          color: '#000',
          weight: 1,
          opacity: 1,
          fillOpacity: 0.8
        };
      };

      const pipelineStyle = (feature) => {
        const pipeline = feature.properties;
        const fullRatio = pipeline.full_capacity_ratio;
        let color = 'gray';
        let weight = 3;

        if (fullRatio !== undefined && fullRatio !== null) {
            if (fullRatio >= 100) {
                color = 'red';
                weight = 6;
            } else if (fullRatio >= 80) {
                color = 'orange';
                weight = 4;
            } else {
                color = 'green';
                weight = 2;
            }
        }
        return { color: color, weight: weight, opacity: 0.7 };
      };
      
      const areaStyle = (feature) => {
        const area = feature.properties;
        const peakFlow = area.calculated_peak_flow;
        let fillColor = '#C8E6C9';
        if (peakFlow !== undefined && peakFlow !== null) {
            if (peakFlow > 10) {
                fillColor = '#4CAF50';
            } else if (peakFlow > 5) {
                fillColor = '#8BC34A';
            } else {
                fillColor = '#C8E6C9';
            }
        }
        return { fillColor: fillColor, weight: 2, opacity: 1, color: 'white', fillOpacity: 0.5 };
      };

      this.manholes.forEach(manhole => {
        if (manhole.geom) {
          const manholeGeoJSON = {
            type: "Feature",
            geometry: manhole.geom,
            properties: manhole
          };
          L.geoJson(manholeGeoJSON, {
            pointToLayer: (feature, latlng) => {
                return L.circleMarker(latlng, manholeStyle(feature));
            },
            onEachFeature: (feature, layer) => {
              layer.bindPopup(`<b>人孔: ${manhole.name}</b><br>水位: ${manhole.calculated_water_level !== null ? manhole.calculated_water_level.toFixed(2) + 'm' : 'N/A'}<br>溢流: ${manhole.is_overflow ? '是' : '否'}`);
              layer.feature.properties.type = 'manhole';
              this.drawnItems.addLayer(layer);
            }
          });
        }
      });
      
      this.pipelines.forEach(pipeline => {
        if (pipeline.geom) {
          const pipelineGeoJSON = {
            type: "Feature",
            geometry: pipeline.geom,
            properties: pipeline
          };
          L.geoJson(pipelineGeoJSON, {
            style: pipelineStyle,
            onEachFeature: (feature, layer) => {
              layer.bindPopup(`<b>管線: ${pipeline.name}</b><br>流量: ${pipeline.calculated_flow !== null ? pipeline.calculated_flow.toFixed(3) + ' CMS' : 'N/A'}<br>滿管度: ${pipeline.full_capacity_ratio !== null ? pipeline.full_capacity_ratio.toFixed(1) + '%' : 'N/A'}`);
              layer.feature.properties.type = 'pipeline';
              this.drawnItems.addLayer(layer);
            }
          });
        }
      });
      
      this.catchmentAreas.forEach(area => {
        if (area.geom) {
          const areaGeoJSON = {
            type: "Feature",
            geometry: area.geom,
            properties: area
          };
          L.geoJson(areaGeoJSON, {
            style: areaStyle,
            onEachFeature: (feature, layer) => {
              layer.bindPopup(`<b>集水區: ${area.name}</b><br>洪峰流量: ${this.formatPeakFlow(area.calculated_peak_flow)} CMS`);
              layer.feature.properties.type = 'area';
              this.drawnItems.addLayer(layer);
            }
          });
        }
      });
    },

    async executeSimulation() {
      try {
        const response = await axios.post(`${API_BASE_URL}/simulate`);
        console.log('模擬執行成功:', response.data);
        // 直接使用後端返回的數據更新前端狀態
        this.manholes = response.data.manholes;
        this.pipelines = response.data.pipelines;
        this.catchmentAreas = response.data.catchment_areas;
        this.updateMapLayers();
        alert('水理檢核模擬執行成功！');
      } catch (error) {
        console.error('模擬執行失敗:', error);
        alert('水理檢核模擬執行失敗！請確認數據是否完整或後端服務正常。');
      }
    },
    
    // 新增 panToFeature 方法
    panToFeature(feature) {
      if (!this.map || !feature.geom) {
        console.error('地圖或要素幾何數據不存在。');
        return;
      }
      
      // 創建一個臨時的 GeoJSON 圖層來獲取邊界
      const geojsonLayer = L.geoJson(feature.geom);
      
      // 如果是點，則直接設定視圖中心和縮放
      if (feature.geom.type === 'Point') {
        const latlng = L.latLng(feature.geom.coordinates[1], feature.geom.coordinates[0]);
        this.map.setView(latlng, 17); // 縮放級別可根據需要調整
      } else {
        // 如果是線或面，則縮放至整個邊界
        this.map.fitBounds(geojsonLayer.getBounds());
      }
    },

    // 格式化洪峰流量的方法 (保持不變)
    formatPeakFlow(value) {
      if (typeof value !== 'number' || isNaN(value)) {
        return 'N/A';
      }
      const threshold = 1e-9;
      if (Math.abs(value) < threshold) {
        return "~0";
      }
      return value.toFixed(6);
    },

    // 新增：格式化面積的方法
    formatArea(value) {
      if (typeof value !== 'number' || isNaN(value)) {
        return 'N/A';
      }
      if (value >= 1000000) {
        return (value / 1000000).toFixed(2) + ' km²';
      }
      return value.toFixed(2) + ' m²';
    },

    // 新增：格式化長度的方法
    formatLength(value) {
      if (typeof value !== 'number' || isNaN(value)) {
        return 'N/A';
      }
      if (value >= 1000) {
        return (value / 1000).toFixed(2) + ' km';
      }
      return value.toFixed(2) + ' m';
    },
  },
  // 新增 computed 屬性來實現搜尋過濾
  computed: {
    filteredManholes() {
      if (!this.manholeSearchQuery) {
        return this.manholes;
      }
      const query = this.manholeSearchQuery.toLowerCase();
      return this.manholes.filter(m => m.name.toLowerCase().includes(query));
    },
    filteredPipelines() {
      if (!this.pipelineSearchQuery) {
        return this.pipelines;
      }
      const query = this.pipelineSearchQuery.toLowerCase();
      return this.pipelines.filter(p => p.name.toLowerCase().includes(query));
    },
    filteredCatchmentAreas() {
      if (!this.catchmentAreaSearchQuery) {
        return this.catchmentAreas;
      }
      const query = this.catchmentAreaSearchQuery.toLowerCase();
      return this.catchmentAreas.filter(c => c.name.toLowerCase().includes(query));
    },
  }
};
</script>

<style scoped>
.home-container {
  display: flex;
  height: 100vh;
  width: 100vw;
}

.sidebar {
  width: 300px;
  background-color: #f4f7f6;
  padding: 20px;
  box-shadow: 2px 0 5px rgba(0,0,0,0.1);
  overflow-y: auto;
  flex-shrink: 0;
  text-align: left;
}

.sidebar h2 {
  color: #2c3e50;
  margin-top: 0;
  font-size: 1.5em;
  border-bottom: 1px solid #ccc;
  padding-bottom: 10px;
  margin-bottom: 20px;
}

.sidebar-button {
  display: block;
  width: 100%;
  padding: 10px 15px;
  margin-bottom: 10px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1em;
  transition: background-color 0.3s ease;
}

.sidebar-button:hover {
  background-color: #45a049;
}

.data-lists {
  margin-top: 20px;
}

.data-lists details {
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-bottom: 10px;
  background-color: #fff;
}

.data-lists summary {
  padding: 10px;
  font-weight: bold;
  cursor: pointer;
  background-color: #e8f5e9;
  border-bottom: 1px solid #ddd;
  list-style: none;
}

.data-lists summary::-webkit-details-marker {
  display: none;
}

.search-input {
  width: 90%;
  padding: 8px;
  margin: 5px 0 10px 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.data-lists ul {
  list-style: none;
  padding: 10px 15px;
  margin: 0;
}

.data-lists li {
  padding: 8px 0;
  border-bottom: 1px dotted #eee;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  cursor: pointer; /* 新增 cursor: pointer 讓使用者知道可以點擊 */
}

.data-lists li:last-child {
  border-bottom: none;
}

.item-actions button {
  background-color: #007bff;
  color: white;
  border: none;
  padding: 5px 10px;
  border-radius: 3px;
  cursor: pointer;
  font-size: 0.8em;
  margin-left: 5px;
  transition: background-color 0.2s;
}

.item-actions button:hover {
  background-color: #0056b3;
}

.item-actions button:last-child {
  background-color: #dc3545;
}

.item-actions button:last-child:hover {
  background-color: #c82333;
}

#map-container {
  flex-grow: 1;
  height: 100%;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
  width: 90%;
  max-width: 500px;
  text-align: left;
}

.modal-content h3 {
  margin-top: 0;
  color: #333;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #555;
}

.form-group input[type="text"],
.form-group input[type="number"] {
  width: calc(100% - 20px);
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1em;
}

.modal-actions {
  margin-top: 25px;
  text-align: right;
}

.button-primary, .button-secondary {
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 1em;
  transition: background-color 0.3s ease;
}

.button-primary:hover {
  background-color: #218838;
}

.button-secondary {
  background-color: #6c757d;
  color: white;
}

.button-secondary:hover {
  background-color: #5a6268;
}
</style>