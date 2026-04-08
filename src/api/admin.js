const TOKEN_KEY = 'admin_token';
const USER_KEY = 'admin_user';
const MINERAL_KEY = 'admin_minerals';

const seedMinerals = [
  {
    id: crypto.randomUUID(),
    name: '红宝石',
    type: '宝石',
    location: '缅甸抹谷',
    era: '近代',
    code: 'R-001',
    description: '呈鲜艳红色的刚玉，常用于高级首饰。',
    updatedAt: new Date().toISOString(),
  },
  {
    id: crypto.randomUUID(),
    name: '蓝宝石',
    type: '宝石',
    location: '斯里兰卡',
    era: '近代',
    code: 'S-002',
    description: '蓝色刚玉，色泽深邃，经典宝石品种。',
    updatedAt: new Date().toISOString(),
  },
  {
    id: crypto.randomUUID(),
    name: '坦桑石',
    type: '宝石',
    location: '坦桑尼亚',
    era: '20世纪',
    code: 'T-003',
    description: '蓝紫色黝帘石，具有多色性与高通透。',
    updatedAt: new Date().toISOString(),
  },
];

const ensureMinerals = () => {
  const saved = localStorage.getItem(MINERAL_KEY);
  if (!saved) {
    localStorage.setItem(MINERAL_KEY, JSON.stringify(seedMinerals));
    return seedMinerals;
  }
  try {
    return JSON.parse(saved);
  } catch (e) {
    console.warn('Mineral data damaged, resetting.', e);
    localStorage.setItem(MINERAL_KEY, JSON.stringify(seedMinerals));
    return seedMinerals;
  }
};

const saveMinerals = (list) => {
  localStorage.setItem(MINERAL_KEY, JSON.stringify(list));
};

export const getToken = () => localStorage.getItem(TOKEN_KEY);

export const logout = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

export async function login({ email, password }) {
  if (!email || !password) {
    throw new Error('请输入账号和密码');
  }
  const token = 'demo-admin-token';
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify({ email }));
  return { token };
}

export async function register({ email, password, nickname }) {
  if (!email || !password || !nickname) {
    throw new Error('请填写完整信息');
  }
  const token = 'demo-admin-token';
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify({ email, nickname }));
  return { token };
}

export async function getCurrentUser() {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch (e) {
    return null;
  }
}

export async function listMinerals({ page = 1, pageSize = 8, keyword = '', type = '' } = {}) {
  const all = ensureMinerals();
  const filtered = all.filter((item) => {
    const matchesKeyword =
      !keyword ||
      item.name.includes(keyword) ||
      item.location.includes(keyword) ||
      item.description.includes(keyword);
    const matchesType = !type || item.type === type;
    return matchesKeyword && matchesType;
  });
  const total = filtered.length;
  const start = (page - 1) * pageSize;
  const end = start + pageSize;
  return {
    items: filtered.slice(start, end),
    total,
  };
}

export async function createMineral(payload) {
  if (!payload.name) {
    throw new Error('请填写矿物名称');
  }
  const all = ensureMinerals();
  const now = new Date().toISOString();
  const record = {
    id: crypto.randomUUID(),
    name: payload.name,
    type: payload.type || '宝石',
    location: payload.location || '未知产地',
    era: payload.era || '未知年代',
    code: payload.code || `M-${Math.floor(Math.random() * 900 + 100)}`,
    description: payload.description || '',
    updatedAt: now,
  };
  all.unshift(record);
  saveMinerals(all);
  return record;
}

export async function updateMineral(id, payload) {
  const all = ensureMinerals();
  const idx = all.findIndex((m) => m.id === id);
  if (idx === -1) throw new Error('找不到该矿物');
  all[idx] = {
    ...all[idx],
    ...payload,
    updatedAt: new Date().toISOString(),
  };
  saveMinerals(all);
  return all[idx];
}

export async function deleteMineral(id) {
  const all = ensureMinerals();
  const next = all.filter((m) => m.id !== id);
  saveMinerals(next);
  return true;
}

