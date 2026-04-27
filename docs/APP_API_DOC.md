# App 接口对接文档

更新时间：2026-04-26

## 1. 部署口径

当前线上服务按下面方式拆分，请 App 直接按端口访问，不要走网页端的代理路径：

| 功能 | 服务 | 端口 | Base URL |
| --- | --- | --- | --- |
| 图谱查询、图谱相关数据 | 当前仓库 `backend_all/backend` | `5000` | `http://154.44.25.243:5000` |
| 智能鉴赏、摄像头实时识别 | 既有服务 `kuangshi-backend` | `8080` | `http://154.44.25.243:8080` |
| 智能问答 | 既有服务 `java-ai-langchain4j-app` | `8081` | `http://154.44.25.243:8081` |
| 管理后台 | 当前仓库 `backendAdmin` | `5002` | `http://154.44.25.243:5002` |

说明：

- App 对接请直接用上面的 Base URL。
- `/backend`、`/qa-api`、`/gem-api`、`/admin-api` 这些是网页前端 Nginx 代理路径，不是给 App 直接调用的公网接口。
- `5000` 和 `5002` 的接口已按当前仓库代码核对。
- `8080` 和 `8081` 的接口结构来自当前前端真实调用方式，因为这两部分服务代码不在本仓库中。

## 2. App 建议对接范围

建议 App 按功能拆分：

- 图谱相关统一接 `5000`
- 智能鉴赏统一接 `8080`
- 智能问答统一接 `8081`
- `5002` 只在 App 需要后台管理能力时才接

不建议 App 调用：

- `POST http://154.44.25.243:5000/ai/mineral_dec`
  - 当前 `5000` 服务默认关闭图像模型
  - 该接口当前会返回 `503`
  - 图片识别请统一改走 `8080`

## 3. 图谱与图谱相关接口

Base URL：`http://154.44.25.243:5000`

### 3.1 图谱查询

`POST /graph`

请求体：

```json
{
  "cypher": "MATCH p=(n)-[r]->(m) RETURN p LIMIT 10"
}
```

返回示例：

```json
{
  "type": "graph",
  "data": {
    "nodes": [],
    "links": []
  }
}
```

说明：

- `cypher` 可不传
- 不传时默认执行：`MATCH p=(n)-[r]->(m) RETURN p LIMIT 10`
- 适合图谱渲染、自定义 Cypher 查询、图数据拉取

### 3.2 自然语言转图谱查询

`POST /ai/nl2cypher`

请求体：

```json
{
  "question": "石英的物理性质是什么"
}
```

返回示例：

```json
{
  "success": true,
  "cypher": "MATCH ...",
  "short_answer": "简短回答",
  "answer": "详细回答",
  "result": {
    "data": {}
  },
  "error": null
}
```

App 建议重点读取：

- `success`
- `cypher`
- `short_answer`
- `answer`
- `result`
- `error`

说明：

- `short_answer` 和 `answer` 可能同时存在，也可能只返回其中一个
- 图数据通常在 `result.data` 中

### 3.3 图谱 Schema

`GET /ai/schema`

返回示例：

```json
{
  "success": true,
  "schema": {
    "nodes": [],
    "relationships": []
  }
}
```

### 3.4 健康检查

`GET /health`

返回示例：

```json
{
  "status": "健康",
  "timestamp": "2026-04-26T10:00:00",
  "services": {
    "database": "已连接",
    "ai_service": "已连接",
    "cache": "已连接"
  }
}
```

说明：

- HTTP `200`：健康
- HTTP `503`：部分不健康或不健康

### 3.5 矿物样品图列表

`GET /api/mineral_samples?name=矿物名`

示例：

```http
GET /api/mineral_samples?name=石英
```

返回示例：

```json
{
  "success": true,
  "samples": [
    {
      "id": 1,
      "image_url": "xxx",
      "description": "xxx"
    }
  ]
}
```

### 3.6 样品特有描述

`GET /api/mineral/table2_description?id=数字ID`

示例：

```http
GET /api/mineral/table2_description?id=12
```

返回示例：

```json
{
  "code": 200,
  "data": {
    "description": "描述文本",
    "特有描述": "描述文本"
  }
}
```

### 3.7 矿物基础信息

`POST /mineral/info`

请求体二选一：

```json
{
  "mineral_id": "12"
}
```

或：

```json
{
  "mineral_name": "石英"
}
```

返回示例：

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "id": "12",
    "中文名称": "石英",
    "英文名称": "Quartz",
    "产地": "..."
  }
}
```

### 3.8 宝玉石基础信息模糊查询

`POST /gems/gems_main`

请求体：

```json
{
  "name": "红宝石",
  "exact_match": false
}
```

返回示例：

```json
{
  "code": 200,
  "message": "查询成功",
  "data": [
    {
      "id": 1,
      "name": "红宝石",
      "type": "Ruby",
      "image_url": "https://example.com/image.jpg",
      "color": "#e0115f",
      "info": "宝石描述信息"
    }
  ]
}
```

说明：

- `exact_match=true` 时走精确匹配
- `exact_match=false` 时走模糊匹配

### 3.9 宝玉石批量查询

`POST /gems/gems_batch`

请求体：

```json
{
  "names": ["红宝石", "蓝宝石"],
  "fields": ["id", "name", "type", "image_url", "color", "info"]
}
```

返回示例：

```json
{
  "code": 200,
  "message": "查询成功",
  "data": [],
  "count": 0
}
```

说明：

- `fields` 可选
- 不传时默认返回：`id`、`name`、`type`、`image_url`、`color`、`info`

### 3.10 宝玉石详情

`POST /gems/gems_detail`

请求体：

```json
{
  "gem_name": "坦桑石"
}
```

返回示例：

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "id": "690ef0ab4b36a72239be3dd9",
    "gem_name": "坦桑石",
    "basic_info": {},
    "material_properties": {},
    "treatments": {}
  }
}
```

说明：

- `basic_info`、`material_properties`、`treatments` 为 JSON 对象

### 3.11 宝玉石属性定向查询

`POST /gems/gems_property`

请求体：

```json
{
  "gem_name": "红宝石",
  "property_type": "material_properties",
  "property_keys": ["化学成分", "摩氏硬度", "密度"]
}
```

返回示例：

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "gem_name": "红宝石",
    "property_type": "material_properties",
    "properties": {}
  }
}
```

说明：

- `property_type` 仅支持：
  - `basic_info`
  - `material_properties`
  - `treatments`
- `property_keys` 可选
- 传了 `property_keys` 时，返回值只保留指定字段

### 3.12 语音转文字

`POST /api/speech-to-text`

请求方式：

- `multipart/form-data`
- 文件字段名：`audio`
- 文件要求：`.pcm`
- 采样率要求：`16000`

返回示例：

```json
{
  "success": true,
  "text": "识别后的文本"
}
```

说明：

- 当前网页前端会先把录音转换成 `PCM 16kHz` 再上传
- App 如直接上传，也需保证格式匹配

## 4. 智能鉴赏接口

Base URL：`http://154.44.25.243:8080`

说明：

- 该服务不是当前仓库的 `backend_all/backend`
- 当前仓库只把它当成既有外部服务来接入
- 以下结构来自前端实际调用

### 4.1 图片鉴赏识别

`POST /api/gem/predict`

请求方式：

- `multipart/form-data`

字段：

- `model`：模型名
  - `convnext`
  - `efficientNetB3`
  - `convnext_all`
- `file`：图片文件
- `text`：可选，补充文字描述

请求示例：

```text
model=convnext
file=<image>
text=可选描述
```

前端期望返回结构：

```json
{
  "top_prediction": "ruby",
  "predictions": [
    {
      "label": "ruby",
      "score": 0.92
    }
  ],
  "analysis": "AI 综合鉴定报告"
}
```

### 4.2 实时摄像头识别

WebSocket：`ws://154.44.25.243:8080/ws/gem/predict`

发送数据格式：

```json
{
  "model": "convnext",
  "image": "data:image/jpeg;base64,xxxxx"
}
```

前端期望接收格式：

```json
{
  "top_prediction": "ruby",
  "predictions": [
    {
      "label": "ruby",
      "score": 0.92
    }
  ]
}
```

## 5. 智能问答接口

Base URL：`http://154.44.25.243:8081`

说明：

- 该服务不是当前仓库代码
- 以下结构来自前端实际调用

### 5.1 获取会话 chat_id

`POST /ai/chat_id`

请求体：

```json
{
  "memoryId": 1745580000000
}
```

返回说明：

- 前端当前按纯文本读取
- 通常返回一个字符串型 `chat_id`

### 5.2 流式问答

`POST /ai/chat_two_step`

请求头：

```http
Content-Type: application/json
Accept: application/x-stream
```

请求体：

```json
{
  "memoryId": 1745580000000,
  "message": "请介绍石英"
}
```

返回说明：

- 返回 HTTP 流式文本
- 前端当前按 `ReadableStream` 逐块拼接
- 当前前端没有按 SSE 事件对象解析，而是直接拼正文

### 5.3 获取历史记录

`GET /ai/history/{memoryId}`

示例：

```http
GET /ai/history/1745580000000
```

前端期望格式：

```json
[
  {
    "question": "问题",
    "answer": "回答",
    "reference_materials": "[{\"document_name\":\"文档1\",\"content\":\"内容\"}]"
  }
]
```

说明：

- `reference_materials` 是 JSON 字符串，不是 JSON 对象
- App 侧如果要使用参考资料，需要再执行一次 JSON 解析

## 6. 后台管理接口

Base URL：`http://154.44.25.243:5002`

说明：

- 这部分通常给后台管理端使用
- App 如果没有后台录入、编辑矿物的需求，可以忽略本节

### 6.1 登录

`POST /auth/login`

请求体：

```json
{
  "username": "admin",
  "password": "Admin@123456"
}
```

返回示例：

```json
{
  "success": true,
  "message": "登录成功",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com"
  },
  "access_token": "jwt-token"
}
```

### 6.2 注册

`POST /auth/register`

请求体：

```json
{
  "username": "admin2",
  "email": "admin2@example.com",
  "password": "Admin@123456"
}
```

### 6.3 修改密码

`POST /auth/change-password`

请求头：

```http
Authorization: Bearer <access_token>
```

请求体：

```json
{
  "old_password": "Admin@123456",
  "new_password": "NewPassword123"
}
```

### 6.4 获取全部矿物

`GET /manage/get_all_minerals`

返回结构示例：

```json
{
  "success": true,
  "message": "查询成功",
  "data": [],
  "count": 0
}
```

### 6.5 查询单个矿物

`POST /manage/get_mineral`

请求体：

```json
{
  "中文名称": "石英"
}
```

### 6.6 添加矿物

`POST /manage/add_mineral`

说明：

- 当前代码要求至少传 `中文名称`
- 实际业务通常还会带 `英文名称`、`化学式`、`产地`、`颜色`、`发现年份`、`基本描述`
- 分类字段命名形式为：`标本分类1-1` 到 `标本分类3-4`

### 6.7 更新矿物

`POST /manage/update_mineral`

说明：

- 请求体结构基本与“添加矿物”一致

### 6.8 删除矿物

`POST /manage/delete_mineral`

请求体：

```json
{
  "中文名称": "石英"
}
```

## 7. 给 App 同事的落地建议

### 7.1 推荐直接接的接口

图谱相关：

- `POST /graph`
- `POST /ai/nl2cypher`
- `GET /ai/schema`
- `GET /health`
- `GET /api/mineral_samples`
- `GET /api/mineral/table2_description`
- `POST /mineral/info`
- `POST /gems/gems_main`
- `POST /gems/gems_batch`
- `POST /gems/gems_detail`
- `POST /gems/gems_property`
- `POST /api/speech-to-text`

智能鉴赏：

- `POST /api/gem/predict`
- `WS /ws/gem/predict`

智能问答：

- `POST /ai/chat_id`
- `POST /ai/chat_two_step`
- `GET /ai/history/{memoryId}`

### 7.2 建议的前后端功能映射

- 图谱页、图谱搜索、矿物详情、样品图、语音搜索：走 `5000`
- 鉴赏拍照识别、摄像头识别：走 `8080`
- 对话问答、历史会话：走 `8081`

### 7.3 注意事项

- App 不要调用网页代理路径 `/backend`、`/qa-api`、`/gem-api`、`/admin-api`
- `5000 /ai/mineral_dec` 当前不要接
- `8080`、`8081` 返回结构后续如果服务方有调整，需要以线上实际返回为准
