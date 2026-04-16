import { reactive } from "vue"

export const auth = reactive({
  token: localStorage.getItem("token"),
  user: null
})