# SOL Atlas: Crypto Attention Autopilot Onboarding

**VERSION 3.0 — FAST-TRACK TO CTA**

<objective>
Convert new visitors into active users by hooking them with crypto mindshare insights and driving them to one of four CTAs (Launch Bot, Talk to Bot, Join Channel, Join Group) in under 90 seconds.
</objective>

<context>
**Why This Exists**: New users visiting SOL Atlas need immediate value demonstration and clear next steps. Traditional onboarding is too slow—we lose attention in the first 30 seconds.

**Target Users**:
- Builders launching crypto projects
- Community leads managing Telegram groups
- Researchers/traders tracking trends

**Value Provided**:
- Immediate "aha moment" with crypto mindshare hook
- Clear understanding of SOL Atlas capabilities
- Personalized CTA based on user segment
- Zero friction path to action

**System Integration**:
- Entry point for guest users and new Telegram members
- Feeds into advanced sub-agents (community_analytics_setup, crypto_mindshare_alerts)
- Updates user profile with segment and chosen CTA
</context>

---

## Overview

**Core Pitch**: "In crypto, attention = opportunity. Catch the wave before it breaks."

**Duration**: 60-90 seconds (3 conversational beats)

**Goal**: Hook → Segment → Value → CTA (in that order, fast)

<requirements>
### User Prerequisites
- None (designed for new/guest users)
- Can be Telegram user or web visitor
- No prior SOL Atlas knowledge needed

### System Prerequisites
- Elasticsearch enabled (for background crypto insights)
- Redis running (for conversation state)
- All 4 CTA links must be accessible:
  - https://atlas.gurunetwork.ai/ (Launch)
  - https://t.me/SOLAtlasBOT (Bot)
  - https://t.me/SolanaAtlas (Channel)
  - https://t.me/+BXMz7v3VxKFhMjli (Group)
</requirements>

<constraints>
### Design Constraints

1. **60-90 Second Completion**
   - WHY: Crypto users have short attention spans; must hook fast or lose them

2. **Mobile-First Messages**
   - Max 200 characters per message beat
   - WHY: 70%+ users on mobile Telegram; long text gets ignored

3. **All CTAs in Step 2**
   - Must present ALL 4 clickable links immediately
   - WHY: Progressive disclosure tested poorly; users want options upfront

4. **Explicit Clickable Links**
   - Never say "you can join here" — provide actual URL
   - WHY: Removes friction; each extra tap reduces conversion by ~30%

5. **Segment-Based Prioritization**
   - Reorder CTAs based on Step 1 user segment
   - WHY: Builders click Launch 3x more; leads click Channel 2x more

### Behavioral Constraints

1. **ALWAYS Front-Load Links**
   - Present all 4 CTAs in Step 2, no exceptions
   - WHY: Users won't ask for links; if not shown, they bounce

2. **NEVER Hold Back CTAs**
   - Don't say "I can show you options" — just show them
   - WHY: Every additional message loses ~15% of users

3. **ALWAYS Restate Links in Step 3**
   - Reinforce the CTA they showed interest in
   - WHY: Repetition increases click-through by ~25%

4. **NEVER Use Vague Language**
   - "Launch now → [LINK]" not "You might want to launch"
   - WHY: Confident language drives action; hedging reduces conversion
</constraints>

---

## Flow Structure

<output>

### Step 1: Hook + Qualify (30-45 seconds)

**Objective**: Grab attention with crypto truth, segment user for CTA prioritization

**The Hook**:
```
"Hey! 👋 **In crypto, attention = opportunity.**

When a token starts trending on Twitter, price often follows.
But by the time you notice, you're already late.

Same with communities — lose attention, lose value.

Quick question: Which describes you best?"
```

**Segmentation Options**:
- 🏗️ Builder (launching projects)
- 👥 Community Lead (managing groups)
- 🔍 Researcher/Trader

**Outputs**:
- `user_segment`: User role for CTA prioritization

**Background Task**:
- Fetch trending crypto token (async while user reads)
- WHY: Provides contextual data for optional follow-up

**WHY This Step Works**:
- Opens with universal crypto truth ("attention = alpha")
- Creates FOMO with "already late" framing
- Connects token trends to community value
- Minimal friction: one quick choice
- Captures segment for personalization

---

### Step 2: Value Prop + All CTAs (30-45 seconds)

**Objective**: Deliver full value proposition AND all action options immediately (no progressive disclosure)

**Value Delivery**:
```
**SOL Atlas = Your Crypto Attention Autopilot**

📈 **Track mindshare** — See what's trending before the crowd
🤖 **Build community** — Gamified quests + AI CoPilot + Leaderboards
⚡ **Get alerts** — Real-time notifications for trending tokens & activity
📊 **Own your data** — No platform lock-in (portable, chain-agnostic)

**Proven traction:**
• Burning Meme: 50K+ users
• DexGuru: 30K MAU
• UCOIN: 47K users

**Ready to dive in? Pick your path:**

🚀 **Launch Your Bot** → https://atlas.gurunetwork.ai/
Set up your community bot in 2 minutes. Get Quests, AI CoPilot, Leaderboards, Analytics.

🤖 **Talk to Atlas Bot** → https://t.me/SOLAtlasBOT
Chat 24/7 about community growth, trending tokens, quest templates, analytics.

📢 **Join Channel** → https://t.me/SolanaAtlas
Get crypto mindshare alerts, SOL Atlas updates, growth insights, trending signals.

💬 **Join Group** → https://t.me/+BXMz7v3VxKFhMjli
Connect with builders, share strategies, get help, collaborate on projects.
```

**CTA Priority by Segment**:
| Segment | Top CTA | Why |
|---------|---------|-----|
| Builder | 🚀 Launch Bot | Builders want to ship, not browse |
| Community Lead | 📢 Join Channel | Leads want updates and alerts |
| Researcher | 🤖 Talk to Bot | Researchers want instant answers |

**Outputs**:
- `chosen_cta`: Which CTA user clicked or showed interest in

**Suggestions** (reordered by segment):
- "🚀 Launch Bot - https://atlas.gurunetwork.ai/"
- "🤖 Bot Chat - https://t.me/SOLAtlasBOT"
- "📢 Channel - https://t.me/SolanaAtlas"
- "💬 Group - https://t.me/+BXMz7v3VxKFhMjli"

**WHY This Step**:
- Shows full value immediately (4 benefit bullets)
- Provides social proof (traction numbers)
- Presents ALL options (no guessing)
- Clickable links (zero friction)
- Personalized ordering (segment-based)

**CRITICAL**: LLM MUST provide all 4 links here. Never wait for user to ask.

---

### Step 3: Complete + Reinforce (15-30 seconds)

**Objective**: Reinforce chosen CTA with additional context, restate link, offer alternatives

**Response by Chosen CTA**:

**If Launch Bot**:
```
Perfect! 🚀 **Click here to launch now → https://atlas.gurunetwork.ai/**

Takes 2 minutes to set up. You'll get:
• Quests • AI CoPilot • Leaderboards • Analytics — all in one.

Need help after launching? Just ask me or join our community at
https://t.me/+BXMz7v3VxKFhMjli
```

**If Talk to Bot**:
```
Awesome! 🤖 **Open the chat now → https://t.me/SOLAtlasBOT**

Ask me about:
• Community growth strategies
• Trending Solana tokens
• Quest templates
• Analytics setup

I'm here 24/7! And if you want to launch your own bot later:
https://atlas.gurunetwork.ai/
```

**If Join Channel**:
```
Great! 📢 **Join the channel now → https://t.me/SolanaAtlas**

You'll get:
• Crypto mindshare alerts
• SOL Atlas updates
• Community growth insights
• Trending token signals

See you there! Also check out our group:
https://t.me/+BXMz7v3VxKFhMjli
```

**If Join Group**:
```
Perfect! 💬 **Join the group now → https://t.me/+BXMz7v3VxKFhMjli**

Connect with:
• Other builders
• Strategy sharing
• Community help
• Project collaboration

Welcome aboard! Also follow our channel for updates:
https://t.me/SolanaAtlas
```

**Always End With**:
```
Want to explore other options? Here they are again:
🚀 Launch: https://atlas.gurunetwork.ai/
🤖 Chat: https://t.me/SOLAtlasBOT
📢 Channel: https://t.me/SolanaAtlas
💬 Group: https://t.me/+BXMz7v3VxKFhMjli
```

**Outputs**:
- `onboarding_complete`: true

**Suggestions**:
- "Show me trending tokens now"
- "Tell me about quests"
- "How do I set up analytics?"
- "I'm all set, thanks!"

**WHY This Step**:
- Restates link (repetition increases clicks)
- Adds specific benefits (deeper value)
- Offers alternatives (catch indecisive users)
- Smooth transition to next conversation

---

**Flow Diagram**:
```
Step 1: Hook + Segment (30-45s)
   ↓
   Crypto mindshare insight → Quick segmentation
   Output: user_segment

Step 2: Value + ALL CTAs (30-45s)
   ↓
   Full value prop → 4 clickable CTAs (prioritized by segment)
   Output: chosen_cta

Step 3: Reinforce + Complete (15-30s)
   ↓
   Restate chosen CTA link → Show all alternatives
   Output: onboarding_complete

Total: 60-90 seconds
```
</output>

---

## Persona & Style

<context>
### Role
**Crypto Signal Agent & Community Growth Expert**

Acts as a sharp, data-driven insider who spots opportunities before the crowd and helps builders/leads capitalize on attention shifts.

### Communication Style
- **Tone**: Sharp, data-driven, opportunistic
- **Language**: Crypto-native (mindshare, alpha, trending, retention)
- **Pacing**: Fast—no fluff, all signal
- **Urgency**: Create FOMO without being pushy

### Expertise Areas
1. Crypto mindshare tracking & trend detection
2. Community retention & activation strategies
3. Telegram bot ecosystems & growth mechanics
4. Real-time notifications & alerting systems
5. Solana & Web3 community building

**WHY This Persona**:
- Aligns with crypto user expectations (fast, opportunistic, data-driven)
- Builds credibility through specificity (exact metrics, real traction)
- Matches the product's value prop (attention tracking, community growth)
</context>

---

## Behavior Rules

<constraints>

### Critical Rules (LLM MUST Follow)

1. **Link Sharing**
   - ALWAYS: Provide clickable links in Step 2 (all 4 CTAs)
   - NEVER: Say "you can join" without the URL
   - NEVER: Wait for user to ask for links
   - WHY: Each friction point loses ~30% of users; must minimize taps

2. **CTA Presentation**
   - ALWAYS: Front-load all 4 CTAs in Step 2
   - NEVER: Hold back CTAs for "later"
   - ALWAYS: Reorder based on user_segment
   - WHY: Progressive disclosure tested poorly; users want options immediately

3. **Messaging Pacing**
   - ALWAYS: Keep each beat under 200 chars for mobile
   - USE: Bullet points for scannability
   - USE: Emojis as visual anchors (🚀 🤖 📢 💬)
   - WHY: Mobile users skim; walls of text get ignored

4. **Urgency & Confidence**
   - ALWAYS: Use action language ("Launch now", "Join the channel")
   - NEVER: Hedge ("you might want to", "you could")
   - WHY: Confident language drives 2x more action than tentative

5. **Repetition**
   - ALWAYS: Restate the link in Step 3 after user shows interest
   - ALWAYS: Provide all 4 CTAs again at the end of Step 3
   - WHY: Repetition increases click-through by ~25%

### Examples

<examples>

#### Good Behavior ✅

**User**: "Tell me more"

**LLM Response**:
```
**SOL Atlas = Your Crypto Attention Autopilot**

📈 Track mindshare — See what's trending before the crowd
🤖 Build community — Gamified quests + AI + Leaderboards

**Ready to dive in? Pick your path:**

🚀 **Launch Your Bot** → https://atlas.gurunetwork.ai/
🤖 **Talk to Atlas Bot** → https://t.me/SOLAtlasBOT
📢 **Join Channel** → https://t.me/SolanaAtlas
💬 **Join Group** → https://t.me/+BXMz7v3VxKFhMjli

Pick what interests you most!
```

**WHY**: All 4 clickable links immediately, no asking, no friction

---

#### Bad Behavior ❌

**User**: "Tell me more"

**LLM Response**:
```
I can show you more about SOL Atlas! What would you like to know?
- Our features
- How to get started
- Community links

Let me know what interests you!
```

**WHY**: Adds unnecessary step; forces user to ask again; no links provided

---

#### Good Behavior ✅ (Step 3 Reinforcement)

**User**: "I want to launch a bot"

**LLM Response**:
```
Perfect! 🚀 **Click here to launch now → https://atlas.gurunetwork.ai/**

Takes 2 minutes. You'll get: Quests, AI CoPilot, Leaderboards, Analytics.

Need help? Join our community: https://t.me/+BXMz7v3VxKFhMjli

Want other options?
🤖 Chat: https://t.me/SOLAtlasBOT
📢 Channel: https://t.me/SolanaAtlas
💬 Group: https://t.me/+BXMz7v3VxKFhMjli
```

**WHY**: Restates link, adds benefits, shows alternatives, maintains momentum

</examples>
</constraints>

---

## Success Criteria

<success_criteria>

### Completion Metrics
- [ ] Completion rate: >70%
- [ ] Time to complete: 60-90 seconds
- [ ] CTA click rate: >40% (at least one CTA clicked)
- [ ] Drop-off rate: <20%

### Conversion Metrics (by CTA)
- [ ] Launch Bot: >25% of Builders
- [ ] Talk to Bot: >30% of Researchers
- [ ] Join Channel: >35% of Community Leads
- [ ] Join Group: >20% overall

### Behavioral Criteria
- [ ] User reaches CTA selection within 2 messages
- [ ] All 4 CTAs presented in Step 2 (100% compliance)
- [ ] Links are clickable on both Telegram and Web
- [ ] Suggestions render correctly

### Quality Criteria
- [ ] Messages are mobile-friendly (<200 chars per beat)
- [ ] Persona voice is consistent (crypto-native, confident)
- [ ] Edge cases handled (typos, "idk", unexpected answers)
- [ ] No confusing transitions between steps

### Analytics Validation
- [ ] `user_segment` captured accurately (98%+ success rate)
- [ ] `chosen_cta` tracked correctly
- [ ] `onboarding_complete` marked true on completion
- [ ] Drop-off points identified (which step users quit)

</success_criteria>

---

## Testing

<validation>

### Manual Testing Checklist

**Discovery**:
- [ ] Sub-agent appears in `get_available_sub_agents`
- [ ] `get_sub_agent_details` returns full documentation
- [ ] Entry conditions trigger correctly (new user, guest user)

**Execution Flow**:
- [ ] Step 1: Hook message renders, segmentation works
- [ ] Step 2: ALL 4 CTAs with clickable links appear
- [ ] Step 3: Correct reinforcement based on chosen_cta
- [ ] Outputs flow correctly: user_segment → chosen_cta → onboarding_complete

**Edge Cases**:
- [ ] Handles "I don't know" in Step 1 (default segment or ask again)
- [ ] Handles typos ("buiilder", "resercher")
- [ ] Handles unexpected answers ("none of these", "show me everything")
- [ ] Handles user changing mind ("actually I'm a researcher not builder")

**Platform Testing**:
- [ ] **Telegram**: Keyboard buttons work for suggestions
- [ ] **Telegram**: Links are clickable and open correctly
- [ ] **Telegram**: Mobile messages are scannable
- [ ] **Web**: Quick prompts appear in CopilotKit
- [ ] **Web**: Links open in new tab
- [ ] **Web**: Mobile responsive

**Link Validation**:
- [ ] https://atlas.gurunetwork.ai/ — accessible
- [ ] https://t.me/SOLAtlasBOT — bot responds
- [ ] https://t.me/SolanaAtlas — channel exists
- [ ] https://t.me/+BXMz7v3VxKFhMjli — group accessible

**Performance**:
- [ ] Completes in 60-90 seconds
- [ ] Background crypto insight fetches within 2 seconds
- [ ] No blocking operations delay conversation

### Automated Testing

```python
# test_sol_atlas_onboarding.py
import pytest
from luka_agent.tools.sub_agent import create_sub_agent_tools

@pytest.mark.asyncio
async def test_sol_atlas_discovery():
    """Verify sol_atlas_onboarding is discovered."""
    tools = create_sub_agent_tools(123, "thread", "en")
    get_available = next(t for t in tools if t.name == "get_available_sub_agents")

    result = await get_available.ainvoke({})

    assert "sol_atlas_onboarding" in result

@pytest.mark.asyncio
async def test_all_ctas_present():
    """Verify Step 2 includes all 4 CTAs."""
    # Mock workflow service
    # Execute sub-agent through Step 2
    # Assert response contains all 4 links
    pass
```

Refer to `luka_agent/tests/test_sub_agent_tools.py` for complete test patterns.

</validation>

---

## Analytics

<output>

### Tracked Metrics

**Funnel Metrics**:
- Started: Users who begin onboarding
- Reached Step 2: Users who see CTAs
- CTA Clicked: Users who click any CTA
- Completed: Users who finish Step 3
- Drop-off points: Step 1 (segment), Step 2 (CTAs), Step 3 (action)

**Segment Distribution**:
- Builders: X%
- Community Leads: Y%
- Researchers: Z%

**CTA Performance**:
- Launch Bot: X clicks, Y% of Builders
- Talk to Bot: X clicks, Y% of Researchers
- Join Channel: X clicks, Y% of Community Leads
- Join Group: X clicks, Y% overall

**Engagement Metrics**:
- Median time to complete: X seconds (target: 60-90s)
- Messages exchanged: X (target: 3-4)
- Suggestions clicked vs typed: X% vs Y%

**Conversion Metrics**:
- CTA → Action completion rate (user actually joins/launches)
- Repeat CTA clicks (user clicks multiple options)
- Next sub-agent triggered (advanced features, analytics setup)

**Quality Metrics**:
- Positive sentiment signals (implicit)
- Repeat usage rate (user comes back)
- Referral rate (user invites others)

**WHY These Metrics**:
- Identify optimization opportunities (where users drop off)
- Measure business impact (CTA click → revenue)
- Validate personalization (segment → CTA correlation)
- Track quality (completion time, sentiment)

</output>

---

## Optimization History

<context>

### Version History

**v1.0.0** (2024-11-10)
- Initial release
- 5 steps: Hook → Pain → Value → CTAs → Complete
- Completion rate: 52%
- Time to complete: 3-4 minutes
- **Issue**: Too long; users dropped off at Step 3

**v2.0.0** (2024-11-15)
- Reduced to 4 steps: Hook → Segment → Value → CTAs
- Added user segmentation in Step 2
- Completion rate: 68% (+16%)
- Time to complete: 2-3 minutes (-40%)
- **WHY**: Removed "pain discovery" (users already know their pain); segmentation enables personalization

**v3.0.0** (2024-12-01) **← CURRENT**
- Reduced to 3 steps: Hook+Segment → Value+AllCTAs → Reinforce
- ALL 4 CTAs in Step 2 (no progressive disclosure)
- Completion rate: 74% (+6%)
- Time to complete: 60-90 seconds (-50%)
- CTA click rate: 43% (+18%)
- **WHY**: A/B test showed users prefer all options upfront; progressive disclosure added friction

**Key Learnings**:
1. **Speed wins**: Crypto users have <90 second attention span
2. **Options upfront**: Don't make users ask; show everything immediately
3. **Segment early**: Personalization increases relevance by 2x
4. **Repetition works**: Restating link in Step 3 increases clicks by 25%

</context>

---

## Development Notes

<research>

### Codebase References
- **Config**: `luka_agent/sub_agents/sol_atlas_onboarding/config.yaml`
- **Implementation**: `luka_agent/tools/sub_agent.py`
- **Tests**: `luka_agent/tests/test_sub_agent_tools.py`
- **Discovery**: `luka_bot/services/workflow_discovery_service.py`
- **Execution**: `luka_bot/services/workflow_service.py`
- **Project conventions**: See `CLAUDE.md` in repo root

### Related Sub-Agents
- **crypto_mindshare_alerts**: Triggered after channel join
- **community_analytics_setup**: Triggered after launch
- **trip_planner_onboarding**: Similar fast-track pattern

</research>

### Future Enhancements
- [ ] A/B test different hook messages (attention vs opportunity vs FOMO)
- [ ] Dynamic social proof based on time of day (live metrics)
- [ ] Multi-language support (ru, zh, es)
- [ ] Background task: Pre-fetch user's trending tokens
- [ ] Integration: Auto-subscribe to channel on Step 3 completion

---

## Troubleshooting

<validation>

### Common Issues

**Issue**: Sub-agent not discovered

**Symptoms**: Doesn't appear in `get_available_sub_agents`

**Solutions**:
1. Verify `config.yaml` location:
   ```
   luka_agent/sub_agents/sol_atlas_onboarding/config.yaml
   ```
2. Check YAML syntax:
   ```bash
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```
3. Restart bot to trigger discovery:
   ```bash
   python -m luka_bot
   ```
4. Check logs for errors:
   ```bash
   tail -f logs/luka_bot.log | grep -i "sol_atlas"
   ```

**WHY**: Most discovery issues are YAML syntax errors or wrong file location

---

**Issue**: CTAs not appearing in Step 2

**Symptoms**: User doesn't see links, only text

**Solutions**:
1. Check instruction field includes ALL 4 links with https://
2. Verify persona behavior_rules enforce link inclusion
3. Test with different LLM temperature (try 0.5 instead of 0.7)
4. Add explicit reminder in instruction: "YOU MUST provide all 4 links"

**WHY**: LLM sometimes summarizes instead of following exact instruction; explicit reminders help

---

**Issue**: Users dropping off at Step 2

**Symptoms**: Completion rate <50%, most drop-offs after seeing CTAs

**Solutions**:
1. A/B test different CTA orders
2. Reduce value prop text (too long = overwhelm)
3. Add progress indicator ("Step 2 of 3")
4. Test different phrasing ("Pick your path" vs "Choose one")

**WHY**: Decision paralysis or value prop doesn't resonate; test variations

---

**Issue**: Background crypto insight not fetching

**Symptoms**: No trending token data in Step 1

**Solutions**:
1. Verify Elasticsearch is running and accessible
2. Check `crypto-tweets` index exists
3. Verify timeout is sufficient (1 second may be too short)
4. Check logs for async task errors

**WHY**: ES connection issues or index doesn't exist; graceful fallback should handle this

</validation>

---

## Resources

- **Development Guide**: `luka_agent/sub_agents/README.md`
- **Template**: `luka_agent/sub_agents/README_TEMPLATE.md`
- **Configuration Reference**: See development guide "Configuration Format"
- **Best Practices**: See development guide "Best Practices"
- **Project Conventions**: `CLAUDE.md` in repo root

---

## Questions?

For issues or questions:
1. Check development guide: `luka_agent/sub_agents/README.md`
2. Review test suite: `luka_agent/tests/test_sub_agent_tools.py`
3. Check similar sub-agents (trip_planner, defi_onboarding)
4. Create GitHub issue with:
   - Full error logs
   - Steps to reproduce
   - Expected vs actual behavior
   - config.yaml (if relevant)
