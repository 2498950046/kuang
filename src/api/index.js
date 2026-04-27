const APP_HOST = '154.44.25.243';
const IS_LOCAL_TEST = ['localhost', '127.0.0.1'].includes(window.location.hostname);
const API_BASE = IS_LOCAL_TEST ? `http://${APP_HOST}:5000` : '/backend';
const QA_API_BASE = IS_LOCAL_TEST ? `http://${APP_HOST}:8081` : '/qa-api';

const withBase = (path) => `${API_BASE}${path}`;

async function handleJSONResponse(response) {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`HTTP ${response.status}: ${text || response.statusText}`);
  }
  return response.json();
}

export async function graphQuery(cypher) {
  const resp = await fetch(withBase('/graph'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ cypher }),
  });
  return handleJSONResponse(resp);
}

export async function nl2cypher(question) {
  const resp = await fetch(withBase('/ai/nl2cypher'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  return handleJSONResponse(resp);
}

// 获取图谱统计数据
export async function fetchStats() {
  const resp = await fetch(withBase('/stats'));
  return handleJSONResponse(resp);
}

export async function fetchSchema() {
  const resp = await fetch(withBase('/ai/schema'));
  return handleJSONResponse(resp);
}

/**
 * 以 fetch + SSE 文本解析的方式流式读取 /ai/rag
 * onEvent 接收 { event, data }，其中 data 已 JSON.parse
 */
// export async function ragStream(question, { onEvent, signal } = {}) {
//   const controller = new AbortController();
//   if (signal) signal.addEventListener('abort', () => controller.abort(), { once: true });

//   try {
//     const resp = await fetch(withBase('/ai/rag'), {
//       method: 'POST',
//       headers: { 
//         'Content-Type': 'application/json',
//         'Accept': 'text/event-stream'
//       },
//       body: JSON.stringify({ question }),
//       signal: controller.signal,
//     });

//     if (!resp.ok) {
//       const text = await resp.text().catch(() => '');
//       throw new Error(text || `HTTP ${resp.status}: ${resp.statusText}`);
//     }

//     if (!resp.body) {
//       throw new Error('响应体为空');
//     }

//     const reader = resp.body.getReader();
//     const decoder = new TextDecoder('utf-8');
//     let buffer = '';

//     const flush = (chunk) => {
//       buffer += chunk;
//       // SSE 格式：每个事件以 \n\n 分隔
//       const parts = buffer.split('\n\n');
//       // 保留最后一个不完整的部分
//       buffer = parts.pop() || '';
//       // 处理完整的事件块
//       parts.forEach(parseEventBlock);
//     };

//     const parseEventBlock = (block) => {
//       if (!block.trim()) return;
//       const lines = block.trim().split('\n');
//       let event = 'message';
//       let dataLines = [];
      
//       lines.forEach((line) => {
//         if (line.startsWith('event:')) {
//           event = line.replace(/^event:\s*/, '').trim();
//         } else if (line.startsWith('data:')) {
//           // 处理多行 data
//           dataLines.push(line.replace(/^data:\s*/, ''));
//         }
//       });
      
//       if (dataLines.length > 0) {
//         // 合并多行 data
//         const dataStr = dataLines.join('\n');
//         try {
//           const parsed = JSON.parse(dataStr);
//           onEvent?.({ event, data: parsed });
//         } catch (e) {
//           // 如果解析失败，尝试作为字符串传递
//           console.warn('SSE 数据解析失败:', e, dataStr);
//           onEvent?.({ event, data: dataStr });
//         }
//       }
//     };

//     while (true) {
//       const { value, done } = await reader.read();
//       if (done) break;
      
//       try {
//         const chunk = decoder.decode(value, { stream: true });
//         flush(chunk);
//       } catch (e) {
//         console.error('解码 SSE 数据失败:', e);
//         throw e;
//       }
//     }
    
//     // 处理剩余的缓冲区数据
//     if (buffer.trim()) {
//       parseEventBlock(buffer);
//     }
//   } catch (e) {
//     // 如果是 AbortError，不抛出错误
//     if (e.name === 'AbortError') {
//       return;
//     }
//     console.error('RAG Stream 请求失败:', e);
//     throw e;
//   }

//   return () => controller.abort();
// }

export const ragStream = async (payload, callbacks) => {
  try {
    // 换成你的 Spring Boot 地址
    const response = await fetch(`${QA_API_BASE}/ai/chat_two_step`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      // payload 就是我们刚才传的 { memoryId: xxx, message: 'xxx' }
      body: JSON.stringify(payload) 
    });

    if (!response.ok) {
      throw new Error(`HTTP Error: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const textChunk = decoder.decode(value, { stream: true });
      
      // 解析 Spring Boot 发来的 SSE 格式 (data: xxxx)
      const lines = textChunk.split('\n');
      for (const line of lines) {
        if (line.startsWith('data:')) {
          let content = line.substring(5).trim();
          if (content) {
            // 如果 Spring Boot 传的是普通文本，直接用；如果是 JSON 需要 JSON.parse(content)
            callbacks.onEvent(content);
          }
        }
      }
    }
    
    // 读取完毕
    if (callbacks.onComplete) {
      callbacks.onComplete();
    }
    
  } catch (error) {
    if (callbacks.onError) {
      callbacks.onError(error.message);
    }
  }
};



export async function fetchMineralSamples(name) {
  const resp = await fetch(withBase(`/api/mineral_samples?name=${encodeURIComponent(name)}`));
  return handleJSONResponse(resp);
}

// 矿物基本信息（节点详情面板用，对接 POST /mineral/info）
export async function getMineralInfo({ mineral_id, mineral_name }) {
  const isDev = import.meta.env.DEV;
  const apiPath = isDev ? '/mineral/info' : withBase('/mineral/info');
  const resp = await fetch(apiPath, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mineral_id: mineral_id || undefined, mineral_name: mineral_name || undefined }),
  });
  const result = await resp.json();
  if (result.code !== 200) {
    throw new Error(result.message || '获取矿物信息失败');
  }
  return result.data;
}

// 根据表2的 id（图片文件夹名 _ 前的数字）获取特有描述（table1&2.db 表2）
export async function getSpecimenDescriptionByTable2Id(id) {
  try {
    const isDev = import.meta.env.DEV;
    const url = isDev ? `/api/mineral/table2_description?id=${encodeURIComponent(id)}` : withBase(`/api/mineral/table2_description?id=${encodeURIComponent(id)}`);
    const resp = await fetch(url);
    if (!resp.ok) return '';
    const result = await resp.json();
    if (result.code === 200 && result.data != null) {
      const d = result.data;
      return d.description ?? d['特有描述'] ?? d['每个样品特有的描述'] ?? '';
    }
    return '';
  } catch {
    return '';
  }
}

// 批量获取宝玉石基本信息（用于标本库卡片：英文名、图片等）
export async function fetchGemsBatch(names, fields = ['id', 'name', 'type', 'image_url', 'color', 'info']) {
  const resp = await fetch(withBase('/gems/gems_batch'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ names, fields }),
  });
  return handleJSONResponse(resp);
}

// 获取单个宝石的详细信息（用于智能鉴赏）
export async function fetchGemDetail(gemName) {
  const resp = await fetch(withBase('/gems/gems_detail'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ gem_name: gemName }),
  });
  return handleJSONResponse(resp);
}

// 智能鉴赏：识别矿物图片（适配后端 /ai/mineral_dec 接口）
export async function identifyMineral(base64Image) {
  try {
    // 处理 base64 字符串：可能包含 data:image/xxx;base64, 前缀
    let base64Data = base64Image;
    let mimeType = 'image/jpeg'; // 默认类型
    
    // 如果包含 data URL 前缀，提取 MIME 类型和 base64 数据
    if (base64Image.includes(',')) {
      const parts = base64Image.split(',');
      const header = parts[0];
      base64Data = parts[1];
      
      // 提取 MIME 类型
      const mimeMatch = header.match(/data:([^;]+)/);
      if (mimeMatch) {
        mimeType = mimeMatch[1];
      }
    }
    
    // 将 base64 转换为 Blob
    const byteCharacters = atob(base64Data);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: mimeType });
    
    // 根据 MIME 类型确定文件扩展名
    const extension = mimeType.includes('png') ? 'png' : 
                     mimeType.includes('webp') ? 'webp' : 
                     mimeType.includes('gif') ? 'gif' : 'jpg';
    
    // 创建 File 对象
    const file = new File([blob], `mineral_image.${extension}`, { type: mimeType });
    
    // 创建 FormData
    const formData = new FormData();
    formData.append('file', file);
    
    // 在开发环境下，强制使用相对路径走 Vite 代理，避免 CORS 问题
    const isDev = import.meta.env.DEV;
    const apiPath = isDev ? '/ai/mineral_dec' : withBase('/ai/mineral_dec');
    
    const resp = await fetch(apiPath, {
      method: 'POST',
      body: formData, // 不要设置 Content-Type，让浏览器自动设置 multipart/form-data
    });
    
    if (!resp.ok) {
      const errorText = await resp.text().catch(() => resp.statusText);
      throw new Error(`识别失败: ${resp.status} ${errorText}`);
    }
    
    const result = await resp.json();
    
    // 适配后端返回格式：后端返回 {code, message, data: {result_dicts: [{name, confidence}]}}
    // 转换为前端需要的格式：{success: true, results: [{name, confidence, rank, description}]}
    if (result.code === 200 && result.data && result.data.result_dicts) {
      return {
        success: true,
        results: result.data.result_dicts.map((item, index) => ({
          name: item.name,
          confidence: item.confidence,
          rank: index + 1,
          description: `${item.name}，置信度 ${Math.round(item.confidence * 100)}%` // 临时描述，后续可以从数据库获取详细信息
        }))
      };
    } else {
      throw new Error(result.message || '识别失败');
    }
  } catch (error) {
    // 如果是网络错误或 CORS 错误，提供更友好的提示
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('无法连接到服务器，请检查后端服务是否启动');
    }
    throw error;
  }
}

// 将录音 Blob（webm 等）转为后端要求的 PCM 16kHz 单声道 16bit
async function audioBlobToPcm16k(blob) {
  const arrayBuffer = await blob.arrayBuffer();
  const audioContext = new (window.AudioContext || window.webkitAudioContext)();
  const decoded = await audioContext.decodeAudioData(arrayBuffer);
  const duration = decoded.duration;
  const sampleRate = 16000;
  const offline = new OfflineAudioContext(1, Math.ceil(duration * sampleRate), sampleRate);
  const source = offline.createBufferSource();
  source.buffer = decoded;
  source.connect(offline.destination);
  source.start(0);
  const resampled = await offline.startRendering();
  const float32 = resampled.getChannelData(0);
  const int16 = new Int16Array(float32.length);
  for (let i = 0; i < float32.length; i++) {
    const s = Math.max(-1, Math.min(1, float32[i]));
    int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return new Blob([int16.buffer], { type: 'application/octet-stream' });
}

// 语音识别：将音频转换为文字（前端自动转为 PCM 16kHz 以适配后端百度接口）
export async function speechToText(audioBlob, language = 'zh') {
  try {
    const pcmBlob = await audioBlobToPcm16k(audioBlob);
    const formData = new FormData();
    formData.append('audio', pcmBlob, 'audio.pcm');
    formData.append('language', language);

    const isDev = import.meta.env.DEV;
    const apiPath = isDev ? '/api/speech-to-text' : withBase('/api/speech-to-text');

    const resp = await fetch(apiPath, {
      method: 'POST',
      body: formData,
    });

    if (!resp.ok) {
      const errorText = await resp.text().catch(() => resp.statusText);
      throw new Error(`语音识别失败: ${resp.status} ${errorText}`);
    }

    const result = await resp.json();

    if (result.success) {
      return {
        success: true,
        text: result.text ?? '',
        language: result.language,
        confidence: result.confidence,
      };
    } else {
      throw new Error(result.error || '语音识别失败');
    }
  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('无法连接到语音识别服务，请检查后端服务是否启动');
    }
    throw error;
  }
}
