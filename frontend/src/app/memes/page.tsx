import { Button, Caption } from '@/components/ui'

export default function PageMemes() {
  return (
    <div>
      <Caption variant="header" size="xxl" decorated="fire" strong>
        Something Awesome <br /> Is On The Way!
      </Caption>
      <p>
        Get ready to embark on a thrilling adventure! Why not start with our quests and check back
        soon for more surprises?
      </p>
      <Button href="/">Go to Quests</Button>
    </div>
  )
}
