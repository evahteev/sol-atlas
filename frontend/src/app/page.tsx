import Intro from '@/components/composed/Intro'

import PageIndexRedirect from './_redirect'

export default function PageIndex() {
  return (
    <>
      <Intro>{process.env.NEXT_PUBLIC_APP_INTRO}</Intro>
      <PageIndexRedirect />
    </>
  )
}
