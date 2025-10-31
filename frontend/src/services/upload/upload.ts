export interface UploadResponse {
  success: boolean
  fileKey: string
  uploadUrl: string
  fileName: string
  fileSize: number
  fileType: string
}

export interface UploadProgress {
  loaded: number
  total: number
  percentage: number
}

export async function uploadFile(file: File): Promise<string> {
  try {
    // Create FormData
    const formData = new FormData()
    formData.append('file', file)

    // Upload to our API endpoint
    const response = await fetch('/api/upload', {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Upload failed')
    }

    const result: UploadResponse = await response.json()

    if (!result.success) {
      throw new Error('Upload failed')
    }

    return result.uploadUrl
  } catch (error) {
    console.error('File upload error:', error)
    throw error
  }
}

// Legacy functions for backward compatibility (if needed)
export async function getPresignedUrl(): Promise<UploadResponse> {
  throw new Error('Presigned URLs are no longer supported. Use server-side uploads.')
}

export async function uploadToS3(): Promise<void> {
  throw new Error('Direct S3 uploads are no longer supported. Use server-side uploads.')
}
