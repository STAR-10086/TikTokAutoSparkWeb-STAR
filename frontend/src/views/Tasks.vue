<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1 class="section-title">定时任务</h1>
        <p class="section-description">管理好友定时发送消息任务</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openAddDialog">
        添加任务
      </el-button>
    </div>

    <div class="card">
      <el-table :data="tasks" empty-text="暂无定时任务">
        <el-table-column prop="friend" label="好友" min-width="150">
          <template #default="{ row }">
            <span class="friend-name">{{ row.friend }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="time" label="发送时间" width="120">
          <template #default="{ row }">
            <span class="time-badge">
              <el-icon><Clock /></el-icon>
              {{ row.time }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="next_run" label="下次执行" min-width="180">
          <template #default="{ row }">
            <span class="next-run">{{ row.next_run || '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              text
              @click="openEditDialog(row)"
            >
              修改时间
            </el-button>
            <el-button
              type="danger"
              size="small"
              text
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Add Task Dialog -->
    <el-dialog v-model="addDialogVisible" title="添加定时任务" width="400px">
      <el-form :model="addForm">
        <el-form-item label="好友名称">
          <el-input v-model="addForm.friend" placeholder="输入好友昵称" />
        </el-form-item>
        <el-form-item label="发送时间">
          <el-time-picker
            v-model="addForm.time"
            format="HH:mm"
            placeholder="选择时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="消息内容（可选）">
          <el-input
            v-model="addForm.message"
            type="textarea"
            :rows="2"
            placeholder="留空则使用每日名言"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAdd" :loading="submitting">
          添加
        </el-button>
      </template>
    </el-dialog>

    <!-- Edit Task Dialog -->
    <el-dialog v-model="editDialogVisible" title="修改任务时间" width="350px">
      <el-form :model="editForm">
        <el-form-item label="好友">
          <el-input :model-value="editForm.friend" disabled />
        </el-form-item>
        <el-form-item label="新时间">
          <el-time-picker
            v-model="editForm.newTime"
            format="HH:mm"
            placeholder="选择新时间"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleEdit" :loading="submitting">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Clock } from '@element-plus/icons-vue'
import { useAppStore } from '../stores/app'

const appStore = useAppStore()
const tasks = computed(() => appStore.tasks)

const addDialogVisible = ref(false)
const editDialogVisible = ref(false)
const submitting = ref(false)

const addForm = ref({
  friend: '',
  time: null,
  message: ''
})

const editForm = ref({
  id: '',
  friend: '',
  newTime: null
})

onMounted(() => {
  appStore.fetchTasks()
})

function openAddDialog() {
  addForm.value = { friend: '', time: null, message: '' }
  addDialogVisible.value = true
}

function openEditDialog(row) {
  editForm.value = { id: row.id, friend: row.friend, newTime: null }
  editDialogVisible.value = true
}

async function handleAdd() {
  if (!addForm.value.friend) {
    ElMessage.warning('请输入好友昵称')
    return
  }
  if (!addForm.value.time) {
    ElMessage.warning('请选择发送时间')
    return
  }

  submitting.value = true
  const hours = addForm.value.time.getHours().toString().padStart(2, '0')
  const minutes = addForm.value.time.getMinutes().toString().padStart(2, '0')
  const timeStr = `${hours}:${minutes}`

  const result = await appStore.addTask(timeStr, addForm.value.friend, addForm.value.message || null)
  submitting.value = false

  if (result.code === 200) {
    ElMessage.success('任务已添加')
    addDialogVisible.value = false
  } else {
    ElMessage.error(result.data)
  }
}

async function handleEdit() {
  if (!editForm.value.newTime) {
    ElMessage.warning('请选择新时间')
    return
  }

  submitting.value = true
  const hours = editForm.value.newTime.getHours().toString().padStart(2, '0')
  const minutes = editForm.value.newTime.getMinutes().toString().padStart(2, '0')
  const timeStr = `${hours}:${minutes}`

  const result = await appStore.updateTask(editForm.value.id, timeStr)
  submitting.value = false

  if (result.code === 200) {
    ElMessage.success('任务已更新')
    editDialogVisible.value = false
  } else {
    ElMessage.error(result.data)
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定要删除 ${row.friend} 的定时任务吗？`,
      '确认删除',
      { type: 'warning' }
    )

    const result = await appStore.deleteTask(row.id)
    if (result.code === 200) {
      ElMessage.success('任务已删除')
    } else {
      ElMessage.error(result.data)
    }
  } catch {}
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-6);
}

.friend-name {
  font-weight: 500;
  color: var(--text-primary);
}

.time-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  color: var(--color-primary);
  font-weight: 500;
}

.next-run {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}
</style>
