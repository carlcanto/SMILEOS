import { useQuasar } from 'quasar'
import { ref } from 'vue'

const isDark = ref(true)

export function useTheme() {
  const $q = useQuasar()

  const toggleDark = () => {
    $q.dark.toggle()
    isDark.value = $q.dark.isActive
    document.body.classList.toggle('light', !isDark.value)
    document.querySelector(':root')?.classList.toggle('light', !isDark.value)
  }

  const initTheme = () => {
    $q.dark.set(true)
    isDark.value = true
    document.body.classList.remove('light')
    document.querySelector(':root')?.classList.remove('light')
  }

  return { isDark, toggleDark, initTheme }
}
