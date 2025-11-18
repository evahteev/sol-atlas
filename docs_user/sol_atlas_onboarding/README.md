# SOL Atlas: Crypto Attention Autopilot Onboarding

**VERSION 3.0 — FAST-TRACK TO CTA**

A lightning-fast, narrative-driven onboarding that hooks users with crypto mindshare insights and drives them to action in under 90 seconds.

## Overview

**Core Pitch**: "In crypto, attention = opportunity. Catch the wave before it breaks."

**Duration**: 60-90 seconds (3 conversational beats)

**Goal**: Hook with mindshare insight → Present full value → Drive to CTA (Launch/Bot/Community)

## Narrative Arc

```
Opening Beat: "Attention = Opportunity" (crypto mindshare hook)
     ↓
Development: "SOL Atlas tracks & builds community attention"
     ↓
Resolution: User chooses their path → Immediate action
```

## Flow Structure

### Step 1: Hook + Qualify (30-45 seconds)

**Objective**: Grab attention with crypto insight, establish credibility, quick segment

**The Hook**:

> "Hey! 👋 **In crypto, attention = opportunity.**
>
> When a token starts trending on Twitter, price often follows. But by the time you notice, you're already late.
>
> Same with communities — lose attention, lose value.
>
> Quick question: Which describes you best?"

**Segmentation Options**:
- 🏗️ Builder (launching projects)
- 👥 Community Lead (managing groups)
- 🔍 Researcher/Trader

**What We Capture**:
- `user_segment`: Role identification for CTA prioritization

**Why This Works**:
- Opens with universal crypto truth (attention = alpha)
- Creates FOMO with "you're already late" framing
- Connects token trends to community value
- Minimal friction: one quick choice

---

### Step 2: Value Prop + All CTAs (30-45 seconds)

**Objective**: Deliver full value proposition and present ALL action options immediately

**Value Delivery**:

> "**SOL Atlas = Your Crypto Attention Autopilot**
>
> 📈 **Track mindshare** — See what's trending before the crowd
> 🤖 **Build community** — Gamified quests + AI CoPilot + Leaderboards
> ⚡ **Get alerts** — Real-time notifications for trending tokens & community activity
> 📊 **Own your data** — No platform lock-in (portable, chain-agnostic)
>
> **Proven traction:**
> • Burning Meme: 50K+ users
> • DexGuru: 30K MAU
> • UCOIN: 47K users
>
> **Ready to dive in? Pick your path:**
>
> 🚀 **Launch Your Bot** → https://atlas.gurunetwork.ai/
> Set up your community bot in 2 minutes. Get Quests, AI CoPilot, Leaderboards, Analytics.
>
> 🤖 **Talk to Atlas Bot** → https://t.me/SOLAtlasBOT
> Chat 24/7 about community growth, trending tokens, quest templates, analytics.
>
> 📢 **Join Channel** → https://t.me/SolanaAtlas
> Get crypto mindshare alerts, SOL Atlas updates, growth insights, trending signals.
>
> 💬 **Join Group** → https://t.me/+BXMz7v3VxKFhMjli
> Connect with builders, share strategies, get help, collaborate on projects."

**CRITICAL: All 4 CTAs with CLICKABLE LINKS presented immediately** (reordered by segment):

| CTA | Link | Priority For |
|-----|------|--------------|
| 🚀 Launch Your Bot | https://atlas.gurunetwork.ai/ | Builders |
| 🤖 Talk to Atlas Bot | https://t.me/SOLAtlasBOT | Researchers |
| 📢 Join Channel | https://t.me/SolanaAtlas | Community Leads |
| 💬 Join Group | https://t.me/+BXMz7v3VxKFhMjli | All |

**Enforcement Rules:**
- ✅ LLM MUST provide all 4 links in Step 2 (no holding back)
- ✅ Links appear as clickable URLs, not "you can join here"
- ✅ CTAs reordered by user segment, but ALL 4 shown
- ✅ No waiting for user to ask - immediate presentation

**What We Capture**:
- `chosen_cta`: Which action user selected

**Why This Works**:
- No multi-step qualification friction
- Social proof builds credibility instantly
- Four clear paths for different user types
- All CTAs visible = no hidden options

---

### Step 3: Complete + Next Steps (15-20 seconds)

**Objective**: Confirm choice, provide link with context, keep conversation open

**Response Templates**:

**If Launch Your Bot**:
> "Perfect! 🚀 Head to **https://atlas.gurunetwork.ai/** to set up your community bot in 2 minutes.
>
> You'll get: Quests, AI CoPilot, Leaderboards, Analytics — all in one.
>
> Need help? Just ask me or join our community!"

**If Talk to Atlas Bot**:
> "Awesome! 🤖 Start chatting at **https://t.me/SOLAtlasBOT**
>
> Ask about:
> • Community growth strategies
> • Trending Solana tokens
> • Quest templates
> • Analytics setup
>
> I'm here 24/7!"

**If Join Channel**:
> "Great! 📢 Join **https://t.me/SolanaAtlas** for:
> • Crypto mindshare alerts
> • SOL Atlas updates
> • Community growth insights
> • Trending token signals
>
> See you there!"

**If Join Group**:
> "Perfect! 💬 Join **https://t.me/+BXMz7v3VxKFhMjli** to:
> • Connect with builders
> • Share strategies
> • Get help from the community
> • Collaborate on projects
>
> Welcome aboard!"

**Always Add**:
> "Want to explore other options? Just ask!"

**What We Capture**:
- `onboarding_complete`: Boolean flag for analytics

**Next-Step Suggestions**:
- "Show me trending tokens now"
- "Tell me about quests"
- "How do I set up analytics?"
- "I'm all set, thanks!"

---

## Persona: Crypto Signal Agent

**Role**: Crypto Signal Agent & Community Growth Expert
**Voice**: Sharp, data-driven, opportunistic
**Style**: Crypto-native language with urgency, lead with insight → value → immediate action
**Approach**: No fluff, all signal. Create FOMO, establish credibility, empower choice.

**Key Characteristics**:
- Opens with attention-grabbing crypto insight
- Moves fast — 60-90 seconds to CTA
- Delivers social proof for credibility
- Presents clear, immediate action options
- Maintains momentum without overwhelming

---

## Success Metrics

### Qualitative

✅ User understands "attention = opportunity" concept
✅ User role identified (Builder/Community Lead/Researcher)
✅ All 4 CTAs presented clearly
✅ User clicks at least one CTA
✅ Workflow completes in under 90 seconds

### Analytics Tracked

- **Completion rate**: % reaching step 3
- **Drop-off points**: Where users abandon
- **Time to complete**: Average duration
- **Segment distribution**: Builder vs Community Lead vs Researcher
- **CTA click rate**: % clicking each option
- **Launcher conversion**: % visiting atlas.gurunetwork.ai
- **Bot interaction rate**: % messaging @SOLAtlasBOT
- **Channel join rate**: % joining @SolanaAtlas
- **Group join rate**: % joining group chat

---

## Integration Points

### Data Captured

```yaml
user_segment: "Builder" | "Community Lead" | "Researcher"
chosen_cta: "launch_bot" | "talk_to_bot" | "join_channel" | "join_group"
onboarding_complete: true
timestamp: ISO 8601
```

### Triggered Workflows

After onboarding completes:
- `crypto_mindshare_alerts`: Subscribe to trending token notifications
- `community_analytics_setup`: Configure group analytics (if applicable)

### Technical Requirements

- Redis state management for user preferences
- Background task: Fetch trending crypto token during Step 1
- WebSocket support for real-time streaming responses
- Button rendering via Telegram inline keyboards

---

## Testing Checklist

**Workflow Mechanics**:
- ✅ Workflow auto-starts for new/guest users
- ✅ Step 1: Hook displays, role selection works
- ✅ Step 2: Value prop renders, all 4 CTAs show correctly
- ✅ Step 3: Link confirmation matches chosen CTA
- ✅ Onboarding completion flag sets correctly

**User Experience**:
- ✅ Completes in under 90 seconds
- ✅ No more than 3 user interactions required
- ✅ CTA buttons are clickable and route correctly
- ✅ Mobile-optimized (messages under 200 chars per block)
- ✅ Suggestions appear after each step

**Analytics**:
- ✅ Segment capture fires on Step 1
- ✅ CTA selection tracked on Step 2
- ✅ Completion event fires on Step 3
- ✅ Time-to-complete calculated correctly

---

## Example Conversation Flow

**Bot** (Step 1):
> Hey! 👋 **In crypto, attention = opportunity.**
>
> When a token starts trending on Twitter, price often follows. But by the time you notice, you're already late.
>
> Same with communities — lose attention, lose value.
>
> Quick question: Which describes you best?
>
> [🏗️ Builder] [👥 Community Lead] [🔍 Researcher/Trader]

**User**: *Clicks "Builder"*

**Bot** (Step 2):
> Perfect! Builders need tools that move fast.
>
> **SOL Atlas = Your Crypto Attention Autopilot**
>
> 📈 **Track mindshare** — See what's trending before the crowd
> 🤖 **Build community** — Gamified quests + AI CoPilot + Leaderboards
> ⚡ **Get alerts** — Real-time notifications for trending tokens & community activity
> 📊 **Own your data** — No platform lock-in (portable, chain-agnostic)
>
> **Proven traction:**
> • Burning Meme: 50K+ users
> • DexGuru: 30K MAU
> • UCOIN: 47K users
>
> **Ready to dive in?** Pick your path:
>
> [🚀 Launch Your Bot] [🤖 Talk to Atlas Bot]
> [📢 Join Channel] [💬 Join Group]

**User**: *Clicks "🚀 Launch Your Bot"*

**Bot** (Step 3):
> Perfect! 🚀 Head to **https://atlas.gurunetwork.ai/** to set up your community bot in 2 minutes.
>
> You'll get: Quests, AI CoPilot, Leaderboards, Analytics — all in one.
>
> Need help? Just ask me or join our community!
>
> Want to explore other options? Just ask!
>
> [Show me trending tokens now] [Tell me about quests]
> [How do I set up analytics?] [I'm all set, thanks!]

---

## Design Rationale

### Why This Flow Works

**1. Attention Economics Hook**
- Opens with universal crypto insight everyone recognizes
- Creates immediate relevance for both traders and community builders
- "You're already late" creates urgency without pressure

**2. Dual Value Proposition**
- Crypto mindshare tracking (trader appeal)
- Community building tools (builder appeal)
- Unified under "attention autopilot" concept

**3. Zero-Friction CTA Presentation**
- All options presented at once (no hidden paths)
- User chooses their own adventure
- No forced qualification sequence

**4. Fast Time-to-Value**
- Under 90 seconds to action
- Minimal clicks (2-3 max)
- Social proof builds trust quickly

**5. Conversation Continuity**
- Onboarding "completes" but conversation stays open
- Next-step suggestions keep engagement
- Can pivot to other features without restarting

---

## Future Enhancements

### Potential Additions (v4.0)

- ✅ **Mindshare alert preview**: Show real trending token during onboarding
- ✅ **Interactive quest builder**: 30-second quest template demo
- ✅ **CAC calculator**: If user wants ROI math (optional branch)
- ✅ **Video testimonials**: Embedded social proof from real users
- ✅ **A/B testing**: Test different hooks ("attention" vs "retention")
- ✅ **Multi-language support**: i18n for international communities
- ✅ **Smart CTA ordering**: ML-driven CTA priority based on behavior

---

**Version**: 3.0.0
**Last Updated**: 2025-01-11
**Maintained By**: Guru Network Team
**Workflow Type**: Conversational Sales Onboarding
**Target Duration**: 60-90 seconds
**Success Criteria**: User clicks CTA within 2-3 messages
