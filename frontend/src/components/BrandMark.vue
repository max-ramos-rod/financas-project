<script setup lang="ts">
interface Props {
  size?: number | string
  color?: string
  inverted?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 32,
  color: '#1F5C3A',
  inverted: false,
})

const bg = props.inverted ? '#ffffff' : props.color
const fg = props.inverted ? props.color : '#ffffff'
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 100 100"
    xmlns="http://www.w3.org/2000/svg"
    role="img"
    aria-label="Finanças Cristãs"
  >
    <rect x="0" y="0" width="100" height="100" rx="20" :fill="bg" />
    <!-- Haste vertical -->
    <rect x="22" y="22" width="14" height="56" :fill="fg" />
    <!-- Braço superior -->
    <rect x="22" y="22" width="56" height="14" :fill="fg" />
    <!-- Braço do meio -->
    <rect x="22" y="43" width="42" height="14" :fill="fg" />
  </svg>
</template>
