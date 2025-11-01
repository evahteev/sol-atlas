import { FC } from 'react'

import { hashOfString } from '@/utils/strings'

type SimpleLineChartProps = {
  values?: number[]
  color?: string
  stroke?: number
  className?: string
  gradient?: boolean
  zeroBased?: boolean
  smooth?: boolean // conditional chart path smoothing
}

type TChartCoord = [number, number]

const calcLine = (pointA: TChartCoord, pointB: TChartCoord): { length: number; angle: number } => {
  const lengthX = pointB[0] - pointA[0]
  const lengthY = pointB[1] - pointA[1]
  return {
    length: Math.sqrt(Math.pow(lengthX, 2) + Math.pow(lengthY, 2)),
    angle: Math.atan2(lengthY, lengthX),
  }
}

const calcKeyPoint = (
  current: TChartCoord,
  previous: TChartCoord,
  next: TChartCoord,
  reverse?: boolean
): TChartCoord => {
  const cur = current
  const prev = previous ? previous : cur
  const nxt = next ? next : cur
  const smoothing = 0.2
  const o = calcLine(prev, nxt)
  const rev = reverse ? Math.PI : 0

  const x = cur[0] + Math.cos(o.angle + rev) * o.length * smoothing
  const y = cur[1] + Math.sin(o.angle + rev) * o.length * smoothing

  return [x, y]
}

const renderPath = (points: number[], smooth?: boolean): string => {
  const mappedPoints: TChartCoord[] = points.map((val, idx) => [idx, val])

  let path = `${mappedPoints}`

  if (smooth) {
    path = mappedPoints.reduce((accumulate, val, idx, arr) => {
      if (idx > 0) {
        const cs = calcKeyPoint(arr[idx - 1], arr[idx - 2], val)
        const ce = calcKeyPoint(val, arr[idx - 1], arr[idx + 1], true)
        return `${accumulate} C ${cs[0]},${cs[1]} ${ce[0]},${ce[1]} ${val[0]},${val[1]}`
      } else {
        return ''
      }
    }, '')
  }

  return `M -1,${points[0] || 0} ${path} H ${points.length} V 200 H -1 Z`
}

export const SimpleLineChart: FC<SimpleLineChartProps> = ({
  values,
  color = '#fff',
  stroke = 1,
  className,
  gradient,
  zeroBased = true,
  smooth,
}) => {
  if (!values?.length) {
    return null
  }

  const diff = zeroBased ? 0 : Math.min(...values) || 0
  const max = (Math.max(...values) || 1) - diff

  const percentsOfMax: Array<number> = values.map(
    // creating path points with percentage value as Y
    (item: number) => ((max - item + diff) / (max || 1)) * 100
  )

  const pathDraw = renderPath(percentsOfMax, smooth)

  const hash = hashOfString(`${values.join(',')}-${className}`)

  return (
    // svg template with values.length as width and 100 as height for 100% in viewBox
    // no width and height set, resized by styles
    // using preserveAspectRatio and vectorEffect for correct svg scaling without squeezed and smashed
    <svg
      preserveAspectRatio="none meet"
      viewBox={`0 -10 ${values.length - 1} 120`}
      className={className}
      width="100"
      height="100">
      <path
        stroke={color}
        strokeWidth={stroke}
        d={pathDraw}
        vectorEffect="non-scaling-stroke"
        fill={gradient ? `url(#simplechart-bg-${hash})` : 'none'}
      />
      {gradient && (
        <defs>
          <linearGradient
            id={`simplechart-bg-${hash}`}
            gradientUnits="userSpaceOnUse"
            x1="0"
            y1="0"
            x2="0"
            y2="80">
            <stop className="gradStart" offset="0" stopColor="#000" stopOpacity="0" />
            <stop className="gradEnd" offset="1" stopColor="#000" stopOpacity="0" />
          </linearGradient>
        </defs>
      )}
    </svg>
  )
}
