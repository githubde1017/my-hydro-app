// D:\00_Project\my-hydro-app\frontend\src\main.js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // 導入 router

import 'leaflet/dist/leaflet.css'; // 導入 Leaflet CSS
import 'leaflet-draw/dist/leaflet.draw.css'; // 導入 Leaflet.draw CSS

createApp(App).use(router).mount('#app') // 將 router 加入到 Vue 應用程式中