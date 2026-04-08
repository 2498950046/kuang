<!-- src/components/TableView.vue -->
<template>
  <div v-if="tableData.rows.length > 0" class="table-container">
    <table>
      <thead>
      <tr>
        <th v-for="header in tableData.headers" :key="header">{{ header }}</th>
      </tr>
      </thead>
      <tbody>
      <tr v-for="(row, index) in tableData.rows" :key="index">
        <td v-for="header in tableData.headers" :key="header">{{ row[header] }}</td>
      </tr>
      </tbody>
    </table>
  </div>
  <div v-else>
    <p> non 似乎没有查询到任何数据~</p>
  </div>
</template>

<script setup>
defineProps({ tableData: Object });
</script>

<style scoped>
.table-container {
  max-height: 628px;  /* 设置最大高度，超出此高度将显示滚动条 */
  overflow-y: auto;   /* 垂直方向自动显示滚动条 */
  overflow-x: auto;   /* 水平方向自动显示滚动条 */
}

table {
  width: 100%;
  border-collapse: collapse;
}
</style>
