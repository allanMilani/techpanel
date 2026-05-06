import { library } from '@fortawesome/fontawesome-svg-core'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import {
  faArrowLeft,
  faBars,
  faGripVertical,
  faHome,
  faLayerGroup,
  faPenToSquare,
  faPlay,
  faPlus,
  faProjectDiagram,
  faRightToBracket,
  faServer,
  faSignOutAlt,
  faTerminal,
  faTrash,
  faUser,
  faUserPlus,
  faXmark,
} from '@fortawesome/free-solid-svg-icons'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import './style.css'

library.add(
  faArrowLeft,
  faBars,
  faGripVertical,
  faHome,
  faLayerGroup,
  faPenToSquare,
  faPlay,
  faPlus,
  faProjectDiagram,
  faRightToBracket,
  faServer,
  faSignOutAlt,
  faTerminal,
  faTrash,
  faUser,
  faUserPlus,
  faXmark,
)

const app = createApp(App)
app.component('FontAwesomeIcon', FontAwesomeIcon)
app.use(router)

app.mount('#app')
