import os
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Config:
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

    # 矿石neo4j数据库配置
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7688")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "12345678")

    # AI configuration
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "deepseek")
    AI_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "sk-816a3669b8f2457dac1d68b16a75188b")
    AI_BASE_URL: str = os.getenv("AI_BASE_URL", "https://api.deepseek.com")
    AI_MODEL: str = os.getenv("AI_MODEL", "deepseek-chat")
    AI_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.001"))
    AI_MAX_TOKENS: int = int(os.getenv("AI_MAX_TOKENS", "8192"))

    # Redis configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")

    # Cache configuration
    SCHEMA_CACHE_TTL: int = int(os.getenv("SCHEMA_CACHE_TTL", "3600"))  # 1 hour
    QUERY_CACHE_TTL: int = int(os.getenv("QUERY_CACHE_TTL", "1800"))  # 30 minutes
    ENTITY_CACHE_TTL: int = int(os.getenv("ENTITY_CACHE_TTL", "1200"))  # 20 minutes

    # Performance configuration
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "4"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "2"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))

    # 图片上传配置
    ROOT_DIR = Path(__file__).parent
    UPLOAD_FOLDER = ROOT_DIR / 'uploadImages'  # 图片保存目录
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}  # 允许的文件类型
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 最大文件大小 16MB

    # 深度学习配置
    NUM_CLASSES = 87  # 根据实际矿物类别数调整
    MODEL_NAME = 'convit_tiny'
    LEARNING_RATE = 1e-4
    NUM_EPOCHS = 50
    BATCH_SIZE = 64
    LOCAL_MODEL_PATH = ROOT_DIR / 'image_recognition' / 'convit_tiny'
    TRAIN_DIR = ROOT_DIR / 'image_recognition' / 'mineral_dataset' / 'train'
    VAL_DIR = ROOT_DIR / 'image_recognition' / 'mineral_dataset' / 'test'
    BEST_MODEL_PATH = ROOT_DIR / 'image_recognition' / 'myMineralModel' / 'convit_mineral.pth'

    # 矿物英文名到中文
    mineral_translate_dic = {
        'Alexandrite': '变石/亚历山大石',
        'Almandine': '铁铝榴石',
        'Amazonite': '天河石',
        'Amber': '琥珀',
        'Amethyst': '紫水晶',
        'Ametrine': '紫黄晶',
        'Andalusite': '红柱石',
        'Andradite': '钙铁榴石',
        'Aquamarine': '海蓝宝石',
        'Aventurine Green': '绿东陵石',
        'Aventurine Yellow': '黄东陵石',
        'Benitoite': '蓝锥矿',
        'Beryl Golden': '金绿柱石',
        'Bixbite': '红色绿柱石',
        'Bloodstone': '血石',
        'Blue Lace Agate': '蓝纹玛瑙',
        'Carnelian': '红玉髓',
        'Cats Eye': '猫眼石',
        'Chalcedony': '玉髓',
        'Chalcedony Blue': '蓝玉髓',
        'Chrome Diopside': '铬透辉石',
        'Chrysoberyl': '金绿宝石',
        'Chrysocolla': '硅孔雀石',
        'Chrysoprase': '绿玉髓',
        'Citrine': '黄水晶',
        'Coral': '珊瑚',
        'Danburite': '赛黄晶',
        'Diamond': '钻石',
        'Diaspore': '硬水铝石',
        'Dumortierite': '蓝线石',
        'Emerald': '祖母绿',
        'Fluorite': '萤石',
        'Garnet Red': '红色石榴石',
        'Goshenite': '无色绿柱石',
        'Grossular': '钙铝榴石',
        'Hessonite': '桂榴石',
        'Hiddenite': '翠绿锂辉石',
        'Iolite': '堇青石',
        'Jade': '翡翠/玉石',
        'Jasper': '碧玉',
        'Kunzite': '紫锂辉石',
        'Kyanite': '蓝晶石',
        'Labradorite': '拉长石',
        'Lapis Lazuli': '青金石',
        'Larimar': '海纹石',
        'Malachite': '孔雀石',
        'Moonstone': '月光石',
        'Morganite': '摩根石',
        'Onyx Black': '黑玛瑙',
        'Onyx Green': '绿玛瑙',
        'Onyx Red': '红玛瑙',
        'Opal': '欧泊',
        'Pearl': '珍珠',
        'Peridot': '橄榄石',
        'Prehnite': '葡萄石',
        'Pyrite': '黄铁矿',
        'Pyrope': '镁铝榴石',
        'Quartz Beer': '啤酒石英',
        'Quartz Lemon': '柠檬石英',
        'Quartz Rose': '玫瑰石英',
        'Quartz Rutilated': '金发晶',
        'Quartz Smoky': '烟晶',
        'Rhodochrosite': '菱锰矿',
        'Rhodolite': '玫红榴石',
        'Rhodonite': '蔷薇辉石',
        'Ruby': '红宝石',
        'Sapphire Blue': '蓝宝石',
        'Sapphire Pink': '粉色蓝宝石',
        'Sapphire Purple': '紫色蓝宝石',
        'Sapphire Yellow': '黄色蓝宝石',
        'Scapolite': '方柱石',
        'Serpentine': '蛇纹石',
        'Sodalite': '方钠石',
        'Spessartite': '锰铝榴石',
        'Sphene': '榍石',
        'Spinel': '尖晶石',
        'Spodumene': '锂辉石',
        'Sunstone': '日光石',
        'Tanzanite': '坦桑石',
        'Tigers Eye': '虎眼石',
        'Topaz': '托帕石',
        'Tourmaline': '碧玺',
        'Tsavorite': '沙弗莱石',
        'Turquoise': '绿松石',
        'Variscite': '磷铝石',
        'Zircon': '锆石',
        'Zoisite': '黝帘石'
    }

    # 宝玉石mysql数据库配置
    # 数据库配置
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',  # 修改为您的用户名
        'password': '123456',  # 修改为您的密码
        'database': 'mineral_database',  # 确保这是您的数据库名
        'charset': 'utf8mb4'
    }

    # 百度语音识别配置
    API_KEY = "1nYv7Ew43IR0DR5sPGOU6aeb"
    SECRET_KEY = "wjou04uqgxDyRpegMcEsjEMontfLIlG5"
    TOKEN = '24.9bb4a5ef3d767423256b239c92ea7d11.2592000.1772187247.282335-121962399'


config = Config()
