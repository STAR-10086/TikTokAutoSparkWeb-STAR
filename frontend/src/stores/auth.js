import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(username, password) {
    try {
      const res = await api.post('/api/auth/login', { username, password })
      if (res.data.code === 200) {
        token.value = res.data.data.token
        localStorage.setItem('token', token.value)
        return { success: true }
      }
      return { success: false, message: res.data.data }
    } catch (err) {
      return { success: false, message: err.message }
    }
  }

  async function logout() {
    try {
      await api.post('/api/auth/logout')
    } catch {}
    token.value = ''
    localStorage.removeItem('token')
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    logout
  }
})
