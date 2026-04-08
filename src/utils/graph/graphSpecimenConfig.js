/**
 * 图谱相关“配置/常量/Cypher 查询”集中管理。
 * 只包含数据定义，不包含响应式状态与副作用，方便在 App.vue 中直接 import 使用。
 */

// 节点类型常量
export const CATEGORY_NODE_TYPES = ['Category', '分类'];
export const MINERAL_NODE_TYPES = ['Mineral', '中文名称', '矿物', 'Specimen', '标本'];
export const CHILD_CATEGORIES = ['Year', '年份', 'Location', '产地', 'Color', '颜色'];
export const INVALID_VALUES = ['不详', '未知', '暂无', '无', '暂无无年份信息'];

// 实体分类标签映射
export const entityCategoryLabels = {
  Category: '分类',
  Mineral: '矿物',
  Specimen: '矿物',
  Color: '颜色',
  Location: '产地',
  Year: '年份',
  Formula: '化学式',
};

// 边类型标签映射
export const edgeTypeLabels = {
  BELONGS_TO: '属于',
  FROM_LOCATION: '来自',
  HAS_COLOR: '具有颜色',
  DISCOVERED_IN: '发现于',
  DONATED_BY: '捐赠者',
  HAS_SUBCATEGORY: '包含子类',
};

// 属性标签映射
export const propertyLabels = {
  system: '系统',
  level: '分类层级',
  created_at: '创建时间',
  updated_at: '更新时间',
  description: '描述',
  name: '名称',
  category: '分类',
  type: '类型',
  source_info: '来源信息',
  source_text: '来源文本',
};

// 定义各图谱的颜色配置（与 GraphChart3D.vue 保持一致）
export const specimenColorPalettes = {
  '宝玉石': {
    category: '#6200EA', // Deep Vivid Velvet Purple
    mineral: '#FF0090', // Electric Magenta/Rose (Very Vivid)
    color: '#00B4D8', // Bright Cyan
    location: '#00E676', // Vivid Emerald
    formula: '#FFD600', // Pure Gold
    year: '#FF6D00', // Vivid Orange
    dotColor: '#6200EA', // 列表点颜色同步分类颜色
  },
  '岩石标本': {
    // 黄色+青绿色色调配置 - 与GraphChart3D.vue完全一致
    category: '#F57F17', // 分类节点：深橙黄色（饱和度高，偏橙，最突出）✨
    mineral: '#FFDD4B', // 矿物节点：鲜亮纯黄色（饱和度高，纯黄，与橙黄完全不同）💛
    color: '#FFF59D', // 颜色节点：青绿色（中等饱和度，明显可见）
    location: '#8BC34A', // 产地节点：浅青绿（中等饱和度，清晰）
    formula: '#A5D6A7', // 化学式节点：浅绿色（中等饱和度，淡雅）
    year: '#C0CA33', // 年份节点：极浅黄绿（饱和度适中，最淡）
    dotColor: '#F57F17', // 列表点颜色同步分类颜色
  },
  '矿石标本': {
    // 橙色+橘色色调配置 - 与GraphChart3D.vue完全一致
    category: '#FF5722', // 分类节点：深橙红色（饱和度高，偏红，最突出）✨
    mineral: '#FF9800', // 矿物节点：琥珀金色（饱和度高，偏黄，与橙红完全不同）🧡
    color: '#FF8A65', // 颜色节点：柔和珊瑚橘（中等饱和度，明显可见）
    location: '#FFCC80', // 产地节点：浅橘色（中等饱和度，清晰）
    formula: '#FFE082', // 化学式节点：浅黄橘（中等饱和度，淡雅）
    year: '#FFF59D', // 年份节点：极浅黄（饱和度适中，最淡）
    dotColor: '#FF5722', // 列表点颜色同步分类颜色
  },
  '铀矿物': {
    category: '#1B5E20', // Dark Radiation Green
    mineral: '#76FF03', // Fluorescent Lime (High contrast)
    color: '#00BFA5', // Teal Green (Distinct from Lime)
    location: '#AFB42B', // Olive Yellow
    formula: '#FFFF00', // Pure Yellow (Warning sign color)
    year: '#69F0AE', // Mint Green
    dotColor: '#1B5E20', // 列表点颜色同步分类颜色
  },
  '构造标本': {
    // 灰黄色调渐变色配置 - 使用第一个颜色作为主色
    category: '#FFD700', // 分类节点：纯金黄（使用渐变色的第一个颜色）
    mineral: '#D4A574', // 矿物节点：金黄（使用渐变色的第一个颜色）
    color: '#F4C430', // 颜色节点：金丝雀黄
    location: '#C9B8A0', // 产地节点：浅灰棕
    formula: '#DEB887', // 化学式节点：硬木色
    year: '#F0E68C', // 年份节点：卡其黄
    dotColor: '#FFD700', // 列表点颜色同步分类颜色
  },
  '矿物标本': {
    category: '#2962FF',
    mineral: '#00B0FF',
    color: '#00E5FF',
    location: '#00E676',
    formula: '#C6FF00',
    year: '#C6FF00',
    dotColor: '#2962FF', // 列表点颜色同步分类颜色
  },
};

// 标本类型到 Cypher 查询的映射
export const specimenTypeQueries = {
  '矿物标本': `// 步骤1：圈定“矿物标本”大类的分类树
    MATCH (topX:Category {name: "矿物标本", system: "system1", level: 1})
    OPTIONAL MATCH (topX)-[:HAS_SUBCATEGORY*0..]->(subX:Category)
    WITH collect(DISTINCT topX) + collect(DISTINCT subX) AS X_Cats

    // 步骤2：筛选只属于 X 体系的样本（按分类归属过滤）
    MATCH (s:Specimen)-[:BELONGS_TO]->(c:Category)
    WHERE c IN X_Cats
    WITH X_Cats, collect(DISTINCT s) AS X_Specimens

    // 分支1：样本及其合规关联
    UNWIND X_Specimens AS s_x
    MATCH p = (s_x)-[r:BELONGS_TO|FROM_LOCATION|HAS_COLOR|DISCOVERED_IN|DONATED_BY]-(n)
    WHERE (type(r) = 'BELONGS_TO' AND n IN X_Cats) OR (type(r) <> 'BELONGS_TO' AND NOT (n:Category))
    RETURN DISTINCT p

    UNION ALL

    // 分支2：X 大类内部分类层级
    MATCH (topX:Category {name: "矿物标本", system: "system1", level: 1})
    OPTIONAL MATCH (topX)-[:HAS_SUBCATEGORY*0..]->(subX:Category)
    WITH collect(DISTINCT topX) + collect(DISTINCT subX) AS X_Cats
    UNWIND X_Cats AS cat_x
    MATCH p = (cat_x)<-[:HAS_SUBCATEGORY]-(parent_x:Category)
    WHERE parent_x IN X_Cats
    RETURN DISTINCT p
    LIMIT 500`,

  '岩石标本': `// 步骤1：圈定“岩石标本”大类的分类树
    MATCH (topX:Category {name: "岩石标本", system: "system1", level: 1})
    OPTIONAL MATCH (topX)-[:HAS_SUBCATEGORY*0..]->(subX:Category)
    WITH collect(DISTINCT topX) + collect(DISTINCT subX) AS X_Cats

    // 步骤2：筛选只属于 X 体系的样本
    MATCH (s:Specimen)-[:BELONGS_TO]->(c:Category)
    WHERE c IN X_Cats
    WITH X_Cats, collect(DISTINCT s) AS X_Specimens

    // 分支1：样本及其合规关联
    UNWIND X_Specimens AS s_x
    MATCH p = (s_x)-[r:BELONGS_TO|FROM_LOCATION|HAS_COLOR|DISCOVERED_IN|DONATED_BY]-(n)
    WHERE (type(r) = 'BELONGS_TO' AND n IN X_Cats) OR (type(r) <> 'BELONGS_TO' AND NOT (n:Category))
    RETURN DISTINCT p

    UNION ALL

    // 分支2：X 大类内部分类层级
    MATCH (topX:Category {name: "岩石标本", system: "system1", level: 1})
    OPTIONAL MATCH (topX)-[:HAS_SUBCATEGORY*0..]->(subX:Category)
    WITH collect(DISTINCT topX) + collect(DISTINCT subX) AS X_Cats
    UNWIND X_Cats AS cat_x
    MATCH p = (cat_x)<-[:HAS_SUBCATEGORY]-(parent_x:Category)
    WHERE parent_x IN X_Cats
    RETURN DISTINCT p
    LIMIT 500`,

  '铀矿物': `// 步骤1：圈定“铀矿物”大类的分类树
    MATCH (topX:Category {name: "铀矿物", system: "system1", level: 1})
    OPTIONAL MATCH (topX)-[:HAS_SUBCATEGORY*0..]->(subX:Category)
    WITH collect(DISTINCT topX) + collect(DISTINCT subX) AS X_Cats

    // 步骤2：筛选只属于 X 体系的样本
    MATCH (s:Specimen)-[:BELONGS_TO]->(c:Category)
    WHERE c IN X_Cats
    WITH X_Cats, collect(DISTINCT s) AS X_Specimens

    // 分支1：样本及其合规关联
    UNWIND X_Specimens AS s_x
    MATCH p = (s_x)-[r:BELONGS_TO|FROM_LOCATION|HAS_COLOR|DISCOVERED_IN|DONATED_BY]-(n)
    WHERE (type(r) = 'BELONGS_TO' AND n IN X_Cats) OR (type(r) <> 'BELONGS_TO' AND NOT (n:Category))
    RETURN DISTINCT p

    UNION ALL

    // 分支2：X 大类内部分类层级
    MATCH (topX:Category {name: "铀矿物", system: "system1", level: 1})
    OPTIONAL MATCH (topX)-[:HAS_SUBCATEGORY*0..]->(subX:Category)
    WITH collect(DISTINCT topX) + collect(DISTINCT subX) AS X_Cats
    UNWIND X_Cats AS cat_x
    MATCH p = (cat_x)<-[:HAS_SUBCATEGORY]-(parent_x:Category)
    WHERE parent_x IN X_Cats
    RETURN DISTINCT p
    LIMIT 500`,

  '构造标本': `// 步骤1：圈定“构造标本”大类的分类树
    MATCH (topX:Category {name: "构造标本", system: "system1", level: 1})
    OPTIONAL MATCH (topX)-[:HAS_SUBCATEGORY*0..]->(subX:Category)
    WITH collect(DISTINCT topX) + collect(DISTINCT subX) AS X_Cats

    // 步骤2：筛选只属于 X 体系的样本
    MATCH (s:Specimen)-[:BELONGS_TO]->(c:Category)
    WHERE c IN X_Cats
    WITH X_Cats, collect(DISTINCT s) AS X_Specimens

    // 分支1：样本及其合规关联
    UNWIND X_Specimens AS s_x
    MATCH p = (s_x)-[r:BELONGS_TO|FROM_LOCATION|HAS_COLOR|DISCOVERED_IN|DONATED_BY]-(n)
    WHERE (type(r) = 'BELONGS_TO' AND n IN X_Cats) OR (type(r) <> 'BELONGS_TO' AND NOT (n:Category))
    RETURN DISTINCT p

    UNION ALL

    // 分支2：X 大类内部分类层级
    MATCH (topX:Category {name: "构造标本", system: "system1", level: 1})
    OPTIONAL MATCH (topX)-[:HAS_SUBCATEGORY*0..]->(subX:Category)
    WITH collect(DISTINCT topX) + collect(DISTINCT subX) AS X_Cats
    UNWIND X_Cats AS cat_x
    MATCH p = (cat_x)<-[:HAS_SUBCATEGORY]-(parent_x:Category)
    WHERE parent_x IN X_Cats
    RETURN DISTINCT p
    LIMIT 500`,

  '宝玉石': `// 步骤1：圈定“宝玉石”大类的分类树（该类没有 system/level 限制）
    MATCH (topX:Category {name: "宝玉石"})
    OPTIONAL MATCH (topX)-[:HAS_SUBCATEGORY*0..]->(subX:Category)
    WITH collect(DISTINCT topX) + collect(DISTINCT subX) AS X_Cats

    // 步骤2：筛选只属于 X 体系的样本
    MATCH (s:Specimen)-[:BELONGS_TO]->(c:Category)
    WHERE c IN X_Cats
    WITH X_Cats, collect(DISTINCT s) AS X_Specimens

    // 分支1：样本及其合规关联
    UNWIND X_Specimens AS s_x
    MATCH p = (s_x)-[r:BELONGS_TO|FROM_LOCATION|HAS_COLOR|DISCOVERED_IN|DONATED_BY]-(n)
    WHERE (type(r) = 'BELONGS_TO' AND n IN X_Cats) OR (type(r) <> 'BELONGS_TO' AND NOT (n:Category))
    RETURN DISTINCT p

    UNION ALL

    // 分支2：X 大类内部分类层级
    MATCH (topX:Category {name: "宝玉石"})
    OPTIONAL MATCH (topX)-[:HAS_SUBCATEGORY*0..]->(subX:Category)
    WITH collect(DISTINCT topX) + collect(DISTINCT subX) AS X_Cats
    UNWIND X_Cats AS cat_x
    MATCH p = (cat_x)<-[:HAS_SUBCATEGORY]-(parent_x:Category)
    WHERE parent_x IN X_Cats
    RETURN DISTINCT p
    LIMIT 500`,

  '矿石标本': `// 步骤1：圈定“矿石标本”大类的分类树
    MATCH (topX:Category {name: "矿石标本", system: "system1", level: 1})
    OPTIONAL MATCH (topX)-[:HAS_SUBCATEGORY*0..]->(subX:Category)
    WITH collect(DISTINCT topX) + collect(DISTINCT subX) AS X_Cats

    // 步骤2：筛选只属于 X 体系的样本
    MATCH (s:Specimen)-[:BELONGS_TO]->(c:Category)
    WHERE c IN X_Cats
    WITH X_Cats, collect(DISTINCT s) AS X_Specimens

    // 分支1：样本及其合规关联
    UNWIND X_Specimens AS s_x
    MATCH p = (s_x)-[r:BELONGS_TO|FROM_LOCATION|HAS_COLOR|DISCOVERED_IN|DONATED_BY]-(n)
    WHERE (type(r) = 'BELONGS_TO' AND n IN X_Cats) OR (type(r) <> 'BELONGS_TO' AND NOT (n:Category))
    RETURN DISTINCT p

    UNION ALL

    // 分支2：X 大类内部分类层级
    MATCH (topX:Category {name: "矿石标本", system: "system1", level: 1})
    OPTIONAL MATCH (topX)-[:HAS_SUBCATEGORY*0..]->(subX:Category)
    WITH collect(DISTINCT topX) + collect(DISTINCT subX) AS X_Cats
    UNWIND X_Cats AS cat_x
    MATCH p = (cat_x)<-[:HAS_SUBCATEGORY]-(parent_x:Category)
    WHERE parent_x IN X_Cats
    RETURN DISTINCT p
    LIMIT 500`,
};

export const specimenTypeToTitleMap = {
  '矿物标本': '矿物图谱',
  '宝玉石': '宝玉石图谱',
  '岩石标本': '岩石图谱',
  '矿石标本': '矿石图谱',
  '铀矿物': '铀矿物图谱',
  '构造标本': '构造标本图谱',
};

// 左侧图谱/标本类型列表顺序（与 UI 展示顺序保持一致）
export const specimenList = ['矿物标本', '岩石标本', '铀矿物', '构造标本', '宝玉石', '矿石标本'];

