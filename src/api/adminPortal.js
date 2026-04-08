// 后台管理接口基址：优先使用 VITE_ADMIN_API_URL，没有则回退到 VITE_API_URL
const API_BASE = (import.meta.env.VITE_ADMIN_API_URL || import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

const TOKEN_KEY = 'admin_token';
const USERNAME_KEY = 'admin_username';

const withBase = (path) => `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`;

async function request(path, { method = 'GET', body, headers = {} } = {}) {
  const token = localStorage.getItem(TOKEN_KEY);
  const finalHeaders = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...headers,
  };

  const resp = await fetch(withBase(path), {
    method,
    headers: finalHeaders,
    body,
  });

  const data = await resp.json().catch(() => ({
    success: false,
    message: '响应解析失败',
  }));
  return data;
}

export const authApi = {
  async login({ username, password }) {
    if (!username || !password) {
      return { success: false, message: '请输入账号和密钥' };
    }
    const res = await request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    
    // 适配多种后端返回格式
    const token = res?.data?.token || res?.token || res?.access_token;
    const user = res?.data?.username || res?.username || username;
    
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
      localStorage.setItem(USERNAME_KEY, user);
      // 确保返回格式统一
      return {
        success: true,
        message: res?.message || '登录成功',
        data: { token, username: user },
      };
    }
    
    // 如果没有 token，返回原始响应或错误
    return res || { success: false, message: '登录失败' };
  },
  logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USERNAME_KEY);
  },
  getToken() {
    return localStorage.getItem(TOKEN_KEY);
  },
  getUsername() {
    return localStorage.getItem(USERNAME_KEY) || 'Admin';
  },
};

export const mineralApi = {
  async getAll() {
    return request('/manage/get_all_minerals', { method: 'GET' });
  },
  async add(payload) {
    return request('/manage/add_mineral', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  async update(payload) {
    return request('/manage/update_mineral', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  async remove(name) {
    return request('/manage/delete_mineral', {
      method: 'POST',
      body: JSON.stringify({ 中文名称: name }),
    });
  },
};

export const adminState = {
  TOKEN_KEY,
  USERNAME_KEY,
};

