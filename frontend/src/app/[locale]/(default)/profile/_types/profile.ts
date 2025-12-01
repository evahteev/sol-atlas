export interface UserProfile {
  id: string
  name: string
  email: string
  avatar: string
  walletAddress: string
  telegramId: string
  rank: number
  level: number
  experience: number
  caps: number
  joinDate: string
  stats: ProfileStats
  rankHistory: RankHistory[]
  capsHistory: CapsHistory[]
  certificates: Certificate[]
  learningProgress: LearningProgress[]
  badges: Badge[]
  achievements: Achievement[]
  services: Service[]
  availableActions: Action[]
  messages: Message[]
  posts: Post[]
}

export interface ProfileStats {
  totalActions: number
  successfulTasks: number
  communityContributions: number
  referrals: number
  averageRating: number
  responseTime: number
}

export interface RankHistory {
  date: string
  rank: number
}

export interface CapsHistory {
  date: string
  caps: number
}

export interface Certificate {
  id: string
  name: string
  description: string
  issuedDate: string
  status: 'completed' | 'in-progress' | 'available'
  progress?: number
}

export interface LearningProgress {
  courseId: string
  courseName: string
  progress: number
  totalLessons: number
  completedLessons: number
}

export interface Badge {
  id: string
  name: string
  description: string
  icon: string
  earnedDate: string
  rarity: 'common' | 'rare' | 'epic' | 'legendary'
}

export interface Achievement {
  id: string
  name: string
  description: string
  icon: string
  earnedDate: string
  points: number
}

export interface Service {
  id: string
  name: string
  icon: string
  status: 'active' | 'inactive' | 'pending'
  plan: string
  nextBilling?: string
}

export interface Action {
  id: string
  title: string
  description: string
  icon: string
  category: string
  difficulty: 'Easy' | 'Medium' | 'Hard'
  reward: number
  estimatedTime: string
}

export interface Message {
  id: string
  sender: string
  senderAvatar?: string
  content: string
  timestamp: string
  isRead: boolean
  type: 'direct' | 'system' | 'notification'
}

export interface Post {
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

// Hardcoded profile data for development - Updated to match Figma design
export const HARDCODED_PROFILE_DATA: UserProfile = {
  id: '1',
  name: 'Alex Doomguy',
  email: 'alex.doomguy@example.com',
  avatar: '/api/avatar/alex',
  walletAddress: '0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6',
  telegramId: '@alexdoomguy',
  rank: 12,
  level: 4.8,
  experience: 34540,
  caps: 34540,
  joinDate: '2025-08-04',
  stats: {
    totalActions: 47982,
    successfulTasks: 47982,
    communityContributions: 156,
    referrals: 8,
    averageRating: 4.8,
    responseTime: 2.3,
  },
  rankHistory: [
    { date: '2024-01-15', rank: 150 },
    { date: '2024-02-15', rank: 120 },
    { date: '2024-03-15', rank: 95 },
    { date: '2024-04-15', rank: 78 },
    { date: '2024-05-15', rank: 45 },
    { date: '2024-06-15', rank: 32 },
    { date: '2024-07-15', rank: 25 },
    { date: '2024-08-15', rank: 15 },
  ],
  capsHistory: [
    { date: '2024-01-15', caps: 0 },
    { date: '2024-02-15', caps: 150 },
    { date: '2024-03-15', caps: 320 },
    { date: '2024-04-15', caps: 480 },
    { date: '2024-05-15', caps: 650 },
    { date: '2024-06-15', caps: 820 },
    { date: '2024-07-15', caps: 1050 },
    { date: '2024-08-15', caps: 1250 },
  ],
  certificates: [
    {
      id: 'cert-1',
      name: 'Blockchain Fundamentals',
      description: 'Complete understanding of blockchain technology basics',
      issuedDate: '2024-03-20',
      status: 'completed',
    },
    {
      id: 'cert-2',
      name: 'Smart Contract Development',
      description: 'Advanced smart contract programming skills',
      issuedDate: '2024-05-15',
      status: 'completed',
    },
    {
      id: 'cert-3',
      name: 'DeFi Protocols',
      description: 'Deep dive into decentralized finance protocols',
      issuedDate: '2024-07-10',
      status: 'in-progress',
      progress: 75,
    },
    {
      id: 'cert-4',
      name: 'AI Integration',
      description: 'AI-powered blockchain solutions',
      issuedDate: '',
      status: 'available',
    },
  ],
  learningProgress: [
    {
      courseId: 'course-1',
      courseName: 'Base level',
      progress: 20,
      totalLessons: 100,
      completedLessons: 20,
    },
    {
      courseId: 'course-2',
      courseName: 'Expert level',
      progress: 0,
      totalLessons: 100,
      completedLessons: 0,
    },
  ],
  badges: [
    {
      id: 'badge-1',
      name: 'First Steps',
      description: 'Completed your first task',
      icon: '🎯',
      earnedDate: '2024-01-20',
      rarity: 'common',
    },
    {
      id: 'badge-2',
      name: 'Task Master',
      description: 'Completed 100 tasks',
      icon: '🏆',
      earnedDate: '2024-04-15',
      rarity: 'rare',
    },
    {
      id: 'badge-3',
      name: 'Community Hero',
      description: 'Made 20 community contributions',
      icon: '🌟',
      earnedDate: '2024-06-20',
      rarity: 'epic',
    },
    {
      id: 'badge-4',
      name: 'Legendary Warrior',
      description: 'Reached legendary status',
      icon: '⚔️',
      earnedDate: '2025-08-01',
      rarity: 'legendary',
    },
  ],
  achievements: [
    {
      id: 'ach-1',
      name: 'Rising Star',
      description: 'Reached top 50 ranking',
      icon: '⭐',
      earnedDate: '2024-05-10',
      points: 100,
    },
    {
      id: 'ach-2',
      name: 'CAPS Collector',
      description: 'Accumulated 1000 CAPS',
      icon: '💰',
      earnedDate: '2024-07-05',
      points: 250,
    },
    {
      id: 'ach-3',
      name: 'Task Master',
      description: 'Completed 1000 tasks',
      icon: '🎯',
      earnedDate: '2025-01-15',
      points: 500,
    },
    {
      id: 'ach-4',
      name: 'Community Leader',
      description: 'Helped 100 users',
      icon: '👑',
      earnedDate: '2025-07-20',
      points: 1000,
    },
  ],
  services: [
    {
      id: 'service-1',
      name: 'AI Assistant Pro',
      icon: '🤖',
      status: 'active',
      plan: 'Premium',
      nextBilling: 'Feb 15, 2025',
    },
    {
      id: 'service-2',
      name: 'Automated Trading',
      icon: '📈',
      status: 'active',
      plan: 'Advanced',
      nextBilling: 'Feb 20, 2025',
    },
    {
      id: 'service-3',
      name: 'Portfolio Analytics',
      icon: '📊',
      status: 'pending',
      plan: 'Basic',
      nextBilling: 'Feb 10, 2025',
    },
    {
      id: 'service-4',
      name: 'Security Monitoring',
      icon: '🛡️',
      status: 'inactive',
      plan: 'Standard',
    },
  ],
  availableActions: [
    {
      id: 'action-1',
      title: 'Complete KYC Verification',
      description: 'Verify your identity to unlock premium features',
      icon: '🔒',
      category: 'Security',
      difficulty: 'Easy',
      reward: 100,
      estimatedTime: '5 min',
    },
    {
      id: 'action-2',
      title: 'Stake 1000 GURU Tokens',
      description: 'Stake tokens to earn rewards and boost your ranking',
      icon: '💎',
      category: 'Staking',
      difficulty: 'Medium',
      reward: 500,
      estimatedTime: '10 min',
    },
    {
      id: 'action-3',
      title: 'Refer 5 New Users',
      description: 'Share the platform with friends and earn bonuses',
      icon: '👥',
      category: 'Referral',
      difficulty: 'Hard',
      reward: 1000,
      estimatedTime: '1 week',
    },
    {
      id: 'action-4',
      title: 'Complete Trading Course',
      description: 'Learn advanced trading strategies',
      icon: '📚',
      category: 'Education',
      difficulty: 'Medium',
      reward: 250,
      estimatedTime: '2 hours',
    },
  ],
  messages: [
    {
      id: 'msg-1',
      sender: 'System Admin',
      content: 'Welcome to Axioma! Your account has been successfully verified.',
      timestamp: '2025-01-19T10:30:00Z',
      isRead: false,
      type: 'system',
    },
    {
      id: 'msg-2',
      sender: 'Sarah Chen',
      content:
        'Hey Alex! Thanks for the help with the smart contract audit. Really appreciate your expertise!',
      timestamp: '2025-01-18T15:45:00Z',
      isRead: true,
      type: 'direct',
    },
    {
      id: 'msg-3',
      sender: 'Notification Bot',
      content: 'You have earned 250 CAPS for completing the Trading Course action!',
      timestamp: '2025-01-18T09:20:00Z',
      isRead: false,
      type: 'notification',
    },
    {
      id: 'msg-4',
      sender: 'Mike Rodriguez',
      content:
        "Would love to collaborate on the upcoming DeFi project. Let me know if you're interested!",
      timestamp: '2025-01-17T14:15:00Z',
      isRead: true,
      type: 'direct',
    },
    {
      id: 'msg-5',
      sender: 'Community Manager',
      content: 'Congratulations on reaching Legendary Warrior status! 🎉',
      timestamp: '2025-01-16T12:00:00Z',
      isRead: true,
      type: 'system',
    },
  ],
  posts: [
    {
      id: 'post-1',
      title: 'Understanding Smart Contract Security Best Practices',
      content:
        "After years of auditing smart contracts, I've compiled a comprehensive guide on the most critical security practices every developer should follow. From reentrancy attacks to integer overflows, here are the top vulnerabilities to watch out for...",
      timestamp: '2025-01-19T08:00:00Z',
      likes: 127,
      comments: 23,
      shares: 15,
      category: 'Education',
      status: 'published',
      tags: ['blockchain', 'security', 'smartcontracts', 'defi', 'audit'],
    },
    {
      id: 'post-2',
      title: 'My Journey to Legendary Warrior Status',
      content:
        "Just hit a major milestone! Reflecting on the path from newcomer to Legendary Warrior. It's been an incredible journey of learning, contributing, and growing with this amazing community. Here's what I've learned along the way...",
      timestamp: '2025-01-18T16:30:00Z',
      likes: 89,
      comments: 34,
      shares: 8,
      category: 'Personal',
      status: 'published',
      tags: ['milestone', 'community', 'growth', 'reflection'],
    },
    {
      id: 'post-3',
      title: 'DeFi Protocol Analysis: Compound vs Aave',
      content:
        'Deep dive into two of the most popular lending protocols in DeFi. Comparing their mechanisms, security models, and user experience. Draft analysis of their latest updates and what it means for users...',
      timestamp: '2025-01-17T11:45:00Z',
      likes: 0,
      comments: 0,
      shares: 0,
      category: 'Analysis',
      status: 'draft',
      tags: ['defi', 'compound', 'aave', 'lending', 'analysis'],
    },
    {
      id: 'post-4',
      title: 'Building Cross-Chain Applications: Lessons Learned',
      content:
        'After working on several cross-chain projects, I want to share some key insights about the challenges and solutions in building applications that work seamlessly across multiple blockchains...',
      timestamp: '2025-01-16T13:20:00Z',
      likes: 156,
      comments: 41,
      shares: 22,
      category: 'Technical',
      status: 'published',
      tags: ['crosschain', 'development', 'blockchain', 'interoperability'],
    },
  ],
}
