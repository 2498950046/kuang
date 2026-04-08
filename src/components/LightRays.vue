<template>
  <canvas ref="canvasRef" :class="['light-rays-canvas', className]" />
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { Renderer, Camera, Transform, Program, Mesh, Geometry } from 'ogl';

type Origin =
  | 'top-left'
  | 'top-center'
  | 'top-right'
  | 'center-left'
  | 'center'
  | 'center-right'
  | 'bottom-left'
  | 'bottom-center'
  | 'bottom-right';

const props = withDefaults(
  defineProps<{
    raysOrigin?: Origin;
    raysColor?: string;
    raysSpeed?: number;
    lightSpread?: number;
    rayLength?: number;
    followMouse?: boolean;
    mouseInfluence?: number;
    noiseAmount?: number;
    distortion?: number;
    className?: string;
  }>(),
  {
    raysOrigin: 'top-center',
    raysColor: '#00ffff',
    raysSpeed: 1.5,
    lightSpread: 0.8,
    rayLength: 1.2,
    followMouse: true,
    mouseInfluence: 0.1,
    noiseAmount: 0.1,
    distortion: 0.05,
    className: '',
  },
);

const canvasRef = ref<HTMLCanvasElement | null>(null);
let renderer: Renderer | null = null;
let camera: Camera | null = null;
let scene: Transform | null = null;
let mesh: Mesh | null = null;
let frameId: number | null = null;

const mouse = { x: 0.5, y: 0.5 };

const originVec = computed(() => {
  const map: Record<Origin, [number, number]> = {
    'top-left': [0, 0],
    'top-center': [0.5, 0],
    'top-right': [1, 0],
    'center-left': [0, 0.5],
    center: [0.5, 0.5],
    'center-right': [1, 0.5],
    'bottom-left': [0, 1],
    'bottom-center': [0.5, 1],
    'bottom-right': [1, 1],
  };
  return map[props.raysOrigin] || [0.5, 0.5];
});

function hexToRgb(hex: string): [number, number, number] {
  const norm = hex.replace('#', '');
  const bigint = parseInt(norm, 16);
  return [((bigint >> 16) & 255) / 255, ((bigint >> 8) & 255) / 255, (bigint & 255) / 255];
}

function init() {
  if (!canvasRef.value) return;
  renderer = new Renderer({
    canvas: canvasRef.value,
    dpr: Math.min(window.devicePixelRatio || 1, 2),
    alpha: true,
    antialias: true,
    premultipliedAlpha: false,
  });
  const gl = renderer.gl;
  camera = new Camera(gl);
  camera.position.set(0, 0, 1);
  scene = new Transform();

  const geometry = new Geometry(gl, {
    position: {
      size: 2,
      data: new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]),
    },
    uv: {
      size: 2,
      data: new Float32Array([0, 0, 1, 0, 0, 1, 1, 1]),
    },
    index: { data: new Uint16Array([0, 1, 2, 2, 1, 3]) },
  });

  const program = new Program(gl, {
    vertex: /* glsl */ `
      attribute vec2 position;
      attribute vec2 uv;
      varying vec2 vUv;
      void main() {
        vUv = uv;
        gl_Position = vec4(position, 0.0, 1.0);
      }
    `,
    fragment: /* glsl */ `
      precision highp float;
      varying vec2 vUv;

      uniform float uTime;
      uniform vec2 uResolution;
      uniform vec2 uOrigin;
      uniform vec2 uMouse;
      uniform float uFollowMouse;
      uniform vec3 uColor;
      uniform float uSpeed;
      uniform float uSpread;
      uniform float uLength;
      uniform float uMouseInfluence;
      uniform float uNoise;
      uniform float uDistortion;

      // Simple hash noise
      float hash(vec2 p) {
        return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
      }

      float noise(vec2 p) {
        vec2 i = floor(p);
        vec2 f = fract(p);
        float a = hash(i);
        float b = hash(i + vec2(1.0, 0.0));
        float c = hash(i + vec2(0.0, 1.0));
        float d = hash(i + vec2(1.0, 1.0));
        vec2 u = f * f * (3.0 - 2.0 * f);
        return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
      }

      void main() {
        vec2 uv = vUv;

        // Base direction from origin
        vec2 dir = uv - uOrigin;

        // Optional mouse steering
        vec2 target = mix(uOrigin, uMouse, uMouseInfluence * uFollowMouse);
        dir = uv - target;

        float dist = length(dir);
        float angle = atan(dir.y, dir.x);

        // Animated radial rays
        float rayFreq = 20.0;
        float anim = uTime * 0.001 * uSpeed;
        float ray = sin(angle * rayFreq + anim + noise(vec2(angle, anim)) * 4.0);

        float spread = smoothstep(uSpread, 0.0, dist);
        float lengthMask = smoothstep(uLength, 0.0, dist);

        float n = noise(vec2(angle * 2.0, dist * 4.0 + anim)) * uNoise;
        float distortion = sin(dist * 8.0 + anim) * uDistortion;

        float intensity = clamp(ray * spread * lengthMask + n + distortion, 0.0, 1.0);
        float fadeEdges = smoothstep(0.0, 0.05, uv.x) *
                          smoothstep(0.0, 0.05, uv.y) *
                          smoothstep(0.0, 0.05, 1.0 - uv.x) *
                          smoothstep(0.0, 0.05, 1.0 - uv.y);

        float alpha = intensity * fadeEdges;
        gl_FragColor = vec4(uColor, alpha);
      }
    `,
    uniforms: {
      uTime: { value: 0 },
      uResolution: { value: [1, 1] },
      uOrigin: { value: originVec.value },
      uMouse: { value: [0.5, 0.5] },
      uFollowMouse: { value: props.followMouse ? 1 : 0 },
      uColor: { value: hexToRgb(props.raysColor) },
      uSpeed: { value: props.raysSpeed },
      uSpread: { value: props.lightSpread },
      uLength: { value: props.rayLength },
      uMouseInfluence: { value: props.mouseInfluence },
      uNoise: { value: props.noiseAmount },
      uDistortion: { value: props.distortion },
    },
    transparent: true,
    depthTest: false,
    depthWrite: false,
  });

  mesh = new Mesh(gl, { geometry, program });
  mesh.setParent(scene);

  resize();
  start();
}

function resize() {
  if (!renderer || !canvasRef.value || !mesh) return;
  const w = canvasRef.value.clientWidth;
  const h = canvasRef.value.clientHeight;
  renderer.setSize(w, h);
  mesh.program.uniforms.uResolution.value = [w, h];
}

function start() {
  const loop = (t: number) => {
    if (!renderer || !camera || !scene || !mesh) return;
    mesh.program.uniforms.uTime.value = t;
    renderer.render({ scene, camera });
    frameId = requestAnimationFrame(loop);
  };
  frameId = requestAnimationFrame(loop);
}

function cleanup() {
  if (frameId) cancelAnimationFrame(frameId);
  window.removeEventListener('resize', resize);
  renderer = null;
  camera = null;
  scene = null;
  mesh = null;
}

function handleMouse(event: MouseEvent) {
  if (!canvasRef.value) return;
  const rect = canvasRef.value.getBoundingClientRect();
  mouse.x = (event.clientX - rect.left) / rect.width;
  mouse.y = (event.clientY - rect.top) / rect.height;
  if (mesh) mesh.program.uniforms.uMouse.value = [mouse.x, mouse.y];
}

onMounted(() => {
  init();
  window.addEventListener('resize', resize);
  window.addEventListener('mousemove', handleMouse);
});

onUnmounted(() => {
  cleanup();
  window.removeEventListener('mousemove', handleMouse);
});

watch(
  () => [
    props.raysOrigin,
    props.raysColor,
    props.raysSpeed,
    props.lightSpread,
    props.rayLength,
    props.followMouse,
    props.mouseInfluence,
    props.noiseAmount,
    props.distortion,
  ],
  () => {
    if (!mesh) return;
    const uniforms = mesh.program.uniforms;
    uniforms.uOrigin.value = originVec.value;
    uniforms.uColor.value = hexToRgb(props.raysColor);
    uniforms.uSpeed.value = props.raysSpeed;
    uniforms.uSpread.value = props.lightSpread;
    uniforms.uLength.value = props.rayLength;
    uniforms.uFollowMouse.value = props.followMouse ? 1 : 0;
    uniforms.uMouseInfluence.value = props.mouseInfluence;
    uniforms.uNoise.value = props.noiseAmount;
    uniforms.uDistortion.value = props.distortion;
  },
  { deep: true },
);
</script>

<style scoped>
.light-rays-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: -1;
}
</style>

