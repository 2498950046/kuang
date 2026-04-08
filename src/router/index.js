import { createRouter, createWebHistory } from 'vue-router';
import { authApi } from '../api/adminPortal';

// 懒加载视图组件，避免首屏体积变大
const HomeView = () => import('../views/HomeView.vue');
const GraphView = () => import('../views/GraphView.vue');
const QAView = () => import('../views/QAView.vue');
// const GemAppreciationView = () => import('../views/GemAppreciationView.vue');

// 懒加载视图组件
const SpecimenLibraryView = () => import('../views/SpecimenLibraryView.vue');
const MineralDetailView = () => import('../views/MineralDetailView.vue');
// 后台管理
const AdminLayout = () => import('../views/admin/AdminLayout.vue');
const AdminLoginView = () => import('../views/admin/AdminLoginView.vue');
const AdminMineralsView = () => import('../views/admin/AdminMineralsView.vue');

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
  },
  // 允许直接访问标本库根路径，自动跳转到默认分类
  {
    path: '/specimen-library',
    redirect: '/specimen-library/宝玉石',
  },
  {
    path: '/graph',
    name: 'graph',
    component: GraphView,
  },
  {
    path: '/qa',
    name: 'qa',
    component: QAView,
  },
  // {
  //   path: '/gems/appreciation',
  //   name: 'gems-appreciation',
  //   component: GemAppreciationView,
  // },
  {
    path: '/specimen-library/:type',
    name: 'specimen-library',
    component: SpecimenLibraryView,
  },
  {
    path: '/specimen-library/:type/:name',
    name: 'mineral-detail',
    component: MineralDetailView,
  },
  {
    path: '/admin',
    component: AdminLayout,
    redirect: '/admin/login',
    children: [
      {
        path: 'login',
        name: 'admin-login',
        component: AdminLoginView,
      },
      {
        path: 'minerals',
        name: 'admin-minerals',
        meta: { requiresAuth: true },
        component: AdminMineralsView,
      },
    ],
  },
  // 兼容历史地址：默认跳到图谱页
  {
    path: '/:pathMatch(.*)*',
    redirect: '/graph',
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

const getAdminToken = () => authApi.getToken();

router.beforeEach((to, from, next) => {
  const token = getAdminToken();
  if (to.meta.requiresAuth && !token) {
    return next({ name: 'admin-login', query: { redirect: to.fullPath } });
  }
  if (to.name === 'admin-login' && token) {
    return next({ name: 'admin-minerals' });
  }
  next();
});

export default router;


