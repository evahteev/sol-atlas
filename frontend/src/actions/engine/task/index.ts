'use server'

import { getFlowClient } from '@/services/flow'
import { components, operations } from '@/services/flow/schema'

export async function getTaskList(params?: {
  query?: operations['filter_tasks_engine_task_post']['parameters']['query']
  body?: components['schemas']['Body_filter_tasks_engine_task_post']
}) {
  const client = getFlowClient()

  const { data, error } = await client.POST('/engine/task', {
    params: { query: params?.query },
    body: params?.body,
    next: { revalidate: 10, tags: ['all', 'flowClient', 'flowClientEngine', 'getTaskList'] },
  })
  if (error) {
    console.error('Error in Engine Task List:', error)
    throw new Error('Error in Engine Task List')
  }
  return data
}

// export async function getTaskCount(body?: components['schemas']['TaskQueryDto']) {
//   const client = getFlowClient()
//
//   const { data, error } = await client.POST('/task/count', {
//     body,
//     next: { revalidate: 10, tags: ['all', 'flowClient', 'flowClientEngine', 'getTaskCount'] },
//   })
//   if (error) {
//     console.error('Error in Engine Task List:', error)
//     throw new Error('Error in Engine Task List')
//   }
//   return data
// }

// export async function getTask(id: string) {
//   const client = getFlowClient()
//
//   const { data, error } = await client.GET('/engine/task/{id}', {
//     params: {
//       path: {
//         id,
//       },
//     },
//     next: { revalidate: 60, tags: ['all', 'flowClient', 'flowClientEngine', 'getTask'] },
//   })
//   if (error) {
//     console.error('Error in Engine Task Get By Id:', error)
//     throw new Error('Error in Engine Task Get By Id')
//   }
//   return data
// }

// export async function getTaskVariables(id: string) {
//   const client = getFlowClient()
//
//   const { data, error } = await client.GET('/engine/task/{id}/variables', {
//     params: {
//       path: {
//         id,
//       },
//     },
//     next: { revalidate: 60, tags: ['all', 'flowClient', 'flowClientEngine', 'getTaskVariables'] },
//   })
//   if (error) {
//     console.error('Error in Engine Task Variables:', error)
//     throw new Error('Error in Engine Task Variables')
//   }
//   return data
// }
