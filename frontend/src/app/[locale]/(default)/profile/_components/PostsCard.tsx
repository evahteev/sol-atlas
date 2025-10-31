'use client'

import styles from '../_assets/page.module.scss'

interface Post {
  id: string
  title: string
  content: string
  timestamp: string
  likes: number
  comments: number
  shares: number
  category: string
  status: 'published' | 'draft' | 'pending'
  tags: string[]
}

interface PostsCardProps {
  posts: Post[]
}

export function PostsCard({ posts }: PostsCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'published':
        return '#22D49F'
      case 'draft':
        return '#64748b'
      case 'pending':
        return '#FAA61A'
      default:
        return '#64748b'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'published':
        return '✅'
      case 'draft':
        return '📝'
      case 'pending':
        return '⏳'
      default:
        return '📄'
    }
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))

    if (diffInHours < 1) return 'Just now'
    if (diffInHours < 24) return `${diffInHours}h ago`
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}d ago`
    return date.toLocaleDateString()
  }

  const truncateContent = (content: string, maxLength: number = 120) => {
    if (content.length <= maxLength) return content
    return content.substring(0, maxLength) + '...'
  }

  return (
    <div className={styles.profileCard}>
      <div className={styles.postsHeader}>
        <h3 className={styles.profileTitle}>Posts</h3>
        <div className={styles.postsStats}>
          <span className={styles.publishedCount}>
            {posts.filter((p) => p.status === 'published').length} published
          </span>
          <span className={styles.totalPosts}>{posts.length} total</span>
        </div>
      </div>

      <div className={styles.postsList}>
        {posts.map((post) => (
          <div key={post.id} className={styles.postItem}>
            <div className={styles.postHeader}>
              <div className={styles.postTitleSection}>
                <h4 className={styles.postTitle}>{post.title}</h4>
                <div className={styles.postMeta}>
                  <span
                    className={styles.postStatus}
                    style={{ color: getStatusColor(post.status) }}>
                    {getStatusIcon(post.status)}{' '}
                    {post.status.charAt(0).toUpperCase() + post.status.slice(1)}
                  </span>
                  <span className={styles.postTime}>{formatTimestamp(post.timestamp)}</span>
                </div>
              </div>
            </div>

            <p className={styles.postContent}>{truncateContent(post.content)}</p>

            <div className={styles.postTags}>
              {post.tags.slice(0, 3).map((tag, index) => (
                <span key={index} className={styles.postTag}>
                  #{tag}
                </span>
              ))}
              {post.tags.length > 3 && (
                <span className={styles.moreTags}>+{post.tags.length - 3} more</span>
              )}
            </div>

            <div className={styles.postFooter}>
              <div className={styles.postEngagement}>
                <span className={styles.engagementItem}>👍 {post.likes}</span>
                <span className={styles.engagementItem}>💬 {post.comments}</span>
                <span className={styles.engagementItem}>🔄 {post.shares}</span>
              </div>
              <span className={styles.postCategory}>{post.category}</span>
            </div>
          </div>
        ))}
      </div>

      <div className={styles.postsActions}>
        <button className={styles.viewAllButton}>View All Posts</button>
        <button className={styles.createPostButton}>Create New Post</button>
      </div>
    </div>
  )
}
