/**
 * 图谱展开/子节点相关辅助函数（抽离自 App.vue）
 * 纯函数：不直接操作 Vue ref。
 */

/**
 * 获取分类节点下的矿物子节点 ID 集合（基于 BELONGS_TO 关系）
 */
export function getCategoryChildNodes({ categoryNodeId, nodes, links, isMineralCategory }) {
  const childNodes = new Set();
  const nodeIdStr = String(categoryNodeId);

  (links || []).forEach((link) => {
    const sourceId = String(typeof link.source === 'object' ? link.source.id : link.source);
    const targetId = String(typeof link.target === 'object' ? link.target.id : link.target);

    if ((link.name === 'BELONGS_TO' || link.name === '属于') && targetId === nodeIdStr) {
      const sourceNode = (nodes || []).find((n) => String(n.id) === sourceId);
      if (sourceNode && isMineralCategory(sourceNode.category)) {
        childNodes.add(sourceId);
      }
    }
  });

  return childNodes;
}

/**
 * 获取矿物节点的子节点（年份/产地/颜色）ID 集合
 */
export function getMineralChildNodes({ mineralNodeId, nodes, links, isChildCategory }) {
  const childNodes = new Set();
  const nodeIdStr = String(mineralNodeId);
  const childLinkNames = ['FROM_LOCATION', '来自', 'HAS_COLOR', '具有颜色', 'DISCOVERED_IN', '发现于'];

  (links || []).forEach((link) => {
    if (!childLinkNames.includes(link.name)) return;

    const sourceId = String(typeof link.source === 'object' ? link.source.id : link.source);
    const targetId = String(typeof link.target === 'object' ? link.target.id : link.target);

    if (sourceId === nodeIdStr) {
      const targetNode = (nodes || []).find((n) => String(n.id) === targetId);
      if (targetNode && isChildCategory(targetNode.category)) childNodes.add(targetId);
    } else if (targetId === nodeIdStr) {
      const sourceNode = (nodes || []).find((n) => String(n.id) === sourceId);
      if (sourceNode && isChildCategory(sourceNode.category)) childNodes.add(sourceId);
    }
  });

  return childNodes;
}

/**
 * 计算每个矿物节点的子节点数量（年份/产地/颜色）
 * @returns {Map<string, number>}
 */
export function calculateMineralChildNodesCount({ nodes, links, isMineralCategory, isChildCategory }) {
  const countMap = new Map();

  (nodes || []).forEach((node) => {
    if (!isMineralCategory(node.category)) return;

    const nodeId = String(node.id);
    const connectedNodeIds = new Set();

    (links || []).forEach((link) => {
      const sourceId = String(typeof link.source === 'object' ? link.source.id : link.source);
      const targetId = String(typeof link.target === 'object' ? link.target.id : link.target);
      if (sourceId === nodeId) connectedNodeIds.add(targetId);
      else if (targetId === nodeId) connectedNodeIds.add(sourceId);
    });

    let count = 0;
    (nodes || []).forEach((childNode) => {
      if (connectedNodeIds.has(String(childNode.id)) && isChildCategory(childNode.category)) count++;
    });

    countMap.set(nodeId, count);
  });

  return countMap;
}

