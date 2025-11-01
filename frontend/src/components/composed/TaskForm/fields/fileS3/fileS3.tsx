import { FC, useState } from 'react'

import { FileAsset } from '@/components/atoms/FileAsset/FileAsset'
import FormField from '@/components/composed/FormField'
import { FormFieldFileProps } from '@/components/composed/FormField/FormFieldFile'
import Show from '@/components/ui/Show'
import { uploadFile } from '@/services/upload/upload'

import styles from './fileS3.module.scss'

type FileWithProgress = {
  file?: File
  name: string
  size: number
  type: string
  url?: string | null
  status: 'pending' | 'uploading' | 'completed' | 'error'
  error?: string
}

export const TaskFormFieldFileS3: FC<
  FormFieldFileProps & {
    onPending: (input: HTMLInputElement) => void
    onComplete: (input: HTMLInputElement) => void
  }
> = ({ onPending, onComplete, ...props }) => {
  const [files, setFiles] = useState<FileWithProgress[]>([
    {
      file: undefined,
      name: '',
      size: 0,
      type: '',
      status: 'completed',
      url: `${props.defaultValue}` || null,
    },
  ])

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    props?.onChange?.(e)
    const eventTargetInput = e.currentTarget
    onPending?.(eventTargetInput)

    const selectedFiles = [...(e.target.files ?? [])]

    if (selectedFiles.length === 0) {
      setFiles([])
      props?.onValueChange?.([])
      onComplete(eventTargetInput)
      return
    }

    const newFiles: FileWithProgress[] = selectedFiles.map((file) => ({
      file,
      name: file.name,
      type: file.type,
      size: file.size,
      status: 'pending',
      url: null,
    }))

    setFiles(newFiles)

    // Upload files automatically using server-side upload
    const uploadPromises = newFiles.map(async (fileWithProgress, index) => {
      try {
        setFiles((prev) => {
          const next = [...prev]
          next[index] = { ...fileWithProgress, status: 'uploading' }
          return next
        })

        const url = await uploadFile(fileWithProgress.file!)

        setFiles((prev) => {
          const next = [...prev]
          next[index] = { ...fileWithProgress, status: 'completed', url }
          return next
        })

        return url
      } catch (error) {
        setFiles((prev) => {
          const next = [...prev]
          next[index] = {
            ...fileWithProgress,
            status: 'error' as const,
            error: (error as Error).message,
          }
          return next
        })
        throw error
      }
    })

    try {
      const urls = await Promise.all(uploadPromises)
      props?.onValueChange?.(urls)
    } catch (error) {
      console.error('File upload error:', error)
      // Keep the files in the state but mark them as errored
    }

    onComplete(eventTargetInput)
  }

  return (
    <FormField
      type="file"
      {...props}
      required={undefined}
      name={undefined}
      onValueChange={undefined}
      onChange={handleFileChange}>
      <input
        type="hidden"
        required={props.required}
        name={props.name}
        value={`${files.map((file) => file.url).join(',')}` || props.defaultValue}
      />

      <Show if={files.length}>
        <span className={styles.files}>
          <ul className={styles.list}>
            {files?.map((file, idx) => {
              return (
                <li key={idx} className={styles.item}>
                  <FileAsset
                    className={styles.entry}
                    file={{ ...file, name: file.name || file.url || '?' }}
                    isLoading={file.status === 'uploading'}
                    isPending={file.status === 'pending'}
                    isError={file.status === 'error'}
                    image={file.url || null} // Use url if available, otherwise null
                  />
                </li>
              )
            })}
          </ul>
        </span>
      </Show>
    </FormField>
  )
}
