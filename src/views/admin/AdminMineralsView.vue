<template>
  <div class="min-h-screen bg-[#fbfbfc] text-[#1d1d1f]">
    <!-- 顶部导航 -->
    <nav class="h-20 bg-white/80 backdrop-blur-xl border-b border-slate-100 sticky top-0 z-40 px-8 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <div class="w-10 h-10 bg-emerald-600 rounded-xl flex items-center justify-center text-white soft-shadow">
          <Gem :size="22" />
        </div>
        <div class="flex flex-col">
          <span class="text-lg font-black tracking-tight leading-none">MineralNode</span>
          <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">知识图谱门户</span>
        </div>
      </div>

      <div class="flex items-center gap-6">
        <div class="flex items-center gap-3 px-4 py-2 bg-slate-50 rounded-2xl border border-slate-100">
          <div class="w-8 h-8 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs">
            {{ displayInitial }}
          </div>
          <span class="text-sm font-bold text-slate-700">{{ username }}</span>
          <div class="w-px h-4 bg-slate-200 mx-1" />
          <button @click="handleLogout" class="text-xs font-bold text-slate-400 hover:text-red-500 transition-colors uppercase tracking-wider">
            退出登录
          </button>
        </div>
      </div>
    </nav>

    <!-- 主内容区 -->
    <main class="max-w-7xl mx-auto px-8 py-10">
      <!-- 工具栏与标题 -->
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
        <div>
          <h2 class="text-4xl font-extrabold tracking-tight mb-2">矿物节点管理</h2>
          <p class="text-slate-400 font-medium">在此对图谱中的矿物标本节点进行维护、更新与删除操作</p>
        </div>
        <div class="flex items-center gap-3">
          <div class="relative group">
            <Search class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4 transition-colors group-focus-within:text-emerald-600" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索矿物名称、产地..."
              class="w-72 h-12 pl-12 pr-6 bg-white border border-slate-200 rounded-2xl text-sm font-medium focus:ring-4 focus:ring-emerald-500/5 focus:border-emerald-500/20 outline-none transition-all"
            />
          </div>
          <button
            @click="handleOpenAdd"
            class="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white px-8 h-12 rounded-2xl text-sm font-bold transition-all soft-shadow active:scale-95"
          >
            <Plus :size="18" />
            录入新节点
          </button>
        </div>
      </div>

      <!-- 提示信息 -->
      <div
        v-if="message.text"
        class="mb-8 p-4 rounded-2xl flex items-center justify-between animate-in fade-in slide-in-from-top-4"
        :class="message.type === 'success' ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' : 'bg-red-50 text-red-700 border border-red-100'"
      >
        <div class="flex items-center gap-3">
          <CheckCircle2 v-if="message.type === 'success'" :size="18" />
          <AlertCircle v-else :size="18" />
          <span class="text-sm font-bold">{{ message.text }}</span>
        </div>
        <button @click="message.text = ''">
          <X :size="16" />
        </button>
      </div>

      <!-- 数据面板 -->
      <div class="grid grid-cols-1 gap-8">
        <div class="bg-white rounded-[32px] soft-shadow border border-slate-100 overflow-hidden">
          <div class="p-8 border-b border-slate-50 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <Filter class="text-slate-300" :size="20" />
              <h3 class="font-bold text-lg">矿物资源库</h3>
              <span class="px-2.5 py-1 bg-slate-100 text-slate-500 text-[10px] font-black rounded-lg uppercase tracking-wider">
                {{ filteredMineralsAll.length }} 总计
                <span v-if="filteredMineralsAll.length !== minerals.length" class="ml-1 text-emerald-600">
                  ({{ minerals.length }} 全部)
                </span>
              </span>
            </div>
            <button @click="fetchMinerals" class="p-2 hover:bg-slate-50 rounded-xl text-slate-400 transition-colors" :aria-busy="loading">
              <RefreshCw :size="18" :class="loading ? 'animate-spin' : ''" />
            </button>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left">
              <thead>
                <tr class="text-slate-400 text-[15px] font-black uppercase tracking-[0.2em] border-b border-slate-50">
                  <th class="px-10 py-6">标识与详情</th>
                  <th class="px-10 py-6">化学式</th>
                  <th class="px-10 py-6">产地</th>
                  <th class="px-10 py-6">年代</th>
                  <th class="px-10 py-6 text-right">操作</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-50">
                <template v-if="loading">
                  <tr v-for="i in 4" :key="`skeleton-${i}`">
                    <td colspan="5" class="px-10 py-10">
                      <div class="h-10 bg-slate-50 rounded-2xl animate-pulse" />
                    </td>
                  </tr>
                </template>

                <template v-else-if="filteredMinerals.length">
                  <tr v-for="(m, idx) in filteredMinerals" :key="`${m['中文名称']}-${idx}`" class="group hover:bg-slate-50/40 transition-all">
                    <td class="px-10 py-6">
                      <div class="flex items-center gap-4">
                        <div class="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-black text-xl soft-shadow transition-transform group-hover:scale-105">
                          {{ m['中文名称']?.[0] || '矿' }}
                        </div>
                        <div>
                          <p class="font-bold text-slate-800 text-base tracking-tight">{{ m['中文名称'] }}</p>
                          <p class="text-[10px] text-slate-400 font-bold uppercase tracking-widest">{{ m['英文名称'] || '未知' }}</p>
                        </div>
                      </div>
                    </td>
                    <td class="px-10 py-6">
                      <span class="px-3 py-1.5 bg-slate-100 text-slate-600 rounded-xl text-xs font-mono font-bold tracking-tight">
                        {{ m['化学式'] || '--' }}
                      </span>
                    </td>
                    <td class="px-10 py-6">
                      <div class="flex items-center gap-2 text-slate-500 text-sm font-medium">
                        <MapPin :size="14" class="text-slate-300" />
                        {{ m['产地'] || '未知' }}
                      </div>
                    </td>
                    <td class="px-10 py-6 text-sm text-slate-400 font-bold">{{ m['发现年份'] || '--' }}</td>
                    <td class="px-10 py-6 text-right">
                      <div class="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-all transform translate-x-2 group-hover:translate-x-0">
                        <button
                          @click="handleEdit(m)"
                          class="w-10 h-10 flex items-center justify-center rounded-xl bg-white border border-slate-100 text-slate-400 hover:text-emerald-600 soft-shadow transition-all"
                        >
                          <Edit3 :size="16" />
                        </button>
                        <button
                          @click="handleDelete(m['中文名称'])"
                          class="w-10 h-10 flex items-center justify-center rounded-xl bg-white border border-slate-100 text-slate-400 hover:text-red-500 soft-shadow transition-all"
                        >
                          <Trash2 :size="16" />
                        </button>
                      </div>
                    </td>
                  </tr>
                </template>

                <template v-else>
                  <tr>
                    <td colspan="5" class="px-10 py-20 text-center">
                      <div class="flex flex-col items-center gap-4 opacity-60">
                        <Box :size="48" />
                        <p class="text-sm font-bold uppercase tracking-widest">未找到矿物节点</p>
                      </div>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>

          <!-- 分页组件 -->
          <div v-if="!loading && filteredMineralsAll.length > 0" class="px-8 py-6 border-t border-slate-50 flex items-center justify-between">
            <div class="text-sm text-slate-500 font-medium">
              显示第 {{ (currentPage - 1) * pageSize + 1 }} - {{ Math.min(currentPage * pageSize, filteredMineralsAll.length) }} 条，
              共 {{ filteredMineralsAll.length }} 条
            </div>
            <div class="flex items-center gap-2">
              <button
                @click="currentPage = Math.max(1, currentPage - 1)"
                :disabled="currentPage === 1"
                class="w-10 h-10 flex items-center justify-center rounded-xl border border-slate-200 text-slate-400 hover:text-slate-700 hover:border-slate-300 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronLeft :size="18" />
              </button>

              <div class="flex items-center gap-1">
                <button
                  v-for="page in getPageNumbers()"
                  :key="page"
                  @click="currentPage = page"
                  :class="[
                    'min-w-[40px] h-10 px-3 flex items-center justify-center rounded-xl text-sm font-bold transition-all',
                    page === currentPage
                      ? 'bg-slate-900 text-white'
                      : 'text-slate-600 hover:bg-slate-50 border border-transparent hover:border-slate-200',
                    page === '...' && 'cursor-default hover:bg-transparent',
                  ]"
                >
                  {{ page }}
                </button>
              </div>

              <button
                @click="currentPage = Math.min(totalPages, currentPage + 1)"
                :disabled="currentPage === totalPages"
                class="w-10 h-10 flex items-center justify-center rounded-xl border border-slate-200 text-slate-400 hover:text-slate-700 hover:border-slate-300 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronRight :size="18" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 表单抽屉层 -->
    <div v-if="isFormOpen" class="fixed inset-0 z-50 overflow-hidden">
      <div class="absolute inset-0 bg-slate-900/10 backdrop-blur-sm" @click="setIsFormOpen(false)" />
      <div class="absolute inset-y-0 right-0 max-w-2xl w-full bg-white shadow-2xl animate-in slide-in-from-right duration-500">
        <form class="h-full flex flex-col" @submit.prevent="handleFormSubmit">
          <div class="px-8 py-8 border-b border-slate-50 flex items-center justify-between">
            <div>
              <h3 class="text-2xl font-black tracking-tight">{{ editingName ? '更新元数据' : '录入新矿物' }}</h3>
              <p class="text-slate-400 text-sm font-medium mt-1">
                {{ editingName ? `正在修改: ${editingName}` : '请填写矿物节点的相关科学属性' }}
              </p>
            </div>
            <button type="button" @click="setIsFormOpen(false)" class="w-10 h-10 flex items-center justify-center rounded-full hover:bg-slate-50 transition-colors">
              <X :size="20" />
            </button>
          </div>

          <div class="flex-1 overflow-y-auto px-10 py-10 space-y-12 custom-scroll">
            <!-- 基础属性组 -->
            <section class="space-y-8">
              <div class="flex items-center gap-3 text-emerald-600">
                <Database :size="18" />
                <h4 class="font-bold text-lg uppercase tracking-widest">基本信息</h4>
              </div>

              <div class="grid grid-cols-2 gap-6">
                <div class="space-y-2 col-span-2 md:col-span-1">
                  <label class="text-[14px] font-black text-slate-600 uppercase tracking-widest ml-1">中文名称 *</label>
                  <input
                    v-model="formData['中文名称']"
                    :disabled="Boolean(editingName)"
                    required
                    class="w-full h-12 bg-slate-50 border-transparent focus:bg-white focus:border-emerald-500 rounded-2xl px-5 text-sm font-bold outline-none transition-all disabled:opacity-50"
                  />
                </div>

                <div class="space-y-2 col-span-2 md:col-span-1">
                  <label class="text-[14px] font-black text-slate-600 uppercase tracking-widest ml-1">英文名称</label>
                  <input
                    v-model="formData['英文名称']"
                    class="w-full h-12 bg-slate-50 border-transparent focus:bg-white focus:border-emerald-500 rounded-2xl px-5 text-sm font-bold outline-none transition-all"
                  />
                </div>

                <div class="space-y-2 col-span-2">
                  <label class="text-[14px] font-black text-slate-600 uppercase tracking-widest ml-1">晶体化学式</label>
                  <input
                    v-model="formData['化学式']"
                    class="w-full h-12 bg-slate-50 border border-slate-200 focus:bg-white focus:border-emerald-500 rounded-2xl px-5 text-sm font-mono font-bold outline-none transition-all"
                  />
                </div>

                <div class="space-y-2 col-span-2">
                  <label class="text-[14px] font-black text-slate-600 uppercase tracking-widest ml-1">产地</label>
                  <input
                    v-model="formData['产地']"
                    class="w-full h-12 bg-slate-50 border border-slate-200 focus:bg-white focus:border-emerald-500 rounded-2xl px-5 text-sm font-bold outline-none transition-all"
                  />
                </div>

                <div class="space-y-2">
                  <label class="text-[14px] font-black text-slate-600 uppercase tracking-widest ml-1">颜色</label>
                  <input
                    v-model="formData['颜色']"
                    class="w-full h-12 bg-slate-50 border border-slate-200 focus:bg-white focus:border-emerald-500 rounded-2xl px-5 text-sm font-bold outline-none transition-all"
                  />
                </div>

                <div class="space-y-2">
                  <label class="text-[14px] font-black text-slate-600 uppercase tracking-widest ml-1">发现/命名年份</label>
                  <input
                    v-model="formData['发现年份']"
                    class="w-full h-12 bg-slate-50 border border-slate-200 focus:bg-white focus:border-emerald-500 rounded-2xl px-5 text-sm font-bold outline-none transition-all"
                  />
                </div>

                <div class="space-y-2 col-span-2">
                  <label class="text-[14px] font-black text-slate-600 uppercase tracking-widest ml-1">基本描述</label>
                  <textarea
                    v-model="formData['基本描述']"
                    rows="3"
                    class="w-full bg-slate-50 border border-slate-200 focus:bg-white focus:border-emerald-500 rounded-[20px] p-5 text-sm font-medium outline-none transition-all resize-none"
                  />
                </div>
              </div>
            </section>

            <!-- 分类体系组 -->
            <section class="space-y-8 pt-4">
              <div class="flex items-center gap-3 text-emerald-600">
                <Layers :size="18" />
                <h4 class="font-bold text-lg uppercase tracking-widest">分类体系</h4>
              </div>

              <div class="space-y-10">
                <div v-for="sys in [1, 2, 3]" :key="`sys-${sys}`" class="bg-slate-50 rounded-[32px] p-8 border border-slate-200">
                  <div class="flex items-center justify-between mb-6">
                    <span class="text-[16px] font-black text-emerald-600 uppercase tracking-[0.2em]">分类体系 {{ sys }}</span>
                    <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  </div>

                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div v-for="lv in [1, 2, 3, 4]" :key="`sys-${sys}-lv-${lv}`" class="space-y-1.5">
                      <label class="text-[14px] font-black text-slate-600 uppercase ml-1">层级 {{ lv }}</label>
                      <input
                        v-model="formData[`标本分类${sys}-${lv}`]"
                        :placeholder="`请输入层级 ${lv} 名称`"
                        class="w-full h-10 bg-white border border-slate-200 rounded-xl px-4 text-xs font-bold text-slate-600 focus:border-emerald-500/40 outline-none transition-all"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </section>
          </div>

          <div class="px-10 py-8 border-t border-slate-50 flex items-center justify-end gap-4">
            <button type="button" @click="setIsFormOpen(false)" class="px-8 py-3 text-slate-400 font-bold hover:text-slate-800 transition-all">
              取消
            </button>
            <button type="submit" class="flex items-center gap-2 px-10 py-4 bg-slate-900 hover:bg-slate-800 text-white font-bold rounded-2xl soft-shadow transition-all active:scale-95">
              <Save :size="18" />
              同步至图谱
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import {
  Plus,
  Search,
  RefreshCw,
  Trash2,
  Edit3,
  Gem,
  Box,
  MapPin,
  X,
  Save,
  AlertCircle,
  CheckCircle2,
  Filter,
  Database,
  Layers,
  ChevronLeft,
  ChevronRight,
} from 'lucide-vue-next';
import { authApi, mineralApi } from '../../api/adminPortal';

type MineralData = Record<string, string>;

const router = useRouter();

const username = ref(authApi.getUsername());
const minerals = ref<MineralData[]>([]);
const loading = ref(true);
const isFormOpen = ref(false);
const editingName = ref<string | null>(null);
const searchQuery = ref('');
const message = ref<{ text: string; type: 'success' | 'error' | null }>({ text: '', type: null });

// 分页相关
const currentPage = ref(1);
const pageSize = ref(20);

const initialForm: MineralData = {
  中文名称: '',
  英文名称: '',
  化学式: '',
  产地: '',
  颜色: '',
  发现年份: '',
  基本描述: '',
};
const formData = ref<MineralData>({ ...initialForm });

const displayInitial = computed(() => (username.value ? username.value[0].toUpperCase() : 'A'));

const ensureAuthed = () => {
  if (!authApi.getToken()) {
    router.replace('/admin/login');
  }
};

const fetchMinerals = async () => {
  loading.value = true;
  try {
    const res = await mineralApi.getAll();
    if (res?.success && Array.isArray(res.data)) {
      minerals.value = res.data as MineralData[];
    } else {
      message.value = { text: res?.message || '无法获取矿物数据', type: 'error' };
    }
  } catch (err) {
    message.value = { text: '获取数据失败，已使用本地缓存', type: 'error' };
  } finally {
    setTimeout(() => {
      loading.value = false;
    }, 300);
  }
};

// 过滤后的矿物列表（不分页）
const filteredMineralsAll = computed(() =>
  minerals.value.filter((m) => {
    const query = searchQuery.value.trim().toLowerCase();
    if (!query) return true;
    const cn = m['中文名称'] || '';
    const en = m['英文名称'] || '';
    const origin = m['产地'] || '';
    return cn.toLowerCase().includes(query) || en.toLowerCase().includes(query) || origin.toLowerCase().includes(query);
  }),
);

// 分页后的矿物列表
const filteredMinerals = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  const end = start + pageSize.value;
  return filteredMineralsAll.value.slice(start, end);
});

// 总页数
const totalPages = computed(() => Math.ceil(filteredMineralsAll.value.length / pageSize.value));

// 当搜索时重置到第一页
watch(searchQuery, () => {
  currentPage.value = 1;
});

const handleOpenAdd = () => {
  formData.value = { ...initialForm };
  editingName.value = null;
  isFormOpen.value = true;
};

const setIsFormOpen = (value: boolean) => {
  isFormOpen.value = value;
};

const handleEdit = (mineral: MineralData) => {
  formData.value = { ...mineral };
  editingName.value = mineral['中文名称'] || null;
  isFormOpen.value = true;
};

const handleDelete = async (name: string) => {
  if (!name) return;
  const confirmed = window.confirm(`确定要彻底移除矿物节点 "${name}" 吗？此操作不可撤销。`);
  if (!confirmed) return;
  try {
    const res = await mineralApi.remove(name);
    if (res?.success) {
      message.value = { text: '节点已成功从图谱中移除', type: 'success' };
      fetchMinerals();
    } else {
      message.value = { text: res?.message || '删除失败', type: 'error' };
    }
  } catch (err) {
    message.value = { text: '删除请求失败，请检查网络连接', type: 'error' };
  }
};

const handleFormSubmit = async () => {
  if (!formData.value['中文名称']) {
    message.value = { text: '请填写中文名称', type: 'error' };
    return;
  }
  try {
    const apiCall = editingName.value ? mineralApi.update : mineralApi.add;
    const payload = { ...formData.value };
    const res = await apiCall(payload as any);
    if (res?.success) {
      message.value = {
        text: editingName.value ? '节点元数据更新成功' : '新矿物节点已同步至图谱',
        type: 'success',
      };
      isFormOpen.value = false;
      fetchMinerals();
    } else {
      message.value = { text: res?.message || '提交失败', type: 'error' };
    }
  } catch (err) {
    message.value = { text: '提交失败，后端服务无响应', type: 'error' };
  }
};

const handleLogout = () => {
  authApi.logout();
  router.replace('/admin/login');
};

// 生成分页页码数组
const getPageNumbers = () => {
  const total = totalPages.value;
  const current = currentPage.value;
  const pages: (number | string)[] = [];

  if (total <= 7) {
    // 如果总页数少于等于7，显示所有页码
    for (let i = 1; i <= total; i++) {
      pages.push(i);
    }
  } else {
    // 总是显示第一页
    pages.push(1);

    if (current <= 4) {
      // 当前页在前4页
      for (let i = 2; i <= 5; i++) {
        pages.push(i);
      }
      pages.push('...');
      pages.push(total);
    } else if (current >= total - 3) {
      // 当前页在后4页
      pages.push('...');
      for (let i = total - 4; i <= total; i++) {
        pages.push(i);
      }
    } else {
      // 当前页在中间
      pages.push('...');
      for (let i = current - 1; i <= current + 1; i++) {
        pages.push(i);
      }
      pages.push('...');
      pages.push(total);
    }
  }

  return pages;
};

onMounted(() => {
  ensureAuthed();
  fetchMinerals();
});
</script>

<style scoped>
.soft-shadow {
  box-shadow: 0 12px 40px rgba(15, 23, 42, 0.08);
}

.custom-scroll::-webkit-scrollbar {
  width: 8px;
}

.custom-scroll::-webkit-scrollbar-thumb {
  background: rgba(15, 23, 42, 0.12);
  border-radius: 999px;
}
</style>

