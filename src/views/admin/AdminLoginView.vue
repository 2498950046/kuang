<template>
  <div class="min-h-screen bg-gradient-to-br from-emerald-50/40 via-white to-white flex items-center justify-center px-4 py-10">
    <div class="w-full max-w-5xl grid grid-cols-1 md:grid-cols-2 bg-white rounded-[40px] border border-slate-100 soft-shadow-lg overflow-hidden">
      <!-- 左侧品牌视觉区 -->
      <section class="hidden md:flex flex-col justify-between px-16 py-16 bg-slate-50 border-r border-slate-100">
        <div>
          <div class="flex items-center gap-3 text-emerald-600 mb-12">
            <Gem :size="32" stroke-width="2.5" />
            <span class="font-extrabold text-2xl tracking-tight text-slate-900">后台管理系统</span>
          </div>

          <h2 class="text-4xl font-extrabold leading-tight text-slate-900 mb-10">
            连接节点，洞察<br />
            <span class="text-emerald-600">矿物图谱</span>与关联脉络
          </h2>
        </div>

        <div class="space-y-4">
          <div class="flex items-center gap-4 px-4 py-4 bg-white rounded-2xl soft-shadow text-slate-700 font-medium w-max">
            <div class="w-10 h-10 rounded-full bg-emerald-50 flex items-center justify-center text-emerald-600">
              <ShieldCheck :size="20" />
            </div>
            <p class="text-sm font-medium">矿物图谱节点管理</p>
          </div>

          <!-- <p class="text-xs text-slate-400 font-medium ml-1">© 2024 Geological Data Management System</p> -->
        </div>
      </section>

      <!-- 右侧表单区 -->
      <section class="px-10 sm:px-16 py-16 flex flex-col justify-center bg-white relative">
        <!-- 返回按钮 -->
        <button
          @click="goBackToGraph"
          class="absolute top-6 left-6 sm:left-10 flex items-center gap-2 text-slate-500 hover:text-emerald-600 transition-colors group"
          title="返回图谱页面"
        >
          <ArrowLeft :size="18" class="group-hover:-translate-x-1 transition-transform" />
          <span class="text-sm font-medium">返回图谱</span>
        </button>

        <div class="mb-10">
          <h3 class="text-2xl font-extrabold text-slate-900 mb-2">欢迎回来</h3>
          <p class="text-slate-500 text-sm">请输入账号密码以访问图谱中心</p>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-6">
          <div class="space-y-2">
            <label class="text-[11px] font-bold text-slate-400 uppercase tracking-[0.22em]">账号名称</label>
            <input
              v-model="username"
              type="text"
              class="w-full h-14 rounded-2xl bg-slate-50 border border-transparent px-6 text-slate-800 font-medium placeholder-slate-400 focus:border-emerald-500 focus:bg-white focus:ring-4 focus:ring-emerald-500/5 outline-none transition-all"
              placeholder="admin"
              autocomplete="username"
            />
          </div>

          <div class="space-y-2">
            <label class="text-[11px] font-bold text-slate-400 uppercase tracking-[0.22em]">安全密钥</label>
            <input
              v-model="password"
              type="password"
              class="w-full h-14 rounded-2xl bg-slate-50 border border-transparent px-6 text-slate-800 font-medium placeholder-slate-400 focus:border-emerald-500 focus:bg-white focus:ring-4 focus:ring-emerald-500/5 outline-none transition-all"
              placeholder="••••••••"
              autocomplete="current-password"
            />
          </div>

          <div v-if="error" class="text-red-500 text-xs font-bold flex items-center gap-2 px-1">
            <span class="w-1 h-1 rounded-full bg-red-500" />
            {{ error }}
          </div>

          <button
            :disabled="loading"
            class="w-full h-14 bg-slate-900 hover:bg-slate-800 text-white rounded-2xl font-bold flex items-center justify-center gap-2 transition-all active:scale-[0.98] shadow-xl shadow-slate-200 disabled:opacity-80 disabled:cursor-not-allowed"
          >
            <template v-if="loading">
              <div class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            </template>
            <template v-else>
              <span>进入管理系统</span>
              <ArrowRight :size="18" />
            </template>
          </button>
        </form>

        <div class="mt-10 flex justify-center">
          <button class="text-xs font-bold text-slate-400 hover:text-emerald-600 transition-colors flex items-center gap-2">
            <Compass :size="14" />
            无法登录？
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { Gem, ShieldCheck, ArrowRight, Compass, ArrowLeft } from 'lucide-vue-next';
import { authApi } from '../../api/adminPortal';

const router = useRouter();

const username = ref('admin');
const password = ref('');
const loading = ref(false);
const error = ref('');

const goBackToGraph = () => {
  router.push('/graph');
};

const handleSubmit = async () => {
  if (!username.value || !password.value) {
    error.value = '请输入账号和密钥';
    return;
  }
  loading.value = true;
  error.value = '';
  try {
    const res = await authApi.login({ username: username.value, password: password.value });
    // 检查登录是否成功：要么返回 success，要么 token 已保存到 localStorage
    const token = authApi.getToken();
    if (res?.success || token) {
      // 登录成功，跳转到矿物管理页面
      await router.replace('/admin/minerals');
    } else {
      error.value = res?.message || '凭据验证失败';
    }
  } catch (err) {
    console.error('登录错误:', err);
    error.value = '无法连接至安全认证中心';
  } finally {
    loading.value = false;
  }
};
</script>
