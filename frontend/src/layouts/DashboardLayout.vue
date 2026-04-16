<script setup>
import { useRouter } from "vue-router"
import { ref, onMounted } from "vue"

const router = useRouter()
const userRole = ref("")
const userEmail = ref("")

onMounted(() => {
  const token = localStorage.getItem("token")
  if (token) {
    try {
      const payload = JSON.parse(atob(token.split(".")[1]))
      userRole.value = payload.role
      userEmail.value = payload.email
    } catch {
      logout()
    }
  } else {
    logout()
  }
})

const logout = () => {
  localStorage.removeItem("token")
  router.push("/")
}
</script>

<template>
  <div class="flex h-screen bg-slate-50 font-sans">
    <!-- Sidebar -->
    <aside class="w-64 bg-white border-r border-slate-200 shadow-sm flex flex-col">
      <div class="p-6 border-b border-slate-100">
        <h2 class="text-2xl font-black text-purple-600 tracking-tight">Study Rooms</h2>
        <p class="text-xs text-slate-400 mt-1 uppercase font-bold tracking-widest">{{ userRole }} Portal</p>
      </div>

      <nav class="flex-1 px-4 py-6 space-y-2">
        <router-link 
          to="/rooms" 
          class="flex items-center px-4 py-3 rounded-xl text-slate-500 font-bold text-sm uppercase tracking-widest hover:bg-purple-50 hover:text-purple-600 transition-all duration-300"
          active-class="bg-purple-100 text-purple-700 shadow-sm"
        >
          <svg class="w-5 h-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>
          Rooms
        </router-link>
        
        <router-link 
          to="/reservations" 
          class="flex items-center px-4 py-3 rounded-xl text-slate-500 font-bold text-sm uppercase tracking-widest hover:bg-purple-50 hover:text-purple-600 transition-all duration-300"
          active-class="bg-purple-100 text-purple-700 shadow-sm"
        >
          <svg class="w-5 h-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
          Reservations
        </router-link>
        
        <router-link 
          v-if="userRole === 'admin'"
          to="/users" 
          class="flex items-center px-4 py-3 rounded-xl text-slate-500 font-bold text-sm uppercase tracking-widest hover:bg-purple-50 hover:text-purple-600 transition-all duration-300"
          active-class="bg-purple-100 text-purple-700 shadow-sm"
        >
          <svg class="w-5 h-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
          Users
        </router-link>
      </nav>

      <div class="p-6 border-t border-slate-100 bg-slate-50/50">
        <div class="mb-5">
          <p class="text-[10px] text-slate-400 font-black uppercase tracking-[0.2em] mb-1">User Identity</p>
          <p class="text-xs font-bold text-slate-700 truncate" :title="userEmail">{{ userEmail }}</p>
        </div>
        <button @click="logout" class="w-full flex items-center justify-center px-4 py-2.5 border border-slate-200 shadow-sm text-[10px] font-black uppercase tracking-widest rounded-xl text-slate-600 bg-white hover:bg-slate-50 hover:text-purple-600 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all">
          Sign out
        </button>
      </div>
    </aside>

    <!-- Content -->
    <main class="flex-1 overflow-x-hidden overflow-y-auto bg-slate-50 p-10">
      <div class="max-w-6xl mx-auto">
        <router-view />
      </div>
    </main>
  </div>
</template>