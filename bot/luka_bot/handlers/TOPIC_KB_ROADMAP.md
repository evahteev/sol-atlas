# Topic-Specific Knowledge Bases - Implementation Roadmap

## Current State

**Status:** Topics are detected and tracked, but all messages use the group-wide KB

**How it works now:**
- Group messages → `tg-kb-group-{group_id}`
- Topic messages → Same `tg-kb-group-{group_id}` (with thread_id in metadata)
- Search searches entire group, not individual topics

**Example:**
```
Group: -1002493387211
KB: tg-kb-group-1002493387211

Topic 1 (ID: 12345) → Messages go to group KB
Topic 2 (ID: 67890) → Messages go to group KB  
Topic 3 (ID: 99999) → Messages go to group KB
```

## Proposed Implementation

### Phase 1: Separate KB Per Topic ✅

**Goal:** Each topic gets its own KB index

**Changes needed:**

1. **KB Index Naming Convention:**
   ```python
   # Group-wide (general chat)
   tg-kb-group-{group_id}
   
   # Topic-specific
   tg-kb-group-{group_id}-topic-{thread_id}
   ```

2. **Update `group_service.py`:**
   ```python
   async def get_topic_kb_index(
       self, 
       group_id: int, 
       thread_id: int
   ) -> Optional[str]:
       """Get KB index for a specific topic."""
       return f"{settings.ELASTICSEARCH_GROUP_KB_PREFIX}{abs(group_id)}-topic-{thread_id}"
   ```

3. **Update `handle_group_message` in `group_messages.py`:**
   ```python
   # Determine which KB to use
   if thread_id:
       kb_index = f"{kb_index}-topic-{thread_id}"
   ```

4. **Update `/search` command:**
   - Show topics as separate searchable items
   - Allow filtering by specific topics

### Phase 2: Topic Metadata & Management 🔄

**Goal:** Rich topic management and discovery

**Features:**
- Track topic creation dates
- Store topic names/descriptions
- Topic activity metrics
- Topic member lists

**Data Model:**
```python
class TopicLink:
    group_id: int
    thread_id: int
    topic_name: str
    kb_index: str
    created_at: datetime
    message_count: int
    last_activity: datetime
```

### Phase 3: Advanced Topic Search 🔮

**Goal:** Powerful topic-specific search capabilities

**Features:**
- Search within a single topic
- Search across multiple selected topics
- Cross-topic search with filtering
- Topic similarity search
- "Find similar discussions" across topics

**Search UI:**
```
/search command shows:

📋 Select Knowledge Bases:

👤 Personal KB (1,234 messages)
👥 Axioma-GURu Group (5,678 messages)
  🧵 Deployment Updates (234 messages)
  🧵 Bug Reports (456 messages)
  🧵 Feature Requests (890 messages)
```

## Implementation Priority

### High Priority (Implement Soon)
- [x] Detect and track topic IDs ✅
- [x] Show topic information in welcome messages ✅
- [ ] Separate KB index per topic
- [ ] Update elasticsearch indexing to use topic-specific KBs
- [ ] Update search to show topics as separate options

### Medium Priority
- [ ] Topic metadata storage (TopicLink model)
- [ ] Topic activity tracking
- [ ] Topic-specific search filtering

### Low Priority
- [ ] Cross-topic similarity search
- [ ] Topic analytics
- [ ] Topic recommendations

## Technical Considerations

### Storage Impact
**Current:** 1 KB index per group (all topics combined)
**Proposed:** 1 KB index per group + 1 KB index per topic

**Example calculation:**
- Group with 10 topics
- Each topic has 500 messages
- Total: 5,000 messages

**Current storage:**
```
1 index × 5,000 messages = 5,000 documents
```

**Proposed storage:**
```
Group index: ~0 messages (general chat only)
10 topic indices: 500 messages each = 5,000 documents
Total: Still 5,000 documents, just organized differently
```

**Impact:** Minimal additional storage, better organization

### Search Performance
- **Pro:** Faster topic-specific searches (smaller indices)
- **Pro:** Better relevance (topic-focused results)
- **Con:** Cross-topic search requires multi-index query
- **Mitigation:** Elasticsearch handles multi-index queries efficiently

### Migration Path
For existing groups with messages:
1. Create topic-specific indices
2. Re-index existing messages to topic-specific KBs
3. Keep group-wide KB for backward compatibility
4. Gradual migration over time

## Benefits

✅ **Better organization** - Each topic is self-contained
✅ **Faster search** - Smaller indices = faster queries
✅ **Better relevance** - Results are topic-specific
✅ **Scalability** - Large groups with many topics stay performant
✅ **Flexibility** - Users can choose which topics to search

## Example User Flow

**Before (Current):**
```
User: /search
Bot: Select KB:
  ☐ Personal KB
  ☐ Axioma-GURu Group

User: [Selects group]
User: "How do we deploy?"
Bot: [Returns results from ALL topics mixed together]
```

**After (Proposed):**
```
User: /search
Bot: Select KB:
  ☐ Personal KB
  ☐ Axioma-GURu Group (general chat)
  ☐ Axioma-GURu › Deployment Updates
  ☐ Axioma-GURu › Bug Reports
  ☐ Axioma-GURu › Feature Requests

User: [Selects "Deployment Updates"]
User: "How do we deploy?"
Bot: [Returns results only from Deployment Updates topic]
```

## Next Steps

1. **Design decision:** Confirm approach with team
2. **Implement** separate KB indexing per topic
3. **Update** search UI to show topics
4. **Test** with real group data
5. **Monitor** performance and storage impact
6. **Iterate** based on user feedback

## Questions to Resolve

- Should general chat (no topic) have its own KB or share with topics?
- How to handle topic deletion? Archive KB or delete it?
- Should we backfill existing messages into topic-specific KBs?
- UI: Show topics as nested or flat list in /search?
- Should topic KB creation be automatic or manual?

---

**Status:** Planning phase
**Next action:** Get feedback and begin implementation
**ETA:** Can be implemented in current sprint if approved

