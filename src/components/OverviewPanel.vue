<!-- src/components/OverviewPanel.vue -->
<template>
  <div class="overview-floating">
    <el-collapse v-model="activeCollapseNames" class="collapse-plain">
        <el-collapse-item name="nodes">
          <template #title>
            <span class="collapse-title">当前查询节点 ({{ rawData.nodes.length }})</span>
          </template>
          <div 
            v-for="[category, items] in overview.nodes" 
            :key="category" 
            class="overview-item-pro"
            :title="`占比: ${((items.length / rawData.nodes.length) * 100).toFixed(1)}%`"
          >
            <component :is="iconMap[category] || iconMap.defaultNode" class="item-icon" :size="18" />
            <div class="item-label">
              {{ entityCategoryLabels[category] || category }} ({{ items.length }})
            </div>
            <el-progress 
              :percentage="(items.length / rawData.nodes.length) * 100" 
              :show-text="false"
              :stroke-width="6"
              class="item-progress"
            :color="nodeColorMap[category] || defaultProgressColor"
              @click.stop
            />
          </div>
        </el-collapse-item>
      </el-collapse>
    
    <div v-if="!isLoading && rawData.nodes.length === 0" class="no-data-placeholder">
      <p>当前查询无结果</p>
      <p>请尝试其他查询</p>
    </div>

    <div class="overview-copyright">Copyright © 2026  三秋二月创新创业工作室 • 成都理工大学</div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { ElCollapse, ElCollapseItem, ElProgress } from 'element-plus';
// 引入图标库
import { Users, Building, Swords, School, Link, GitMerge, UserCheck, Handshake, Briefcase, Box, Share2 } from 'lucide-vue-next';

// 定义 Props，增加 totalNodes 和 totalEdges
const props = defineProps({
  isLoading: Boolean,
  overview: { type: Object, required: true },
  rawData: { type: Object, required: true },
  editorTargetName: String,
  entityCategoryLabels: Object,
  edgeTypeLabels: Object,
  totalNodes: { type: Number, default: 0 }, // 新增：全局节点总数
  totalEdges: { type: Number, default: 0 }, // 新增：全局关系总数
  nodeColorMap: { type: Object, default: () => ({}) },
});

const emit = defineEmits(['show-editor']);

// 默认展开
const activeCollapseNames = ref(['nodes']);
const defaultProgressColor = 'var(--accent-primary)';

// 图标映射
const iconMap = {
  Person: Users,
  Event: Building,
  教育和工作经历: Building,
  参加的战役战斗: Swords,

  Grandparent: Users,
  Parent: Users,
  Child: Users,
  革命事件: Building,
  战役事件: Swords,
  生平事件: School,

  PARTICIPATED_IN: UserCheck,
  COMRADE_WITH: GitMerge,
  PARTICIPATED_IN_ORG: Briefcase,
  POSSIBLE_SAME_AS: Swords,
  
  COLLEAGUE_OF: Handshake,
  ATTENDED: School,
  RELATED_TO: Link,
  FRIEND_OF: Handshake,
  WORKED_AT: Briefcase,
  defaultNode: Box,
  defaultEdge: Share2,
};
</script>

<style scoped>
.overview-floating {
  width: max-content;
  max-width: 220px;
  padding: 4px 4px 0px 4px;
  border-radius: 10px;
  background: transparent;
  border: none;
  box-shadow: none;
}

.collapse-title {
  font-weight: 700;
  font-size: 0.95rem;
  color: #f4f8ff;
}
:deep(.collapse-plain) {
  border: none;
}
:deep(.el-collapse-item__header),
:deep(.el-collapse-item__wrap) {
  border: none;
  background: transparent;
  padding: 0;
}
:deep(.el-collapse-item__header) {
  gap: 4px;
  padding-right: 0;
}
:deep(.el-collapse-item__arrow) {
  margin-left: 2px;
}
:deep(.el-collapse-item__content) {
  padding: 4px 0 0 0;
}

.overview-item-pro {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 4px;
  border-radius: 8px;
  transition: background-color 0.2s ease;
}
.overview-item-pro:hover {
  background: rgba(255, 255, 255, 0.04);
}
.item-icon {
  color: rgba(240, 248, 255, 0.7);
  flex-shrink: 0;
}
.item-label {
  flex-grow: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 0.9em;
  font-weight: 600;
  color: #f4f8ff;
}
.item-progress {
  width: 55px;
  flex-shrink: 0;
  margin-left: 0;
}
:deep(.item-progress .el-progress-bar__outer) {
  height: 6px !important;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.15) !important;
}
:deep(.item-progress .el-progress-bar__inner) {
  border-radius: 999px;
  box-shadow: 0 0 6px rgba(90, 200, 255, 0.22);
}

.no-data-placeholder {
  text-align: center;
  color: rgba(214, 228, 255, 0.82);
  padding: 20px 0 6px;
  font-size: 0.92em;
}
.no-data-placeholder p {
  margin: 4px 0;
}

.overview-copyright {
  margin-top: 12px;
  padding: 10px 0 0px 0;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 11px;
  color: rgba(196, 214, 244, 0.72);
  text-align: center;
  white-space: nowrap;
  overflow: visible;
  min-width: max-content;
}
</style>
