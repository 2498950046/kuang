/**
 * 样式编辑器可用 label 属性推导（抽离自 App.vue）
 * 纯函数：不依赖 Vue 运行时。
 */

export function getAvailableLabelProps({ targetType, targetName, nodes, links }) {
  if (!targetName) return [];

  if (targetType === 'nodes') {
    const sampleNode = (nodes || []).find((n) => n.category === targetName);
    if (!sampleNode) return ['name', 'id', 'category'];
    return [...new Set(['name', 'id', 'category', ...Object.keys(sampleNode.properties || {})])];
  }

  const sampleLink = (links || []).find((l) => l.name === targetName);
  if (!sampleLink) return ['type'];
  return [...new Set(['type', ...Object.keys(sampleLink.properties || {})])];
}

