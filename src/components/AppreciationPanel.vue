<template>
  <div class="appreciation-panel">
    
    <div class="welcome-section">
      <div class="welcome-icon">🔍</div>
      <h3>智能鉴赏与实时识别</h3>
      <p>通过图像识别模型和多模态 AI，为您提供专业的矿物鉴定辅助。</p>
    </div>

    <div class="model-selector-container">
      <div class="model-selector-label">
        <el-icon style="margin-right: 6px;"><Cpu /></el-icon>
        选择底层 AI 识别引擎：
      </div>
      <el-select v-model="selectedModel" class="model-select" style="width: 340px;">
        <el-option label="ConvNeXt-44种宝玉石(最新推荐版)" value="convnext" />
        <el-option label="EfficientNetB3-44种宝玉石(稳定基础版)" value="efficientNetB3" />
        <el-option label="ConvNeXt-557种矿物(Beta)" value="convnext_all" />
      </el-select>
    </div>

    <div class="features-container">
      
      <div class="feature-card" @click="openDialog">
        <div class="card-icon-box blue-theme">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        </div>
        <div class="card-content">
          <h4>智能图片识别</h4>
          <p>上传矿物图片，结合您的文本描述，AI 将为您生成综合鉴定报告。</p>
        </div>
        <div class="card-action">
          <span>立即上传</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </div>
      </div>

      <div class="feature-card rt-card" @click="openRtDialog">
        <div class="card-icon-box orange-theme">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
            <circle cx="12" cy="13" r="3" />
          </svg>
        </div>
        <div class="card-content">
          <h4>实时摄像头识别</h4>
          <p>打开电脑或手机摄像头，动态追踪并实时识别镜头中的矿物目标。</p>
        </div>
        <div class="card-action">
          <span>开启摄像头</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </div>
      </div>

      <!-- <div class="feature-card dl-card" @click="openDeepLearningPlatform">
        <div class="card-icon-box green-theme">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2v4" />
            <path d="M12 18v4" />
            <path d="M4.93 4.93l2.83 2.83" />
            <path d="M16.24 16.24l2.83 2.83" />
            <path d="M2 12h4" />
            <path d="M18 12h4" />
            <path d="M4.93 19.07l2.83-2.83" />
            <path d="M16.24 7.76l2.83-2.83" />
            <circle cx="12" cy="12" r="4" />
          </svg>
        </div>
        <div class="card-content">
          <h4>算法模型可视化平台</h4>
          <p>进入独立深度学习平台，直接切换到训练与推理页面。</p>
        </div>
        <div class="card-action">
          <span>打开平台</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </div>
      </div> -->

    </div>

    <el-dialog 
      title="智能鉴赏" 
      v-model="dialogVisible" 
      width="500px" 
      :close-on-click-modal="false" 
      @close="handleClose"
      class="mac-el-dialog"
    >
      <div v-if="!resultData" v-loading="loading" element-loading-text="正在智能分析中..." element-loading-background="rgba(15, 23, 42, 0.7)">
        <el-form :model="form" label-position="top">
          <el-form-item label="上传图片 (必须)">
            <el-upload
              v-if="!previewUrl"
              class="upload-area"
              drag
              action="#"
              :auto-upload="false"
              :show-file-list="false"
              :on-change="handleFileChange"
              accept=".jpg,.jpeg,.png,.bmp,.webp"
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">点击或拖拽上传图片</div>
            </el-upload>
            <div v-else class="preview-container">
              <img :src="previewUrl" class="preview-img" />
              <div class="preview-actions">
                <el-button type="danger" circle size="small" @click="removeImage">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </el-form-item>

          <el-form-item label="文本描述 (可选补充)">
            <el-input

            
              type="textarea"
              v-model="form.text"
              placeholder="例如：这是在哪里购买的，有什么明显的物理特征..."
              :autosize="{ minRows: 3, maxRows: 6 }"
              class="custom-textarea"
            />
          </el-form-item>
        </el-form>
      </div>

      <div v-else class="result-container">
        <div class="top-prediction">
          <div class="prediction-label">AI 视觉识别结果</div>
          <div class="prediction-value">{{ translateGemName(resultData.top_prediction) }}</div>
        </div>
        
        <div class="result-list">
          <div v-for="(item, index) in resultData.predictions" :key="index" class="result-item">
            <div class="result-info">
              <span class="gem-name">{{ index + 1 }}. {{ translateGemName(item.label) }}</span>
              <span class="gem-score">{{ (item.score * 100).toFixed(2) }}%</span>
            </div>
            <el-progress 
              :percentage="Number((item.score * 100).toFixed(2))" 
              :stroke-width="8" 
              :color="getProgressColor(index)"
              :show-text="false"
            />
          </div>
        </div>
        
        <div v-if="resultData.analysis" class="ai-analysis-card">
          <div class="ai-analysis-header">
            <span>✨ AI 综合鉴定报告</span>
          </div>
          <div class="ai-analysis-body">
            {{ resultData.analysis }}
          </div>
        </div>

        <div class="action-buttons-group">
          <el-button type="primary" size="large" round class="action-btn" @click="goToDetails(resultData.top_prediction)">
            <el-icon class="btn-icon"><Document /></el-icon>
            矿物详细百科
          </el-button>
          <el-button type="warning" size="large" round class="action-btn market-btn" @click="openMarketDashboard(resultData.top_prediction)">
            <el-icon class="btn-icon"><TrendCharts /></el-icon>
            市场行情走势
          </el-button>
        </div>

        <div class="disclaimer">⚠️ 本系统识别结果仅供参考，其准确性需送检专业检测机构确认。</div>
      </div>

      <template #footer>
        <div v-if="!resultData">
          <el-button @click="dialogVisible = false" class="cancel-btn">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="loading" :disabled="isSubmitDisabled" class="submit-btn">
            立即鉴定
          </el-button>
        </div>
        <div v-else>
          <el-button @click="dialogVisible = false" class="cancel-btn">关闭</el-button>
          <el-button type="primary" @click="resetForm" class="submit-btn">重新鉴定</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog 
      title="实时摄像头识别" 
      v-model="rtDialogVisible" 
      width="600px" 
      :close-on-click-modal="false" 
      @close="closeRtDialog"
      class="mac-el-dialog"
    >
      <div class="rt-container" v-loading="rtConnecting" element-loading-text="正在连接模型引擎..." element-loading-background="rgba(15,23,42,0.8)">
        
        <div class="video-wrapper">
          <video ref="videoRef" autoplay playsinline class="rt-video"></video>
          <canvas ref="canvasRef" style="display: none;"></canvas>
          
          <div v-if="rtResultData" class="rt-overlay-result">
            <div class="rt-top-label">{{ translateGemName(rtResultData.top_prediction) }}</div>
            <div class="rt-sub-label" v-if="rtResultData.predictions && rtResultData.predictions.length > 0">
              置信度: {{ (rtResultData.predictions[0].score * 100).toFixed(1) }}%
            </div>
          </div>
        </div>
        
        <div v-if="rtResultData && rtResultData.top_prediction" class="action-buttons-group">
          <el-button type="primary" size="large" round class="action-btn" @click="goToDetails(rtResultData.top_prediction)">
            <el-icon class="btn-icon"><Document /></el-icon>
            矿物详细百科
          </el-button>
          <el-button type="warning" size="large" round class="action-btn market-btn" @click="openMarketDashboard(rtResultData.top_prediction)">
            <el-icon class="btn-icon"><TrendCharts /></el-icon>
            市场行情走势
          </el-button>
        </div>

        <div class="disclaimer">📌 请将需要识别的物体对准摄像头中心，并保持稳定</div>
      </div>
    </el-dialog>

    <el-dialog
      title="商业化鉴赏大屏"
      v-model="marketDialogVisible"
      width="850px"
      append-to-body
      class="mac-el-dialog market-dialog"
    >
      <CommodityDashboard :gemData="marketGemData" />
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeUnmount } from "vue";
// 🔥 引入了 Document 页面图标
import { UploadFilled, Delete, TrendCharts, Cpu, Document } from "@element-plus/icons-vue"; 
import { ElMessage } from "element-plus";
import CommodityDashboard from "../components/shangpin/CommodityDashboard.vue";

const APP_HOST = import.meta.env.VITE_APP_HOST || '154.44.25.243';
const IS_LOCAL_TEST = ['localhost', '127.0.0.1'].includes(window.location.hostname);
const GEM_API_BASE = IS_LOCAL_TEST ? `http://${APP_HOST}:8080` : '/gem-api';
const GEM_WS_BASE = IS_LOCAL_TEST
  ? `ws://${APP_HOST}:8080`
  : `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/gem-ws`;
const DEEP_LEARNING_URL = import.meta.env.VITE_DEEP_LEARNING_URL || `http://${APP_HOST}:18080/`;

const emit = defineEmits(['query-mineral']);

// 默认选中我们最新的满血版模型
const selectedModel = ref("convnext"); 

// ================= 字典与翻译函数 =================
const engToChnMap: Record<string, string> = {
  "ruby": "红宝石", "sapphire": "蓝宝石", "amethyst": "水晶",
  "fledspar": "长石族宝石", "feldspar": "长石族宝石", "beryl": "绿柱石族宝石",
  "tourmaline": "碧玺", "scapolite": "方柱石", "peridot": "橄榄石",
  "iolite": "堇青石", "tanzanite": "坦桑石", "topaz": "托帕石",
  "fluorite": "萤石", "spinel": "尖晶石", "jadeite": "翡翠",
  "amber": "琥珀", "natural pearl": "珍珠", "coral": "珊瑚",
  "ivory": "象牙", "garnet": "石榴石", "sillimanite": "矽线石",
  "apatite": "磷灰石", "andalusite": "红柱石", "pyroxene": "辉石",
  "chrysoberyl": "金绿宝石", "diamond": "钻石", "zircon": "锆石",
  "natural glass": "天然玻璃", "malachite": "孔雀石", "larderite": "寿山石",
  "opal": "欧泊", "dushan yu": "独山玉", "quartzite": "石英质玉石",
  "turquoise": "绿松石", "rhodonite": "蔷薇辉石", "serpentine": "蛇纹石玉",
  "nephrite": "软玉", "albite jade": "钠长石玉", "qingtian stone": "青田石",
  "lapis lazuli": "青金石", "chicken-blood stone": "鸡血石", "jet": "煤精",
  "pertrified wood": "硅化木", "petrified wood": "硅化木", "shell": "贝壳",
  "tortoise shell": "龟甲"
};

const translateGemName = (enName: string | undefined) => {
  if (!enName) return '未知';
  const lowerName = enName.toLowerCase().trim();
  return engToChnMap[lowerName] || enName;
};

// ================= 🔥 新增：前往详情页逻辑 🔥 =================
const goToDetails = (predictionName: string) => {
  const cnName = translateGemName(predictionName);
  ElMessage.success(`正在为您跳转至【${cnName}】标本详情页...`);
  // 跳转到你指定的详情页URL
  // 提示：如果你希望把识别到的名字传过去，可以改成 'http://localhost:5173/specimen-library/宝玉石?name=' + cnName
  window.open(`${window.location.origin}/specimen-library/%E5%AE%9D%E7%8E%89%E7%9F%B3/${encodeURIComponent(cnName)}`, '_self');
};

// === 市场大盘逻辑 (保持不变) ===
const openDeepLearningPlatform = () => {
  window.open(DEEP_LEARNING_URL, '_self');
};

const marketDialogVisible = ref(false);
const marketGemData = ref<any>(null); 

const openMarketDashboard = (predictionName: string) => {
  if (!predictionName) return;
  const cnName = translateGemName(predictionName);
  marketGemData.value = {
    name: cnName,
    type: predictionName,
    color: '#F59E0B'
  };
  marketDialogVisible.value = true;
};
// ===========================================

// ================= 类型定义 =================
interface PredictionItem { label: string; probability: string; score: number; }
interface ResultData { top_prediction: string; predictions: PredictionItem[]; analysis?: string; }
interface FormState { text: string; file: File | null; }

// ================= 图文鉴赏 (静态) 逻辑 =================
const dialogVisible = ref(false);
const loading = ref(false);
const previewUrl = ref(""); 
const resultData = ref<ResultData | null>(null);

const form = ref<FormState>({ text: "", file: null });

const isSubmitDisabled = computed(() => {
  return !form.value.file; 
});

const openDialog = () => { dialogVisible.value = true; };
const handleClose = () => { if (!resultData.value) resetForm(); };

const handleFileChange = (uploadFile: any) => {
  const rawFile = uploadFile.raw;
  if (!rawFile) return;
  const isImg = rawFile.type.startsWith('image/');
  if (!isImg) { ElMessage.error('请上传图片文件！'); return; }
  form.value.file = rawFile;
  previewUrl.value = URL.createObjectURL(rawFile);
};

const removeImage = () => {
  form.value.file = null;
  previewUrl.value = "";
};

const resetForm = () => {
  form.value.text = "";
  removeImage();
  resultData.value = null;
  loading.value = false;
};

const handleSubmit = async () => {
  if (!form.value.file) {
    ElMessage.warning("请先上传需要鉴定的矿物图片");
    return;
  }
  
  loading.value = true;
  const fd = new FormData();
  
  fd.append("model", selectedModel.value);
  fd.append("file", form.value.file);
  if (form.value.text.trim()) fd.append("text", form.value.text.trim());

  try {
    const response = await fetch(`${GEM_API_BASE}/api/gem/predict`, {
      method: "POST",
      body: fd,
    });

    if (!response.ok) {
      throw new Error(`网络请求失败，状态码: ${response.status}`);
    }

    const data = await response.json();
    resultData.value = data;
    
  } catch (error: any) {
    ElMessage.error(error.message || "鉴定失败，请检查网络或后端服务");
  } finally {
    loading.value = false;
  }
};

const getProgressColor = (index: number) => {
  const colors = ['#3b82f6', '#8b5cf6', '#14b8a6', '#64748b', '#475569'];
  return colors[index] || '#475569';
};

// ================= 实时识别 (动态) 逻辑 =================
const rtDialogVisible = ref(false);
const rtConnecting = ref(false);
const videoRef = ref<HTMLVideoElement | null>(null);
const canvasRef = ref<HTMLCanvasElement | null>(null);
const rtResultData = ref<ResultData | null>(null);

let stream: MediaStream | null = null;
let ws: WebSocket | null = null;
let captureInterval: number | null = null;

const ensureBrowserCameraAvailable = () => {
  if (!navigator.mediaDevices?.getUserMedia) {
    throw new Error("当前浏览器不支持摄像头访问，请使用最新版 Chrome、Edge 或 Safari");
  }

  if (!window.isSecureContext && !IS_LOCAL_TEST) {
    throw new Error("线上访问浏览器摄像头必须使用 HTTPS 或 localhost，当前部署地址不是安全上下文");
  }
};

const openBrowserCamera = async () => {
  const candidateConstraints: MediaStreamConstraints[] = [
    {
      video: {
        facingMode: { ideal: "environment" },
        width: { ideal: 400 },
        height: { ideal: 400 },
      },
      audio: false,
    },
    {
      video: {
        facingMode: { ideal: "user" },
        width: { ideal: 400 },
        height: { ideal: 400 },
      },
      audio: false,
    },
    {
      video: true,
      audio: false,
    },
  ];

  let lastError: unknown = null;

  for (const constraints of candidateConstraints) {
    try {
      return await navigator.mediaDevices.getUserMedia(constraints);
    } catch (error) {
      lastError = error;
    }
  }

  throw lastError instanceof Error ? lastError : new Error("无法打开当前浏览器摄像头");
};

const openRtDialog = async () => {
  rtDialogVisible.value = true;
  rtConnecting.value = true;
  rtResultData.value = null;
  
  try {
    ensureBrowserCameraAvailable();
    stream = await openBrowserCamera();
    
    if (videoRef.value) {
      videoRef.value.srcObject = stream;
      await videoRef.value.play?.().catch(() => {});
    }

    ws = new WebSocket(`${GEM_WS_BASE}/ws/gem/predict`);
    
    ws.onopen = () => {
      rtConnecting.value = false;
      ElMessage.success(`已连接实时引擎 (${selectedModel.value})`);
      captureInterval = window.setInterval(captureAndSendFrame, 500);
    };

    ws.onmessage = (event) => {
      try {
        const res = JSON.parse(event.data);
        if (res.error) {
          console.error("后端处理错误:", res.error);
        } else {
          rtResultData.value = res; 
        }
      } catch (e) {}
    };

    ws.onerror = () => {
      ElMessage.error("WebSocket 连接发生错误");
      rtConnecting.value = false;
    };

    ws.onclose = () => {
      if (rtDialogVisible.value) {
        rtConnecting.value = false;
      }
    };

  } catch (err: any) {
    ElMessage.error("无法访问摄像头: " + err.message);
    rtConnecting.value = false;
  }
};

const captureAndSendFrame = () => {
  if (!videoRef.value || !canvasRef.value || !ws || ws.readyState !== WebSocket.OPEN) return;

  const video = videoRef.value;
  const canvas = canvasRef.value;
  const ctx = canvas.getContext('2d');
  
  if (!ctx || video.videoWidth === 0) return;

  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  const base64Data = canvas.toDataURL('image/jpeg', 0.8);
  
  ws.send(JSON.stringify({
    model: selectedModel.value, 
    image: base64Data
  }));
};

const closeRtDialog = () => {
  if (captureInterval) { clearInterval(captureInterval); captureInterval = null; }
  if (stream) { stream.getTracks().forEach(track => track.stop()); stream = null; }
  if (ws) { ws.close(); ws = null; }
  rtResultData.value = null;
};

onBeforeUnmount(() => { closeRtDialog(); });
</script>

<style scoped>
.appreciation-panel { height: 100%; display: flex; flex-direction: column; padding: 40px; overflow-y: auto; background: transparent; }

.welcome-section { text-align: center; margin-bottom: 24px; }
.welcome-icon { font-size: 48px; margin-bottom: 16px; }
.welcome-section h3 { font-size: 24px; color: var(--chat-text); margin: 0 0 12px 0; }
.welcome-section p { color: var(--chat-text-sub); font-size: 15px; max-width: 600px; margin: 0 auto; }

.model-selector-container { display: flex; flex-direction: column; align-items: center; margin-bottom: 40px; }
.model-selector-label { display: flex; align-items: center; font-size: 14px; color: var(--chat-text-sub); margin-bottom: 10px; font-weight: 500; }
:deep(.model-select .el-input__wrapper) { background-color: rgba(0, 0, 0, 0.15); box-shadow: 0 0 0 1px var(--chat-border) inset; border-radius: 8px; }
:deep(.model-select .el-input__inner) { color: var(--chat-text); font-weight: 600; text-align: center; }
:deep(.model-select.el-select:hover:not(.el-select--disabled) .el-input__wrapper) { box-shadow: 0 0 0 1px #3b82f6 inset; }

.features-container { display: flex; gap: 24px; justify-content: center; flex-wrap: wrap; max-width: 900px; margin: 0 auto; }

.feature-card { flex: 1; min-width: 300px; max-width: 400px; background: var(--panel-bg); border: 1px solid var(--chat-border); border-radius: 20px; padding: 32px; cursor: pointer; transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); display: flex; flex-direction: column; position: relative; overflow: hidden; }
.feature-card:hover { transform: translateY(-4px); box-shadow: 0 20px 40px rgba(0,0,0,0.15); border-color: rgba(255,255,255,0.2); background: rgba(255, 255, 255, 0.05); }
:global(.dark-theme) .feature-card:hover { background: rgba(255, 255, 255, 0.03); }

.card-icon-box { width: 64px; height: 64px; border-radius: 16px; display: flex; align-items: center; justify-content: center; margin-bottom: 24px; }
.blue-theme { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
.orange-theme { background: rgba(249, 115, 22, 0.15); color: #f97316; }
.green-theme { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
.dl-card:hover .card-action { color: #22c55e; }

.card-content h4 { font-size: 20px; color: var(--chat-text); margin: 0 0 12px 0; }
.card-content p { color: var(--chat-text-sub); font-size: 14px; line-height: 1.6; margin: 0 0 32px 0; }

.card-action { margin-top: auto; display: flex; align-items: center; justify-content: space-between; color: var(--chat-text); font-weight: 600; font-size: 15px; }
.feature-card:hover .card-action { color: #3b82f6; }
.rt-card:hover .card-action { color: #f97316; }

:deep(.mac-el-dialog) { background: var(--chat-surface); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border-radius: 16px; border: 1px solid var(--chat-border); box-shadow: 0 24px 60px rgba(0,0,0,0.4); }
:deep(.el-dialog__header) { border-bottom: 1px solid var(--chat-border); margin-right: 0; padding: 20px 24px; }
:deep(.el-dialog__title) { color: var(--chat-text); font-weight: 600; font-size: 16px; }
:deep(.el-dialog__body) { padding: 24px; color: var(--chat-text); }
:deep(.el-dialog__footer) { border-top: 1px solid var(--chat-border); padding: 16px 24px; }
:deep(.el-form-item__label) { color: var(--chat-text); font-weight: 500; }

:deep(.el-upload-dragger) { background: rgba(0,0,0,0.1); border: 1px dashed var(--chat-border); border-radius: 12px; transition: all 0.3s; }
:deep(.el-upload-dragger:hover) { border-color: #3b82f6; background: rgba(59, 130, 246, 0.05); }

.preview-container { width: 100%; height: 200px; border-radius: 12px; overflow: hidden; position: relative; background: #000; border: 1px solid var(--chat-border); }
.preview-img { width: 100%; height: 100%; object-fit: contain; }
.preview-actions { position: absolute; top: 10px; right: 10px; }

:deep(.custom-textarea .el-textarea__inner) { background: rgba(0,0,0,0.1); border: 1px solid var(--chat-border); color: var(--chat-text); border-radius: 8px; }
:deep(.custom-textarea .el-textarea__inner:focus) { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2); }

.cancel-btn { background: transparent !important; border: 1px solid var(--chat-border) !important; color: var(--chat-text) !important; border-radius: 8px; }
.submit-btn { background: #3b82f6 !important; border: none !important; border-radius: 8px; font-weight: 500; }

.top-prediction { text-align: center; margin-bottom: 24px; padding: 20px; background: rgba(59, 130, 246, 0.1); border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.2); }
.prediction-label { font-size: 13px; color: var(--chat-text-sub); margin-bottom: 8px; }
.prediction-value { font-size: 28px; font-weight: 700; color: #3b82f6; }

.result-item { margin-bottom: 16px; }
.result-info { display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 14px; color: var(--chat-text); }
.gem-score { color: #3b82f6; font-weight: 600; }

.ai-analysis-card { margin-top: 24px; background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.2); border-radius: 12px; padding: 16px; }
.ai-analysis-header { color: #a78bfa; font-weight: 600; margin-bottom: 12px; font-size: 15px; }
.ai-analysis-body { color: var(--chat-text); font-size: 14px; line-height: 1.6; white-space: pre-wrap; }

/* 🔥 新增的双按钮布局样式 🔥 */
.action-buttons-group {
  margin-top: 24px;
  display: flex;
  gap: 16px;
  justify-content: center;
  width: 100%;
}
.action-btn {
  flex: 1;
  font-weight: bold;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.btn-icon {
  margin-right: 6px;
  font-size: 18px;
}
.market-btn {
  box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4);
}

.disclaimer { margin-top: 24px; text-align: center; font-size: 12px; color: var(--chat-text-sub); }

.video-wrapper { position: relative; width: 100%; height: 400px; background: #000; border-radius: 12px; overflow: hidden; border: 1px solid var(--chat-border); }
.rt-video { width: 100%; height: 100%; object-fit: cover; transform: scaleX(-1); }

.rt-overlay-result { position: absolute; bottom: 24px; left: 50%; transform: translateX(-50%); background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(8px); padding: 12px 32px; border-radius: 30px; text-align: center; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
.rt-top-label { color: #f97316; font-size: 24px; font-weight: bold; }
.rt-sub-label { color: #cbd5e1; font-size: 13px; margin-top: 4px; }

:global(.market-dialog) { background: #0f172a !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7) !important; border-radius: 16px !important; }
:global(.market-dialog .el-dialog__header) { border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important; padding: 20px 24px !important; margin-right: 0 !important; }
:global(.market-dialog .el-dialog__title) { color: #f8fafc !important; font-weight: 600 !important; font-size: 1.1rem !important; }
:global(.market-dialog .el-dialog__headerbtn .el-dialog__close) { color: #94a3b8 !important; font-size: 20px; }
:global(.market-dialog .el-dialog__headerbtn:hover .el-dialog__close) { color: #f59e0b !important; }

:global(.market-dialog .el-dialog__body) { 
  padding: 0 !important; 
  height: 70vh !important; 
  min-height: 600px !important; 
  background-color: transparent !important; 
  display: flex !important; 
  flex-direction: column !important; 
  overflow: hidden !important; 
}
</style>
