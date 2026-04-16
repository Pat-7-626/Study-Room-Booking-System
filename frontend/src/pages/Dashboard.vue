<template>
  <div class="flex">
    <aside class="w-60 bg-gray-800 text-white p-4">
      <router-link to="/rooms">Rooms</router-link><br />
      <router-link to="/reservations">Reservations</router-link><br />
      <router-link to="/users">Users</router-link>
    </aside>

    <main class="flex-1 p-6">
      <slot />
    </main>
  </div>
</template>