'use client'

import styles from '../_assets/page.module.scss'

interface Message {
  id: string
  sender: string
  senderAvatar?: string
  content: string
  timestamp: string
  isRead: boolean
  type: 'direct' | 'system' | 'notification'
}

interface MessagesCardProps {
  messages: Message[]
}

export function MessagesCard({ messages }: MessagesCardProps) {
  const getMessageTypeIcon = (type: string) => {
    switch (type) {
      case 'direct':
        return '💬'
      case 'system':
        return '⚙️'
      case 'notification':
        return '🔔'
      default:
        return '📧'
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'direct':
        return '#22D49F'
      case 'system':
        return '#9488F0'
      case 'notification':
        return '#FAA61A'
      default:
        return '#64748b'
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

  return (
    <div className={styles.profileCard}>
      <div className={styles.messagesHeader}>
        <h3 className={styles.profileTitle}>Messages</h3>
        <div className={styles.messagesStats}>
          <span className={styles.unreadCount}>
            {messages.filter((m) => !m.isRead).length} unread
          </span>
          <span className={styles.totalMessages}>{messages.length} total</span>
        </div>
      </div>

      <div className={styles.messagesList}>
        {messages.map((message) => (
          <div
            key={message.id}
            className={`${styles.messageItem} ${!message.isRead ? styles.messageUnread : ''}`}>
            <div className={styles.messageIcon}>
              <span className={styles.messageTypeIcon}>{getMessageTypeIcon(message.type)}</span>
              {!message.isRead && <div className={styles.unreadIndicator} />}
            </div>

            <div className={styles.messageContent}>
              <div className={styles.messageHeader}>
                <span className={styles.messageSender}>{message.sender}</span>
                <span className={styles.messageTime}>{formatTimestamp(message.timestamp)}</span>
              </div>

              <p className={styles.messageText}>{message.content}</p>

              <div className={styles.messageFooter}>
                <span className={styles.messageType} style={{ color: getTypeColor(message.type) }}>
                  {message.type.charAt(0).toUpperCase() + message.type.slice(1)}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className={styles.messagesActions}>
        <button className={styles.viewAllButton}>View All Messages</button>
        <button className={styles.composeButton}>New Message</button>
      </div>
    </div>
  )
}
