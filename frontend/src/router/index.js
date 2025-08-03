// D:\00_Project\my-hydro-app\frontend\src\router\index.js
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  }
  // 您可以在這裡添加其他路由
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router