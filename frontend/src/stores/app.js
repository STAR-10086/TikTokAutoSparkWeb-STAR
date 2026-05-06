import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useAppStore = defineStore('app', () => {
  const systemInfo = ref({
    version: '2.0.0',
    uptime: '0:00:00',
    browser_initialized: false,
    user_logged_in: false,
    scheduled_tasks: 0,
    last_login_ip: 'N/A'
  })

  const friends = ref([])
  const tasks = ref([])
  const loading = ref(false)

  async function fetchSystemInfo() {
    try {
      const res = await api.get('/api/system/info')
      if (res.data.code === 200) {
        systemInfo.value = res.data.data
      }
    } catch {}
  }

  async function fetchFriends() {
    loading.value = true
    try {
      const res = await api.get('/api/friends/list')
      if (res.data.code === 200) {
        friends.value = res.data.data.list
      }
    } catch {}
    loading.value = false
  }

  async function fetchTasks() {
    try {
      const res = await api.get('/api/tasks/list')
      if (res.data.code === 200) {
        tasks.value = res.data.data.tasks
      }
    } catch {}
  }

  async function initBrowser() {
    try {
      const res = await api.post('/api/browser/init')
      return res.data
    } catch (err) {
      return { code: 500, data: err.message }
    }
  }

  async function getScreenshot() {
    try {
      const res = await api.get('/api/browser/screenshot')
      return res.data
    } catch (err) {
      return { code: 500, data: err.message }
    }
  }

  async function addTask(time, friend, message) {
    try {
      const res = await api.post('/api/tasks/add', { time, friend, message })
      if (res.data.code === 200) {
        await fetchTasks()
      }
      return res.data
    } catch (err) {
      return { code: 500, data: err.message }
    }
  }

  async function deleteTask(taskId) {
    try {
      const res = await api.delete(`/api/tasks/${taskId}`)
      if (res.data.code === 200) {
        await fetchTasks()
      }
      return res.data
    } catch (err) {
      return { code: 500, data: err.message }
    }
  }

  async function updateTask(taskId, newTime) {
    try {
      const res = await api.put(`/api/tasks/${taskId}`, { new_time: newTime })
      if (res.data.code === 200) {
        await fetchTasks()
      }
      return res.data
    } catch (err) {
      return { code: 500, data: err.message }
    }
  }

  return {
    systemInfo,
    friends,
    tasks,
    loading,
    fetchSystemInfo,
    fetchFriends,
    fetchTasks,
    initBrowser,
    getScreenshot,
    addTask,
    deleteTask,
    updateTask
  }
})
