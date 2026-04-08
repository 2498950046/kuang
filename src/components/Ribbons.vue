<template>
  <canvas ref="canvasRef" class="ribbons-canvas"></canvas>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch, computed } from 'vue';
import { Renderer, Camera, Transform, Program, Mesh, Geometry } from 'ogl';

type Vec4 = [number, number, number, number];

const MAX_COLORS = 8;

const props = withDefaults(
  defineProps<{
    colors?: string[];
    baseSpring?: number;
    baseFriction?: number;
    baseThickness?: number;
    offsetFactor?: number;
    maxAge?: number;
    pointCount?: number;
    speedMultiplier?: number;
    enableFade?: boolean;
    enableShaderEffect?: boolean;
    effectAmplitude?: number;
    backgroundColor?: Vec4;
  }>(),
  {
    colors: () => ['#7B542F', '#B6771D', '#FF9D00', '#FFCF71'],
    baseSpring: 0.03,
    baseFriction: 0.9,
    baseThickness: 30,
    offsetFactor: 0.05,
    maxAge: 500,
    pointCount: 50,
    speedMultiplier: 0.6,
    enableFade: true,
    enableShaderEffect: true,
    effectAmplitude: 2,
    backgroundColor: () => [0, 0, 0, 0],
  },
);

const canvasRef = ref<HTMLCanvasElement | null>(null);

let renderer: Renderer | null = null;
let camera: Camera | null = null;
let scene: Transform | null = null;
let mesh: Mesh | null = null;
let frameId: number | null = null;

const colorBuffer = new Float32Array(MAX_COLORS * 3);

const normalizedColors = computed(() => {
  const palette = props.colors?.length ? props.colors : ['#7B542F', '#B6771D', '#FF9D00', '#FFCF71'];
  return palette.slice(0, MAX_COLORS).map((hex) => {
    const normalized = hex.replace('#', '');
    const bigint = parseInt(normalized, 16);
    const r = ((bigint >> 16) & 255) / 255;
    const g = ((bigint >> 8) & 255) / 255;
    const b = (bigint & 255) / 255;
    return [r, g, b] as [number, number, number];
  });
});

function updateColorUniform() {
  colorBuffer.fill(0);
  normalizedColors.value.forEach((c, idx) => {
    colorBuffer[idx * 3] = c[0];
    colorBuffer[idx * 3 + 1] = c[1];
    colorBuffer[idx * 3 + 2] = c[2];
  });
  if (mesh) {
    mesh.program.uniforms.uColors.value = colorBuffer;
    mesh.program.uniforms.uColorCount.value = normalizedColors.value.length;
  }
}

function updateDynamicUniforms() {
  if (!mesh) return;
  const uniforms = mesh.program.uniforms;
  uniforms.uBaseThickness.value = props.baseThickness;
  uniforms.uOffsetFactor.value = props.offsetFactor * props.effectAmplitude;
  uniforms.uSpeed.value = props.speedMultiplier;
  uniforms.uSpring.value = props.baseSpring;
  uniforms.uFriction.value = props.baseFriction;
  uniforms.uMaxAge.value = props.maxAge;
  uniforms.uPointCount.value = props.pointCount;
  uniforms.uEnableFade.value = props.enableFade ? 1 : 0;
  uniforms.uEnableShader.value = props.enableShaderEffect ? 1 : 0;
  uniforms.uBgColor.value = props.backgroundColor ?? [0, 0, 0, 0];
  updateColorUniform();
}

function initRenderer() {
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
      data: new Float32Array([
        -1, -1,
        1, -1,
        -1, 1,
        1, 1,
      ]),
    },
    uv: {
      size: 2,
      data: new Float32Array([
        0, 0,
        1, 0,
        0, 1,
        1, 1,
      ]),
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
      uniform float uBaseThickness;
      uniform float uOffsetFactor;
      uniform float uSpeed;
      uniform float uSpring;
      uniform float uFriction;
      uniform float uMaxAge;
      uniform float uPointCount;
      uniform int uEnableFade;
      uniform int uEnableShader;
      uniform vec4 uBgColor;
      uniform int uColorCount;
      uniform vec3 uColors[${MAX_COLORS}];

      float hash(float n) { return fract(sin(n) * 43758.5453123); }

      void main() {
        vec2 uv = vUv;
        vec3 baseColor = uBgColor.rgb;
        float alpha = uBgColor.a;

        if (uEnableShader == 0) {
          gl_FragColor = vec4(baseColor, alpha);
          return;
        }

        vec3 color = baseColor;
        float thicknessPx = uBaseThickness / uResolution.y;
        float ageFactor = clamp(uTime / max(uMaxAge, 1.0), 0.0, 1.0);

        for (int i = 0; i < ${MAX_COLORS}; i++) {
          if (i >= uColorCount) { continue; }
          float fi = float(i);

          // A tiny noisy offset so ribbons don't overlap perfectly.
          float noise = hash(fi * 13.1 + uTime * 0.001) * 0.5;

          float freq = 1.2 + uSpring * 40.0 + fi * 0.35;
          float speed = uSpeed * (0.5 + fi * 0.08);
          float phase = fi * 1.37 + noise * uFriction;

          float wave = sin(uv.x * freq + uTime * speed + phase);
          float center = 0.5 + wave * uOffsetFactor;

          // Vary thickness a little across ribbons and time
          float ribbonThickness = thicknessPx * (1.0 - fi * 0.08) * (1.0 + noise * 0.3);
          float dist = abs(uv.y - center);
          float band = smoothstep(ribbonThickness, ribbonThickness * 0.6, ribbonThickness - dist);

          // Age factor softly ramps in the ribbons to avoid harsh starts.
          float fadeIn = smoothstep(0.0, 0.25, ageFactor);
          float fadeOut = uEnableFade == 1 ? smoothstep(1.0, 0.7, ageFactor) : 1.0;
          float visibility = band * fadeIn * fadeOut;

          color = mix(color, uColors[i], visibility);
          alpha = clamp(alpha + visibility, 0.0, 1.0);
        }

        // Optional vignette fade
        if (uEnableFade == 1) {
          float edge = smoothstep(0.02, 0.2, uv.x) *
                       smoothstep(0.02, 0.2, uv.y) *
                       smoothstep(0.02, 0.2, 1.0 - uv.x) *
                       smoothstep(0.02, 0.2, 1.0 - uv.y);
          alpha *= edge;
        }

        gl_FragColor = vec4(color, alpha);
      }
    `,
    uniforms: {
      uTime: { value: 0 },
      uResolution: { value: [1, 1] },
      uBaseThickness: { value: props.baseThickness },
      uOffsetFactor: { value: props.offsetFactor * props.effectAmplitude },
      uSpeed: { value: props.speedMultiplier },
      uSpring: { value: props.baseSpring },
      uFriction: { value: props.baseFriction },
      uMaxAge: { value: props.maxAge },
      uPointCount: { value: props.pointCount },
      uEnableFade: { value: props.enableFade ? 1 : 0 },
      uEnableShader: { value: props.enableShaderEffect ? 1 : 0 },
      uBgColor: { value: props.backgroundColor ?? [0, 0, 0, 0] },
      uColors: { value: colorBuffer },
      uColorCount: { value: normalizedColors.value.length },
    },
    transparent: true,
    depthTest: false,
    depthWrite: false,
  });

  mesh = new Mesh(gl, { geometry, program });
  mesh.setParent(scene);

  resize();
  updateDynamicUniforms();
  start();
}

function resize() {
  if (!renderer || !mesh || !canvasRef.value) return;
  const width = canvasRef.value.clientWidth;
  const height = canvasRef.value.clientHeight;
  renderer.setSize(width, height);
  mesh.program.uniforms.uResolution.value = [width, height];
}

function start() {
  const renderLoop = (t: number) => {
    if (!renderer || !camera || !scene) return;
    if (mesh) {
      mesh.program.uniforms.uTime.value = t * 0.001;
    }
    renderer.render({ scene, camera });
    frameId = requestAnimationFrame(renderLoop);
  };
  frameId = requestAnimationFrame(renderLoop);
}

function cleanup() {
  if (frameId !== null) {
    cancelAnimationFrame(frameId);
    frameId = null;
  }
  window.removeEventListener('resize', resize);
  renderer = null;
  camera = null;
  scene = null;
  mesh = null;
}

onMounted(() => {
  initRenderer();
  window.addEventListener('resize', resize);
});

onUnmounted(() => {
  cleanup();
});

watch(
  () => [
    props.colors,
    props.baseThickness,
    props.offsetFactor,
    props.speedMultiplier,
    props.baseSpring,
    props.baseFriction,
    props.maxAge,
    props.pointCount,
    props.enableFade,
    props.enableShaderEffect,
    props.effectAmplitude,
    props.backgroundColor,
  ],
  () => updateDynamicUniforms(),
  { deep: true },
);
</script>

<style scoped>
.ribbons-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: -1;
}
</style>

