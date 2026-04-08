/**
 * 节点/边选择映射（抽离自 App.vue）
 * 纯函数：返回 nextSelectedItem，由 App.vue 负责赋值。
 */

export function buildSelectedItemFromNode({ nodeData, nodes, currentSelectedItem }) {
  if (!nodeData || !nodeData.id) return currentSelectedItem;
  const fullNode = (nodes || []).find((n) => n.id === nodeData.id);
  if (!fullNode) return currentSelectedItem;

  // 再次点击同一节点：取消选择
  if (currentSelectedItem?.data?.id === fullNode.id) return null;

  return {
    dataType: 'node',
    data: { ...fullNode, properties: fullNode.properties || {} },
  };
}

export function buildSelectedItemFromEdge({ edgeData, links }) {
  if (!edgeData || !edgeData.source || !edgeData.target) return null;
  const fullLink = (links || []).find(
    (l) =>
      l.source === edgeData.source &&
      l.target === edgeData.target &&
      l.name === edgeData.name &&
      l.properties?.event_name === edgeData.properties?.event_name,
  );
  if (!fullLink) return null;

  return {
    dataType: 'edge',
    data: { ...fullLink, properties: fullLink.properties || {} },
  };
}

