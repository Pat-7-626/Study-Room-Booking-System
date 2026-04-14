<script setup>
import axios from "axios"
import { ref, onMounted } from "vue"

const rooms = ref([])
const email = ref("")
const password = ref("")

const login = async () => {
  const res = await axios.post("http://localhost:8000/login", {
    email: email.value,
    password: password.value
  })
  localStorage.setItem("token", res.data.access_token)
}

const loadRooms = async () => {
  const res = await axios.get("http://localhost:8000/rooms")
  rooms.value = res.data
}

onMounted(loadRooms)
</script>

<template>
  <h1>Study Room System</h1>

  <input v-model="email" placeholder="email" />
  <input v-model="password" type="password" />
  <button @click="login">Login</button>

  <h2>Rooms</h2>
  <div v-for="r in rooms" :key="r.name">
    {{ r.name }}
  </div>
</template>