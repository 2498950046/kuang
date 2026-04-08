# 矿物图谱管理系统

### 系统架构
- **微服务架构**：5001端口（普通功能后台）、5002端口（矿物管理后台）
- **缓存机制**：Redis缓存优化查询性能

### 后端技术
- **Web框架**：Flask + Flask-RESTful
- **数据库**：MySQL（关系数据）、Neo4j（图谱数据）
- **缓存**：Redis
- **ORM**：SQLAlchemy + PyMySQL


```
mineral-graph-system/
├── backendAdmin/                 # 后台管理服务（5002端口）
│   ├── models/                  # 数据模型
│   │   ├── user.py      # MySQL模型
│   │   └── neo4j_models.py      # Neo4j图模型
│   ├── extensions.py           # 扩展模块
│   ├── utils/                  # 工具类
│   │   ├── cache_manager.py    # 缓存管理
│   │   └── validators.py       # 数据验证
│   └── routes/                 # 路由模块
│       ├── mineral.py   # 矿物管理接口
│       └── auth.py     # 管理员接口
├── config.py                 # 配置文件
|── run.py                 # 运行文件
|── create_GemMainInfo.py  # 创建宝玉石mysql表文件
|── create_neo4j_fromMysql.py  # 创建所有矿物neo4j图
└── README.md                 # 项目说明
```
    '''
        backend/
        ├── image_recognition # 矿物识别相关文件
            └── convit_tiny # 微调模型
            └── mineral_dataset # 矿物数据集
            └── myMineralModel # 目前训练的用于矿物识别的模型
            └── testImgMineral # 测试的一些图片
        ├── mineral_data_test/
        │   └── 矿物基本信息.csv     # mysql导出的矿物信息
        └── uploadImages     # 用户矿物识别上传的图片
        imgae_module.py # 模型训练/测试
    '''

## 🚀 快速开始
1.运行create_neo4j_fromMysql.py 完成所有矿物neo4j图谱建立，需在main函数中配置neo4j密码与csv路径信息。 \
2.在create_GemMainInfo.py完成宝玉石基本信息和详细信息建表。（1 sql语句1建立宝玉石基本信息表并从csv文件导入基本信息， 2 sql语句2建立详细信息表 3.运行文件从csv文件导入详细信息到mysql中）\
3.运行backend/app.py  图谱信息获取，问答，宝玉石信息获取，等 \
4.运行backendAdmin/run.py 后台用户的登录注册接口，矿物的增删改查接口




## 📊 数据库设计

### MySQL表结构
- `gems_info`：宝玉石详细信息表
- `gems`：宝玉石基本信息表
- `users`：管理员用户表
- `矿物基本信息`：
- `矿物样品图`：
- 
# postman接口信息
https://tx12377-6896845.postman.co/workspace/Eros's-Workspace~d732bc6d-4c7f-457b-842a-d9951df05b65/collection/50930657-5adc874a-2992-422f-85f4-2d96ddc0f562?action=share&source=copy-link&creator=50930657


# 深度学习环境
    cuda: 11.8
    其他: requirements.txt