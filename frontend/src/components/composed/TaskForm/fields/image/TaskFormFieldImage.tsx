import { DetailedHTMLProps, FC, ImgHTMLAttributes } from 'react'

import ImageFallback from '@/components/atoms/ImageFallback'

export const TaskFormFieldImage: FC<
  DetailedHTMLProps<ImgHTMLAttributes<HTMLImageElement>, HTMLImageElement>
> = ({ src, ...props }) => {
  return <ImageFallback {...props} fallback={null} src={src} />
}
