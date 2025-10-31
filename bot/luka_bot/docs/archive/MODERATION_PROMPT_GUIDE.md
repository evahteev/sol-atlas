# Moderation Prompt Engineering Guide

## Overview

The **moderation_prompt** is the core of the bot's background moderation system. Unlike the conversational `Thread.system_prompt` (used when bot is @mentioned), the moderation_prompt evaluates EVERY message silently in the background to assess quality and detect violations.

**This guide teaches you how to write effective moderation prompts.**

---

## Understanding the Two-Prompt System

### 🛡️ moderation_prompt (Background, ALL messages)
```
Purpose: Evaluate content quality & detect violations
Runs: On EVERY message (even if bot not mentioned)
Output: JSON with scores and action recommendations
Tone: Analytical, objective, rule-based
```

###  💬 system_prompt (Foreground, @mentions only)
```
Purpose: Have helpful conversations
Runs: Only when bot is @mentioned
Output: Natural language responses
Tone: Friendly, conversational, helpful
```

**Key Difference**: Moderation prompt is a **judge**, system prompt is a **helper**.

---

## Moderation Prompt Structure

### Required Format

Your moderation prompt MUST:
1. ✅ Clearly define what is HELPFUL
2. ✅ Clearly define VIOLATION types
3. ✅ Request specific JSON output format
4. ✅ Provide examples for consistency

### JSON Output Format

```json
{
  "helpful": true/false,
  "violation": null or "spam"|"toxic"|"off-topic"|"other",
  "quality_score": 0-10,
  "action": "none"|"warn"|"delete",
  "reason": "Brief 1-sentence explanation"
}
```

---

## Template Anatomy

### 1. Introduction
Define the role clearly:
```
You are a content moderator for [GROUP TYPE].
```

### 2. Helpful Content Definition
Be specific about what you WANT:
```
HELPFUL content:
- Answers questions
- Shares knowledge
- Contributes to discussion
- Asks thoughtful questions
```

### 3. Violation Categories
Define what's NOT allowed:
```
VIOLATIONS:
- SPAM: Advertising, promotional content, repeated messages
- TOXIC: Personal attacks, harassment, excessive profanity
- OFF-TOPIC: Unrelated to group purpose
```

### 4. Special Rules (Optional)
Add context-specific guidelines:
```
IMPORTANT:
- Financial advice is OK, medical advice is NOT
- Memes are allowed if relevant
- Constructive criticism is encouraged
```

### 5. Output Format
Always end with JSON schema:
```
Return JSON with these exact fields:
{
  "helpful": true/false,
  "violation": null or "spam"|"toxic"|"off-topic",
  "quality_score": 0-10,
  "action": "none"|"warn"|"delete",
  "reason": "Brief explanation"
}
```

### 6. Examples (Critical!)
Provide 3-5 concrete examples:
```
Examples:
- "Great question! Here's how..." → {"helpful": true, "quality_score": 8, "action": "none"}
- "BUY NOW!!!" → {"helpful": false, "violation": "spam", "action": "delete"}
```

---

## Writing Effective Prompts

### ✅ DO

**Be Specific**
```
❌ BAD:  "Don't allow spam"
✅ GOOD: "SPAM: Repeated promotional messages, affiliate links, MLM schemes"
```

**Define Thresholds**
```
❌ BAD:  "Delete bad content"
✅ GOOD: "Use action: 'delete' for obvious violations (score 8+), 'warn' for borderline (score 5-7)"
```

**Use Examples**
```
❌ BAD:  "Detect toxic behavior"
✅ GOOD: "Toxic examples: 'You're an idiot' (delete), 'That's wrong' (none)"
```

**Consider Context**
```
❌ BAD:  "No off-topic discussions"
✅ GOOD: "OFF-TOPIC: Unrelated to cryptocurrency. Some general chat OK if friendly."
```

**Balance Strictness**
```
❌ BAD:  "Delete everything questionable"
✅ GOOD: "When in doubt, prefer 'warn' over 'delete'. Value learning over punishment."
```

### ❌ DON'T

**Don't Be Vague**
```
❌ "Moderate this group appropriately"
```

**Don't Conflict with System Prompt**
```
❌ "Answer user questions" (that's system_prompt's job)
```

**Don't Forget JSON Format**
```
❌ "Return your evaluation" (without specifying structure)
```

**Don't Over-Penalize**
```
❌ "Delete anything with a link" (too strict, use patterns instead)
```

**Don't Under-Specify**
```
❌ "Detect spam" (what IS spam for your group?)
```

---

## Examples by Group Type

### Crypto/Trading Group

```
You are a content moderator for a cryptocurrency trading group.

HELPFUL content:
- Market analysis with reasoning
- Technical analysis and charts
- Questions about crypto concepts
- Sharing legitimate news sources
- Risk management discussion

VIOLATIONS:
- SPAM: Pump-and-dump schemes, "JOIN MY GROUP", referral spam
- TOXIC: FUD without reasoning, personal attacks
- OFF-TOPIC: Politics, unrelated finance topics

IMPORTANT:
- Price predictions are OK if they include reasoning
- "Buy now" alone is spam; "Buy now because [analysis]" is OK
- Disagreement is healthy; personal attacks are NOT

Return JSON:
{
  "helpful": true/false,
  "violation": null or "spam"|"toxic"|"off-topic",
  "quality_score": 0-10,
  "action": "none"|"warn"|"delete",
  "reason": "Brief explanation"
}

Examples:
- "BTC broke $45k resistance, volume increasing" → {"helpful": true, "quality_score": 8, "action": "none"}
- "🚀🚀🚀 JOIN MY PUMP GROUP 🚀🚀🚀" → {"helpful": false, "violation": "spam", "action": "delete"}
- "This project is a scam, team is incompetent" → {"helpful": false, "violation": "toxic", "quality_score": 2, "action": "warn"}
```

### Tech/Programming Group

```
You are a content moderator for a programming community.

HELPFUL content:
- Code examples and explanations
- Debugging help
- Architecture discussions
- Resource recommendations with context
- Questions (all skill levels)

VIOLATIONS:
- SPAM: Job postings, course promotions, affiliate links
- TOXIC: Belittling beginners, language wars, elitism
- OFF-TOPIC: Non-programming topics

IMPORTANT:
- ALL questions are valid (beginners welcome!)
- "Why don't you Google it?" is TOXIC
- Constructive criticism of code is OK
- Passionate preference != toxic (unless insulting)

Return JSON:
{
  "helpful": true/false,
  "violation": null or "spam"|"toxic"|"off-topic",
  "quality_score": 0-10,
  "action": "none"|"warn"|"delete",
  "reason": "Brief explanation"
}

Examples:
- "Here's how to fix that bug: [code]" → {"helpful": true, "quality_score": 9, "action": "none"}
- "That's a stupid question, Google it" → {"helpful": false, "violation": "toxic", "action": "warn"}
- "Check out my programming course (link)" → {"helpful": false, "violation": "spam", "action": "delete"}
- "I prefer Python but Go is great too" → {"helpful": true, "quality_score": 6, "action": "none"}
```

### Educational Group

```
You are a content moderator for a learning community.

HELPFUL content:
- Questions (ANY level)
- Clear explanations
- Study resources
- Encouraging others
- Constructive feedback

VIOLATIONS:
- SPAM: Course promotions, tutoring ads
- TOXIC: Mocking questions, discouraging learners
- OFF-TOPIC: Unrelated to subject matter

IMPORTANT:
- NO question is stupid
- "Just Google it" is TOXIC
- Mistakes are learning opportunities
- Encourage curiosity

Return JSON:
{
  "helpful": true/false,
  "violation": null or "spam"|"toxic"|"off-topic",
  "quality_score": 0-10,
  "action": "none"|"warn"|"delete",
  "reason": "Brief explanation"
}

Examples:
- "Can someone explain X?" → {"helpful": true, "quality_score": 7, "action": "none"}
- "That's basic, why don't you know this?" → {"helpful": false, "violation": "toxic", "action": "warn"}
- "Enroll in my course to learn" → {"helpful": false, "violation": "spam", "action": "delete"}
```

---

## Tuning Your Prompt

### Testing Process

1. **Start Lenient**
   - Set auto_delete_threshold = 9.0 (very strict)
   - Monitor for false positives
   - Adjust based on results

2. **Collect Examples**
   - Note messages that were wrongly flagged
   - Note messages that should have been flagged
   - Add these as examples to your prompt

3. **Iterate**
   - Refine violation definitions
   - Adjust examples
   - Test again

4. **Fine-Tune Thresholds**
   ```python
   # Lenient
   auto_delete_threshold = 9.5
   auto_warn_threshold = 7.0
   
   # Balanced
   auto_delete_threshold = 8.0
   auto_warn_threshold = 5.0
   
   # Strict
   auto_delete_threshold = 6.0
   auto_warn_threshold = 4.0
   ```

### Common Issues & Fixes

**Issue: Too many false positives**
```
Fix: Add examples of acceptable content
     Lower thresholds
     Add "When in doubt, choose 'none'" guidance
```

**Issue: Missing violations**
```
Fix: Be more specific about what constitutes violation
     Add examples of violations
     Raise quality_threshold for helpful content
```

**Issue: Inconsistent scoring**
```
Fix: Provide clear numerical anchors
     "Score 9-10: Exceptional, detailed help"
     "Score 7-8: Solid contribution"
     "Score 5-6: Acceptable but basic"
     "Score 0-4: Low value or violation"
```

---

## Advanced Techniques

### Dynamic Moderation

Adjust strictness over time:
```
During onboarding (first week):
- More lenient
- Focus on education over punishment
- Lower thresholds

After establishment:
- Standard strictness
- Balanced approach

During spam attacks:
- Temporarily stricter
- Higher sensitivity to patterns
```

### Context-Aware Rules

```
SPAM detection considerations:
- New users: More strict on promotional content
- Established users (100+ messages): More lenient
- Links: Depends on context and user history
```

### Multi-Language Support

```
IMPORTANT:
- Evaluate content in any language
- Spam and toxicity transcend language
- When unsure about language nuance, prefer "warn" over "delete"
```

---

## Quality Score Guidelines

Provide clear anchors:

```
quality_score guidelines:
- 9-10: Exceptional content (detailed help, thorough explanations)
- 7-8: High quality (solid answers, good questions)
- 5-6: Acceptable (basic but OK, relevant)
- 3-4: Low quality (vague, minimal value)
- 0-2: Violations or harmful content
```

---

## Testing Your Prompt

### Manual Testing

1. Send test messages in a test group:
   - Obvious spam
   - Helpful content
   - Borderline cases
   - Edge cases

2. Check moderation results in logs

3. Verify JSON output is valid

4. Adjust prompt based on results

### A/B Testing

1. Try different prompts for 1 day each
2. Compare:
   - False positive rate
   - False negative rate
   - User complaints
   - Message deletion rate

---

## Prompt Library

Use the built-in templates as starting points:

```python
from luka_bot.utils.moderation_templates import get_template

# Available templates:
templates = [
    "general",      # Balanced, fair for any group
    "crypto",       # Crypto/trading focused
    "tech",         # Programming/tech communities
    "educational",  # Learning environments
    "community",    # Social/casual groups
    "business",     # Professional groups
]

# Get a template
prompt = get_template("crypto")

# Customize it
custom_prompt = prompt.replace(
    "IMPORTANT:",
    "IMPORTANT:\n- Our specific rule here\n- Another specific rule"
)
```

---

## Best Practices Summary

1. ✅ **Be explicit** - Define exactly what you want
2. ✅ **Provide examples** - 3-5 concrete cases
3. ✅ **Balance strictness** - Prefer warn over delete
4. ✅ **Test thoroughly** - Start lenient, adjust
5. ✅ **Iterate** - Improve based on real data
6. ✅ **Document changes** - Track what works
7. ✅ **Consider context** - Not all groups are the same
8. ✅ **Respect users** - Encourage improvement, not just punish

---

## FAQ

**Q: How long should my prompt be?**
A: 200-400 words is ideal. Too short = vague, too long = LLM loses focus.

**Q: Should I include group rules?**
A: Yes! But translate them into behavioral guidelines:
- ❌ "Rule 3: No spam" 
- ✅ "SPAM: Promotional content, repeated advertisements..."

**Q: Can I use multiple languages?**
A: The prompt itself should be in English. The LLM will understand and evaluate messages in any language.

**Q: How often should I update my prompt?**
A: Review monthly, or when you notice consistent false positives/negatives.

**Q: What if my prompt isn't working?**
A: Check logs for actual LLM responses, add specific examples for problem cases, adjust thresholds before rewriting prompt.

---

## Resources

- **View your current prompt**: `/moderation` command
- **Apply templates**: `/moderation` → Templates menu
- **Check logs**: Look for "🛡️ Moderation result" in server logs
- **View settings**: Redis key `group_settings:{group_id}`

---

## Conclusion

A well-crafted moderation prompt is the foundation of effective automated moderation. Take time to:
1. Understand your community's needs
2. Write clear, specific guidelines
3. Test and iterate
4. Monitor and adjust

Remember: **The goal is to foster positive community behavior, not just punish violations.**

---

**Version**: 1.0  
**Last Updated**: 2025-10-11  
**See Also**: MODERATION_SYSTEM.md, THREAD_ARCHITECTURE.md

