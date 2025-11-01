import {
  getArtById,
  getArtFinances,
  getArts,
  getArtsNext,
  getArtsRecommended,
  getCollectionById,
} from '@/actions/arts'
import { getConfigByKey } from '@/actions/config'
import {
  completeTask,
  deleteProcessInstanceById,
  getProcessDefinitionByKey,
  getProcessDefinitionList,
  getProcessInstanceById,
  getProcessInstanceTasks,
  getProcessInstanceVariables,
  getProcessInstances,
  getTaskDeployedForm,
  getTaskVariables,
  getTasks,
  proxyGet,
  proxyPut,
  startProcessInstanceByKey,
} from '@/actions/engine'
import {
  getProcessDefinitionDeployedStartForm,
  getProcessDefinitionStartFormVariables,
} from '@/actions/engine/process/definition'
import { getFlowById, getFlows } from '@/actions/flows'
import { getLeaderBoardArts, getLeaderBoardUser, getLeaderBoardUsers } from '@/actions/leaderboard'
import { createUser, getUser, loginUser, refreshToken, updateUser } from '@/actions/user'

export const FlowClientObject = {
  config: { get: getConfigByKey },
  flows: {
    list: getFlows,
    get: getFlowById,
  },
  user: {
    create: createUser,
    get: getUser,
    login: loginUser,
    update: updateUser,
    refreshToken: refreshToken,
  },
  engine: {
    process: {
      definitions: {
        list: getProcessDefinitionList,
        get: getProcessDefinitionByKey,
        start: startProcessInstanceByKey,
        variables: getProcessDefinitionStartFormVariables,
        form: getProcessDefinitionDeployedStartForm,
        delete: deleteProcessInstanceById,
      },
      instance: {
        list: getProcessInstances,
        get: getProcessInstanceById,
        delete: deleteProcessInstanceById,
        task: {
          list: getProcessInstanceTasks,
        },
        variables: {
          list: getProcessInstanceVariables,
        },
      },
    },
    task: {
      list: getTasks,
      variables: {
        list: getTaskVariables,
      },
      form: getTaskDeployedForm,
      complete: completeTask,
    },
    proxy: { get: proxyGet, put: proxyPut },
  },
  arts: {
    get: getArtById,
    list: getArts,
    next: getArtsNext,
    recommended: getArtsRecommended,
    finances: getArtFinances,
    collection: getCollectionById,
  },
  leaderboard: {
    users: {
      list: getLeaderBoardUsers,
      get: getLeaderBoardUser,
    },
    arts: {
      list: getLeaderBoardArts,
    },
  },
}
