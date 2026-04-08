<!-- src/App.vue -->
<template>
  <div id="app-container" :class="themeClass">
    <template v-if="isAdminRoute">
      <router-view />
    </template>
    <template v-else>
      <!-- 启动阶段：只显示全屏 Loading，避免任何介绍页或主界面残影 -->
      <transition name="fade">
        <div v-if="bootLoading" class="boot-loading">
          <Loading />
        </div>
      </transition>

      <!-- 启动完成后，正常显示系统介绍 + 主界面 -->
      <div v-if="!bootLoading">
        <svg class="squircle-defs" width="0" height="0" aria-hidden="true">
          <defs>
            <clipPath id="squircleClip" clipPathUnits="objectBoundingBox">
              <path d="M 0,0.5 C 0,0 0,0 0.5,0 S 1,0 1,0.5 1,1 0.5,1 0,1 0,0.5" />
            </clipPath>
          </defs>
        </svg>

        <!-- SystemIntroduction 始终挂载：
             - 首页：展示全屏介绍层（show-overlay=true）
             - 非首页：只显示右下角“回到首页”浮动按钮，不盖住图谱 -->
        <SystemIntroduction
          :has-entered-system="hasEnteredSystem"
          :stats-data="globalStats"
          :hide-home-button="currentView === 'ai'"
          :show-overlay="isHomeRoute"
          @enter-system="handleEnterSystem"
          @open-home="handleBackToHome"
        />

        <!-- 首页仅加载 SystemIntroduction；图谱/问答等重组件仅在非首页挂载 -->
        <template v-if="!isHomeRoute">
        <!-- 顶部横幅（抽离为独立组件） -->
        <TopBanner
          v-if="isGraphView && !isMineralDetailVisible && !isSpecimenRoute"
          :title="graphTitle"
          ref="bannerRef"
        />

          <!-- 图谱列表（抽离为独立组件） -->
        <div
          v-if="isGraphView && !isSpecimenRoute && sidebarMode === 'graph' && !isMineralDetailVisible"
          class="mac-glass floating-sidebar"
          :class="{ open: categoryListOpen }"
          ref="sidebarRef"
        >
          <GraphSpecimenSidebar
            :category-list-open="categoryListOpen"
            :specimen-list="specimenList"
            :selected-specimen-type="selectedSpecimenType"
            :specimen-color-palettes="specimenColorPalettes"
            :sidebar-mode="sidebarMode"
            @update:category-list-open="val => (categoryListOpen = val)"
            @specimen-click="handleSpecimenClick"
            @toggle-sidebar-mode="toggleSidebarMode"
            @go-to-specimen-library="goToSpecimenLibrary"
          />
        </div>

          <!-- 标本库列表 -->
        <SpecimenLibrarySidebar 
          v-if="isGraphView && !isSpecimenRoute && sidebarMode === 'library'"
          :sidebar-mode="sidebarMode"
          @switch-mode="toggleSidebarMode"
        />

          <!-- 顶部操作栏（抽离为独立组件） -->
        <TopActionsBar
          v-if="(isGraphView || currentView === 'ai') && !isMineralDetailVisible && !isSpecimenRoute"
          :show-search="isGraphView"
          :theme="theme"
          :button-label="detailButtonLabel"
          :search-loading="searchLoading"
          :search-type="searchType"
          @open-search="handleSearch"
          @go-to-admin="goToAdmin"
          @toggle-theme="toggleTheme"
          @toggle-main-view="toggleMainView"
          @update:searchType="searchType = $event"
          ref="actionsRef"
        />

          <div class="graph-stage" :class="{ 'mineral-mode': isMineralDetailVisible }" ref="graphStageRef">
        <!-- 移除背景遮罩层，不添加笼罩效果 -->

          <!-- 标本库路由视图 -->
        <transition
          name="page-fade"
          mode="out-in"
          @before-leave="onSpecimenRouteBeforeLeave"
          @after-leave="onSpecimenRouteAfterLeave"
        >
          <router-view v-if="route.path.startsWith('/specimen-library')" :key="route.path" />
        </transition>

          <!-- 图谱容器 - 当矿物面板打开时向左移动并变暗 -->
        <div 
          v-if="!route.path.startsWith('/specimen-library') && !isSpecimenRouteLeaving"
          class="graph-wrapper" 
          :class="{ 'mineral-panel-open': isMineralDetailVisible }"
        >
          <transition name="view-fade" mode="out-in">
            <div :key="currentView" class="view-shell">
              <div v-if="currentView === 'graph'" class="graph-area">
                <!-- 查询回答显示区域（抽离为独立组件） -->
                <GraphAnswerPanel
                  v-if="graphQueryAnswer"
                  :answer="graphQueryAnswer"
                  @close="graphQueryAnswer = ''"
                  ref="graphAnswerRef"
                />
                
                <div class="graph-content" :style="graphScaleStyle">
                  <GraphChart3D
                    ref="graphRef"
                    :graph-data="filteredData"
                    :style-config="styleConfig"
                    :layout-config="layoutConfig"
                    :force-label-show="forceLabelShow"
                    :key="chartKey"
                    :entityCategoryLabels="entityCategoryLabels"
                    :edgeTypeLabels="edgeTypeLabels"
                    :selected-specimen-type="selectedSpecimenType"
                    :expanded-mineral-nodes="Array.from(expandedMineralNodes)"
                    :expanded-category-nodes="Array.from(expandedCategoryNodes)"
                    :mineral-child-nodes-count="Object.fromEntries(mineralChildNodesCount)"
                    :expand-level="expandLevel"
                    @legend-select-changed="handleLegendChange"
                    @query-related-nodes="handleRelatedNodesQuery"
                    @node-select="handleNodeSelect"
                    @edge-select="handleEdgeSelect"
                    @clear-select="handleClearSelect"
                    @toggle-mineral-expansion="handleToggleMineralExpansion"
                    @toggle-category-expansion="handleToggleCategoryExpansion"
                  />
                </div>

                <TimeSlider
                  v-if="TimeSliderCurrentView"
                  :min-date="minGraphDate"
                  :max-date="maxGraphDate"
                  :time-period-labels="timePeriodMap"
                  v-model:selected-range="currentSelectedRange"
                />
              </div>

              <div v-else-if="currentView === 'table'" class="table-view mac-glass-panel">
                <TableView :table-data="tableData" />
              </div>

              <div v-else class="ai-view mac-glass-panel">
                <AIChat @graph-query-result="handleAIGraphQuery" />
              </div>
            </div>
          </transition>

          <transition name="fade">
            <div v-if="viewLoading || isLoading" class="loading-overlay">
              <Loading />
            </div>
          </transition>
        </div>

          <!-- 矿物详情面板 - 从右侧滑入（抽离为独立组件） -->
        <transition name="mineral-panel">
          <MineralDetailPanel
            v-if="isMineralDetailVisible"
            :mineral-title-color="mineralTitleColor"
            :mineral-detail="mineralDetail"
            :active-specimen="activeSpecimen"
            :specimen-state="specimenState"
            :current-specimen-image="currentSpecimenImage"
            :specimen-description="specimenDescription"
            :mineral-basic-info="mineralBasicInfo"
            :mineral-description-k-vs="mineralDescriptionKVs"
            :mineral-detail-image="mineralDetailImage"
            :on-close="handleClearSelect"
            :on-toggle-specimen-fullscreen="toggleSpecimenFullscreen"
            :on-prev-sample="prevSample"
            :on-next-sample="nextSample"
            :on-image-pointer-down="onImagePointerDown"
            :on-image-pointer-move="onImagePointerMove"
            :on-image-pointer-up="onImagePointerUp"
            :is-gemstone-graph="isGemstoneGraph"
          />
        </transition>

          <div class="mac-glass info-panel" v-if="currentView !== 'ai' && !isMineralDetailVisible && !isSpecimenRoute" ref="infoPanelRef">
          <InfoPanel
            :selected-item="selectedItem"
            :nodes="rawData.nodes"
            :entity-category-labels="entityCategoryLabels"
            :edge-type-labels="edgeTypeLabels"
            :property-labels="propertyLabels"
            :node-color-map="nodeColorMap"
          />
        </div>
        </div>

        <!-- 底部 Dock 栏（抽离为独立组件） -->
        <BottomDock
          v-if="isGraphView && !isMineralDetailVisible && !isSpecimenRoute"
          v-model:dock-panel="dockPanel"
          :stats="globalStats"
          :is-loading-stats="!hasLoadedGlobalStats"
          :selected-specimen-type="selectedSpecimenType"
          v-model:layout-config="layoutConfig"
          :selected-item="selectedItem"
          :nodes="rawData.nodes"
          :entity-category-labels="entityCategoryLabels"
          :edge-type-labels="edgeTypeLabels"
          :property-labels="propertyLabels"
          :zoom-level="zoomLevel"
          :expand-level="expandLevel"
          :is-gesture-enabled="isGestureEnabled"
          @run-query="handleStatsQuery"
          @zoom-in="zoomIn"
          @zoom-out="zoomOut"
          @toggle-fullscreen="toggleFullscreen"
          @update:expand-level="expandLevel = $event"
          @toggle-gesture="toggleGestureControl"
          ref="dockRef"
        />

      <!-- 手势控制覆盖层 -->
          <GestureOverlay
          v-if="isGestureEnabled && isGraphView && !isMineralDetailVisible && !isSpecimenRoute"
          :on-gesture="handleGesture"
        />

      <!-- 手势指引 -->
          <GestureGuide
          v-if="isGestureEnabled && isGraphView && !isMineralDetailVisible && !isSpecimenRoute"
          :gesture-state="gestureState"
          :stability-count="gestureStability.count"
          :confirmed-gesture="confirmedGesture"
          :hide-status-bar="!!dockPanel"
        />

          <div v-if="isGraphView && !isMineralDetailVisible && !isSpecimenRoute" class="overview-fab">
          <OverviewPanel
            :is-loading="isLoading"
            :overview="overview"
            :raw-data="rawData"
            :editor-target-name="editor.targetName"
            :entity-category-labels="entityCategoryLabels"
            :edge-type-labels="edgeTypeLabels"
            :total-nodes="globalStats.totalNodes"
            :total-edges="globalStats.totalEdges"
            :node-color-map="nodeColorMap"
            @show-editor="handleShowEditor"
          />
        </div>

      <!-- 节点操作提示卡片：在小恐龙上方，与 Dino 无关联，独立显示逻辑 -->
          <NodeTipCard v-if="isGraphView && !isMineralDetailVisible && !isSpecimenRoute" />

        <!-- Dino 组件：只在图谱视图时显示，点击后切换到智能问答页面 -->
          <Dino v-if="isGraphView && !isMineralDetailVisible && !isSpecimenRoute" @navigate-to-ai="handleNavigateToAI" />

          <StyleEditor
          :visible="editor.visible"
          :position="editor.position"
          :target-type="editor.targetType"
          :target-name="editor.targetName"
          :config="activeEditorConfig"
          :available-props="availableLabelProps"
          :entity-category-labels="entityCategoryLabels"
          :edge-type-labels="edgeTypeLabels"
          @close="editor.visible = false"
          @update-style="handleStyleUpdate"
          @update-position="handleEditorMove"
        />

        </template>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { useRouter, useRoute } from 'vue-router';
// 仅保留暗色模式，不再需要 useDark/useToggle
import gsap from 'gsap';
import gemsBasicInfoCsv from '../backend_all/backendAdmin/mineral_data_test/gemsBasicInfo.csv?raw';

// 导入子组件
import GraphChart3D from './components/GraphChart3D.vue';
import GraphSpecimenSidebar from './components/GraphSpecimenSidebar.vue';
import TableView from './components/TableView.vue';
import StyleEditor from './components/StyleEditor.vue';
import OverviewPanel from './components/OverviewPanel.vue';
import InfoPanel from './components/InfoPanel.vue';
import TimeSlider from './components/TimeSlider.vue';
import AIChat from './components/AIChat.vue';
import SystemIntroduction from './components/SystemIntroduction.vue';
import Loading from './components/Loading.vue';
import Dino from './components/Dino.vue';
import NodeTipCard from './components/NodeTipCard.vue';
import SpecimenLibrarySidebar from './components/SpecimenLibrarySidebar.vue';
import MineralDetailPanel from './components/MineralDetailPanel.vue';
import TopBanner from './components/TopBanner.vue';
import TopActionsBar from './components/TopActionsBar.vue';
import GraphAnswerPanel from './components/GraphAnswerPanel.vue';
import BottomDock from './components/BottomDock.vue';
import GestureOverlay from './components/GestureOverlay.vue';
import GestureGuide from './components/GestureGuide.vue';

// 导入工具函数
import { graphQuery, fetchMineralSamples, nl2cypher, getMineralInfo, getSpecimenDescriptionByTable2Id } from './api';
import { GestureType } from './services/gestureRecognition';
import { createGestureControl } from './utils/gesture/gestureControl.js';
import { parseGemsBasicInfo, getPointerX, preloadSamplesImages, preloadImage } from './utils/mineral/mineralAppHelpers.js';
import { createGraphEngine } from './utils/graph/graphEngine.js';
import { normalizeLinkTime as normalizeLinkTimeUtil, computeGraphDateRange } from './utils/graph/graphTimeRange.js';
import {
  getCategoryChildNodes as getCategoryChildNodesUtil,
  getMineralChildNodes as getMineralChildNodesUtil,
  calculateMineralChildNodesCount as calculateMineralChildNodesCountUtil,
} from './utils/graph/graphExpandHelpers.js';
import { buildSelectedItemFromNode, buildSelectedItemFromEdge } from './utils/graph/graphSelection.js';
import { getAvailableLabelProps as getAvailableLabelPropsUtil } from './utils/graph/graphStyleEditor.js';
import { fetchGlobalStats as fetchGlobalStatsFromApi } from './utils/graph/graphStats.js';
import { useMineralDetailPanelLogic } from './utils/mineral/mineralDetailPanelLogic.js';
import { createGraphInteractionsApp } from './utils/graph/graphInteractionsApp.js';
import {
  initExpandedState as initExpandedStateUtil,
  computeAutoExpandMineralNodesInResult as computeAutoExpandMineralNodesInResultUtil,
} from './utils/graph/graphExpansionState.js';
import { computeFilteredData as computeFilteredDataUtil } from './utils/graph/graphFilteredData.js';
import { createGraphSearchHandlers } from './utils/graph/graphSearch.js';
import {
  CATEGORY_NODE_TYPES,
  MINERAL_NODE_TYPES,
  CHILD_CATEGORIES,
  INVALID_VALUES,
  entityCategoryLabels,
  edgeTypeLabels,
  propertyLabels,
  specimenColorPalettes,
  specimenTypeQueries,
  specimenTypeToTitleMap,
  specimenList,
} from './utils/graph/graphSpecimenConfig.js';

import { parseMineralDescriptionKVs } from './utils/mineral/mineralDescriptionParser.js';

const router = useRouter();
const route = useRoute();

// 首页路由：只展示 SystemIntroduction，不挂载图谱重组件/不触发图谱初始化
// 使用 window.location.pathname 作为初始值，避免在非首页刷新时出现首页残影
const isHomeRoute = ref(typeof window !== 'undefined' ? window.location.pathname === '/' : false);
watch(
  () => route.path,
  (newPath) => {
    isHomeRoute.value = newPath === '/';
  }
);

// 标本库路由离场期间，先不渲染下层 view（避免离场动画时“露底”造成切影/闪烁）
const isSpecimenRouteLeaving = ref(false);
function onSpecimenRouteBeforeLeave() {
  isSpecimenRouteLeaving.value = true;
}
function onSpecimenRouteAfterLeave() {
  isSpecimenRouteLeaving.value = false;
}

// 解析 gemsBasicInfo.csv
const gemNameMap = parseGemsBasicInfo(gemsBasicInfoCsv);
console.log('Parsed gemNameMap:', gemNameMap);

// 启动阶段全屏 Loading，避免任何介绍页/主界面闪现
const bootLoading = ref(true);

// 工具函数：判断节点类型
const isMineralCategory = (category) => MINERAL_NODE_TYPES.includes(category || '');
const isCategoryType = (category) => CATEGORY_NODE_TYPES.includes(category || '');
const isChildCategory = (category) => CHILD_CATEGORIES.includes(category || '');

// --- STATE MANAGEMENT ---
const rawData = reactive({ nodes: [], links: [] });
const tableData = reactive({ headers: [], rows: [] });
// currentView 依然控制图谱/智能问答内部视图，但会和路由保持同步
const currentView = ref('graph');
const TimeSliderCurrentView = ref(false);
const dockPanel = ref(null);
const zoomLevel = ref(1);
const searchKeyword = ref('');
const searchType = ref('name');
const categoryListOpen = ref(true);

// 搜索优化相关状态
const searchLoading = ref(false);
const searchCache = ref(new Map()); // 缓存搜索结果
const searchHistory = ref([]); // 搜索历史
const sidebarMode = ref('graph'); // 'graph' 或 'library'

// 手势控制相关状态
const isGestureEnabled = ref(false);
const gestureState = ref({ type: GestureType.NONE, x: 0, y: 0, distance: 0, fingerCount: 0 });
const gestureStability = ref({ type: GestureType.NONE, count: 0, lastX: 0, lastY: 0 });
const confirmedGesture = ref(null);
const lastGestureState = ref({ type: GestureType.NONE, x: 0, y: 0, distance: 0, fingerCount: 0 });

// 收缩式交互功能：管理已展开的矿物节点和分类节点
const expandedMineralNodes = ref(new Set()); // 记录已展开的矿物节点ID（字符串格式）
const expandedCategoryNodes = ref(new Set()); // 记录已展开的分类节点ID（字符串格式）
const mineralChildNodesCount = ref(new Map()); // 记录每个矿物节点的子节点数量

// 标志：是否显示所有节点（从统计卡片点击时使用）
const showAllNodesFromStats = ref(false);

// 标志：统计卡片的全局统计是否已经加载（只在首次打开“统计”面板时按需请求）
const hasLoadedGlobalStats = ref(false);

// 展开层级：1级=只显示分类节点，2级=显示分类+矿物节点，3级=显示所有节点
const expandLevel = ref(3);

// 初始化层级状态
function initializeLevelState(level) {
  const result = initExpandedStateUtil({
    nodes: rawData.nodes,
    level,
    isCategoryType,
    isMineralCategory,
  });
  if (!result) return;

  expandedCategoryNodes.value = result.expandedCategoryNodes;
  expandedMineralNodes.value = result.expandedMineralNodes;
}

// 监听层级变化，重置到该层级的初始状态
watch(expandLevel, (newLevel) => {
  initializeLevelState(newLevel);
});

// 自动展开：图谱查询返回结果时，让“矿物节点”的子节点（产地/颜色/年份）默认展开
function autoExpandMineralNodesInResult() {
  const result = computeAutoExpandMineralNodesInResultUtil({
    nodes: rawData.nodes,
    links: rawData.links,
    isMineralCategory,
    isChildCategory,
  });
  if (!result) return;
  expandedMineralNodes.value = result;
}


// 是否已经进入系统：直接根据当前路由是否为首页判断，避免初始渲染时状态不同步导致残影
const hasEnteredSystem = computed(() => route.path !== '/');
const graphStageRef = ref(null);
const graphRef = ref(null);
const bannerRef = ref(null);
const sidebarRef = ref(null);
const actionsRef = ref(null);
const dockRef = ref(null);
const infoPanelRef = ref(null);
const graphAnswerRef = ref(null);

const graphQueryAnswer = ref('');

const chartKey = ref(0);
const viewLoading = ref(true);
const editor = reactive({ visible: false, position: { top: 0, left: 0 }, targetType: null, targetName: null });
const styleConfig = reactive({ nodes: {}, edges: {} });
const layoutConfig = reactive({
  repulsion: 400,
  edgeLength: 200,
  radialBase: 80,
  radialStep: 180,
  radialStrength: 0.25,
});
const forceLabelShow = ref('on');
const isLoading = ref(true);
const selectedItem = ref(null);

const globalStats = reactive({
  totalNodes: 0,
  totalPersonNodes: 0,
  totalBattleNodes: 0,
  totalEventNodes: 0,
  totalEdges: 0,
  totalComradeEdges: 0,
  totalParticipatedEdges: 0,
  totalFamilyEdges: 0,
});

const initialQuery = specimenTypeQueries['矿物标本'];
const selectedSpecimenType = ref('矿物标本');

const {
  isMineralNode,
  isMineralDetailVisible,
  isGemstoneGraph,

  mineralDetail,
  mineralDetailImage,

  mineralTitleColor,
  mineralBasicInfoFromApi,
  mineralCategories,
  mineralColors,
  mineralLocation,
  mineralDiscoveryYear,
  mineralBasicInfo,

  mineralDescription,
  mineralDescriptionKVs,

  specimenState,
  activeSpecimen,
  specimenViewMode,
  activeFrameCount,
  specimenFrameIndex,
  currentSpecimenImage,
  specimenDescription,

  resetSpecimenState,
  loadSpecimenSamples,
  nextSample,
  prevSample,
  changeFrame,
  onImagePointerDown,
  onImagePointerMove,
  onImagePointerUp,
  toggleSpecimenZoom,
  toggleSpecimenFullscreen,
} = useMineralDetailPanelLogic({
  selectedItem,
  rawData,
  selectedSpecimenType,
  styleConfig,
  entityCategoryLabels,
  gemNameMap,
  getMineralInfo,
  getSpecimenDescriptionByTable2Id,
  currentView,
  graphRef,
});

const minGraphDate = ref(new Date('1900-01-01'));
const maxGraphDate = ref(new Date('2025-12-31'));
const currentSelectedRange = ref([new Date('1941-01-01'), new Date('1945-10-01')]);

// --- API & DATA HANDLING ---
const { runQuery, initGraphOnce, initializeStyleConfig } = createGraphEngine({
  graphQuery,
  INVALID_VALUES,
  routePath: () => route.path,
  currentView,
  editor,
  rawData,
  tableData,
  styleConfig,
  selectedSpecimenType,
  specimenColorPalettes,
  expandLevel,
  showAllNodesFromStats,
  isLoading,
  viewLoading,
  chartKey,
  bootLoading,
  initializeLevelState,
  handleClearSelect,
  updateGraphDateRange,
  initialQuery,
});

async function fetchGlobalStats() {
  const apiUrl = import.meta.env.VITE_API_URL;
  const stats = await fetchGlobalStatsFromApi({ apiUrl });
  Object.assign(globalStats, stats);
}

// time_period -> 时间区间 映射（用于 normalizeLinkTime）
// 尽量覆盖 PERIODS.name 与 PERIODS.shortName 两种命名，避免数据字段不一致导致过滤为空。
const timePeriodMap = {
  '早期革命时期': { start: '1920-01-01', end: '1927-12-31' },
  '早期革命': { start: '1920-01-01', end: '1927-12-31' },
  '土地革命战争时期': { start: '1927-01-01', end: '1937-12-31' },
  '土地革命': { start: '1927-01-01', end: '1937-12-31' },
  '抗日战争时期': { start: '1937-01-01', end: '1945-12-31' },
  '抗日战争': { start: '1937-01-01', end: '1945-12-31' },
  '解放战争时期': { start: '1945-01-01', end: '1949-12-31' },
  '解放战争': { start: '1945-01-01', end: '1949-12-31' },
  '新中国成立初期': { start: '1949-01-01', end: '1956-12-31' },
  '新中国成立初': { start: '1949-01-01', end: '1956-12-31' },
  '社会主义建设探索时期': { start: '1956-01-01', end: '1966-12-31' },
  '社会主义探索': { start: '1956-01-01', end: '1966-12-31' },
  '文化大革命时期': { start: '1966-01-01', end: '1976-12-31' },
  '文革时期': { start: '1966-01-01', end: '1976-12-31' },
  '改革开放初期': { start: '1976-01-01', end: '1992-12-31' },
  '改革开放初期': { start: '1976-01-01', end: '1992-12-31' },
  '改革开放深化时期': { start: '1992-01-01', end: '2012-12-31' },
  '改革开放深化时期': { start: '1992-01-01', end: '2012-12-31' },
  '新时代': { start: '2012-01-01', end: '2025-12-31' },
  '新时代': { start: '2012-01-01', end: '2025-12-31' },
};

function normalizeLinkTime(link) {
  return normalizeLinkTimeUtil(link, timePeriodMap);
}

function updateGraphDateRange() {
  const { minDate, maxDate, selectedRange } = computeGraphDateRange(rawData.links, {
    minFallback: new Date('1941-01-01'),
    maxFallback: new Date('1945-10-01'),
    timePeriodMap,
  });
  minGraphDate.value = minDate;
  maxGraphDate.value = maxDate;
  currentSelectedRange.value = selectedRange;
}

// --- UI INTERACTION HANDLERS ---
function handleShowEditor({ type, name, event }) {
  const rect = event.currentTarget.getBoundingClientRect();
  editor.targetType = type;
  editor.targetName = name;
  editor.position = { top: rect.top, left: rect.right + 10 };
  editor.visible = true;
}

function handleStyleUpdate({ key, value }) {
  if (!editor.targetName) return;
  const config = styleConfig[editor.targetType]?.[editor.targetName];
  if (config) {
    config[key] = value;
    if (key === 'labelProp') {
      if (editor.targetType === 'nodes') {
        config.labelFormatter = (node) => node.properties[value] || node[value] || '';
      } else {
        config.labelFormatter = (link) => (value === 'none' ? '' : link.properties[value] || '');
      }
    }
  }
}

function handleEditorMove(newPosition) {
  editor.position.top = newPosition.top;
  editor.position.left = newPosition.left;
}

function handleLegendChange(selected) {
  Object.keys(selected).forEach((categoryName) => {
    if (styleConfig.nodes[categoryName]) {
      styleConfig.nodes[categoryName].visible = selected[categoryName];
    }
  });
}

const graphAppInteractions = createGraphInteractionsApp({
  rawData,
  selectedItem,
  expandedCategoryNodes,
  expandedMineralNodes,
  graphRef,
  runQuery,
  isLoading,
  styleConfig,
  getCategoryChildNodes,
  getMineralChildNodes,
  buildSelectedItemFromNode,
  buildSelectedItemFromEdge,
});

async function handleRelatedNodesQuery(nodeName) {
  return graphAppInteractions.handleRelatedNodesQuery(nodeName);
}

function handleNodeSelect(nodeData) {
  return graphAppInteractions.handleNodeSelect(nodeData);
}

function handleEdgeSelect(edgeData) {
  return graphAppInteractions.handleEdgeSelect(edgeData);
}

function handleClearSelect() {
  return graphAppInteractions.handleClearSelect();
}

function getCategoryChildNodes(categoryNodeId) {
  return getCategoryChildNodesUtil({
    categoryNodeId,
    nodes: rawData.nodes,
    links: rawData.links,
    isMineralCategory,
  });
}

function getMineralChildNodes(mineralNodeId) {
  return getMineralChildNodesUtil({
    mineralNodeId,
    nodes: rawData.nodes,
    links: rawData.links,
    isChildCategory,
  });
}

function checkCategoryNodeState(categoryNodeId) {
  const childNodes = getCategoryChildNodes(categoryNodeId);
  let allChildrenExpanded = true;
  let allChildrenCollapsed = true;
  let allGrandchildrenExpanded = true;
  let allGrandchildrenCollapsed = true;
  
  if (childNodes.size === 0) {
    return {
      childrenExpanded: false,
      childrenCollapsed: true,
      grandchildrenExpanded: false,
      grandchildrenCollapsed: true
    };
  }
  
  childNodes.forEach(mineralNodeId => {
    // 检查矿物节点是否展开（通过检查其子节点是否可见）
    const mineralChildNodes = getMineralChildNodes(mineralNodeId);
    const isMineralExpanded = expandedMineralNodes.value.has(String(mineralNodeId));
    
    if (isMineralExpanded) {
      allChildrenCollapsed = false;
      
      // 检查孙子节点（矿物节点的子节点）是否都展开
      if (mineralChildNodes.size > 0) {
        let allGrandchildrenOfThisMineralExpanded = true;
        let allGrandchildrenOfThisMineralCollapsed = true;
        
        mineralChildNodes.forEach(grandchildId => {
          // 孙子节点是否可见（通过检查其父节点是否展开）
          // 如果矿物节点展开，孙子节点应该可见
          allGrandchildrenOfThisMineralExpanded = allGrandchildrenOfThisMineralExpanded && true;
          allGrandchildrenOfThisMineralCollapsed = false;
        });
        
        if (!allGrandchildrenOfThisMineralExpanded) {
          allGrandchildrenExpanded = false;
        }
        if (!allGrandchildrenOfThisMineralCollapsed) {
          allGrandchildrenCollapsed = false;
        }
      } else {
        allGrandchildrenExpanded = false;
        allGrandchildrenCollapsed = true;
      }
    } else {
      allChildrenExpanded = false;
      allGrandchildrenExpanded = false;
      allGrandchildrenCollapsed = true;
    }
  });
  
  return {
    childrenExpanded: !allChildrenCollapsed && childNodes.size > 0,
    childrenCollapsed: allChildrenCollapsed,
    grandchildrenExpanded: allGrandchildrenExpanded && childNodes.size > 0,
    grandchildrenCollapsed: allGrandchildrenCollapsed
  };
}

function handleToggleCategoryExpansion(nodeId) {
  return graphAppInteractions.handleToggleCategoryExpansion(nodeId);
}

function handleToggleMineralExpansion(nodeId) {
  return graphAppInteractions.handleToggleMineralExpansion(nodeId);
}

function handleAIGraphQuery(result) {
  console.log('收到图谱查询结果:', result);
  if (result.type === 'graph' && result.data) {
    viewLoading.value = true;
    const nodes = result.data.nodes || [];
    nodes.forEach((n) => {
      if (n.category === 'Event' && n.properties?.category) {
        n.category = n.properties.category;
      }
    });

    rawData.nodes = nodes;
    rawData.links = result.data.links || [];

    tableData.headers = [];
    tableData.rows = [];
    initializeStyleConfig();
    
    // 强制设置为3级展开
    expandLevel.value = 3;
    // 初始化层级状态（根据当前层级设置展开状态）
    initializeLevelState(expandLevel.value);
    
    if (expandLevel.value === 3) {
      autoExpandMineralNodesInResult();
    }
    // 统一用路由驱动视图：把用户带回图谱页，避免停留在 /qa 导致视图/路由不同步
    if (route.path !== '/graph') {
      router.push('/graph');
    }
    currentView.value = 'graph';
    updateGraphDateRange();
    chartKey.value++;
    scheduleGraphRefresh();
    
    // 存储回答内容
    graphQueryAnswer.value = result.answer || '';
    console.log('设置的回答内容:', graphQueryAnswer.value);
  }
}

function zoomIn() {
  zoomLevel.value = Math.min(2, Number((zoomLevel.value + 0.1).toFixed(2)));
  graphRef.value?.adjustZoom(0.9);
}

function zoomOut() {
  zoomLevel.value = Math.max(0.5, Number((zoomLevel.value - 0.1).toFixed(2)));
  graphRef.value?.adjustZoom(1.1);
}

function toggleFullscreen() {
  const el = graphStageRef.value;
  if (!el) return;
  if (!document.fullscreenElement) {
    el.requestFullscreen?.();
  } else {
    document.exitFullscreen?.();
  }
}

// 主页/路由切换相关逻辑
function handleEnterSystem() {
  // 直接跳转到图谱页面 /graph，hasEnteredSystem 由路由自动推导
  router.push('/graph');
}

function handleBackToHome() {
  // 回到首页 /，并让首页介绍层重新可见（具体显示由 SystemIntroduction 自己控制）
  router.push('/');
}

function syncViewWithRoute() {
  // 根据当前路由路径决定内部视图
  if (route.path === '/qa') {
    currentView.value = 'ai';
  } else {
    // 其他路径一律视为图谱视图（包括 / 和 /graph）
    currentView.value = 'graph';
  }
}

function navigateTo(view) {
  if (view === 'ai') {
    router.push('/qa');
  } else {
    router.push('/graph');
  }
}

function toggleMainView() {
  // 点击按钮时只切路由；currentView 由 syncViewWithRoute 统一维护，避免不同步
  const nextView = currentView.value === 'ai' ? 'graph' : 'ai';
  navigateTo(nextView);
}

function handleNavigateToAI() {
  navigateTo('ai');
}

function goToAdmin() {
  router.push('/admin/login');
}

function goToSpecimenLibrary() {
  router.push('/specimen-library/宝玉石');
}

// 图谱搜索（抽离自 App.vue）
const { handleSearch } = createGraphSearchHandlers({
  nl2cypher,
  rawData,
  initializeStyleConfig,
  currentView,
  searchKeyword,
  searchType,
  searchLoading,
  searchCache,
  searchHistory,
});

function toggleSidebarMode() {
  if (sidebarMode.value === 'graph') {
    // 切换到标本库列表
    sidebarMode.value = 'library';
    // 如果当前不在图谱页面，导航到图谱页面
    if (route.path !== '/graph') {
      router.push('/graph');
    }
  } else {
    // 切换到图谱列表
    sidebarMode.value = 'graph';
    // 如果当前在标本库页面，导航到图谱页面
    if (route.path.startsWith('/specimen-library')) {
      router.push('/graph');
    }
  }
}

function handleGlobalClick(event) {
  const dockEl = document.querySelector('.bottom-dock-wrapper');
  if (dockEl && dockEl.contains(event.target)) return;
  dockPanel.value = null;
}

// 监听底部 Dock 面板的切换：仅当首次打开“统计”面板时，按需加载全局统计数据
watch(dockPanel, async (val) => {
  if (val === 'stats' && !hasLoadedGlobalStats.value) {
    await fetchGlobalStats();
    hasLoadedGlobalStats.value = true;
  }
});

function handleStatsQuery(cypher) {
  runQuery(cypher, true);
}

function handleSpecimenClick(specimenType) {
  selectedSpecimenType.value = specimenType;
  const query = specimenTypeQueries[specimenType] || specimenTypeQueries['矿物标本'];
  showAllNodesFromStats.value = false;
  runQuery(query);
}

// 手势控制逻辑抽离（保留与原 App.vue 完全一致的行为）
const { toggleGestureControl, handleGesture } = createGestureControl({
  GestureType,
  graphRef,
  isGestureEnabled,
  gestureState,
  gestureStability,
  confirmedGesture,
  lastGestureState,
  specimenList,
  selectedSpecimenType,
  handleSpecimenClick,
});

// --- COMPUTED PROPERTIES ---
const theme = computed(() => 'dark');
const themeClass = computed(() => 'dark-theme');

const nodeColorMap = computed(() => {
  const map = {};
  Object.entries(styleConfig.nodes || {}).forEach(([key, cfg]) => {
    if (cfg?.color) map[key] = cfg.color;
  });
  return map;
});

// 当前是否在标本库相关路由
const isSpecimenRoute = computed(() => route.path.startsWith('/specimen-library'));
const isAdminRoute = computed(() => route.path.startsWith('/admin'));

const isGraphView = computed(() => currentView.value === 'graph');

const graphScaleStyle = computed(() => ({
  transform: 'none',
}));

watch(
  () => route.path,
  (newPath) => {
    // 当地址栏变化时，同步 currentView
    syncViewWithRoute();
    // 如果路由是标本库相关，切换到标本库模式
    if (newPath.startsWith('/specimen-library/')) {
      sidebarMode.value = 'library';
    } else if (isGraphView.value) {
      sidebarMode.value = 'graph';
    }
  },
  { immediate: true },
);

// 从首页进入系统时（/ -> /graph），再按需初始化图谱（只会执行一次）
watch(
  () => route.path,
  (newPath, oldPath) => {
    if (oldPath === '/' && newPath !== '/' && !newPath.startsWith('/admin')) {
      initGraphOnce();
    }
  },
);

// 确保标本列表在图谱视图时显示
function ensureSidebarVisible() {
  if (!sidebarRef.value) return;
        sidebarRef.value.style.display = 'block';
        sidebarRef.value.style.visibility = 'visible';
        sidebarRef.value.style.opacity = '1';
        sidebarRef.value.style.pointerEvents = 'auto';
      }

watch(currentView, async (view) => {
  if (view === 'graph') {
    nextTick(ensureSidebarVisible);
    setTimeout(() => {
      if (currentView.value === 'graph') ensureSidebarVisible();
    }, 100);
    scheduleGraphRefresh();
  } else {
    viewLoading.value = false;
  }
}, { immediate: true });

// 额外守护：只要回到图谱视图，就确保标本列表显示
watch(isGraphView, (isGraph) => {
  if (isGraph) {
    nextTick(ensureSidebarVisible);
    setTimeout(() => {
      if (isGraphView.value) ensureSidebarVisible();
    }, 100);
  }
}, { immediate: true });

watch(isLoading, async (loading) => {
  if (!loading && currentView.value === 'graph') {
    scheduleGraphRefresh(false);
  }
});

function scheduleGraphRefresh(withMask = true) {
  if (withMask) viewLoading.value = true;
  nextTick(() => {
    graphRef.value?.refreshGraph?.();
    setTimeout(() => {
      graphRef.value?.refreshGraph?.();
      viewLoading.value = false;
    }, 480);
  });
}

const detailButtonLabel = computed(() => (currentView.value === 'ai' ? '图谱视图' : '智能问答'));

// 根据当前选择的标本类型动态计算图谱标题
const graphTitle = computed(() => {
  return specimenTypeToTitleMap[selectedSpecimenType.value] || '矿物图谱';
});

const overview = computed(() => {
  const nodes = new Map();
  if (rawData.nodes) {
    rawData.nodes.forEach((n) => {
      if (!nodes.has(n.category)) nodes.set(n.category, []);
      nodes.get(n.category).push(n);
    });
  }
  const edges = new Map();
  if (rawData.links) {
    rawData.links.forEach((l) => {
      if (!edges.has(l.name)) edges.set(l.name, []);
      edges.get(l.name).push(l);
    });
  }
  return { nodes, edges };
});

const activeEditorConfig = computed(() => {
  if (!editor.targetName || !styleConfig[editor.targetType] || !styleConfig[editor.targetType][editor.targetName]) return {};
  return styleConfig[editor.targetType][editor.targetName];
});

const availableLabelProps = computed(() => {
  return getAvailableLabelPropsUtil({
    targetType: editor.targetType,
    targetName: editor.targetName,
    nodes: rawData.nodes,
    links: rawData.links,
  });
});

// 计算矿物节点的子节点数量
function calculateMineralChildNodesCount() {
  mineralChildNodesCount.value = calculateMineralChildNodesCountUtil({
    nodes: rawData.nodes,
    links: rawData.links,
    isMineralCategory,
    isChildCategory,
  });
}

const filteredData = computed(() => {
  return computeFilteredDataUtil({
    rawData,
    styleConfig,
    expandLevel,
    expandedMineralNodes,
    expandedCategoryNodes,
    showAllNodesFromStats,
    TimeSliderCurrentView,
    currentSelectedRange,
    isMineralCategory,
    isCategoryType,
    isChildCategory,
    normalizeLinkTime,
    calculateMineralChildNodesCount,
  });

  // 下方旧实现保留但不执行（已抽离到 utils）

});


function toggleTheme() {
  viewLoading.value = true;
  document.body.className = themeClass.value;
  chartKey.value++;
  nextTick(() => {
    graphRef.value?.refreshGraph?.();
    setTimeout(() => {
      viewLoading.value = false;
    }, 500);
  });
}


// --- 动画 ---
function animateEntry() {
  if (bannerRef.value?.$el || bannerRef.value) {
    const el = bannerRef.value?.$el || bannerRef.value;
    gsap.from(el, { y: -50, opacity: 0, duration: 1, ease: 'power3.out', delay: 0.2 });
  }
  if (sidebarRef.value) gsap.from(sidebarRef.value, { x: -50, opacity: 0, duration: 1, ease: 'power3.out', delay: 0.4 });
  if (actionsRef.value?.$el || actionsRef.value) {
    const el = actionsRef.value?.$el || actionsRef.value;
    gsap.from(el, { x: 50, opacity: 0, duration: 1, ease: 'power3.out', delay: 0.4 });
  }
  if (dockRef.value?.$el || dockRef.value) {
    const el = dockRef.value?.$el || dockRef.value;
    gsap.from(el, { y: 50, opacity: 0, duration: 1, ease: 'back.out(1.7)', delay: 0.6 });
  }
}

onMounted(() => {
  document.body.className = themeClass.value;
  // 确保进入知识图谱页面时左侧标本列表默认展开并显示
  categoryListOpen.value = true;
  // 确保初始状态是图谱视图
  if (currentView.value === 'graph') {
    nextTick(() => {
      // 强制确保标本列表可见
      if (sidebarRef.value) {
        sidebarRef.value.style.display = 'block';
        sidebarRef.value.style.visibility = 'visible';
        sidebarRef.value.style.opacity = '1';
        sidebarRef.value.style.pointerEvents = 'auto';
      }
    });
    // 延迟再次确保显示，防止被其他逻辑覆盖
    setTimeout(() => {
      if (sidebarRef.value && currentView.value === 'graph') {
        sidebarRef.value.style.display = 'block';
        sidebarRef.value.style.visibility = 'visible';
        sidebarRef.value.style.opacity = '1';
        sidebarRef.value.style.pointerEvents = 'auto';
      }
    }, 100);
  }
  document.addEventListener('click', handleGlobalClick);
  animateEntry();
  // 首页：只展示 SystemIntroduction，不做图谱初始化，也不显示启动 Loading（避免首页被 Loading 覆盖）
  // 非首页：进入即初始化图谱（例如用户直接打开 /graph）
  if (isHomeRoute.value) {
    bootLoading.value = false;
  } else {
    initGraphOnce();
  }

  setTimeout(() => {
    isLoading.value = false;
    viewLoading.value = false;
  }, 1500);
  
  // 定期检查并确保标本列表在图谱视图时始终显示
  window.sidebarCheckInterval = setInterval(() => {
    if (currentView.value === 'graph') {
      ensureSidebarVisible();
    }
  }, 500);
});

onBeforeUnmount(() => {
  document.removeEventListener('click', handleGlobalClick);
  // 清除标本列表检查定时器
  if (window.sidebarCheckInterval) {
    clearInterval(window.sidebarCheckInterval);
    window.sidebarCheckInterval = null;
  }
});
</script>

<style scoped>
:global(:root) {
  --font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;

  /* Light Mode */
  --bg-light: #ffffff;
  --glass-light: rgba(255, 255, 255, 0.75);
  --glass-border-light: rgba(255, 255, 255, 0.6);
  --text-light: #1d1d1f;
  --text-sub-light: #86868b;
  --shadow-light: 0 8px 32px rgba(0,0,0,0.06);

  /* Dark Mode */
  --bg-dark: #000000;
  --glass-dark: rgba(28, 28, 30, 0.7);
  --glass-border-dark: rgba(255, 255, 255, 0.12);
  --text-dark: #f5f5f7;
  --text-sub-dark: #98989d;
  --shadow-dark: 0 12px 40px rgba(0,0,0,0.5);
  --accent-blue: #007aff;
  --radius-pill: 24px;
  --radius-card: 18px;
}

#app-container {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  font-family: var(--font-family);
  transition: background 0.5s ease;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.dark-theme {
  --bg-primary: var(--bg-dark);
  --glass-bg: var(--glass-dark);
  --glass-border: 1px solid var(--glass-border-dark);
  --text-primary: var(--text-dark);
  --text-secondary: var(--text-sub-dark);
  --panel-shadow: var(--shadow-dark);
  --ray-color: #0acfff;
  --card-bg: rgba(255,255,255,0.08);
  --dock-pill-bg: transparent;
  --dock-pill-active: rgba(60,60,60,0.8);
  --dock-pill-shadow: 0 2px 8px rgba(0,0,0,0.2);
  --sidebar-hover: rgba(255,255,255,0.1);
  --border-color: rgba(255,255,255,0.15);
}

.boot-loading {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
}

.global-rays {
  position: fixed;
  inset: 0;
  z-index: 0;
  opacity: 0.5;
  pointer-events: none;
}

.mac-glass {
  background: var(--glass-bg);
  backdrop-filter: blur(25px) saturate(180%);
  -webkit-backdrop-filter: blur(25px) saturate(180%);
  border: var(--glass-border);
  box-shadow: var(--panel-shadow);
}

.top-banner {
  position: absolute;
  top: -28px;
  left: 50%;
  transform: translateX(-50%);
  padding: 14px 60px;
  border-radius: 0 0 18px 18px;
  background: url('@/assets/title.png') center center / cover no-repeat;
  background-size: 70% 100%;
  box-shadow: none;
  border: none;
  color: #ffffff;
  letter-spacing: 4px;
  font-weight: 800;
  font-size: 2rem;
  z-index: 22;
  min-height: 100px;
  min-width: 520px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.banner-text {
  text-shadow: 0 0 10px rgba(0, 195, 255, 0.5);
  padding: 6px 48px 10px;
}

.sidebar-toggle-btn {
  position: fixed !important;
  top: 20px !important;
  left: 40px !important;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-card);
  z-index: 121 !important;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: var(--glass-bg);
  backdrop-filter: blur(25px) saturate(180%);
  -webkit-backdrop-filter: blur(25px) saturate(180%);
  border: var(--glass-border);
  box-shadow: var(--panel-shadow);
  color: var(--text-primary);
}

.sidebar-toggle-btn:hover {
  background: var(--sidebar-hover);
  transform: scale(1.05);
}

.floating-sidebar {
  /* 固定在视口左上角，避免被 3D 画布覆盖 */
  position: fixed !important;
  top: 20px !important;
  left: 20px !important; /* 往右移动一些，让左侧有明显留白 */
  width: 180px;
  border-radius: var(--radius-card);
  z-index: 120 !important; /* 确保在画布之上 */
  overflow: hidden;
  transition: all 0.3s ease;
  pointer-events: auto !important;
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  /* 使用透明玻璃效果背景 */
  background: var(--glass-bg);
  backdrop-filter: blur(25px) saturate(180%);
  -webkit-backdrop-filter: blur(25px) saturate(180%);
  border: var(--glass-border);
  box-shadow: var(--panel-shadow);
}


/* 矿物面板进入/退出动画 */
.mineral-panel-enter-active {
  transition: transform 0.7s cubic-bezier(0.16, 1, 0.3, 1),
              opacity 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}

.mineral-panel-leave-active {
  transition: transform 0.7s cubic-bezier(0.16, 1, 0.3, 1),
              opacity 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}

.mineral-panel-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.mineral-panel-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

.mineral-panel-enter-to,
.mineral-panel-leave-from {
  transform: translateX(0);
  opacity: 1;
}

.loading-overlay {
  position: absolute;
  inset: 0;
  background: var(--bg-primary);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 999;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}


.graph-stage {
  position: absolute;
  inset: 0;
  display: flex;
  z-index: 1;
  overflow: hidden;
}

.graph-stage.mineral-mode {
  padding-right: 0;
}

/* 背景遮罩层 */
/* 背景遮罩层已移除，不再添加笼罩效果 */

/* 图谱容器 - 当矿物面板打开时的动画效果 */
.graph-wrapper {
  flex: 1;
  position: relative;
  transition: transform 0.7s cubic-bezier(0.16, 1, 0.3, 1),
              opacity 0.7s cubic-bezier(0.16, 1, 0.3, 1),
              filter 0.7s cubic-bezier(0.16, 1, 0.3, 1);
  transform-origin: center;
}

.graph-wrapper.mineral-panel-open {
  transform: translateX(-25%) scale(0.95);
  opacity: 1;
  /* 移除模糊效果，保持画布清晰 */
  filter: none;
  /* 确保节点可以交互和拖拽 */
  pointer-events: auto;
}

/* 确保图谱容器内的所有元素都可以交互 */
.graph-wrapper.mineral-panel-open * {
  pointer-events: auto;
}

.graph-area,
.table-view,
.ai-view,
.view-shell {
  width: 100%;
  height: 100%;
}

/* 确保图谱内容充满舞台，避免底部留白 */
.graph-area {
  display: flex;
  flex-direction: column;
}

.graph-content {
  flex: 1;
  width: 100%;
  height: 100%;
  position: relative;
}

.mac-glass-panel {
  margin: 20px;
  height: calc(100% - 40px);
  width: calc(100% - 40px);
  border-radius: 16px;
  padding: 20px;
  overflow: hidden;
}

/* AI 视图需要紧贴舞台边缘，不保留外边距和圆角 */
.ai-view.mac-glass-panel {
  margin: 0;
  width: 100%;
  height: 100%;
  padding: 0;
  border-radius: 0;
  box-shadow: none;
  background: transparent;
}

.info-panel {
  position: absolute;
  top: 80px;
  right: 20px;
  width: 320px;
  border-radius: 12px;
  padding: 0;
  overflow: hidden;
  z-index: 15;
}

.overview-fab {
  position: absolute;
  left: 20px;
  bottom: 20px;
  z-index: 25;
}

.view-fade-enter-active,
.view-fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.view-fade-enter-from,
.view-fade-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

/* 页面切换动画 */
.page-fade-enter-active {
  transition: opacity 0.4s cubic-bezier(0.4, 0, 0.2, 1), transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.page-fade-leave-active {
  transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1), transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateX(20px) scale(0.98);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateX(-20px) scale(0.98);
}

@media (max-width: 800px) {
  /* 小屏也强制显示标本列表，但做尺寸与位置自适应 */
  .floating-sidebar {
    width: 82vw;
    left: 50%;
    transform: translateX(-50%);
    top: 12px;
  }

  .info-panel {
    display: none;
  }

  .mineral-detail-panel {
    position: fixed;
    inset: 0;
    width: 100%;
    max-width: 100vw;
    z-index: 40;
  }

  .graph-wrapper.mineral-panel-open {
    transform: translateX(-10%) scale(0.98);
    opacity: 0.7;
  }

  .bottom-dock-wrapper {
    width: 90%;
  }
}
</style>

