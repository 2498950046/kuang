import { nextTick } from 'vue';

export function createGraphInteractionsApp({
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
}) {
  async function handleRelatedNodesQuery(nodeName) {
    isLoading.value = true;
    try {
      const cypher = `MATCH p= (n)-[*1]-(x) WHERE n.name='${nodeName}' RETURN p`;
      runQuery(cypher);
    } catch (e) {
      console.error('查询关联节点时出错:', e);
      alert(`查询失败: ${e.message}`);
    } finally {
      isLoading.value = false;
    }
  }

  function handleNodeSelect(nodeData) {
    if (!nodeData || !nodeData.id) return;
    const next = buildSelectedItemFromNode({
      nodeData,
      nodes: rawData.nodes,
      currentSelectedItem: selectedItem.value,
    });
    if (next !== selectedItem.value) selectedItem.value = next;
  }

  function handleEdgeSelect(edgeData) {
    if (!edgeData || !edgeData.source || !edgeData.target) return;
    const next = buildSelectedItemFromEdge({ edgeData, links: rawData.links });
    if (next) selectedItem.value = next;
  }

  function handleClearSelect() {
    selectedItem.value = null;
    graphRef.value?.resetCameraToDefault?.();
    nextTick(() => {
      graphRef.value?.refreshGraph?.();
    });
  }

  function handleToggleCategoryExpansion(nodeId) {
    const nodeIdStr = String(nodeId);
    const childNodes = getCategoryChildNodes(nodeIdStr);

    if (childNodes.size === 0) {
      if (expandedCategoryNodes.value.has(nodeIdStr)) {
        expandedCategoryNodes.value.delete(nodeIdStr);
      } else {
        expandedCategoryNodes.value.add(nodeIdStr);
      }
      return;
    }

    const isCategoryExpanded = expandedCategoryNodes.value.has(nodeIdStr);

    if (isCategoryExpanded) {
      expandedCategoryNodes.value.delete(nodeIdStr);
      childNodes.forEach((mineralNodeId) => {
        expandedMineralNodes.value.delete(String(mineralNodeId));
      });
    } else {
      expandedCategoryNodes.value.add(nodeIdStr);
    }
  }

  function handleToggleMineralExpansion(nodeId) {
    const nodeIdStr = String(nodeId);
    // 保持原逻辑：计算 childNodes 但不使用（用于未来扩展/防止行为差异）
    getMineralChildNodes(nodeIdStr);

    const isExpanded = expandedMineralNodes.value.has(nodeIdStr);
    if (isExpanded) expandedMineralNodes.value.delete(nodeIdStr);
    else expandedMineralNodes.value.add(nodeIdStr);
  }

  return {
    handleRelatedNodesQuery,
    handleNodeSelect,
    handleEdgeSelect,
    handleClearSelect,
    handleToggleCategoryExpansion,
    handleToggleMineralExpansion,
  };
}

