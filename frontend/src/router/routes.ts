import type { RouteRecordRaw } from 'vue-router'

import DashboardView from '../views/DashboardView.vue'
import EnvironmentFormView from '../views/EnvironmentFormView.vue'
import EnvironmentsHubView from '../views/EnvironmentsHubView.vue'
import EnvironmentsListView from '../views/EnvironmentsListView.vue'
import ExecutionMonitorView from '../views/ExecutionMonitorView.vue'
import LoginView from '../views/LoginView.vue'
import MainLayout from '../layouts/MainLayout.vue'
import PipelineDetailView from '../views/PipelineDetailView.vue'
import PipelinesListView from '../views/PipelinesListView.vue'
import PipelineRunView from '../views/PipelineRunView.vue'
import ProjectFormView from '../views/ProjectFormView.vue'
import ProjectsListView from '../views/ProjectsListView.vue'
import RedirectRootView from '../views/RedirectRootView.vue'
import RegisterView from '../views/RegisterView.vue'
import ServerFormView from '../views/ServerFormView.vue'
import ServersListView from '../views/ServersListView.vue'
import StepFormView from '../views/StepFormView.vue'

export const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterView,
    meta: { guest: true },
  },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      { path: '', name: 'root', component: RedirectRootView },
      { path: 'dashboard', name: 'dashboard', component: DashboardView },
      {
        path: 'servers',
        name: 'servers',
        component: ServersListView,
        meta: { requiresAdmin: true },
      },
      {
        path: 'servers/new',
        name: 'servers-new',
        component: ServerFormView,
        meta: { requiresAdmin: true },
      },
      {
        path: 'servers/:id/edit',
        name: 'servers-edit',
        component: ServerFormView,
        meta: { requiresAdmin: true },
      },
      { path: 'projects', name: 'projects', component: ProjectsListView },
      {
        path: 'environments',
        name: 'environments-hub',
        component: EnvironmentsHubView,
      },
      {
        path: 'projects/new',
        name: 'projects-new',
        component: ProjectFormView,
        meta: { requiresAdmin: true },
      },
      {
        path: 'projects/:id/edit',
        name: 'projects-edit',
        component: ProjectFormView,
        meta: { requiresAdmin: true },
      },
      {
        path: 'projects/:projectId/environments',
        name: 'environments',
        component: EnvironmentsListView,
      },
      {
        path: 'projects/:projectId/environments/:environmentId/edit',
        name: 'environments-edit',
        component: EnvironmentFormView,
        meta: { requiresAdmin: true },
      },
      {
        path: 'environments/:environmentId/pipelines',
        name: 'pipelines',
        component: PipelinesListView,
      },
      {
        path: 'pipelines/:pipelineId',
        name: 'pipeline-detail',
        component: PipelineDetailView,
      },
      {
        path: 'pipelines/:pipelineId/steps/:stepId/edit',
        name: 'pipeline-step-edit',
        component: StepFormView,
        meta: { requiresAdmin: true },
      },
      {
        path: 'pipelines/:pipelineId/run',
        name: 'pipeline-run',
        component: PipelineRunView,
      },
      {
        path: 'executions/:executionId/monitor',
        name: 'execution-monitor',
        component: ExecutionMonitorView,
      },
    ],
  },
]
