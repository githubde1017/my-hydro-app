# 智慧水務管網水理檢核模擬系統

## 專案簡介

此專案是一個基於網頁的智慧水務管網水理檢核模擬系統。它提供了一個直觀的地理資訊系統 (GIS) 界面，允許用戶在地圖上繪製和管理人孔、管線、集水區等水利設施要素，並進行初步的水理模擬分析，以協助了解管網的水力運行狀況，特別是檢測潛在的溢流或滿管問題。

本系統採用前後端分離架構，前端使用 Vue.js 構建交互式地圖界面，結合 Leaflet.js 及其繪圖插件實現空間數據的視覺化與編輯；後端則基於 Flask 框架，負責數據管理、模擬計算以及與 PostGIS 空間資料庫的交互。

## 功能特色

- **地圖繪製與編輯：**
    - 在地圖上精確繪製點 (人孔)、線 (管線) 和多邊形 (集水區) 要素。
    - 支援對已繪製要素的空間位置進行修改。
    - 支援對各類要素的屬性（如名稱、標高、管徑、坡度、逕流係數等）進行新增、編輯和刪除。
- **數據管理：**
    - 與 PostGIS 資料庫整合，持久化儲存所有水利設施的空間與屬性數據。
    - 即時載入並顯示所有已儲存的要素。
- **水理檢核模擬：**
    - 執行基於簡單水理公式的模擬計算（例如，人孔水位、管線流量、集水區洪峰流量等）。
    - 視覺化模擬結果：
        - 人孔：根據水位和溢流點判斷是否溢流，並在地圖上以不同顏色標示。
        - 管線：根據滿管度判斷是否超載，並在地圖上以顏色和粗細進行區分。
        - 集水區：根據洪峰流量在地圖上以顏色深淺表示。

## 技術棧

**前端 (Frontend):**
- **Vue.js 3:** 漸進式 JavaScript 框架
- **Leaflet.js:** 輕量級互動式地圖 JavaScript 庫
- **Leaflet.Draw:** Leaflet.js 的繪圖插件
- **Axios:** 基於 Promise 的 HTTP 客戶端，用於前後端通訊

**後端 (Backend):**
- **Python 3.x:** 主要開發語言
- **Flask:** 輕量級 Python Web 框架
- **SQLAlchemy:** Python ORM，用於數據庫操作
- **GeoAlchemy2:** SQLAlchemy 的擴展，支援空間數據類型
- **Shapely:** Python 幾何物件庫，用於處理 GeoJSON 轉換
- **psycopg2:** PostgreSQL 資料庫適配器
- **Flask-CORS:** 處理跨來源資源共享問題

**資料庫 (Database):**
- **PostgreSQL + PostGIS:** 帶有空間數據擴展的強大開源關係型資料庫

## 環境設定與運行

### 前提條件

在開始之前，請確保您的系統已安裝以下軟體：
- Python 3.8+
- Node.js 14+ (推薦 LTS 版本)
- PostgreSQL 數據庫，並啟用 PostGIS 擴展
- Git

### 1. 克隆專案

```bash
git clone [https://github.com/YourUsername/my-hydro-app.git](https://github.com/YourUsername/my-hydro-app.git)
cd my-hydro-app