import { NextRequest, NextResponse } from 'next/server'

import auth from '@/auth'

export async function POST(request: NextRequest) {
  try {
    const session = await auth()
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    // Check if we have the required environment variables
    if (!process.env.AWS_S3_BUCKET_NAME) {
      console.error('Missing AWS_S3_BUCKET_NAME environment variable')
      return NextResponse.json({ error: 'S3 bucket not configured' }, { status: 500 })
    }

    // Parse the form data to get the file
    const formData = await request.formData()
    const file = formData.get('file') as File

    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400 })
    }

    // Generate a unique file key for S3 using UUID
    const fileExtension = file.name.split('.').pop()
    const { v4: uuidv4 } = await import('uuid')
    const uniqueFileName = `${uuidv4()}.${fileExtension}`
    const fileKey = `uploads/${session.user.id}/${uniqueFileName}`

    // Upload file to S3 server-side
    const { S3Client, PutObjectCommand } = await import('@aws-sdk/client-s3')

    if (!process.env.AWS_ACCESS_KEY_ID) {
      throw new Error('AWS_ACCESS_KEY_ID is not defined')
    }

    if (!process.env.AWS_SECRET_ACCESS_KEY) {
      throw new Error('AWS_SECRET_ACCESS_KEY is not defined')
    }

    if (!process.env.AWS_S3_BUCKET_NAME) {
      throw new Error('AWS_S3_BUCKET_NAME is not defined')
    }
    if (!process.env.R2_ENDPOINT_URL) {
      throw new Error('R2_ENDPOINT_URL is not defined')
    }
    const s3Client = new S3Client({
      region: 'auto',
      endpoint: process.env.R2_ENDPOINT_URL,
      credentials: {
        accessKeyId: process.env.AWS_ACCESS_KEY_ID,
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
      },
    })

    // Convert file to buffer
    const fileBuffer = Buffer.from(await file.arrayBuffer())

    const command = new PutObjectCommand({
      Bucket: process.env.AWS_S3_BUCKET_NAME,
      Key: fileKey,
      Body: fileBuffer,
      ContentType: file.type,
      ContentLength: file.size,
    })

    await s3Client.send(command)

    const uploadUrl = `https://assets.gurunetwork.ai/${fileKey}`

    return NextResponse.json({
      success: true,
      fileKey,
      uploadUrl,
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type,
    })
  } catch (error) {
    console.error('Upload API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
