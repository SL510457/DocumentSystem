import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useLinksStore = defineStore('links', () => {
  const links = ref([
    {
      title: 'Documents',
      url: '/',
      icon: 'mdi-file-document-outline'
    },
    {
      title: 'Audits',
      url: '/audit',
      icon: 'mdi-eye-outline'
    },
    {
      title: 'Reviews',
      url: '/reviews',
      icon: 'mdi-file-check-outline'
    }
  ])

  return { links }
})
