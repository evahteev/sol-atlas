// https://nextjs.org/docs/app/building-your-application/routing/router-handlers

export const dynamic = 'force-dynamic' // defaults to auto
export async function GET() {
  return new Response('OK', {
    status: 200,
  })
}
