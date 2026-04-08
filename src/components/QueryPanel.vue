<!-- src/components/QueryPanel.vue -->
<template>
  <div class="query-panel-container">
    <el-tabs v-model="activeName" type="border-card" class="demo-tabs">


      <!-- 1. 人物查询（合并人物关系和生平事件） -->
      <el-tab-pane name="person">
        <template #label>
          <span class="custom-tabs-label">
            <span>矿物</span>
          </span>
        </template>
        <div>
          <el-form :model="personForm" label-width="auto" style="max-width: 300px">
            <!-- 人物姓名 -->
            <el-form-item :label="personForm.queryType == 'event' ? ' 矿石发现地':'矿石中文名称'">
              <el-input v-model="personForm.name" :placeholder="personForm.queryType == 'event' ? ' 请输入地名':'请输入矿石中文名称'"/>
            </el-form-item>

            <!-- 查询类别 -->
            <el-form-item label="查询类别:">
              <el-select v-model="personForm.queryType" placeholder="请选择查询类别" style="width: 100%;">
                <el-option label="矿石名称" value="relationship"/>
                <el-option label="矿石产地" value="event"/>
              </el-select>
            </el-form-item>

            <!-- 人物关系的选项 -->
            <el-form-item label="关系类型:" v-if="personForm.queryType === 'relationship'">
              <el-select v-model="personForm.hops" placeholder="请选择">
                <el-option label="直接关系" value="1"/>
                <el-option label="延伸关系" value="2"/>
              </el-select>
            </el-form-item>

            <!-- 生平事件的选项 -->
            <el-form-item label="事件类型:" v-if="personForm.queryType === 'event'">
              <el-select v-model="personForm.eventTypes" multiple placeholder="可多选" style="width: 100%;">
                <el-option v-for="item in eventTypeOptions" :key="item.value" :label="item.label" :value="item.value"/>
              </el-select>
            </el-form-item>

            <!-- 查询按钮 -->
            <el-form-item>
              <el-button style="width: 100%;" color="#bd93f9" type="primary" @click="handlePersonQuery"
                         :disabled="isLoading">查询
              </el-button>
            </el-form-item>
            
            <!-- 显示全部按钮 -->
            <el-form-item>
              <el-button style="width: 100%;" color="#50fa7b" type="success" @click="handleShowAll"
                         :disabled="isLoading">显示全部数据
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- 2. 战役战斗查询 -->
      <el-tab-pane name="battle">
        <template #label>
          <span class="custom-tabs-label">
            <span>捐赠人查询</span>
          </span>
        </template>
        <div style="max-height: 400px">
          <el-form :model="battleForm" label-width="auto" style="max-width: 300px">
            <el-form-item label="名称:">
              <el-input v-model="battleForm.name" placeholder="请输入捐赠人姓名"/>
            </el-form-item>
            <el-form-item>
              <el-button style="width: 100%;" type="primary" @click="handleBattleQuery"
                         :disabled="isLoading">查询
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- 快速分类 -->
      <el-tab-pane name="quick">
        <template #label>
          <span class="custom-tabs-label">
            <span>快速分类</span>
          </span>
        </template>
        <div>
          <h4 style="margin-top: 0; margin-bottom: 5px; font-size: 14px;">人物</h4>
          <div class="quick-tabs-btn-container">
            <el-button class="quick-tabs-btn"
                       @click="handleQuickQuery('person_category', '新四军五师前辈')" :disabled="isLoading">
              新四军五师前辈
            </el-button>
            <el-button class="quick-tabs-btn"
                       @click="handleQuickQuery('person_category', '百岁诞辰前辈')" :disabled="isLoading">
              百岁诞辰前辈
            </el-button>
            <el-button class="quick-tabs-btn"
                       @click="handleQuickQuery('person_category', '九公山纪念馆')" :disabled="isLoading">
              九公山纪念馆
            </el-button>
          </div>


          <h4 style="margin-top: 5px; margin-bottom: 5px; font-size: 14px;">战役战斗</h4>
          <div class="quick-tabs-btn-container">
            <el-button class="quick-tabs-btn"
                       @click="handleQuickQuery('event_category', '参加的战役战斗')" :disabled="isLoading">
              参加的战役战斗
            </el-button>
            <el-button class="quick-tabs-btn"
                       @click="handleQuickQuery('event_category', '战役战斗')" :disabled="isLoading">
              战役战斗
            </el-button>
          </div>
        </div>
      </el-tab-pane>

      <!-- 3. 自定义查询  -->
      <el-tab-pane name="query">
        <template #label>
          <span class="custom-tabs-label">
            <span>查询</span>
          </span>
        </template>
        <el-input type="textarea" :rows="5" placeholder="输入 Cypher 查询语句..." v-model="customCypher"></el-input>
        <el-button color="#bd93f9" type="primary" @click="emit('run-query', customCypher)" :disabled="isLoading"
                   style="width: 100%; margin-top: 10px;">
          执行查询
        </el-button>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import {ref, reactive} from 'vue';
import {ElMessage} from 'element-plus';

// --- Props & Emits ---
const props = defineProps({
  isLoading: Boolean,
  initialQuery: String,
  totalNodes: {type: Number, default: 0},
  totalPersonNodes: {type: Number, default: 0},
  totalBattleNodes: {type: Number, default: 0},
  totalEventNodes: {type: Number, default: 0},
  totalEdges: {type: Number, default: 0},
  totalComradeEdges: {type: Number, default: 0},
  totalParticipatedEdges: {type: Number, default: 0},
  totalFamilyEdges: {type: Number, default: 0},
});

const emit = defineEmits(['run-query']);
const activeName = ref('person'); // tab默认选中

// --- State ---
// 自定义查询的 v-model
const customCypher = ref(props.initialQuery);

// 合并后的人物查询表单数据
const personForm = reactive({
  name: '',
  queryType: 'relationship', // 默认查询类型：人物关系
  hops: '1', // 人物关系的查询深度
  eventTypes: ['教育和工作经历', '参加的战役战斗'], // 生平事件的类型
});

// 战役查询的表单数据
const battleForm = reactive({
  name: '',
});

// 生平事件的下拉选项
const eventTypeOptions = [
  {label: '教育和工作经历', value: '教育和工作经历'},
  {label: '参加的战役战斗', value: '参加的战役战斗'},
];

// --- Methods ---
// 处理人物查询（包含人物关系和生平事件）
/**
 function handlePersonQuery() {
 if (!personForm.name) {
 ElMessage.error('请输入人物姓名！');
 return;
 }

 if (personForm.queryType === 'relationship') {
 // 人物关系查询逻辑
 //     const cypher = `
 //   MATCH path=(p:Person)-[*1..${personForm.hops}]-(q:Person)
 //   WHERE p.name = "${personForm.name}"
 //   UNWIND relationships(path) AS rel
 //   RETURN DISTINCT startNode(rel) AS source,
 //           endNode(rel) AS target,
 //           rel AS relationship,
 //          labels(startNode(rel)) AS sourceLabels,
 //          labels(endNode(rel)) AS targetLabels
 // `;
 const cypher = `// 1. 获取所有相关的节点和边 (路径长度 1 到 ${personForm.hops})
 MATCH path=(p:Person)-[*1..${personForm.hops}]-(q:Person)
 WHERE p.name CONTAINS "${personForm.name}" OR p.aliases CONTAINS "${personForm.name}" OR "${personForm.name}" IN p.aliases
 UNWIND relationships(path) AS rel
 RETURN DISTINCT startNode(rel) AS source,
 endNode(rel) AS target,
 rel AS relationship,
 labels(startNode(rel)) AS sourceLabels,
 labels(endNode(rel)) AS targetLabels

 UNION ALL

 // 2. 获取所有符合模糊查询条件的 Person 节点自身（作为“孤立”节点处理）
 MATCH (p:Person)
 WHERE p.name CONTAINS "${personForm.name}" OR p.aliases CONTAINS "${personForm.name}" OR "${personForm.name}" IN p.aliases
 // 过滤掉那些至少有一条满足 *1..${personForm.hops} 路径的节点
 AND NOT EXISTS((p)-[*1..${personForm.hops}]-(:Person))
 RETURN p AS source,
 p AS target,
 NULL AS relationship, // 关系为空，表示它是一个孤立的节点记录
 labels(p) AS sourceLabels,
 labels(p) AS targetLabels
 `
 emit('run-query', cypher);
 } else if (personForm.queryType === 'event') {
 // 生平事件查询逻辑
 if (personForm.eventTypes.length === 0) {
 ElMessage.error('请至少选择一个事件类型！');
 return;
 }

 let query = `MATCH (p:Person) WHERE p.name CONTAINS "${personForm.name}" OR p.aliases CONTAINS "${personForm.name}" OR "${personForm.name}" IN p.aliases
 `;
 const optionalMatches = [];
 const relAliases = [];

 personForm.eventTypes.forEach((eventType, index) => {
 const relVar = `r${index}`;
 const nodeVar = `n${index}`;
 optionalMatches.push(
 `OPTIONAL MATCH (p)-[${relVar}]-(${nodeVar}:Event {category:'${eventType}'})`
 );
 relAliases.push(relVar);
 });

 const cypher = `
 ${query}
 ${optionalMatches.join('\n')}
 WITH p, ${relAliases.join(', ')}
 UNWIND [${relAliases.join(', ')}] AS rel
 WITH DISTINCT startNode(rel) AS source, endNode(rel) AS target, rel,
 labels(startNode(rel)) AS sourceLabels,
 labels(endNode(rel)) AS targetLabels
 RETURN source, target, rel AS relationship, sourceLabels, targetLabels
 `;

 emit('run-query', cypher);
 console.log('finalQuery:', cypher);
 }
 } **/

function handlePersonQuery() {
  if (!personForm.name) {
    ElMessage.error('请输入人物姓名！');
    return;
  }

  if (personForm.queryType === 'relationship') {
    /**const cypher = `// 1. 获取所有相关的节点和边 (路径长度 1 到 ${personForm.hops})
     MATCH path=(p:Person)-[*1..${personForm.hops}]-(q:Person)
     WHERE p.name CONTAINS "${personForm.name}" OR p.aliases CONTAINS "${personForm.name}" OR "${personForm.name}" IN p.aliases
     UNWIND relationships(path) AS rel
     RETURN DISTINCT startNode(rel) AS source,
     endNode(rel) AS target,
     rel AS relationship,
     labels(startNode(rel)) AS sourceLabels,
     labels(endNode(rel)) AS targetLabels
     `**/
    const cypher = `MATCH p=(m:Specimen)-[]-()
      WHERE m.name CONTAINS "${personForm.name}"
      RETURN p LIMIT 280`
    emit('run-query', cypher);
  }
  if (personForm.queryType === 'event') {
    const cypher = `MATCH p=(m:Location)-[]-()
      WHERE m.name CONTAINS "${personForm.name}"
      RETURN p LIMIT 280`
    emit('run-query', cypher);
  }
}

// 处理战役查询
/**
function handleBattleQuery() {
  if (!battleForm.name) {
    ElMessage.error('请输入战役名称！');
    return;
  }

  // const cypher = `
  //   MATCH path=(b:Event {name: "${battleForm.name}"})-[r]-(n)
  //   UNWIND relationships(path) AS rel
  //   RETURN DISTINCT startNode(rel) AS source,
  //           endNode(rel) AS target,
  //           rel AS relationship,
  //          labels(startNode(rel)) AS sourceLabels,
  //          labels(endNode(rel)) AS targetLabels
  // `;

  // const cypher = `
  //   MATCH path=(b:Event)-[r]-(n)
  //   WHERE b.name CONTAINS "${battleForm.name}"
  //   UNWIND relationships(path) AS rel
  //   RETURN DISTINCT startNode(rel) AS source,
  //           endNode(rel) AS target,
  //           rel AS relationship,
  //          labels(startNode(rel)) AS sourceLabels,
  //          labels(endNode(rel)) AS targetLabels
  // `;
  const cypher = `// 1. 获取所有相关的节点和边
          MATCH (b:Event)-[r]-(n)
          WHERE b.name CONTAINS "${battleForm.name}"
          RETURN DISTINCT startNode(r) AS source,
                          endNode(r) AS target,
                          r AS relationship,
                          labels(startNode(r)) AS sourceLabels,
                          labels(endNode(r)) AS targetLabels

            UNION ALL

          // 2. 获取所有符合条件的 Event 节点自身（作为“孤立”的边处理）
              MATCH (b:Event)
              WHERE b.name CONTAINS "${battleForm.name}"
              // 过滤掉那些已经在第一部分被包含的节点（它们至少有一条边）
              // 如果您想完全避免重复，这一步是必要的，但如果数据量大，可能会增加开销
              AND NOT EXISTS((b)--()) 
              RETURN b AS source,
                b AS target,
                NULL AS relationship, // 关系为空，表示它是一个孤立的节点记录
                labels(b) AS sourceLabels,
                labels(b) AS targetLabels
                `


  emit('run-query', cypher);
}
**/

function handleBattleQuery() {
  if (!battleForm.name) {
    ElMessage.error('请输入捐赠人名称！');
    return;
  }
    const cypher = `MATCH p=(m:Donor)-[]-()
    WHERE m.name CONTAINS "${battleForm.name}"
    RETURN p LIMIT 280`
  emit('run-query', cypher);
}


// 处理显示全部数据
function handleShowAll() {
  // 查询所有节点和关系，使用路径查询格式，限制数量以避免性能问题
  const cypher = 'MATCH p=(n)-[r]-(m) RETURN p LIMIT 500';
  emit('run-query', cypher);
}

// 处理快速查询
function handleQuickQuery(type, value) {
  let cypher = '';

  if (type === 'person_category') {
    // 人物类别查询
    cypher = `
      MATCH (n:Person) 
      WHERE "${value}" IN n.person_category OR n.person_category CONTAINS "${value}"
      RETURN n
      `;
  } else if (type === 'event_category') {
    // 事件类别查询
    // 这里使用 UNION ALL 确保返回的节点有一个 'relationship' 字段，即使它是 NULL
    // cypher = `// 获取所有 Event 节点及其可能的关系
    //         MATCH (e:Event)
    //         WHERE e.category = '${value}'
    //         OPTIONAL MATCH (e)-[r]-(n)
    //         RETURN 
    //           e AS source,
    //           COALESCE(n, e) AS target,  // 如果没有关联节点，就返回自身
    //           r AS relationship,
    //           labels(e) AS sourceLabels,
    //           COALESCE(labels(n), labels(e)) AS targetLabels`;


    cypher = `
      // 1. 获取所有符合条件的 Event 节点自身
      MATCH (n:Event) 
      WHERE n.category = '${value}' 
      RETURN n AS source,
            n AS target,
            NULL AS relationship, // 关系为空，表示它是一个孤立的节点记录
            labels(n) AS sourceLabels,
            labels(n) AS targetLabels

      // UNION ALL

      // // 2. 获取这些 Event 节点及其直接相连的节点和边
      // MATCH (e:Event)-[r]-(n)
      // WHERE e.category = '${value}'
      // RETURN DISTINCT startNode(r) AS source,
      //                 endNode(r) AS target,
      //                 r AS relationship,
      //                 labels(startNode(r)) AS sourceLabels,
      //                 labels(endNode(r)) AS targetLabels
      `;
  }

  if (cypher) {
    emit('run-query', cypher);
  } else {
    ElMessage.error('无效的快速查询！');
  }
}

</script>

<style scoped>
.query-panel-container {
  padding: 0px 0;
  border-bottom: 0px solid var(--border-color);
}

.demo-tabs > .el-tabs__content {
  padding: 20px;
  color: #6b778c;
}

.custom-tabs-label {
  display: flex;
  align-items: center;
  gap: 4px;
}

.el-form-item {
  margin-bottom: 18px;
}

.el-tabs--border-card {
  border: 0px;
  border-bottom: 1.5px solid var(--border-color);
  background: var(--sidebar-bg);
  backdrop-filter: blur(16px);
}


:deep(.el-tabs--border-card>.el-tabs__header .el-tabs__item.is-active) {
  color: var(--text-secondary) !important;
}

:deep(.el-tabs--border-card>.el-tabs__header .el-tabs__item:not(.is-disabled):hover) {
  color: var(--text-secondary) !important;
}

.el-button--primary {
  background: linear-gradient(120deg, var(--accent-primary), var(--accent-secondary)) !important;
  border-color: var(--accent-secondary) !important;
  color: var(--text-primary) !important;
  box-shadow: 0 4px 12px rgba(212, 165, 116, 0.25) !important;
}
.el-button--primary:hover {
  background: var(--accent-secondary) !important;
  box-shadow: 0 6px 20px rgba(212, 165, 116, 0.35) !important;
}


:deep(.el-tabs--border-card>.el-tabs__header) {
  background: var(--sidebar-bg) !important;
  backdrop-filter: blur(16px);
}

.quick-tabs-btn-container {
  display: flex;
  flex-direction: row;
  gap: 8px;
  flex-wrap: wrap;
}

.quick-tabs-btn {
  white-space: normal;
  font-size: 12px;
  margin: 0px;
}
</style>