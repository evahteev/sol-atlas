import { Button, Caption } from '@/components/ui'

export default function NotFound() {
  return (
    <div>
      <Caption variant="header" size="xxl" decorated="fire" strong>
        Resource Not Found
      </Caption>
      <Button href="/">Go to Main Page</Button>
    </div>
  )
}
