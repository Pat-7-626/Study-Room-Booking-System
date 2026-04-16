<script setup>
import api from "../services/api"
import { ref, onMounted } from "vue"

const users = ref([])
const showModal = ref(false)
const showCreateModal = ref(false)
const editingUser = ref(null)
const newRole = ref("member")

const newUser = ref({ email: "", password: "", role: "member" })
const errorMsg = ref("")

const load = async () => {
  try {
    users.value = (await api.get("/users")).data
  } catch (err) {
    console.error("Failed to load users")
  }
}

const remove = async (email) => {
  if (confirm(`Are you sure you want to delete user: ${email}?`)) {
    await api.delete(`/users/${email}`)
    load()
  }
}

const openEditModal = (u) => {
  editingUser.value = u
  newRole.value = u.role
  showModal.value = true
}

const saveRole = async () => {
  await api.put(`/users/${editingUser.value.email}`, { role: newRole.value })
  showModal.value = false
  load()
}

const createUser = async () => {
  errorMsg.value = ""
  try {
    await api.post("/register", newUser.value)
    showCreateModal.value = false
    newUser.value = { email: "", password: "", role: "member" }
    load()
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || "Failed to create user"
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-10">
      <div>
        <h1 class="text-3xl font-black text-slate-800 tracking-tight">Identity Control</h1>
        <p class="text-slate-500 mt-1 font-medium">Manage access layers and administrative permissions</p>
      </div>
      <button @click="showCreateModal = true" class="btn-primary flex items-center shadow-xl shadow-purple-900/10 uppercase tracking-widest text-[10px] font-black px-8 py-3.5">
        <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 4v16m8-8H4"/></svg>
        Provision New User
      </button>
    </div>

    <!-- Users Table -->
    <div class="bg-white rounded-[2.5rem] shadow-sm border border-slate-50 overflow-hidden hover:shadow-xl hover:shadow-purple-900/5 transition-all duration-500">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-50">
          <thead class="bg-slate-50/50">
            <tr>
              <th scope="col" class="px-8 py-5 text-left text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Identity Handle</th>
              <th scope="col" class="px-8 py-5 text-left text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Access Level</th>
              <th scope="col" class="px-8 py-5 text-right text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Operations</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-slate-50">
            <tr v-for="u in users" :key="u.email" class="hover:bg-purple-50/30 transition-colors group">
              <td class="px-8 py-6 whitespace-nowrap">
                <div class="flex items-center">
                  <div class="flex-shrink-0 h-12 w-12 bg-purple-100 rounded-2xl flex items-center justify-center text-purple-700 font-black text-xs uppercase shadow-inner group-hover:scale-110 transition-transform duration-300">
                    {{ u.email.substring(0,2) }}
                  </div>
                  <div class="ml-5">
                    <div class="text-sm font-black text-slate-800 tracking-tight">{{ u.email }}</div>
                  </div>
                </div>
              </td>
              <td class="px-8 py-6 whitespace-nowrap">
                <span class="px-4 py-1.5 inline-flex text-[10px] leading-5 font-black rounded-full uppercase tracking-widest shadow-sm" 
                      :class="{
                        'bg-violet-600 text-white': u.role === 'admin',
                        'bg-amber-400 text-white': u.role === 'staff',
                        'bg-slate-200 text-slate-600': u.role === 'member'
                      }">
                  {{ u.role }}
                </span>
              </td>
              <td class="px-8 py-6 whitespace-nowrap text-right text-sm">
                <button @click="openEditModal(u)" class="text-[10px] font-black uppercase tracking-widest text-purple-600 hover:text-purple-800 bg-purple-50 px-5 py-2.5 rounded-xl transition-all mr-3">Update Role</button>
                <button @click="remove(u.email)" class="text-[10px] font-black uppercase tracking-widest text-rose-400 hover:text-rose-600 bg-rose-50 px-5 py-2.5 rounded-xl transition-all">Revoke</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Update Role Modal -->
    <div v-if="showModal" class="fixed inset-0 z-50 overflow-y-auto" aria-modal="true">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 bg-slate-900/80 backdrop-blur-xl transition-opacity" @click="showModal = false" aria-hidden="true"></div>
        <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
        <div class="inline-block align-bottom bg-white rounded-[2.5rem] text-left overflow-hidden shadow-2xl transform transition-all sm:my-8 sm:align-middle sm:max-w-md sm:w-full relative z-10 border border-slate-100">
          <div class="px-10 py-8 border-b border-slate-50 flex justify-between items-center bg-slate-50/30">
            <h3 class="text-2xl font-black text-slate-800 tracking-tight">Modify Clearance</h3>
          </div>
          <div class="px-10 py-10 space-y-8">
            <div class="bg-purple-50 p-6 rounded-2xl border border-purple-100">
              <p class="text-[10px] font-black text-purple-400 uppercase tracking-widest mb-1">Target Account</p>
              <p class="text-sm font-black text-purple-900 truncate">{{ editingUser?.email }}</p>
            </div>
            <div>
              <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2.5 ml-1">Assigned Role</label>
              <select v-model="newRole" class="input-field font-bold text-slate-700 bg-slate-50 border-transparent focus:bg-white focus:border-purple-300">
                <option value="member">MEMBER</option>
                <option value="staff">STAFF</option>
                <option value="admin">ADMIN</option>
              </select>
            </div>
          </div>
          <div class="px-10 py-8 bg-slate-50/50 border-t border-slate-50 flex justify-end gap-4">
            <button @click="showModal = false" class="px-6 py-3 text-[10px] font-black text-slate-400 hover:text-slate-800 transition-colors uppercase tracking-[0.2em]">Cancel</button>
            <button @click="saveRole" class="btn-primary px-10 py-4 rounded-2xl shadow-xl shadow-purple-900/10 uppercase tracking-[0.2em] text-[10px] font-black">Commit Role</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create User Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 z-50 overflow-y-auto" aria-modal="true">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 bg-slate-900/80 backdrop-blur-xl transition-opacity" @click="showCreateModal = false" aria-hidden="true"></div>
        <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
        <div class="inline-block align-bottom bg-white rounded-[2.5rem] text-left overflow-hidden shadow-2xl transform transition-all sm:my-8 sm:align-middle sm:max-w-md sm:w-full relative z-10 border border-slate-100">
          <div class="px-10 py-8 border-b border-slate-50 flex justify-between items-center bg-slate-50/30">
            <h3 class="text-2xl font-black text-slate-800 tracking-tight">Provision Identity</h3>
          </div>
          <form @submit.prevent="createUser">
            <div class="px-10 py-10 space-y-8">
              <div v-if="errorMsg" class="bg-rose-50 border border-rose-100 text-rose-600 p-4 rounded-2xl text-xs font-bold">{{ errorMsg }}</div>
              <div>
                <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2.5 ml-1">Email Handle</label>
                <input v-model="newUser.email" type="email" required class="input-field font-bold text-slate-700 bg-slate-50 border-transparent focus:bg-white focus:border-purple-300" placeholder="employee@example.com" />
              </div>
              <div>
                <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2.5 ml-1">Initial Secret</label>
                <input v-model="newUser.password" type="password" required class="input-field font-bold text-slate-700 bg-slate-50 border-transparent focus:bg-white focus:border-purple-300" placeholder="••••••••" />
              </div>
              <div>
                <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2.5 ml-1">Clearance Tier</label>
                <select v-model="newUser.role" class="input-field font-bold text-slate-700 bg-slate-50 border-transparent focus:bg-white focus:border-purple-300">
                  <option value="member">MEMBER</option>
                  <option value="staff">STAFF</option>
                  <option value="admin">ADMIN</option>
                </select>
              </div>
            </div>
            <div class="px-10 py-8 bg-slate-50/50 border-t border-slate-50 flex justify-end gap-4">
              <button type="button" @click="showCreateModal = false" class="px-8 py-3 text-[10px] font-black text-slate-400 hover:text-slate-800 transition-colors uppercase tracking-[0.2em]">Cancel</button>
              <button type="submit" class="btn-primary px-10 py-4 rounded-2xl shadow-xl shadow-purple-900/10 uppercase tracking-[0.2em] text-[10px] font-black">Provision</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>