<script setup>
import api from "../services/api"
import { ref, onMounted, computed } from "vue"
import { useRouter } from "vue-router"

const router = useRouter()

const rooms = ref([])
const newRoom = ref({ room_id: "", capacity: 1, status: "Available", photo_url: "" })
const selectedFile = ref(null)
const filePreview = ref(null)
const isEditing = ref(false)
const showModal = ref(false)
const userRole = ref("")
const isUploading = ref(false)

// ── Filters State ───────────────────────────────────────────────────────────
const filterName = ref("")
const filterStatus = ref("")
const filterMinCapacity = ref("")

const isMember  = computed(() => userRole.value === "member")
const canManage = computed(() => ["staff", "admin"].includes(userRole.value))

const loadRoles = () => {
  const token = localStorage.getItem("token")
  if (token) {
    const payload = JSON.parse(atob(token.split(".")[1]))
    userRole.value = payload.role
  }
}

const load = async () => {
  rooms.value = (await api.get("/rooms")).data
}

// ── Filtered Rooms ─────────────────────────────────────────────────────────
const filteredRooms = computed(() => {
  return rooms.value.filter(r => {
    const matchName = !filterName.value || r.room_id.toLowerCase().includes(filterName.value.toLowerCase())
    const matchStatus = !filterStatus.value || r.status === filterStatus.value || (!r.status && filterStatus.value === 'Available')
    const matchCap = !filterMinCapacity.value || r.capacity >= Number(filterMinCapacity.value)
    return matchName && matchStatus && matchCap
  })
})

const clearFilters = () => {
  filterName.value = ""
  filterStatus.value = ""
  filterMinCapacity.value = ""
}

const onFileChange = (e) => {
  const file = e.target.files[0]
  if (!file) return
  
  if (!['image/jpeg', 'image/png'].includes(file.type)) {
    alert("Only JPG or PNG images are allowed")
    e.target.value = ""
    return
  }
  
  selectedFile.value = file
  filePreview.value = URL.createObjectURL(file)
}

const save = async () => {
  try {
    let finalRoomId = newRoom.value.room_id

    if (isEditing.value) {
      // Find the original ID to handle the update
      const idToUpdate = newRoom.value._original_id || newRoom.value.room_id
      await api.put(`/rooms/${idToUpdate}`, newRoom.value)
    } else {
      await api.post("/rooms", newRoom.value)
    }

    if (selectedFile.value) {
      isUploading.value = true
      const formData = new FormData()
      formData.append("file", selectedFile.value)
      
      const uploadRes = await api.post(`/rooms/${finalRoomId}/photo`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      newRoom.value.photo_url = uploadRes.data.photo_url
    }

    showModal.value = false
    resetForm()
    load()
  } catch (err) {
    alert(err.response?.data?.detail || "Failed to save room")
  } finally {
    isUploading.value = false
  }
}

const resetForm = () => {
  newRoom.value = { room_id: "", capacity: 1, status: "Available", photo_url: "" }
  selectedFile.value = null
  filePreview.value = null
}

const editRoom = (r) => {
  // Store the original ID so the backend knows which record to target if the ID changes
  newRoom.value = { ...r, _original_id: r.room_id }
  filePreview.value = r.photo_url
  isEditing.value = true
  showModal.value = true
}

const deleteRoom = async (id) => {
  if (confirm(`Are you sure you want to delete room ${id}?`)) {
    await api.delete(`/rooms/${id}`)
    load()
  }
}

const openNew = () => {
  resetForm()
  isEditing.value = false
  showModal.value = true
}

const bookRoom = (room) => {
  router.push({ path: "/reservations", query: { room: room.room_id } })
}

onMounted(async () => {
  loadRoles()
  await load()
})
</script>

<template>
  <div>
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
      <div>
        <h1 class="text-3xl font-black text-slate-800 tracking-tight">Study Rooms</h1>
        <p class="text-slate-500 mt-1 font-medium">
          <template v-if="isMember">Browse available study rooms</template>
          <template v-else>Manage all study rooms in the building</template>
        </p>
      </div>
      <button v-if="canManage" @click="openNew" class="btn-primary flex items-center shadow-lg shadow-purple-200 uppercase tracking-widest text-xs font-black">
        <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 4v16m8-8H4"/></svg>
        Add New Room
      </button>
    </div>

    <!-- ── Filter Bar ────────────────────────────────────────────────────────── -->
    <div class="bg-white p-6 rounded-3xl shadow-sm border border-slate-100 mb-8 flex flex-wrap items-end gap-6 transition-all hover:shadow-md">
      <div class="flex-1 min-w-[240px]">
        <label class="block text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-2 ml-1">Search Rooms</label>
        <div class="relative group">
          <input v-model="filterName" type="text" placeholder="Search by name..." class="input-field !pl-10 text-sm bg-slate-50 border-transparent focus:bg-white focus:border-purple-300" />
          <svg class="w-4 h-4 absolute left-3 top-3 text-slate-400 group-focus-within:text-purple-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
        </div>
      </div>

      <div class="w-56">
        <label class="block text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-2 ml-1">Filter by Status</label>
        <select v-model="filterStatus" class="input-field text-sm bg-slate-50 border-transparent focus:bg-white focus:border-purple-300">
          <option value="">All Statuses</option>
          <option value="Available">Available</option>
          <option value="Maintenance">Maintenance</option>
          <option value="Closed">Closed</option>
        </select>
      </div>

      <div class="w-40">
        <label class="block text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-2 ml-1">Min Capacity</label>
        <input v-model="filterMinCapacity" type="number" min="1" placeholder="e.g. 4" class="input-field text-sm bg-slate-50 border-transparent focus:bg-white focus:border-purple-300" />
      </div>

      <button @click="clearFilters" class="px-6 py-2.5 text-[10px] font-black text-slate-500 hover:text-purple-600 transition-all uppercase tracking-widest flex items-center gap-2">
        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12"/></svg>
        Reset
      </button>
    </div>

    <!-- Member info banner -->
    <div v-if="isMember" class="mb-8 bg-purple-50 border border-purple-100 rounded-2xl px-6 py-4 text-xs font-bold text-purple-700 flex items-center gap-3 animate-in fade-in slide-in-from-top-2 duration-500">
      <div class="w-8 h-8 rounded-xl bg-purple-100 flex items-center justify-center shrink-0">
        <svg class="w-4 h-4 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
      </div>
      <p class="tracking-tight">Browse and select a room to start your booking. Showing {{ filteredRooms.length }} spaces.</p>
    </div>

    <!-- Room Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
      <div v-if="filteredRooms.length === 0" class="col-span-full py-32 text-center">
        <div class="w-20 h-20 bg-slate-100 rounded-3xl flex items-center justify-center mx-auto mb-6">
          <svg class="w-10 h-10 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>
        </div>
        <p class="text-xl font-black text-slate-800 tracking-tight">No rooms match your filters</p>
        <p class="text-slate-400 mt-1 font-medium">Try broadening your search criteria.</p>
      </div>

      <div
        v-for="r in filteredRooms"
        :key="r.room_id"
        class="bg-white rounded-[2rem] shadow-sm border border-slate-100 overflow-hidden hover:shadow-xl hover:shadow-purple-900/5 transition-all duration-500 group flex flex-col relative"
        :class="r.status === 'Available' || !r.status ? '' : 'opacity-80'"
      >
        <!-- Room image header -->
        <div class="h-60 flex items-center justify-center relative bg-slate-50 overflow-hidden">
          <template v-if="r.photo_url">
            <img :src="r.photo_url" class="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" />
          </template>
          <template v-else>
            <div class="absolute inset-0 bg-gradient-to-br from-purple-100 to-violet-100 flex items-center justify-center">
              <svg class="w-20 h-20 text-purple-300/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
              </svg>
            </div>
          </template>
          
          <!-- Badges -->
          <div class="absolute top-4 left-4 z-10">
            <span class="px-4 py-1.5 text-[10px] font-black uppercase tracking-widest rounded-full shadow-lg backdrop-blur-md"
                  :class="{
                    'bg-emerald-500/90 text-white': r.status === 'Available' || !r.status,
                    'bg-amber-500/90 text-white': r.status === 'Maintenance',
                    'bg-rose-500/90 text-white': r.status === 'Closed'
                  }">
              {{ r.status || 'Available' }}
            </span>
          </div>

          <div
            v-if="(r.status && r.status !== 'Available')"
            class="absolute inset-0 bg-slate-900/40 flex items-center justify-center backdrop-blur-[2px]"
          >
            <span class="bg-white text-slate-900 text-[10px] font-black px-6 py-2 rounded-2xl shadow-2xl uppercase tracking-[0.2em]">
              {{ r.status === 'Maintenance' ? 'Maintenance' : 'Closed' }}
            </span>
          </div>
        </div>

        <div class="p-8 flex flex-col flex-1 relative bg-white">
          <div class="mb-4">
            <h3 class="text-2xl font-black text-slate-800 tracking-tight mb-1 group-hover:text-purple-600 transition-colors">{{ r.room_id }}</h3>
            <div class="flex items-center text-xs font-bold text-slate-400 gap-2">
              <svg class="w-4 h-4 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
              </svg>
              Capacity: {{ r.capacity }} person(s)
            </div>
          </div>

          <div class="mt-auto pt-6 border-t border-slate-50">
            <button
              v-if="isMember && (r.status === 'Available' || !r.status)"
              @click="bookRoom(r)"
              class="w-full btn-primary py-4 text-xs font-black uppercase tracking-[0.2em] flex items-center justify-center gap-2 shadow-lg shadow-purple-900/10 hover:shadow-purple-900/20"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
              Secure Spot
            </button>

            <div v-if="canManage" class="flex justify-end gap-2">
              <button @click="editRoom(r)" class="w-12 h-12 flex items-center justify-center bg-slate-50 text-slate-400 hover:bg-purple-100 hover:text-purple-600 rounded-2xl transition-all duration-300" title="Edit">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
              </button>
              <button @click="deleteRoom(r.room_id)" class="w-12 h-12 flex items-center justify-center bg-slate-50 text-slate-400 hover:bg-rose-100 hover:text-rose-600 rounded-2xl transition-all duration-300" title="Delete">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <div v-if="showModal && canManage" class="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 bg-slate-900/80 backdrop-blur-xl transition-opacity" @click="showModal = false" aria-hidden="true"></div>
        <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
        <div class="inline-block align-bottom bg-white rounded-[2.5rem] text-left overflow-hidden shadow-2xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full relative z-10 border border-slate-100">
          <div class="px-10 py-8 border-b border-slate-50 flex justify-between items-center bg-slate-50/30">
            <h3 class="text-3xl font-black text-slate-800 tracking-tight" id="modal-title">
              {{ isEditing ? 'Update Space' : 'New Study Room' }}
            </h3>
            <button @click="showModal = false" class="w-10 h-10 flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-all">
              <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
          </div>
          <form @submit.prevent="save">
            <div class="px-10 py-10 space-y-8">
              <div>
                <label for="room_id" class="block text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-2.5 ml-1">Room Identity</label>
                <input v-model="newRoom.room_id" type="text" id="room_id" required class="input-field font-bold text-slate-700 bg-slate-50 border-transparent focus:bg-white focus:border-purple-300" placeholder="e.g. A-101" />
              </div>
              
              <div>
                <label class="block text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-2.5 ml-1">Visual Profile</label>
                <div class="flex items-center gap-6">
                  <div class="h-32 w-32 rounded-3xl border-2 border-dashed border-slate-200 flex items-center justify-center overflow-hidden bg-slate-50 relative group transition-all hover:border-purple-300">
                    <img v-if="filePreview" :src="filePreview" class="h-full w-full object-cover" />
                    <svg v-else class="h-10 w-10 text-slate-200" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
                    
                    <label class="absolute inset-0 cursor-pointer flex items-center justify-center bg-black/0 group-hover:bg-purple-900/40 transition-all">
                      <input type="file" class="hidden" @change="onFileChange" accept="image/png, image/jpeg" />
                      <svg class="h-8 w-8 text-white opacity-0 group-hover:opacity-100 transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/></svg>
                    </label>
                  </div>
                  <div class="flex-1">
                    <button type="button" @click="$el.querySelector('input[type=file]').click()" class="text-[10px] font-black text-purple-600 hover:text-purple-800 transition-colors uppercase tracking-[0.2em] bg-purple-50 px-4 py-2 rounded-xl">
                      {{ filePreview ? 'Switch Frame' : 'Add Image' }}
                    </button>
                    <p class="text-[10px] text-slate-400 mt-2.5 font-bold leading-relaxed">HIGH RES PNG OR JPG<br/>MAX SIZE 5MB</p>
                  </div>
                </div>
              </div>

              <div class="grid grid-cols-2 gap-6">
                <div>
                  <label for="capacity" class="block text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-2.5 ml-1">Load limit</label>
                  <input v-model="newRoom.capacity" type="number" id="capacity" required min="1" class="input-field font-bold text-slate-700 bg-slate-50 border-transparent focus:bg-white focus:border-purple-300" placeholder="e.g. 4" />
                </div>
                <div>
                  <label for="status" class="block text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-2.5 ml-1">Current State</label>
                  <select v-model="newRoom.status" id="status" class="input-field font-bold text-slate-700 bg-slate-50 border-transparent focus:bg-white focus:border-purple-300">
                    <option value="Available">Available</option>
                    <option value="Maintenance">Maintenance</option>
                    <option value="Closed">Closed</option>
                  </select>
                </div>
              </div>
            </div>
            <div class="px-10 py-8 bg-slate-50/50 border-t border-slate-50 flex justify-end gap-4">
              <button type="button" @click="showModal = false" class="px-8 py-3 text-[10px] font-black text-slate-400 hover:text-slate-800 transition-colors uppercase tracking-[0.2em]">Cancel</button>
              <button type="submit" class="btn-primary px-10 py-4 rounded-2xl shadow-xl shadow-purple-900/10 uppercase tracking-[0.2em] text-[10px] font-black" :disabled="isUploading">
                <template v-if="isUploading">
                  <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Processing...
                </template>
                <template v-else>
                  {{ isEditing ? 'Finalize Changes' : 'Launch Room' }}
                </template>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>