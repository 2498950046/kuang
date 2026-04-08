<template>
    <div class="gem-logo-container" :style="{ width: size, height: size }">
      <svg 
        :width="size" 
        :height="size" 
        viewBox="0 0 200 200" 
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="cottonCandyGem" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#FFB7B2;stop-opacity:1" /> 
            <stop offset="50%" style="stop-color:#E2F0CB;stop-opacity:1" /> 
            <stop offset="100%" style="stop-color:#C7CEEA;stop-opacity:1" /> 
          </linearGradient>
  
          <linearGradient id="scanBeam" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style="stop-color:#fff;stop-opacity:0" />
            <stop offset="50%" style="stop-color:#fff;stop-opacity:0.9" /> 
            <stop offset="100%" style="stop-color:#fff;stop-opacity:0" />
          </linearGradient>
  
          <filter id="softGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="blur" />
            <feColorMatrix in="blur" type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 18 -7" result="goo" />
            <feBlend in="SourceGraphic" in2="goo" />
            <feGaussianBlur stdDeviation="3" result="glow"/>
            <feMerge>
              <feMergeNode in="glow"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>
  
        <g class="floater">
          
          <circle cx="100" cy="100" r="80" fill="none" stroke="#A9DEF9" stroke-width="4" stroke-linecap="round" stroke-dasharray="20, 10" opacity="0.6" filter="url(#softGlow)">
            <animateTransform attributeName="transform" type="rotate" from="0 100 100" to="360 100 100" dur="20s" repeatCount="indefinite" />
          </circle>
          
          <circle cx="100" cy="100" r="65" fill="none" stroke="#FF9AA2" stroke-width="2" stroke-dasharray="50, 50" opacity="0.4">
             <animateTransform attributeName="transform" type="rotate" from="360 100 100" to="0 100 100" dur="15s" repeatCount="indefinite" />
          </circle>
  
          <g transform="translate(100, 100)">
              <path d="M -30 -35 L 30 -35 L 48 -10 L 0 55 L -48 -10 Z" 
                    fill="url(#cottonCandyGem)" 
                    stroke="#fff" 
                    stroke-width="2" 
                    stroke-opacity="0.6" 
                    filter="url(#softGlow)">
                  <animateTransform attributeName="transform" type="scale" values="1;1.05;1" dur="3s" repeatCount="indefinite" />
              </path>
              
              <path d="M -48 -10 L 48 -10 M -30 -35 L 0 55 M 30 -35 L 0 55 M -30 -35 L -15 -10 M 30 -35 L 15 -10" 
                    stroke="#fff" 
                    stroke-width="1.5" 
                    stroke-opacity="0.5" 
                    fill="none">
                   <animateTransform attributeName="transform" type="scale" values="1;1.05;1" dur="3s" repeatCount="indefinite" />
              </path>
          </g>
  
          <rect x="40" y="50" width="120" height="8" fill="url(#scanBeam)" opacity="0.8" rx="4">
            <animate attributeName="y" values="50; 160; 50" dur="3s" repeatCount="indefinite" calcMode="spline" keySplines="0.4 0 0.2 1; 0.4 0 0.2 1" />
            <animate attributeName="width" values="100; 120; 100" dur="3s" repeatCount="indefinite" />
            <animate attributeName="x" values="50; 40; 50" dur="3s" repeatCount="indefinite" />
          </rect>
          
        </g>
      </svg>
    </div>
  </template>
  
  <script setup>
  import { defineProps } from 'vue';
  
  const props = defineProps({
    size: {
      type: String,
      default: '250px'
    }
  });
  </script>
  
  <style scoped>
  /* 保留了深色背景以衬托糖果色光效 
    如果你的父级页面已经是深色，可以将 background-color 移除
  */
  .gem-logo-container {
    /* background-color: #1a1a2e;  */
    display: flex;
    justify-content: center;
    align-items: center;
    border-radius: 12px; /* 可选：给容器加个圆角 */
  }
  
  .floater {
    animation: float 4s ease-in-out infinite;
  }
  
  @keyframes float {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
    100% { transform: translateY(0px); }
  }
  </style>
  