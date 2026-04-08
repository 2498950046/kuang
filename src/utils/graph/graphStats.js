/**
 * 全局统计请求（抽离自 App.vue 的 fetchGlobalStats）
 * 保证：
 * - 不抛出异常，失败时返回全 0
 * - 返回字段名与 App.vue/globalStats 保持一致
 */

export async function fetchGlobalStats({ apiUrl, fetchFn = fetch }) {
  const empty = {
    totalNodes: 0,
    totalPersonNodes: 0,
    totalBattleNodes: 0,
    totalEventNodes: 0,
    totalEdges: 0,
    totalComradeEdges: 0,
    totalParticipatedEdges: 0,
    totalFamilyEdges: 0,
  };

  try {
    const [
      specimenResponse,
      colorResponse,
      locationResponse,
      belongsToResponse,
      discoveredInResponse,
      hasSubcategoryResponse,
    ] = await Promise.all([
      fetchFn(`${apiUrl}/graph`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cypher: 'MATCH (n:Specimen) RETURN count(n) AS total' }),
      }),
      fetchFn(`${apiUrl}/graph`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cypher: 'MATCH (n:Color) RETURN count(n) AS total' }),
      }),
      fetchFn(`${apiUrl}/graph`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cypher: 'MATCH (n:Location) RETURN count(n) AS total' }),
      }),
      fetchFn(`${apiUrl}/graph`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cypher: 'MATCH ()-[r:BELONGS_TO]->() RETURN count(r) AS total' }),
      }),
      fetchFn(`${apiUrl}/graph`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cypher: 'MATCH ()-[r:DISCOVERED_IN]->() RETURN count(r) AS total' }),
      }),
      fetchFn(`${apiUrl}/graph`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cypher: 'MATCH ()-[r:HAS_SUBCATEGORY]->() RETURN count(r) AS total' }),
      }),
    ]);

    if (
      !specimenResponse.ok ||
      !colorResponse.ok ||
      !locationResponse.ok ||
      !belongsToResponse.ok ||
      !discoveredInResponse.ok ||
      !hasSubcategoryResponse.ok
    ) {
      throw new Error('Failed to fetch global stats');
    }

    const specimenResult = await specimenResponse.json();
    const colorResult = await colorResponse.json();
    const locationResult = await locationResponse.json();
    const belongsToResult = await belongsToResponse.json();
    const discoveredInResult = await discoveredInResponse.json();
    const hasSubcategoryResult = await hasSubcategoryResponse.json();

    const totalPersonNodes = specimenResult.data?.rows[0]?.total || 0; // 矿物名
    const totalEventNodes = colorResult.data?.rows[0]?.total || 0; // 颜色
    const totalBattleNodes = locationResult.data?.rows[0]?.total || 0; // 发现地区
    const totalComradeEdges = belongsToResult.data?.rows[0]?.total || 0; // 分类关系
    const totalParticipatedEdges = discoveredInResult.data?.rows[0]?.total || 0; // 时间关系
    const totalFamilyEdges = hasSubcategoryResult.data?.rows[0]?.total || 0; // 层级关系

    const totalNodes = totalPersonNodes;
    const totalEdges = totalComradeEdges + totalParticipatedEdges + totalFamilyEdges;

    return {
      totalNodes,
      totalPersonNodes,
      totalBattleNodes,
      totalEventNodes,
      totalEdges,
      totalComradeEdges,
      totalParticipatedEdges,
      totalFamilyEdges,
    };
  } catch (e) {
    console.error('获取全局统计数据失败:', e);
    return empty;
  }
}

