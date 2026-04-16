import { createRouter, createWebHistory } from "vue-router"

import Login from "./pages/Login.vue"
import DashboardLayout from "./layouts/DashboardLayout.vue"

import Rooms from "./pages/Rooms.vue"
import Reservations from "./pages/Reservations.vue"
import Users from "./pages/Users.vue"

const routes = [
  { path: "/", component: Login },

  {
    path: "/",
    component: DashboardLayout,
    children: [
      { path: "rooms", component: Rooms },
      { path: "reservations", component: Reservations },
      { path: "users", component: Users }
    ]
  }
]

export default createRouter({
  history: createWebHistory(),
  routes
})