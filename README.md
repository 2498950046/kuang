## KGraphVis 项目说明

一个基于 Vue 3 + Vite 的矿物知识图谱可视化系统，支持：
- 3D 图谱浏览（节点展开/收缩、筛选、样式编辑）
- 自然语言检索（NL2Cypher）
- AI 问答流式返回（SSE）
- 矿物详情与标本轮播查看
- 手势交互控制（摄像头 + 手势识别）
- 标本库与后台管理页面

该文档面向新同伴，目标是让你可以快速理解系统结构并开始开发。

---

## 1. 技术栈

- 前端框架：`Vue 3`（Composition API）
- 构建工具：`Vite`
- 路由：`vue-router`
- UI：`Element Plus`
- 图谱渲染：`3d-force-graph`、`three-spritetext`
- 动画：`gsap`
- 语音/多模态相关：`vosk-browser`、`@xenova/transformers`
- 数据与管理接口：HTTP API（后端默认 `http://localhost:5000`）

---

## 2. 运行环境要求

- Node.js：建议 `>= 18`
- npm：建议 `>= 9`
- 浏览器：Chrome / Edge 最新版本（手势、媒体能力更稳定）

---

## 3. 快速开始

### 3.1 安装依赖

```bash
npm install
```

### 3.2 启动开发环境

```bash
npm run dev
```

默认由 Vite 启动前端开发服务器。

### 3.3 生产构建与预览

```bash
npm run build
npm run preview
```

---

## 4. 环境变量与后端联调

项目 API 通过 `src/api/index.js` 和 `src/api/adminPortal.js` 访问，主要依赖：

- `VITE_API_URL`：主业务 API 基址
- `VITE_ADMIN_API_URL`：后台管理 API 基址（可选，不配时回退到 `VITE_API_URL`）

### 4.1 建议创建 `.env.development`

```env
VITE_API_URL=http://localhost:5000
VITE_ADMIN_API_URL=http://localhost:5000
```

### 4.2 开发代理（Vite）

`vite.config.js` 中已配置以下代理到 `http://localhost:5000`：
- `/api`
- `/ai`
- `/mineral`

所以开发模式下，部分接口会优先走相对路径（减少 CORS 问题）。

---

## 5. 页面路由说明

路由定义在 `src/router/index.js`：

- `/`：首页（系统介绍）
- `/graph`：图谱视图
- `/qa`：智能问答视图
- `/specimen-library/:type`：标本库分类页
- `/specimen-library/:type/:name`：矿物详情页
- `/admin/login`：后台登录
- `/admin/minerals`：后台矿物管理（需要登录态）
- `*`：其他路径重定向到 `/graph`

后台登录 token 存储在 `localStorage`（见 `src/api/adminPortal.js`）。

---

## 6. 项目结构（核心目录）

```text
src/
  api/                       # 前后端通信封装
  components/                # 业务组件（图谱、侧边栏、问答、面板等）
  router/                    # 路由配置
  services/                  # 手势识别等服务层
  utils/
    graph/                   # 图谱相关纯逻辑/引擎
    mineral/                 # 矿物详情、图片、解析工具
    gesture/                 # 手势控制逻辑
  views/                     # 路由页面
  App.vue                    # 应用总入口（页面编排 + 状态接线）
```

---

## 7. 按文件说明（重点）

你提到希望“着重介绍每一个文件的作用”，这里按目录拆开讲。  
为了可读性，优先覆盖日常开发最常碰到的文件（尤其是图谱链路）。

### 7.1 入口与路由

- `src/main.js`：应用入口，注册 `ElementPlus`、`router`，挂载 `App.vue`。
- `src/App.vue`：全局编排层，负责页面框架、状态接线、模块调用（已经把大量逻辑下沉到 `utils`）。
- `src/router/index.js`：所有前端路由与后台鉴权守卫（`/admin/*`）。

### 7.2 API 层（`src/api`）

- `src/api/index.js`：主业务 API 封装（图查询、NL2Cypher、RAG 流式、矿物详情、识别、语音等）。
- `src/api/adminPortal.js`：后台管理登录与矿物管理接口，包含 token 持久化逻辑。
- `src/api/admin.js`：后台管理的补充接口封装（若页面调用该文件则归属于 admin 侧能力）。

### 7.3 图谱核心逻辑（`src/utils/graph`）

这些文件是图谱行为的“脑子”，建议优先阅读：

- `src/utils/graph/graphEngine.js`：图谱引擎层（`runQuery / initGraphOnce / initializeStyleConfig`）。
- `src/utils/graph/graphFilteredData.js`：最终可见节点/边计算（层级展开 + 样式可见性 + 时间过滤）。
- `src/utils/graph/graphExpansionState.js`：展开状态初始化与查询结果自动展开策略。
- `src/utils/graph/graphSearch.js`：搜索流程（缓存、loading、防并发、NL2Cypher 结果应用）。
- `src/utils/graph/graphNodeClick.js`：图谱节点单击/双击、背景点击等交互判定。
- `src/utils/graph/graphInteractionsApp.js`：`App.vue` 对图谱事件的响应适配层（选择、展开、关联查询等）。
- `src/utils/graph/graphSelection.js`：节点/边 -> `selectedItem` 的映射构建工具。
- `src/utils/graph/graphExpandHelpers.js`：分类子节点/矿物子节点查找与计数等辅助函数。
- `src/utils/graph/graphTimeRange.js`：关系时间解析与图谱时间范围计算。
- `src/utils/graph/graphStyleEditor.js`：样式编辑器的可选标签属性收集逻辑。
- `src/utils/graph/graphStats.js`：统计面板所需全局统计数据获取。
- `src/utils/graph/graphSpecimenConfig.js`：图谱用常量配置（类别、关系标签、配色、查询模板、标本类型映射）。

### 7.4 矿物与标本逻辑（`src/utils/mineral`）

- `src/utils/mineral/mineralDetailPanelLogic.js`：矿物详情面板核心逻辑（详情拼装、轮播、拖拽、缩放等）。
- `src/utils/mineral/mineralAppHelpers.js`：矿物模块通用工具（解析、预加载、指针位置等）。
- `src/utils/mineral/mineralDescriptionParser.js`：矿物描述文本解析。
- `src/utils/mineral/mineralImgLoader.js`：矿物图片资源加载辅助。

### 7.5 手势逻辑（`src/utils/gesture` + `src/services`）

- `src/services/gestureRecognition.js`：手势识别规则（关键点到手势类型）。
- `src/utils/gesture/gestureControl.js`：识别结果到图谱动作的控制层（旋转/缩放/选择等）。

### 7.6 核心视图组件（`src/components`）

图谱主链路常见文件：

- `src/components/GraphChart3D.vue`：3D 图谱渲染主体组件。
- `src/components/GraphSpecimenSidebar.vue`：图谱侧边栏（分类/标本入口与交互）。
- `src/components/TimeSlider.vue`：时间范围筛选组件。
- `src/components/StyleEditor.vue`：图谱样式编辑器。
- `src/components/OverviewPanel.vue`：图谱概览面板。
- `src/components/InfoPanel.vue`：信息面板（节点/边信息展示）。
- `src/components/BottomDock.vue`：底部 Dock（统计/面板切换）。
- `src/components/GraphAnswerPanel.vue`：图谱查询结果相关回答面板。
- `src/components/MineralDetailPanel.vue`：矿物详情 UI 容器（逻辑已下沉到 util）。

AI 与多模态相关：

- `src/components/AIChat.vue`：智能问答主组件。
- `src/components/AIChat/ChatMessages.vue`：消息列表渲染。
- `src/components/AIChat/ModeNavigation.vue`：问答模式切换导航。
- `src/components/AIChat/RecentHistory.vue`：历史记录展示。
- `src/components/GestureOverlay.vue`：摄像头视频层与手势输入桥接。
- `src/components/GestureGuide.vue`：手势说明与教学面板。

其他常见组件（页面壳与功能块）：

- `src/components/SystemIntroduction.vue`：系统介绍首页内容。
- `src/components/Loading.vue`：加载态展示。
- `src/components/TopBanner.vue`：顶部标题栏。
- `src/components/TopActionsBar.vue`：顶部操作按钮区。
- `src/components/SpecimenLibrarySidebar.vue`：标本库侧边导航。
- `src/components/TableView.vue`：表格结果视图（非图谱数据）。
- `src/components/MineralViewer.vue`：矿物展示组件。
- `src/components/GemstoneImageCarousel.vue` / `src/components/ImageCarousel.vue`：轮播展示组件。

### 7.7 路由页面（`src/views`）

- `src/views/HomeView.vue`：首页（系统介绍页）。
- `src/views/GraphView.vue`：图谱路由页面。
- `src/views/QAView.vue`：智能问答路由页面。
- `src/views/SpecimenLibraryView.vue`：标本库列表页。
- `src/views/MineralDetailView.vue`：矿物详情路由页。
- `src/views/admin/AdminLayout.vue`：后台布局容器。
- `src/views/admin/AdminLoginView.vue`：后台登录页。
- `src/views/admin/AdminMineralsView.vue`：后台矿物管理页。

### 7.8 其他文件

- `src/style.css`：全局样式入口。
- `src/data/gemstones.json`：宝玉石静态数据。
- `src/utils/formatters.js`：历史工具文件（若未引用可评估清理）。

---

## 8. 核心模块设计（重点）

### 7.1 图谱引擎层

文件：`src/utils/graph/graphEngine.js`

职责：
- 执行查询（`runQuery`）
- 初始化图谱（`initGraphOnce`）
- 初始化节点/边样式（`initializeStyleConfig`）

特点：
- 通过依赖注入接收 `rawData/styleConfig/route/currentView` 等状态
- 保持与 `App.vue` 的 UI 层解耦

### 7.2 图谱过滤与显示计算

文件：`src/utils/graph/graphFilteredData.js`

职责：
- 根据层级、展开状态、样式可见性、时间范围，计算最终 `nodes/links`
- 控制时间筛选开关状态（`TimeSliderCurrentView`）

这是当前图谱展示逻辑里最核心、最复杂的一层。

### 7.3 节点展开状态

文件：`src/utils/graph/graphExpansionState.js`

职责：
- 初始化层级展开状态（分类节点/矿物节点）
- 查询结果返回后，自动展开矿物子节点

### 7.4 搜索与 AI 转 Cypher

文件：`src/utils/graph/graphSearch.js`

职责：
- 处理搜索输入
- 调用 `nl2cypher`
- 管理搜索缓存与历史
- 应用图数据结果

### 7.5 矿物详情面板逻辑

文件：`src/utils/mineral/mineralDetailPanelLogic.js`

职责：
- 矿物详情信息组装
- 标本图像轮播、放大、拖拽等交互
- 与详情组件状态协同

### 7.6 手势交互

相关文件：
- `src/services/gestureRecognition.js`（手势识别规则）
- `src/utils/gesture/gestureControl.js`（手势到 UI/图谱动作映射）
- `src/components/GestureOverlay.vue`（摄像头与覆盖层）

---

## 9. API 概览（前端调用侧）

`src/api/index.js` 中常用接口：

- `graphQuery(cypher)`：执行图查询
- `nl2cypher(question)`：自然语言转 Cypher
- `ragStream(question, { onEvent })`：流式问答
- `fetchMineralSamples(name)`：矿物标本数据
- `getMineralInfo(...)`：矿物详情
- `getSpecimenDescriptionByTable2Id(id)`：标本特有描述
- `identifyMineral(base64Image)`：矿物识别
- `speechToText(audioBlob)`：语音识别

后台管理接口见：`src/api/adminPortal.js`

---

## 10. 开发建议与协作约定

### 9.1 推荐开发流程

1. 拉取最新代码
2. `npm install`
3. 确认后端服务在 `5000` 端口可用
4. `npm run dev` 本地联调
5. 修改后运行 `npm run build` 做一次构建验证

### 9.2 代码组织建议

- 尽量把“纯计算逻辑”放进 `src/utils/*`
- `App.vue` 主要负责状态编排、路由和组件接线
- 新增功能优先考虑“依赖注入”风格，减少耦合

### 9.3 常见改动入口

- 图谱展示异常：优先看 `graphFilteredData.js`
- 查询/初始化异常：看 `graphEngine.js`
- 搜索行为异常：看 `graphSearch.js`
- 节点展开异常：看 `graphExpansionState.js`
- 详情面板异常：看 `mineralDetailPanelLogic.js`

---

## 11. 常见问题（FAQ）

### Q1：页面一直加载或图谱为空？

先检查：
- 后端是否已启动（默认 `http://localhost:5000`）
- `.env` 的 `VITE_API_URL` 是否正确
- 浏览器控制台是否有接口 4xx/5xx

### Q2：开发环境 API 跨域报错？

确认是否通过 `npm run dev` 启动（走 Vite 代理），并检查 `vite.config.js` 代理配置。

### Q3：手势功能无法启动？

检查：
- 浏览器是否允许摄像头权限
- 是否在 HTTPS 或 localhost 环境
- 控制台是否有媒体设备相关报错

### Q4：后台页无法进入？

`/admin/minerals` 需要登录态 token；若 token 失效，清理本地存储并重新登录。

---

## 12. 可继续完善的方向

- 增加单元测试（尤其是 `src/utils/graph/*` 纯函数）
- 补充 E2E 测试（图谱筛选、搜索、详情面板）
- 统一日志级别与错误提示策略
- 进一步拆分 `App.vue` 的页面编排逻辑

---

## 13. 许可证

当前仓库未显式声明 License。若要对外共享，请先补充许可证文件（如 `MIT`）。
