# Knowledge Base Gathering System - Product Requirements Document

**Version:** 1.0  
**Date:** October 24, 2025  
**Status:** Ready for Implementation  
**Priority:** High  

---

## 📋 Executive Summary

This document outlines the requirements for implementing a comprehensive Knowledge Base Gathering System that transforms luka_bot into a community-driven content curation platform. The system will automatically analyze user-submitted content, evaluate its usefulness, and facilitate a moderation workflow for adding valuable content to the knowledge base.

### Key Features
- **Automatic Content Analysis**: AI-powered evaluation of attachments, links, and messages
- **Usefulness Scoring**: 10-point scale rating system (-10 to +10)
- **Moderation Workflow**: Camunda BPMN-based approval process
- **Atlas Rewards System**: Token-based incentives for quality contributions
- **Multi-Platform Support**: Twitter, Telegram channels, websites, attachments
- **Guest & Authenticated Modes**: Different access levels with wallet integration

---

## 🎯 Business Objectives

### Primary Goals
1. **Content Quality**: Ensure only high-quality, useful content enters the knowledge base
2. **Community Engagement**: Incentivize users to contribute valuable resources
3. **Scalable Moderation**: Automate initial screening while maintaining human oversight
4. **Multi-Platform Integration**: Support content from various sources (Twitter, Telegram, web)

### Success Metrics
- **Content Quality**: >80% of approved submissions rated 7+ on usefulness scale
- **User Engagement**: 50% increase in active contributors within 3 months
- **Moderation Efficiency**: 70% reduction in manual review time
- **Platform Coverage**: Support for 5+ content types by MVP launch

---

## 🏗️ System Architecture

### Core Components

#### 1. **Content Detection & Analysis Engine**
- **Location**: `luka_bot/services/content_analysis_service.py`
- **Purpose**: Automatically detect and analyze submitted content
- **Integration**: Extends existing group message handler

#### 2. **Usefulness Scoring System**
- **Location**: `luka_bot/services/scoring_service.py`
- **Purpose**: AI-powered content evaluation with 10-point scale
- **Integration**: LLM service with custom scoring prompts

#### 3. **Moderation Workflow Engine**
- **Location**: Camunda BPMN processes
- **Purpose**: Automated approval workflow with human oversight
- **Integration**: Existing Camunda service infrastructure

#### 4. **Atlas Rewards System**
- **Location**: `luka_bot/services/rewards_service.py`
- **Purpose**: Token-based incentive system
- **Integration**: Solana wallet connect integration

#### 5. **Multi-Platform Content Processors**
- **Location**: External workers (Twitter, Telegram, Web)
- **Purpose**: Extract and process content from various sources
- **Integration**: Camunda process orchestration

---

## 📱 User Experience Flows

### 1. **Group Chat Content Submission**

```
User posts attachment/link in group
    ↓
Bot detects content type
    ↓
AI analyzes content (usefulness score)
    ↓
If score ≥ 7:
    Bot asks: "Add to knowledge base?"
    ↓
User confirms → Moderation workflow starts
    ↓
Moderator reviews → Approves/Rejects
    ↓
If approved: Added to KB + Atlas rewards
```

### 2. **Private Chat Submission**

```
User sends content to bot in DM
    ↓
Bot analyzes content
    ↓
If score ≥ 7:
    Bot: "Submit for moderation?"
    ↓
User confirms → Submission form
    ↓
Moderator reviews → Approves/Rejects
    ↓
If approved: Added to KB + Atlas rewards
```

### 3. **Guest Mode (Web Interface)**

```
Guest searches knowledge base
    ↓
Finds relevant content
    ↓
Can submit links for review
    ↓
Must sign in for full submission
    ↓
Wallet connect → Full submission workflow
```

---

## 🔧 Technical Requirements

### 1. **Content Detection & Analysis**

#### **Supported Content Types**
- **Attachments**: PDF, DOC, TXT, images, videos
- **Links**: Twitter posts, Telegram channels, websites
- **Messages**: Text content with embedded links
- **Forwarded Content**: From channels, groups, users

#### **Analysis Pipeline**
```python
class ContentAnalysisService:
    async def analyze_content(self, content: ContentItem) -> AnalysisResult:
        # 1. Extract content (text, metadata, source)
        # 2. Run AI analysis for usefulness
        # 3. Generate score (-10 to +10)
        # 4. Determine if worthy of submission
        # 5. Return analysis result
```

#### **Scoring Criteria**
- **Relevance**: How well content matches knowledge base topics
- **Quality**: Accuracy, completeness, clarity
- **Uniqueness**: Novel information not already in KB
- **Authority**: Source credibility and expertise
- **Timeliness**: Current and up-to-date information

### 2. **Moderation Workflow (Camunda BPMN)**

#### **Process Flow**
```
Content Submission
    ↓
AI Pre-screening (score ≥ 7)
    ↓
Moderator Review Task
    ↓
[Moderator Actions]
    ├─ Approve → Add to KB + Rewards
    ├─ Reject → Notify user
    └─ Request Changes → Send back to user
    ↓
Final Decision → Update KB + Notify user
```

#### **Task Variables**
- `content_url`: Link to submitted content
- `content_type`: Type of content (link, attachment, etc.)
- `usefulness_score`: AI-generated score
- `submitted_by`: User who submitted
- `atlas_amount`: Calculated reward amount
- `moderator_comments`: Optional feedback
- `action_approve`: Approve button
- `action_reject`: Reject button
- `action_modify`: Request changes button

### 3. **Atlas Rewards System**

#### **Reward Calculation**
```python
def calculate_atlas_reward(score: int, content_type: str, user_reputation: int) -> int:
    base_reward = score * 10  # 10 Atlas per point
    type_multiplier = get_type_multiplier(content_type)
    reputation_bonus = get_reputation_bonus(user_reputation)
    
    return int(base_reward * type_multiplier * reputation_bonus)
```

#### **Reward Tiers**
- **Score 7-8**: 70-80 Atlas base
- **Score 9**: 90 Atlas base
- **Score 10**: 100 Atlas base
- **Bonus multipliers**: First submission, high-quality source, etc.

### 4. **Multi-Platform Integration**

#### **Twitter Integration**
- **Worker**: External Twitter worker (existing)
- **Process**: `twitter_content_analysis` BPMN
- **Input**: Tweet URL
- **Output**: Extracted content, metadata, analysis

#### **Telegram Channel Integration**
- **Worker**: External Telegram worker (existing)
- **Process**: `telegram_channel_analysis` BPMN
- **Input**: Channel link or forwarded message
- **Output**: Channel info, recent messages, analysis

#### **Website Integration**
- **Worker**: Web scraping worker
- **Process**: `website_content_analysis` BPMN
- **Input**: Website URL
- **Output**: Extracted text, metadata, analysis

#### **Attachment Processing**
- **Local Processing**: PDF, DOC, TXT parsing
- **External Processing**: Images, videos (via external workers)
- **Storage**: Cloudflare R2 (existing S3 service)

### 5. **Authentication & Authorization**

#### **Guest Mode**
- **Access**: Search knowledge base, submit links for review
- **Limitations**: Cannot submit full content, no rewards
- **Authentication**: None required

#### **Authenticated Mode**
- **Access**: Full submission workflow, rewards, leaderboard
- **Authentication**: 
  - Third-party OAuth (Google, GitHub, etc.)
  - Solana wallet connect
  - Telegram account linking

#### **User Profiles**
- **Storage**: Existing UserProfile service
- **Fields**: 
  - `wallet_address`: Solana wallet
  - `atlas_balance`: Current Atlas tokens
  - `submission_count`: Total submissions
  - `approval_rate`: Success rate
  - `reputation_score`: Community standing

---

## 📊 Data Models

### 1. **Content Submission**
```python
class ContentSubmission:
    id: str
    user_id: int
    content_type: str  # "link", "attachment", "message"
    content_url: str
    source_platform: str  # "twitter", "telegram", "web", "direct"
    original_message_id: str
    submission_date: datetime
    status: str  # "pending", "approved", "rejected", "modifying"
    usefulness_score: int  # -10 to +10
    atlas_reward: int
    moderator_id: Optional[int]
    moderator_comments: Optional[str]
    process_instance_id: str  # Camunda process
```

### 2. **Knowledge Base Entry**
```python
class KnowledgeBaseEntry:
    id: str
    title: str
    content: str
    source_url: str
    content_type: str
    tags: List[str]
    added_date: datetime
    added_by: int  # User who submitted
    approved_by: int  # Moderator who approved
    usefulness_score: int
    view_count: int
    rating: float  # Community rating
```

### 3. **Atlas Transaction**
```python
class AtlasTransaction:
    id: str
    user_id: int
    amount: int  # Positive for rewards, negative for spending
    transaction_type: str  # "reward", "purchase", "transfer"
    related_submission_id: Optional[str]
    description: str
    timestamp: datetime
    wallet_address: str
    blockchain_tx_hash: Optional[str]
```

---

## 🔄 Implementation Phases

### **Phase 1: Core Content Analysis (MVP)**
**Timeline**: 2-3 weeks

#### **Features**
- Basic content detection in group chats
- AI-powered usefulness scoring
- Simple approval workflow (approve/reject)
- Basic Atlas rewards calculation
- Guest mode knowledge base search

#### **Technical Tasks**
1. **Content Analysis Service**
   - Implement content type detection
   - Create AI scoring prompts
   - Integrate with existing LLM service

2. **Basic Moderation Workflow**
   - Create simple BPMN process
   - Implement moderator task interface
   - Add approval/rejection actions

3. **Atlas Rewards System**
   - Basic reward calculation
   - User balance tracking
   - Simple leaderboard

4. **Guest Mode**
   - Knowledge base search interface
   - Link submission for review
   - Basic authentication flow

### **Phase 2: Multi-Platform Integration**
**Timeline**: 3-4 weeks

#### **Features**
- Twitter content processing
- Telegram channel analysis
- Website content extraction
- Attachment processing (PDF, DOC, TXT)
- Enhanced moderation workflow

#### **Technical Tasks**
1. **External Worker Integration**
   - Twitter worker integration
   - Telegram worker integration
   - Web scraping worker
   - File processing workers

2. **Enhanced BPMN Processes**
   - Multi-step moderation workflow
   - Content type-specific processes
   - Error handling and retry logic

3. **Advanced Content Analysis**
   - Source credibility assessment
   - Duplicate detection
   - Content categorization

### **Phase 3: Advanced Features**
**Timeline**: 2-3 weeks

#### **Features**
- Solana wallet integration
- Advanced Atlas rewards system
- Community rating system
- Daily digest and leaderboards
- Advanced moderation tools

#### **Technical Tasks**
1. **Wallet Integration**
   - Solana wallet connect
   - Blockchain transaction handling
   - Token balance management

2. **Community Features**
   - User reputation system
   - Community rating of content
   - Advanced leaderboards
   - Daily digest generation

3. **Advanced Moderation**
   - Bulk approval tools
   - Content categorization
   - Automated tagging
   - Quality metrics dashboard

---

## 🎨 User Interface Requirements

### 1. **Group Chat Interface**

#### **Content Detection Messages**
```
🤖 Content Analysis
📎 PDF Document: "Crypto Trading Guide"
📊 Usefulness Score: 8/10
💰 Potential Reward: 80 Atlas

Add to knowledge base?
[✅ Yes] [❌ No]
```

#### **Submission Confirmation**
```
✅ Content Submitted for Review
📋 Submission ID: #12345
⏱️ Expected review time: 24-48 hours
💰 Potential reward: 80 Atlas

Track status: /submissions
```

### 2. **Private Chat Interface**

#### **Submission Form**
```
📝 Submit Content for Knowledge Base

Content Type: [Link] [Attachment] [Text]
URL/Content: [Input field]
Description: [Optional text area]
Tags: [Optional tags]

[Submit for Review] [Cancel]
```

#### **Status Tracking**
```
📊 Your Submissions

#12345 - Crypto Guide (PDF)
Status: ✅ Approved
Reward: 80 Atlas
Date: 2025-10-24

#12346 - Trading Tips (Link)
Status: ⏳ Under Review
Date: 2025-10-23

[View All] [Leaderboard]
```

### 3. **Web Interface (Guest Mode)**

#### **Knowledge Base Search**
```
🔍 Search Knowledge Base
[Search input] [Search button]

📚 Categories:
• Crypto Trading
• DeFi Protocols
• Market Analysis
• Technical Guides

[Browse All] [Submit Content]
```

#### **Content Submission (Guest)**
```
📤 Submit Content

⚠️ Guest Mode Limitations:
• Can submit links for review
• No rewards or full submission
• Sign in for complete features

[Sign In] [Submit Link] [Cancel]
```

### 4. **Moderator Interface**

#### **Review Dashboard**
```
📋 Content Review Queue

#12345 - Crypto Guide (PDF)
Score: 8/10 | User: @trader123
Submitted: 2 hours ago
[Approve] [Reject] [Request Changes]

#12346 - Trading Tips (Link)
Score: 6/10 | User: @newbie456
Submitted: 4 hours ago
[Approve] [Reject] [Request Changes]

[View All] [Bulk Actions]
```

#### **Approval Actions**
```
✅ Approve Content

Content: Crypto Trading Guide
Atlas Reward: 80 tokens
Moderator Comments: [Optional]

[Confirm Approval] [Cancel]
```

---

## 🔒 Security & Privacy Requirements

### 1. **Content Security**
- **Encryption**: All content encrypted in transit and at rest
- **Access Control**: Role-based access to moderation tools
- **Audit Logging**: Complete audit trail of all actions
- **Data Retention**: Configurable retention policies

### 2. **User Privacy**
- **Data Minimization**: Collect only necessary user data
- **Consent Management**: Clear consent for data processing
- **Right to Deletion**: Users can request data deletion
- **Anonymization**: Option to submit anonymously

### 3. **System Security**
- **Rate Limiting**: Prevent spam and abuse
- **Input Validation**: Sanitize all user inputs
- **API Security**: Secure API endpoints with authentication
- **Monitoring**: Real-time security monitoring

---

## 📈 Success Metrics & KPIs

### 1. **Content Quality Metrics**
- **Approval Rate**: % of submissions approved (target: >60%)
- **Quality Score**: Average usefulness score (target: >7.5)
- **Duplicate Rate**: % of duplicate submissions (target: <10%)
- **Community Rating**: Average user rating of approved content (target: >4.0/5.0)

### 2. **User Engagement Metrics**
- **Active Contributors**: Users submitting content monthly (target: 100+)
- **Submission Volume**: Content submissions per day (target: 50+)
- **Retention Rate**: % of users who submit multiple times (target: >40%)
- **Leaderboard Participation**: Users checking leaderboards (target: 200+)

### 3. **System Performance Metrics**
- **Processing Time**: Average time from submission to review (target: <24h)
- **Moderation Efficiency**: Reviews per moderator per hour (target: 20+)
- **System Uptime**: Platform availability (target: >99.5%)
- **Error Rate**: Failed submissions/processing (target: <2%)

### 4. **Business Metrics**
- **Knowledge Base Growth**: New entries per week (target: 100+)
- **Atlas Distribution**: Total Atlas rewards distributed (target: 10,000+/month)
- **User Acquisition**: New registered users (target: 500+/month)
- **Revenue Impact**: Impact on platform usage and engagement

---

## 🚀 Launch Strategy

### 1. **Soft Launch (Beta)**
- **Duration**: 2 weeks
- **Users**: Internal team + 50 beta users
- **Features**: Core content analysis + basic moderation
- **Goals**: Test core functionality, gather feedback

### 2. **Limited Release**
- **Duration**: 4 weeks
- **Users**: 500 selected users
- **Features**: Full MVP functionality
- **Goals**: Validate user experience, optimize performance

### 3. **Full Launch**
- **Duration**: Ongoing
- **Users**: All platform users
- **Features**: Complete system with all integrations
- **Goals**: Scale to full user base, achieve success metrics

---

## 🔮 Future Enhancements

### 1. **Advanced AI Features**
- **Content Summarization**: Auto-generate summaries
- **Topic Clustering**: Group related content
- **Trend Analysis**: Identify trending topics
- **Personalized Recommendations**: AI-powered content suggestions

### 2. **Enhanced Rewards System**
- **NFT Rewards**: Special NFTs for top contributors
- **Tiered Rewards**: Different reward levels based on contribution history
- **Referral Bonuses**: Rewards for bringing new contributors
- **Seasonal Campaigns**: Special reward events

### 3. **Community Features**
- **Content Discussions**: Comments and discussions on submissions
- **Expert Verification**: Verified expert contributors
- **Content Challenges**: Themed submission campaigns
- **Collaborative Curation**: Community-driven content organization

### 4. **Advanced Moderation**
- **AI Pre-moderation**: Automated initial screening
- **Community Moderation**: User-driven content flagging
- **Expert Review**: Specialized reviewers for technical content
- **Quality Assurance**: Automated quality checks

---

## 📞 Support & Maintenance

### 1. **User Support**
- **Documentation**: Comprehensive user guides
- **Help System**: In-bot help and FAQ
- **Support Channels**: Telegram support group, email support
- **Video Tutorials**: Step-by-step submission guides

### 2. **Technical Support**
- **Monitoring**: Real-time system monitoring
- **Alerting**: Automated alerts for issues
- **Backup**: Regular data backups
- **Recovery**: Disaster recovery procedures

### 3. **Content Moderation**
- **Moderator Training**: Training materials and guidelines
- **Quality Assurance**: Regular moderation quality reviews
- **Escalation Process**: Clear escalation procedures
- **Feedback Loop**: Regular feedback from moderators

---

**Document Version**: 1.0  
**Last Updated**: October 24, 2025  
**Author**: AI Assistant  
**Status**: ✅ Ready for Implementation 🚀
