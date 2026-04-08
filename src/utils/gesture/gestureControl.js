/**
 * 手势控制逻辑抽离：
 * - 不改变外部 ref（传入 App.vue 里的同一组响应式引用）
 * - 不改变回调签名（handleGesture(gs)）
 * - 不改变对 graphRef 的调用方式（adjustZoom / rotateGraph）
 */
export function createGestureControl({
  GestureType,
  graphRef,
  isGestureEnabled,
  gestureState,
  gestureStability,
  confirmedGesture,
  lastGestureState,
  specimenList,
  selectedSpecimenType,
  handleSpecimenClick,
}) {
  // 保持与原 App.vue 中一致
  const STABILITY_THRESHOLD = 12;
  const MOVEMENT_THRESHOLD = 0.012;
  const ROTATION_SENSITIVITY = 2.0;
  const ZOOM_SENSITIVITY = 2.5;

  function rotateGraph(deltaX, deltaY) {
    if (!graphRef.value || !graphRef.value.rotateGraph) return;
    graphRef.value.rotateGraph(deltaX, deltaY);
  }

  function toggleGestureControl() {
    isGestureEnabled.value = !isGestureEnabled.value;
    if (!isGestureEnabled.value) {
      // 关闭时重置状态（保持原行为）
      gestureState.value = {
        type: GestureType.NONE,
        x: 0,
        y: 0,
        distance: 0,
        fingerCount: 0,
      };
      gestureStability.value = { type: GestureType.NONE, count: 0, lastX: 0, lastY: 0 };
      lastGestureState.value = {
        type: GestureType.NONE,
        x: 0,
        y: 0,
        distance: 0,
        fingerCount: 0,
      };
    }
  }

  function handleGesture(gs) {
    if (!isGestureEnabled.value) return;

    const dx = Math.abs(gs.x - gestureStability.value.lastX);
    const dy = Math.abs(gs.y - gestureStability.value.lastY);
    const isMoving = dx > MOVEMENT_THRESHOLD || dy > MOVEMENT_THRESHOLD;

    // 把当前手势回填给 GestureGuide（保持原行为）
    gestureState.value = gs;

    const isSelectionShape = gs.type.startsWith('SELECT_');

    // 处理选择手势（切换图谱列表）
    if (isSelectionShape && !isMoving) {
      if (gs.type === gestureStability.value.type) {
        gestureStability.value.count++;
        if (gestureStability.value.count === STABILITY_THRESHOLD) {
          const num = gs.type.split('_')[1];
          const targetIndex = parseInt(num) - 1;
          if (
            targetIndex >= 0 &&
            targetIndex < specimenList.length &&
            specimenList[targetIndex] !== selectedSpecimenType.value
          ) {
            handleSpecimenClick(specimenList[targetIndex]);
            confirmedGesture.value = `切换至: ${specimenList[targetIndex]}`;
            setTimeout(() => {
              confirmedGesture.value = null;
            }, 2000);
          }
        }
      } else {
        gestureStability.value = { ...gestureStability.value, type: gs.type, count: 1 };
      }
    } else {
      gestureStability.value = { ...gestureStability.value, type: GestureType.NONE, count: 0 };
    }

    // 处理旋转（握拳）
    const isRotating = gs.type === GestureType.FIST;
    const wasRotating = lastGestureState.value.type === GestureType.FIST;

    if (isRotating && wasRotating && graphRef.value) {
      const deltaX = (gs.x - lastGestureState.value.x) * ROTATION_SENSITIVITY;
      const deltaY = (gs.y - lastGestureState.value.y) * ROTATION_SENSITIVITY;

      if (Math.abs(deltaX) > 0.0005 || Math.abs(deltaY) > 0.0005) {
        rotateGraph(deltaX, deltaY);
      }
    }

    // 处理缩放（捏合）
    if (gs.type === GestureType.ZOOM && lastGestureState.value.type === GestureType.ZOOM && graphRef.value) {
      const deltaDist = gs.distance - lastGestureState.value.distance;
      if (Math.abs(deltaDist) > 0.001) {
        const factor = 1 - deltaDist * ZOOM_SENSITIVITY;
        graphRef.value.adjustZoom(factor);
      }
    }

    // 更新“上一次手势状态”
    gestureStability.value.lastX = gs.x;
    gestureStability.value.lastY = gs.y;
    lastGestureState.value = gs;
  }

  return { toggleGestureControl, handleGesture };
}

