// https://nextjs.org/docs/app/building-your-application/routing/router-handlers

export const dynamic = 'force-dynamic' // defaults to auto
export async function GET(request: Request) {
  return new Response(
    `{
      ${[...request.headers.entries()]
        .map(([key, value]) => `${key}: "${value.toString()}"`)
        .join(',\r\n      ')}
}`,
    {
      status: 200,
    }
  )
}
