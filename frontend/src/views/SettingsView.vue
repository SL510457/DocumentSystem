<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { useUserStore } from '@/stores/user';

const userStore = useUserStore();

const name = ref('');
const username = ref('');
const emailNotifications = ref(true);
const isLoading = ref(true);
const loadError = ref('');
const saveError = ref('');
const saveSuccess = ref(false);

onMounted(() => {
  axios.get('/api/v1/account/settings/' + encodeURIComponent(userStore.user.username))
  .then(response => {
    name.value = response.data.name;
    username.value = response.data.username;
    emailNotifications.value = response.data.emailNotifications;
    isLoading.value = false;
  }).catch(error => {
    loadError.value = 'Failed to load settings.';
    isLoading.value = false;
  });
});

function saveSettings() {
  saveError.value = '';
  saveSuccess.value = false;
  axios.put('/api/v1/account/settings', {
    username: username.value,
    name: name.value,
    emailNotifications: emailNotifications.value,
  }).then(response => {
    userStore.user.name = response.data.name;
    saveSuccess.value = true;
  }).catch(error => {
    saveError.value = 'Failed to save settings.';
  });
}
</script>

<template>
  <v-main>
    <v-app-bar height="75">
      <v-app-bar-title>Settings</v-app-bar-title>
    </v-app-bar>
    <v-container class="pa-6" style="max-width: 600px;">
      <v-alert v-if="loadError" type="error" class="mb-4">{{ loadError }}</v-alert>
      <v-form v-if="!isLoading && !loadError" @submit.prevent="saveSettings">
        <v-text-field
          label="Username"
          v-model="username"
          disabled
          hint="Set from your Google account and cannot be changed"
          persistent-hint
          class="mb-4"
        ></v-text-field>
        <v-text-field
          label="Name"
          v-model="name"
          class="mb-4"
        ></v-text-field>
        <v-switch
          v-model="emailNotifications"
          label="Email Notifications"
          color="primary"
          true-icon="mdi-email"
          false-icon="mdi-email-off"
        ></v-switch>
        <v-alert v-if="saveError" type="error" class="mb-4">{{ saveError }}</v-alert>
        <v-alert v-if="saveSuccess" type="success" class="mb-4">Settings saved.</v-alert>
        <v-btn color="primary" type="submit">CONFIRM</v-btn>
      </v-form>
    </v-container>
  </v-main>
</template>
