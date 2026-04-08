import { nextTick } from 'vue';

/**
 * GraphChart3D 节点单击/双击交互逻辑（抽离自 GraphChart3D.vue）
 * 目标：不改变任何行为，仅做工程化拆分。
 */
export function createNodeClickHandler({
  emit,
  getGraphInstance,
  saveCameraState,
  resetCameraToDefault,
  selectedNodeId,
  connectedNodeIds,
  updateConnectedNodes,
}) {
  let clickTimer = null;
  let lastClickedNode = null;

  function clearClickState() {
    if (clickTimer) clearTimeout(clickTimer);
    clickTimer = null;
    lastClickedNode = null;
  }

  function handleBackgroundClick() {
    selectedNodeId.value = null;
    connectedNodeIds.value = new Set();
    resetCameraToDefault();
    const graphInstance = getGraphInstance();
    if (graphInstance) graphInstance.refresh();
    emit('clear-select');
  }

  function handleNodeClick(node, event) {
    if (event) event.stopPropagation();

    const graphInstance = getGraphInstance();
    const nodeId = String(node.id);
    const category = node.category || '';
    const isCategoryNode = category === 'Category' || category === '分类';
    const isMineral =
      category === 'Mineral' ||
      category === '中文名称' ||
      category === '矿物' ||
      category === 'Specimen' ||
      category === '标本';
    const isChildNode = ['Year', '年份', 'Location', '产地', 'Color', '颜色'].includes(category);

    // 子节点（年份、产地、颜色等）的双击无效
    if (isChildNode && clickTimer && lastClickedNode && lastClickedNode.id === node.id) {
      clearClickState();
      return;
    }

    if (isMineral) {
      // 矿物节点：区分单击和双击
      if (clickTimer && lastClickedNode && lastClickedNode.id === node.id) {
        // 双击：切换展开/收缩状态
        clearClickState();

        // 检查该节点是否已经被选中（详情面板是否已经打开）
        const isNodeSelected = selectedNodeId.value === nodeId;

        // 切换展开/收缩状态
        emit('toggle-mineral-expansion', nodeId);

        // 如果节点已经被选中（详情面板已打开），保持选中状态并刷新图谱
        if (isNodeSelected) {
          nextTick(() => {
            updateConnectedNodes(nodeId);
            const gi = getGraphInstance();
            if (gi) gi.refresh();
          });
        }
        return;
      }

      // 单击：延迟执行，等待可能的双击
      clickTimer = setTimeout(() => {
        saveCameraState();
        selectedNodeId.value = nodeId;
        updateConnectedNodes(nodeId);

        const gi = getGraphInstance();
        if (gi) gi.refresh();

        emit('node-select', node);

        const distance = 200;
        const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);
        gi?.cameraPosition?.(
          { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
          node,
          3000,
        );

        clickTimer = null;
      }, 250);
      lastClickedNode = node;
      return;
    }

    // 非矿物节点
    if (clickTimer && lastClickedNode && lastClickedNode.id === node.id) {
      // 双击分类节点：切换展开/收缩状态
      if (isCategoryNode) {
        clearClickState();
        const isNodeSelected = selectedNodeId.value === nodeId;
        emit('toggle-category-expansion', nodeId);
        if (isNodeSelected) {
          nextTick(() => {
            updateConnectedNodes(nodeId);
            const gi = getGraphInstance();
            if (gi) gi.refresh();
          });
        }
        return;
      }

      // 双击子节点（年份、产地、颜色等）：无效
      if (isChildNode) {
        clearClickState();
        return;
      }

      // 其他非矿物非子节点：双击触发"查询关联节点"
      clearClickState();
      emit('query-related-nodes', node.name || node.id);
      return;
    }

    clickTimer = setTimeout(() => {
      saveCameraState();
      selectedNodeId.value = nodeId;
      updateConnectedNodes(nodeId);

      const gi = getGraphInstance();
      if (gi) gi.refresh();

      emit('node-select', node);
      const distance = 200;
      const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);
      gi?.cameraPosition?.(
        { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
        node,
        3000,
      );
      clickTimer = null;
    }, 250);
    lastClickedNode = node;
  }

  return { handleNodeClick, handleBackgroundClick, clearClickState };
}

