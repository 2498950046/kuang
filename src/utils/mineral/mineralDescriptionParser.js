/**
 * 将矿物描述文本按「字段名：内容」解析为键值对数组。
 * 保持与原 App.vue 内算法一致，以降低迁移风险。
 */
export function parseMineralDescriptionKVs(descriptionText) {
  const mineralDescriptionValue = descriptionText || '';
  const raw = mineralDescriptionValue.replace(/\r?\n+/g, '\n').trim();
  if (!raw) return [];

  const text = raw;
  const matches = [];

  const COLON_CHARS = ['：', ':'];
  const STOP_CHARS = new Set(['。', '！', '!', '？', '?', '；', ';', '\n']);

  // 1) 遍历所有冒号，向前回溯到最近的标点或行首作为字段名起点
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (!COLON_CHARS.includes(ch)) continue;

    // 回溯到最近的“句内分隔符”之后
    let j = i - 1;
    while (j >= 0 && !STOP_CHARS.has(text[j])) {
      j--;
    }
    const labelStart = j + 1;
    let label = text.slice(labelStart, i).trim();
    if (!label) continue;

    // 去掉空白和括号引号，仅用于长度判断
    const labelPlain = label.replace(/[\s"'“”‘’()（）]/g, '');

    // 规则：
    // 1）字段名至少 2 个有效字符，避免“性”“率”等被当成 label；
    // 2）字段名不超过 25 个字符，超过说明是很长的一句话，不拆分。
    if (labelPlain.length < 2 || labelPlain.length > 25) continue;

    // 避免同一位置重复加入
    if (matches.some((m) => m.start === labelStart)) continue;

    matches.push({
      label,
      start: labelStart,
      valueStart: i + 1, // 冒号之后开始
    });
  }

  // 2) 处理形如 [化学组成]蓝闪石... 的写法：[] 中的是 label，后面整段是 value
  for (let i = 0; i < text.length; i++) {
    if (text[i] !== '[' && text[i] !== '【') continue;

    const closeIndex = text.indexOf(text[i] === '[' ? ']' : '】', i + 1);
    if (closeIndex === -1) continue;

    const labelStart = i;
    let label = text.slice(i + 1, closeIndex).trim();
    if (!label) continue;

    // 检查：如果 [] 里面全是字母或数字（可能是化学式），跳过不分割
    const labelContent = label.replace(/\s/g, ''); // 去掉空格后检查
    if (/^[A-Za-z0-9]+$/.test(labelContent)) {
      // 如果只包含字母和数字，认为是化学式，不进行分割
      continue;
    }

    const labelPlain = label.replace(/[\s"'""''()（）\[\]【】]/g, '');
    if (labelPlain.length < 2 || labelPlain.length > 25) continue;

    // 避免与前面的冒号逻辑产生重复
    if (matches.some((m) => m.start === labelStart)) continue;

    matches.push({
      label,
      start: labelStart,
      valueStart: closeIndex + 1,
    });
  }

  // 按出现顺序排序
  matches.sort((a, b) => a.start - b.start);

  const kvs = [];

  // 处理首段无字段名的引言文字
  if (matches.length && matches[0].start > 0) {
    const intro = text.slice(0, matches[0].start).trim();
    if (intro) {
      kvs.push({ label: '', value: intro });
    }
  } else if (!matches.length && text) {
    // 完全没有冒号，整段作为一行
    kvs.push({ label: '', value: text.trim() });
    return kvs;
  }

  // 处理每个“字段名：值”块，值可以是多句，直到下一个字段名开始
  matches.forEach((item, idx) => {
    const end = idx + 1 < matches.length ? matches[idx + 1].start : text.length;
    const value = text.slice(item.valueStart, end).trim();
    kvs.push({
      label: item.label,
      value,
    });
  });

  return kvs.filter((row) => row.value);
}

