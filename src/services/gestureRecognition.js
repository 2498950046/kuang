// 手势类型枚举
export const GestureType = {
  NONE: 'NONE',
  FIST: 'FIST',
  ZOOM: 'ZOOM',
  SELECT_1: 'SELECT_1',
  SELECT_2: 'SELECT_2',
  SELECT_3: 'SELECT_3',
  SELECT_4: 'SELECT_4',
  SELECT_5: 'SELECT_5',
  SELECT_6: 'SELECT_6'
};

/**
 * 检测手势类型
 * @param {Array} landmarks - MediaPipe手部关键点数组
 * @returns {Object} 手势状态 { type, x, y, distance, fingerCount }
 */
export const detectGesture = (landmarks) => {
  if (!landmarks || landmarks.length === 0) {
    return { type: GestureType.NONE, x: 0, y: 0, distance: 0, fingerCount: 0 };
  }

  // 关键点索引
  const thumbTip = landmarks[4];
  const thumbIp = landmarks[3];
  const thumbMcp = landmarks[2];
  
  const indexTip = landmarks[8];
  const indexPip = landmarks[6];
  const indexMcp = landmarks[5];
  
  const middleTip = landmarks[12];
  const middlePip = landmarks[10];
  const middleMcp = landmarks[9];
  
  const ringTip = landmarks[16];
  const ringPip = landmarks[14];
  const ringMcp = landmarks[13];
  
  const pinkyTip = landmarks[20];
  const pinkyPip = landmarks[18];
  const pinkyMcp = landmarks[17];

  // 判断手指是否伸直
  const isIndexExtended = indexTip.y < indexPip.y - 0.02;
  const isMiddleExtended = middleTip.y < middlePip.y - 0.02;
  const isRingExtended = ringTip.y < ringPip.y - 0.02;
  const isPinkyExtended = pinkyTip.y < pinkyPip.y - 0.02;
  
  // 判断拇指是否伸直（通过拇指到手掌中心的距离）
  const thumbToMiddleMcp = Math.sqrt(
    Math.pow(thumbTip.x - middleMcp.x, 2) + Math.pow(thumbTip.y - middleMcp.y, 2)
  );
  const isThumbExtended = thumbToMiddleMcp > 0.13;
  const isThumbTucked = !isThumbExtended;

  // 计算捏合距离（用于缩放）
  const dx = thumbTip.x - indexTip.x;
  const dy = thumbTip.y - indexTip.y;
  const pinchDist = Math.sqrt(dx * dx + dy * dy);

  // 1. 握拳（旋转）
  if (!isIndexExtended && !isMiddleExtended && !isRingExtended && !isPinkyExtended) {
    return { type: GestureType.FIST, x: middleMcp.x, y: middleMcp.y, distance: 0, fingerCount: 0 };
  }

  // 2. 缩放和选择1的区分
  if (isIndexExtended && !isMiddleExtended && !isRingExtended && !isPinkyExtended) {
    // 如果拇指靠近食指或拇指伸直，则是缩放
    if (pinchDist < 0.12 || isThumbExtended) {
      return { type: GestureType.ZOOM, x: indexTip.x, y: indexTip.y, distance: pinchDist, fingerCount: 2 };
    } else {
      return { type: GestureType.SELECT_1, x: indexTip.x, y: indexTip.y, distance: pinchDist, fingerCount: 1 };
    }
  }

  // 3. 选择6（拇指和小指伸出）
  if (isThumbExtended && isPinkyExtended && !isIndexExtended && !isMiddleExtended && !isRingExtended) {
    return { type: GestureType.SELECT_6, x: indexTip.x, y: indexTip.y, distance: pinchDist, fingerCount: 2 };
  }

  // 4. 多指选择（2-5）
  
  // 手势2（食指+中指）
  if (isIndexExtended && isMiddleExtended && !isRingExtended && !isPinkyExtended) {
    return { type: GestureType.SELECT_2, x: indexTip.x, y: indexTip.y, distance: pinchDist, fingerCount: 2 };
  }
  
  // 手势3（食指+中指+无名指）
  if (isIndexExtended && isMiddleExtended && isRingExtended && !isPinkyExtended) {
    return { type: GestureType.SELECT_3, x: indexTip.x, y: indexTip.y, distance: pinchDist, fingerCount: 3 };
  }
  
  // 手势4和5（四个主要手指都伸出）
  if (isIndexExtended && isMiddleExtended && isRingExtended && isPinkyExtended) {
    // 通过拇指状态区分4和5
    if (isThumbTucked) {
      return { type: GestureType.SELECT_4, x: indexTip.x, y: indexTip.y, distance: pinchDist, fingerCount: 4 };
    } else {
      return { type: GestureType.SELECT_5, x: indexTip.x, y: indexTip.y, distance: pinchDist, fingerCount: 5 };
    }
  }

  return { type: GestureType.NONE, x: 0, y: 0, distance: 0, fingerCount: 0 };
};
