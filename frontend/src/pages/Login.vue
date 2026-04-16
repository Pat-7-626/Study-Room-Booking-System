<script setup>
import api from "../services/api"
import { useRouter } from "vue-router"
import { ref } from "vue"

const router = useRouter()
const email = ref("")
const password = ref("")
const isRegistering = ref(false)
const errorMsg = ref("")

const submit = async () => {
  errorMsg.value = ""
  try {
    if (isRegistering.value) {
      await api.post("/register", { email: email.value, password: password.value, role: "member" })
      // Auto-login after register
      await performLogin()
    } else {
      await performLogin()
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || "Authentication failed"
  }
}

const performLogin = async () => {
  const res = await api.post("/login", { email: email.value, password: password.value })
  localStorage.setItem("token", res.data.access_token)

  const payload = JSON.parse(atob(res.data.access_token.split(".")[1]))

  if (payload.role === "admin") router.push("/users")
  else if (payload.role === "staff") router.push("/rooms")
  else router.push("/reservations")
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-700 to-purple-950 px-4">
    <div class="max-w-md w-full glass-panel rounded-3xl p-10 transform transition-all shadow-2xl relative overflow-hidden">
      <!-- Decorating backdrop glow -->
      <div class="absolute -top-24 -left-24 w-48 h-48 bg-purple-500/20 blur-3xl rounded-full"></div>
      <div class="absolute -bottom-24 -right-24 w-48 h-48 bg-fuchsia-500/10 blur-3xl rounded-full"></div>

      <div class="text-center mb-10 relative z-10">
        <h1 class="text-4xl font-black text-white mb-2 tracking-tight">Study Rooms</h1>
        <p class="text-purple-200/80 font-medium">
          {{ isRegistering ? "Create your account" : "Welcome back to your dashboard" }}
        </p>
      </div>

      <div v-if="errorMsg" class="mb-6 bg-red-500/10 border border-red-500/20 text-red-200 p-3 rounded-xl text-sm font-medium text-center backdrop-blur-md">
        {{ errorMsg }}
      </div>

      <form @submit.prevent="submit" class="space-y-6 relative z-10">
        <div>
          <label class="block text-xs font-bold text-purple-200 uppercase tracking-widest mb-1.5 ml-1">Email address</label>
          <input
            v-model="email"
            type="email"
            required
            class="input-field bg-white/5 border-white/10 text-white placeholder-purple-300/40 focus:bg-white/10 focus:border-purple-400/50"
            placeholder="student@example.com"
          />
        </div>

        <div>
          <label class="block text-xs font-bold text-purple-200 uppercase tracking-widest mb-1.5 ml-1">Password</label>
          <input
            v-model="password"
            type="password"
            required
            class="input-field bg-white/5 border-white/10 text-white placeholder-purple-300/40 focus:bg-white/10 focus:border-purple-400/50"
            placeholder="••••••••"
          />
        </div>

        <button type="submit" class="w-full btn-primary py-4 text-sm font-black uppercase tracking-widest mt-4 shadow-xl shadow-purple-900/40">
          {{ isRegistering ? "Create Account" : "Sign In" }}
        </button>
      </form>

      <div class="mt-8 text-center text-purple-200/60 text-xs font-bold uppercase tracking-widest relative z-10">
        <p v-if="!isRegistering">
          Don't have an account? 
          <button @click="isRegistering = true; errorMsg=''" class="text-white hover:text-purple-400 transition-colors">Register now</button>
        </p>
        <p v-else>
          Already have an account? 
          <button @click="isRegistering = false; errorMsg=''" class="text-white hover:text-purple-400 transition-colors">Sign in</button>
        </p>
      </div>
    </div>
  </div>
</template>