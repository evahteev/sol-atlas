import { useEffect, useState } from 'react'

import { useIntervalWhen } from 'rooks'

export const useTypewriterWords = (text = '', delay = 200) => {
  const [result, setResult] = useState<[string, string, string]>(['', '', ''])

  useEffect(() => {
    setResult(['', '', text])
  }, [text, delay])

  useIntervalWhen(
    () => {
      const notPrintedArr: string[] = result[2].match(/\b(\w+\W+)/g) || []

      const printed = result[0] + result[1]
      const printing = notPrintedArr.shift()
      setResult([printed, printing || '', notPrintedArr.join('')])
    },
    delay,
    !!(result[1].length || result[2].length)
  )

  return result
}

export const useTypewriter = (text = '', delay = 30) => {
  const [index, setIndex] = useState(0)
  const [result, setResult] = useState<[string, string]>(['', ''])

  useEffect(() => {
    setIndex(0)
  }, [text, delay])

  useIntervalWhen(
    () => {
      if (index >= text.length) {
        return
      }

      const [printed, notPrinted] = [text.substring(0, index + 1), text.substring(index)]
      setResult([printed, notPrinted])
      setIndex(index + 1)
    },
    delay,
    index <= text.length
  )

  return result
}
