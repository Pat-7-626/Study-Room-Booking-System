<script setup>
import api from "../services/api"
import { ref, onMounted, computed, watch } from "vue"
import { useRoute } from "vue-router"
import dayjs from "dayjs"

// ── State ──────────────────────────────────────────────────────────────────
const route  = useRoute()
const rooms = ref([])
const selectedRoom = ref("")
const selectedDate = ref("")
const selectedHour = ref("08")
const groupSize = ref(1)
const reservations = ref([])
const userRole = ref("")
const errorMsg = ref("")
const successMsg = ref("")
const slotOccupied = ref(0) // occupied seats for currently-selected slot

// ── Filters State ──────────────────────────────────────────────────────────
const filterRoom = ref("")
const filterDate = ref("")
const filterEmail = ref("")
const filterHour = ref("")

// ── Constants ──────────────────────────────────────────────────────────────
const minDate = computed(() => dayjs().add(1, "day").format("YYYY-MM-DD"))

const timeSlots = [
  { label: "08:00 – 09:00", value: "08" },
  { label: "09:00 – 10:00", value: "09" },
  { label: "10:00 – 11:00", value: "10" },
  { label: "11:00 – 12:00", value: "11" },
  { label: "12:00 – 13:00", value: "12" },
  { label: "13:00 – 14:00", value: "13" },
  { label: "14:00 – 15:00", value: "14" },
  { label: "15:00 – 16:00", value: "15" },
  { label: "16:00 – 17:00", value: "16" },
  { label: "17:00 – 18:00", value: "17" },
]

// ── Role helpers ───────────────────────────────────────────────────────────
const isMember = computed(() => userRole.value === "member")
const isStaff  = computed(() => userRole.value === "staff")
const isAdmin  = computed(() => userRole.value === "admin")

const loadRoles = () => {
  const token = localStorage.getItem("token")
  if (token) {
    const payload = JSON.parse(atob(token.split(".")[1]))
    userRole.value = payload.role
  }
}

// ── Rooms ──────────────────────────────────────────────────────────────────
const loadRooms = async () => {
  rooms.value = (await api.get("/rooms")).data
  // Only pre-select an Available room
  const first = rooms.value.find(r => r.status === "Available" || !r.status)
  // Check if router query pre-selects a room
  if (route.query.room) {
    const preselect = rooms.value.find(r => r.room_id === route.query.room)
    if (preselect) selectedRoom.value = preselect.room_id
  } else if (first) {
    selectedRoom.value = first.room_id
  }
}

// Members can only book Available rooms
const availableRooms = computed(() =>
  rooms.value.filter(r => r.status === "Available" || !r.status)
)

// Remaining capacity for the currently-selected slot
const slotSpotsLeft = computed(() => {
  const room = rooms.value.find(r => r.room_id === selectedRoom.value)
  if (!room) return 0
  return Math.max(0, room.capacity - slotOccupied.value)
})

// Fetch occupancy whenever room, date, or hour changes
const fetchSlotOccupancy = async () => {
  if (!selectedRoom.value || !selectedDate.value) { slotOccupied.value = 0; return }
  const startMs = dayjs(`${selectedDate.value}T${selectedHour.value}:00:00`).valueOf()
  try {
    const res = await api.get(`/slot-occupancy/${selectedRoom.value}?start_ms=${startMs}`)
    slotOccupied.value = res.data.occupied || 0
  } catch {
    slotOccupied.value = 0
  }
}

const selectedRoomCapacity = computed(() => {
  const room = rooms.value.find(r => r.room_id === selectedRoom.value)
  return room ? room.capacity : 1
})

// ── Reservations ───────────────────────────────────────────────────────────
const loadReservations = async () => {
  try {
    if (isMember.value) {
      reservations.value = (await api.get("/my-reservations")).data
    } else {
      reservations.value = (await api.get("/all-reservations")).data
    }
  } catch {
    reservations.value = []
  }
}

// ── Filtered list ────────────────────────────────────────────────────────
const filteredReservations = computed(() => {
  return reservations.value.filter(r => {
    const matchRoom  = !filterRoom.value  || r.room_id === filterRoom.value
    const matchEmail = !filterEmail.value || r.user_email.toLowerCase().includes(filterEmail.value.toLowerCase())
    const matchDate  = !filterDate.value  || dayjs(r.start).format("YYYY-MM-DD") === filterDate.value
    const matchHour  = !filterHour.value  || dayjs(r.start).format("HH") === filterHour.value
    return matchRoom && matchEmail && matchDate && matchHour
  })
})

const clearFilters = () => {
  filterRoom.value = ""
  filterDate.value = ""
  filterEmail.value = ""
  filterHour.value = ""
}

// ── Booking ────────────────────────────────────────────────────────────────
const reserve = async () => {
  errorMsg.value = ""
  successMsg.value = ""

  if (!selectedDate.value) {
    errorMsg.value = "Please select a date."
    return
  }

  const startDt = dayjs(`${selectedDate.value}T${selectedHour.value}:00:00`)
  const endDt   = startDt.add(1, "hour")

  try {
    await api.post("/reserve", {
      room_id:    selectedRoom.value,
      start:      startDt.valueOf(),
      end:        endDt.valueOf(),
      group_size: Number(groupSize.value),
    })
    successMsg.value = "Room reserved successfully!"
    loadReservations()
    fetchSlotOccupancy()
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || "Failed to reserve room"
  }
}

// ── Cancel ─────────────────────────────────────────────────────────────────
const cancel = async (res_id) => {
  if (!confirm("Are you sure you want to cancel this reservation?")) return
  try {
    await api.delete(`/reserve/${res_id}`)
    loadReservations()
    fetchSlotOccupancy()
  } catch (err) {
    alert(err.response?.data?.detail || "Failed to cancel")
  }
}

// ── Init ───────────────────────────────────────────────────────────────────
onMounted(async () => {
  loadRoles()
  await loadRooms()
  await loadReservations()
})

watch([selectedRoom, selectedDate, selectedHour], fetchSlotOccupancy)

const formatDate = (ts) => dayjs(ts).format("MMM D, YYYY h:mm A")
</script>

<template>
  <div>
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
      <div>
        <h1 class="text-3xl font-black text-slate-800 tracking-tight">Records</h1>
        <p class="text-slate-500 mt-1 font-medium">
          <template v-if="isMember">Book a space and view your schedule</template>
          <template v-else-if="isStaff">Monitor all visitor bookings</template>
          <template v-else-if="isAdmin">Control all system reservations</template>
        </p>
      </div>
    </div>

    <!-- ── Filter Bar ────────────────────────────────────────────────────────── -->
    <div class="bg-white p-6 rounded-[2rem] shadow-sm border border-slate-100 mb-8 flex flex-wrap items-end gap-6 hover:shadow-md transition-shadow">
      <div class="w-56">
        <label class="block text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-2.5 ml-1">Location</label>
        <select v-model="filterRoom" class="input-field text-sm font-bold text-slate-700 bg-slate-50 border-transparent focus:bg-white focus:border-purple-300">
          <option value="">Full Inventory</option>
          <option v-for="r in rooms" :key="r.room_id" :value="r.room_id">{{ r.room_id }}</option>
        </select>
      </div>

      <div class="w-48">
        <label class="block text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-2.5 ml-1">Calendar</label>
        <input v-model="filterDate" type="date" class="input-field text-sm font-bold text-slate-700 bg-slate-50 border-transparent focus:bg-white focus:border-purple-300" />
      </div>
      
      <div class="w-56">
        <label class="block text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-2.5 ml-1">Hour Period</label>
        <select v-model="filterHour" class="input-field text-sm font-bold text-slate-700 bg-slate-50 border-transparent focus:bg-white focus:border-purple-300">
          <option value="">Full Schedule</option>
          <option v-for="slot in timeSlots" :key="slot.value" :value="slot.value">{{ slot.label }}</option>
        </select>
      </div>

      <div v-if="!isMember" class="flex-1 min-w-[240px]">
        <label class="block text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-2.5 ml-1">Identity</label>
        <div class="relative group">
          <input v-model="filterEmail" type="text" placeholder="Search by member" class="input-field !pl-10 text-sm font-bold text-slate-700 bg-slate-50 border-transparent focus:bg-white focus:border-purple-300" />
          <svg class="w-4 h-4 absolute left-3 top-3 text-slate-300 group-focus-within:text-purple-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
        </div>
      </div>

      <button @click="clearFilters" class="px-6 py-2.5 text-[10px] font-black text-slate-400 hover:text-purple-600 transition-all uppercase tracking-widest flex items-center gap-2">
        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12"/></svg>
        Reset
      </button>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-10">

      <!-- ── BOOKING PANEL (Member only) ───────────────────────────────── -->
      <div v-if="isMember" class="bg-white rounded-[2.5rem] shadow-sm border border-slate-50 p-8 lg:col-span-1 h-fit sticky top-8">
        <div class="flex items-center gap-4 mb-8">
          <div class="w-12 h-12 rounded-2xl bg-purple-100 flex items-center justify-center">
            <svg class="w-6 h-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
            </svg>
          </div>
          <h2 class="text-2xl font-black text-slate-800 tracking-tight">Rapid Book</h2>
        </div>

        <div v-if="errorMsg"   class="mb-6 bg-rose-50 border border-rose-100 text-rose-600 p-4 rounded-2xl text-xs font-bold">{{ errorMsg }}</div>
        <div v-if="successMsg" class="mb-6 bg-emerald-50 border border-emerald-100 text-emerald-600 p-4 rounded-2xl text-xs font-bold">{{ successMsg }}</div>

        <div class="space-y-6">
          <div>
            <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 ml-1">Select Space</label>
            <select v-model="selectedRoom" class="input-field font-bold text-slate-700 bg-slate-50 border-transparent focus:bg-white focus:border-purple-300">
              <option v-for="r in availableRooms" :key="r.room_id" :value="r.room_id">
                {{ r.room_id }} (Max: {{ r.capacity }})
              </option>
            </select>
            <p v-if="availableRooms.length === 0" class="text-[10px] text-rose-500 mt-2 font-black uppercase tracking-widest">
              ⚠️ NO SPACES AVAILABLE
            </p>
          </div>

          <div>
            <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 ml-1">Date</label>
            <input v-model="selectedDate" type="date" :min="minDate" class="input-field font-bold text-slate-700 bg-slate-50 border-transparent focus:bg-white focus:border-purple-300" />
            <p class="text-[10px] text-slate-400 mt-2 font-medium">NEXT AVAILABLE: {{ dayjs(minDate).format("MMM D") }}</p>
          </div>

          <div>
            <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 ml-1">Duration</label>
            <select v-model="selectedHour" class="input-field font-bold text-slate-700 bg-slate-50 border-transparent focus:bg-white focus:border-purple-300">
              <option v-for="slot in timeSlots" :key="slot.value" :value="slot.value">
                {{ slot.label }}
              </option>
            </select>
            <p class="text-[10px] text-slate-400 mt-2 font-medium">FIXED 1-HOUR SESSIONS ONLY</p>
          </div>

          <div v-if="selectedDate && selectedRoom" class="rounded-[1.5rem] p-5 border transition-all duration-500"
               :class="slotSpotsLeft === 0 ? 'bg-rose-50/50 border-rose-100' : slotSpotsLeft < selectedRoomCapacity ? 'bg-amber-50/50 border-amber-100' : 'bg-purple-50/50 border-purple-100'">
            <div class="flex justify-between items-center text-[10px] font-black uppercase tracking-widest mb-3"
                 :class="slotSpotsLeft === 0 ? 'text-rose-600' : slotSpotsLeft < selectedRoomCapacity ? 'text-amber-600' : 'text-purple-600'">
              <span>Availability</span>
              <span>{{ slotSpotsLeft }} / {{ selectedRoomCapacity }} FREE</span>
            </div>
            <div class="h-2.5 bg-white/80 rounded-full overflow-hidden shadow-inner">
              <div class="h-full rounded-full transition-all duration-1000 ease-out shadow-sm"
                   :class="slotSpotsLeft === 0 ? 'bg-rose-500' : slotSpotsLeft < selectedRoomCapacity ? 'bg-amber-500' : 'bg-purple-500'"
                   :style="{ width: `${Math.min(100, (slotOccupied / selectedRoomCapacity) * 100)}%` }">
              </div>
            </div>
          </div>

          <div>
            <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 ml-1">Group Size</label>
            <input
              v-model.number="groupSize"
              type="number" min="1" :max="slotSpotsLeft || selectedRoomCapacity"
              class="input-field font-bold text-slate-700 bg-slate-50 border-transparent focus:bg-white focus:border-purple-300" placeholder="e.g. 2"
            />
          </div>

          <button
            @click="reserve"
            class="w-full btn-primary py-4 mt-2 text-[10px] font-black uppercase tracking-[0.2em] shadow-xl shadow-purple-900/10"
            :disabled="slotSpotsLeft === 0 && selectedDate !== ''"
            :class="slotSpotsLeft === 0 && selectedDate ? 'bg-slate-200 text-slate-400 shadow-none cursor-not-allowed' : ''"
          >
            {{ slotSpotsLeft === 0 && selectedDate ? 'SESSION FULL' : 'CONFIRM ACCESS' }}
          </button>
        </div>
      </div>

      <!-- ── RESERVATIONS LIST ──────────────────────────────────────────── -->
      <div :class="isMember ? 'lg:col-span-2' : 'lg:col-span-3'" class="space-y-6">
        <div v-if="filteredReservations.length === 0" class="flex flex-col items-center justify-center py-32 bg-white rounded-[3rem] border-2 border-dashed border-slate-100">
          <div class="w-24 h-24 bg-slate-50 rounded-[2rem] flex items-center justify-center mb-6">
            <svg class="h-10 w-10 text-slate-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
            </svg>
          </div>
          <h3 class="text-2xl font-black text-slate-800 tracking-tight">Registry is empty</h3>
          <p class="text-slate-400 mt-1 font-medium">Try broadening your search or secure a spot now.</p>
        </div>

        <div v-else class="grid grid-cols-1 gap-6">
          <div
            v-for="r in filteredReservations"
            :key="r.res_id"
            class="bg-white p-8 rounded-[2.5rem] border border-slate-50 shadow-sm hover:shadow-xl hover:shadow-purple-900/5 transition-all duration-500 flex flex-col md:flex-row md:items-center justify-between gap-8 group"
          >
            <div class="flex-1 min-w-0">
              <div class="flex flex-wrap items-center gap-3 mb-4">
                <span class="px-4 py-1.5 rounded-2xl text-[10px] font-black uppercase tracking-widest bg-purple-50 text-purple-600 shadow-sm">
                  {{ r.room_id }}
                </span>
                <span class="px-4 py-1.5 rounded-2xl text-[10px] font-black uppercase tracking-widest bg-slate-50 text-slate-500">
                  👥 {{ r.group_size || 1 }} person(s)
                </span>
                <span v-if="!isMember" class="text-[10px] font-bold text-black uppercase tracking-widest truncate max-w-[200px]">
                  ID: {{ r.user_email.split('@')[0] }}
                </span>
              </div>
              
              <div class="flex items-center text-slate-800">
                <div class="w-10 h-10 rounded-2xl bg-slate-50 flex items-center justify-center mr-4 group-hover:bg-purple-100 transition-colors">
                  <svg class="w-5 h-5 text-slate-400 group-hover:text-purple-600 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                </div>
                <div>
                  <p class="text-sm font-black tracking-tight">{{ formatDate(r.start).split(' at ')[0] }}</p>
                  <p class="text-xs font-bold text-slate-400 uppercase tracking-widest">{{ dayjs(r.start).format("h:mm A") }} – {{ dayjs(r.end).format("h:mm A") }}</p>
                </div>
              </div>
            </div>

            <div class="flex items-center">
              <button
                v-if="isMember || isAdmin"
                @click="cancel(r.res_id)"
                class="px-8 py-3 text-[10px] font-black uppercase tracking-widest text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-2xl transition-all duration-300"
              >
                Terminate Access
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>