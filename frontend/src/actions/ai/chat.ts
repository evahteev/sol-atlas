import { Session } from '@/lib/session'
import { FlowClientObject } from '@/services/flow'
import { components } from '@/services/flow/schema'

export const fetchAIChatAnswer = async (
  question: string,
  session: Session | null
): Promise<{ question: string; answer: string } | null> => {
  if (!question) {
    return null
  }
  if (!session?.access_token) {
    return { question, answer: `Please, authorize to chat with me` }
  }
  const nextjsServerOrigin = process.env.NEXTJS_SERVER_LOCAL_ORIGIN || 'https://localhost:3000'

  return fetch(
    `${typeof window === 'undefined' ? nextjsServerOrigin : window.location.origin}/api/flowapi/api/chat`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question }),
      next: {
        revalidate: 3,
      },
    }
  )
    .then((res) =>
      res?.ok
        ? res?.json()
        : { question, answer: `Sorry, I've got error: ${res.statusText} (${res.status})` }
    )
    .then((res) => ({ question, answer: res.answer }))
    .catch((e) => {
      console.error(e)
      return { question, answer: `Sorry, I've got error: ${e.message}` }
    })
}

export const fetchAIChatProcess = async ({
  session,
}: {
  session: Session | null
}): Promise<components['schemas']['ProcessInstanceSchema'] | null> => {
  if (!session?.access_token) {
    return null
  }
  const nextjsServerOrigin = process.env.NEXTJS_SERVER_LOCAL_ORIGIN || 'https://localhost:3000'

  const chatinstance = (
    await FlowClientObject.engine.process.instance.list({
      businessKey: `${session.user?.id}-active-dm`,
      session,
    })
  )?.find((x) => x.processDefinitionKey === 'chatbot_thread')

  if (chatinstance) {
    return chatinstance
  }

  console.log('CHAT START CHART START CHAT START')

  return fetch(
    `${typeof window === 'undefined' ? nextjsServerOrigin : window.location.origin}/api/flowapi/api/chat/start`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ messages: [] }),
      next: {
        revalidate: 3,
      },
    }
  )
    .then((res) => (res?.ok ? res?.json() : null))
    .catch((e) => {
      console.error(e)
      return null
    })
}
