import { NextResponse } from 'next/server'

import { AppFetchProps, appFetch } from '@/services/warehouse-redash/fetch'

export async function POST(request: Request) {
  const {
    url: appFetchUrl,
    data: appFetchData,
    ...restAppFetchProps
  } = (await request.json()) as AppFetchProps
  try {
    const res = await appFetch({
      url: `${process.env.WAREHOUSE_API_HOST}/api${appFetchUrl}`,
      method: appFetchData ? 'POST' : 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: process.env.WAREHOUSE_API_KEY ?? '',
      },
      data: appFetchData,
      ...restAppFetchProps,
    })
    const body = await res.json()
    return NextResponse.json(body)
  } catch (error) {
    console.error({ error })
    return NextResponse.json({ error }, { status: 500 })
  }
}
