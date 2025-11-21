# Conversational Trip Planning Workflow - Implementation Guide

## What Changed?

The trip planner workflow has been redesigned from a **tool-focused, linear flow** to a **conversational, iterative, consultative experience**.

### Before (v2.0.0)
- Linear steps: Discover → Select → Execute → Complete
- All stops shown at once
- Tool-focused presentation
- Quick (90-120 seconds)

### After (v3.0.0)
- Conversational steps: Greet → Discover → Plan → Iterate → Celebrate
- Stops suggested **one at a time**
- Human-like consultative approach
- Natural conversation (3-5 minutes)

## Key Improvements

### 1. Iterative Building
**Old:** Show all stops from `plan_trip` at once
**New:** Suggest stops one by one, ask before adding, celebrate each addition

### 2. Natural Conversation
**Old:** "What kind of traveler are you?" (form-like)
**New:** "What makes a trip special for you?" (conversational)

### 3. Consultative Approach
**Old:** Present results, offer next actions
**New:** Ask questions, understand preferences, make personalized suggestions

### 4. Draft Integration
**Old:** Draft saved once at the end
**New:** Draft built incrementally, updated after each confirmed addition

### 5. Strategic Hidden Gems
**Old:** Always offer hidden gems after planning
**New:** Offer strategically when user shows interest, present one at a time

## Workflow Structure

```
1. Warm Greeting & Route Basics
   ↓
2. Interest Discovery (Conversational)
   ↓
3. Plan Initial Route (Base route only)
   ↓
4. Suggest First Stop (One at a time)
   ↓
5. Iterative Stop Suggestions (Loop)
   ├─→ Suggest stop
   ├─→ Ask: "Add it?"
   ├─→ If yes: Add to draft, celebrate
   ├─→ If no: Offer alternative
   └─→ Repeat until user says "enough"
   ↓
6. Strategic Hidden Gems (When requested)
   └─→ Same iterative flow
   ↓
7. Final Review & Celebration
```

## How It Works

### Step-by-Step Flow

1. **Greeting**: Warm welcome, discover origin/destination
2. **Interests**: Natural conversation about preferences
3. **Base Route**: Plan route, save draft, show overview
4. **First Stop**: Find ONE perfect stop, ask before adding
5. **Iterative Loop**: Continue suggesting, one at a time
6. **Hidden Gems**: Offer strategically, same iterative approach
7. **Review**: Celebrate, show complete trip, offer next steps

### Key Behaviors

- **Never overwhelm**: Max 1-2 suggestions at once
- **Always ask**: "Would you like to add [location]?"
- **Celebrate**: "Perfect! [Location] is now part of your journey! 🎉"
- **Show progress**: Display updated trip after each addition
- **Know when to stop**: Suggest wrapping up after 5-7 stops

## Tool Usage

### Tools Used
- `plan_trip` - Create base route (auto-saves draft)
- `suggest_route_stops` - Find stops matching interests
- `add_location_to_draft` - Add confirmed stops incrementally
- `discover_hidden_gems` - Find underrated treasures
- `get_location_details` - Get more info when user asks
- `load_trip_draft` - Show final complete trip

### Tool Orchestration
- Tools support conversation, not drive it
- Agent decides when to call tools based on user responses
- Each tool call is purposeful and contextual

## Example Interaction

```
User: "I want to plan a trip from Prague to Vienna"

Bot: "Hi! 👋 I'm excited to help you plan an amazing trip!
      Perfect! Prague to Vienna - that's a fantastic route! 🗺️
      
      Before I suggest stops, what makes a trip special for you?
      Are you into 🏰 history, 🍷 wine, 🌄 nature, or 🎨 culture?"

User: "I love wine and historic places"

Bot: "Perfect! I'll keep that in mind. Let me map out your route..."
      [Calls plan_trip]
      "Great! Your trip is saved. Now, based on your love of wine and history,
      I found something special:
      
      **Mikulov Wine Region**
      ⭐ Quality: 4.5/5
      📍 Just 15 km from your route
      🎯 Perfect for: Wine tasting + historic castle
      
      Would you like to add this to your trip?"

User: "Yes, add it!"

Bot: "Perfect! Mikulov is now part of your journey! 🎉
      Your trip: Prague → Mikulov → Vienna
      
      Would you like me to find another special stop?"

User: "Sure, maybe something less touristy?"

Bot: "Great choice! 💎 I found a hidden gem:
      
      **Sonberk Winery** (Hidden Gem)
      ⭐ Quality: 4.8/5
      👥 Only visited by ~2K travelers (vs 50K for mainstream spots)
      Authentic local experience, amazing views
      
      Want to add it?"

User: "Yes!"

Bot: "Perfect! Sonberk Winery is now part of your journey! 🎉
      Your trip: Prague → Mikulov → Sonberk Winery → Vienna
      
      Want to add another stop, or review your complete trip?"

User: "That's enough, show me my trip"

Bot: "🎉 Amazing! Your personalized trip is ready!
      [Shows complete trip with all details]
      Your trip has been saved - you can edit it anytime!"
```

## Implementation Notes

### State Management
- Workflow tracks: origin, destination, interests, draft_id, stops added
- Each step passes context to next step
- Draft is updated incrementally

### Loop Handling
- Step 5 (`iterative_stop_suggestions`) can loop multiple times
- Agent decides when to continue or wrap up
- User can exit loop anytime: "that's enough", "show my trip", etc.

### Error Handling
- If user rejects stop: Offer alternative or ask what they prefer
- If draft save fails: Log error, continue conversation
- If no stops found: Apologize, offer to search differently

## Testing Checklist

- [ ] Workflow starts with warm greeting
- [ ] Origin/destination captured correctly
- [ ] Interests discovered naturally
- [ ] Base route planned and draft saved
- [ ] First stop suggested with quality metrics
- [ ] User can accept/reject suggestions
- [ ] Draft updated after each addition
- [ ] Hidden gems offered strategically
- [ ] Final trip review shows all stops
- [ ] Draft accessible for editing

## Migration Notes

### For Existing Users
- New workflow is backward compatible
- Existing drafts still accessible
- Old workflow can coexist (different domain)

### For Developers
- Workflow uses same tools, just orchestrated differently
- No breaking changes to tool APIs
- Draft structure unchanged

## Next Steps

1. **Test the workflow** with real users
2. **Monitor metrics**: Completion rate, stops added, time to complete
3. **Iterate**: Adjust based on user feedback
4. **Enhance**: Add more personalization, smarter suggestions

## Questions?

- See `config.yaml` for detailed step instructions
- See `README.md` for workflow overview
- Check tool documentation for API details

