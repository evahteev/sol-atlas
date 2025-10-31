# Camunda Architecture Update - October 4, 2025

## 🔄 Major Design Change: Thread-Workflow Binding

### What Changed

**Original Design (v1.0):**
- Thread = Camunda process instance
- One-to-one relationship
- Thread controls managed via Camunda

**New Design (v2.0):**
- **Workflows are launched FROM threads**
- **Results are delivered BACK to threads**
- Thread-workflow binding via `source_thread_id`
- Mimics Camunda Tasklist/Cockpit in Telegram

---

## 🎯 Core Principle

> **Workflows are launched from specific threads and deliver results back to those threads.**

This creates a **context-aware workflow execution model** where:
- User starts workflow from a conversation thread
- Workflow stores `source_thread_id` as process variable
- All tasks and results delivered to source thread
- Bot auto-switches to thread when tasks arrive
- `/tasks` command shows all tasks grouped by thread

---

## 📐 Architecture Changes

### 1. Thread Model Extension

**Added Fields:**
```python
class Thread:
    # ... existing fields ...
    
    # NEW: Workflow binding
    active_workflows: List[str] = []  # Process instance IDs
    workflow_results: List[Dict] = []  # Cached results
    
    # Enhanced (not removed)
    process_instance_id: Optional[str]  # Primary workflow
```

**Two Relationship Types:**

1. **Thread IS a Workflow** (original, still valid)
   - `process_instance_id` points to `chatbot_thread` BPMN
   - Used for: Conversational threads with workflow controls

2. **Thread LAUNCHES Workflows** (NEW)
   - `active_workflows` lists workflows launched from thread
   - Used for: Background jobs, scheduled tasks, analysis workflows

---

### 2. Workflow Launch Flow

```python
# User in Thread A: "Analyze YouTube: https://..."
process_id = await workflow_service.launch_workflow(
    thread_id="thread_a_uuid",
    workflow_type="youtube_analysis",
    variables={"video_url": "https://..."},
    user_id=922705
)

# Camunda stores:
# {
#   "source_thread_id": "thread_a_uuid",  ← KEY BINDING
#   "user_id": 922705,
#   "workflow_type": "youtube_analysis",
#   "video_url": "https://..."
# }
```

---

### 3. Auto-Switching on Task Notification

```python
# When task arrives via WebSocket:
async def handle_task_notification(task_id):
    # 1. Get task from Camunda
    task = await camunda_client.get_task(task_id)
    
    # 2. Read source_thread_id from process variables
    variables = await camunda_client.get_process_variables(
        task.process_instance_id
    )
    source_thread_id = variables["source_thread_id"]
    
    # 3. AUTO-SWITCH to source thread
    await thread_service.set_active_thread(user_id, source_thread_id)
    
    # 4. Render task in thread
    await task_service.render_task_in_thread(task_id, source_thread_id)
```

---

### 4. /tasks Command - Camunda Tasklist in Telegram

**New Command:** `/tasks`

**Shows:**
```
📋 Your Active Tasks (5)

🧵 Thread: Python Learning (3 tasks)
  ├─ ⚙️ [chatbot_thread] Configure Model
  ├─ 📚 [kb_search] Review Results
  └─ ✅ [control_add_kb] Add Knowledge Base

🧵 Thread: Video Analysis (2 tasks)
  ├─ 🎥 [youtube_analysis] Extract Timestamps
  └─ 📝 [youtube_analysis] Generate Summary

[Tap any task to open in its thread]
```

**Interaction:**
1. User taps task from `/tasks`
2. Bot auto-switches to source thread
3. Task rendered in thread context
4. User completes task
5. Result delivered back to same thread

**Mimics:**
- Camunda Tasklist (all tasks in one view)
- Camunda Cockpit (grouped by process/workflow)

---

## 🔧 Implementation Changes

### Phase 4 Implementation Plan Updated

**New Deliverables:**
1. Thread model extension (`active_workflows`, `workflow_results`)
2. `WorkflowService.launch_workflow(thread_id, ...)` - Bind to thread
3. `TaskService.group_tasks_by_thread()` - Group for `/tasks`
4. `TaskService.handle_task_notification()` - Auto-switch logic
5. `/tasks` command handler - Tasklist/Cockpit UX
6. Auto-switching on task interaction

**New Files (~600 lines):**
- `services/camunda_client.py` (150 lines)
- `services/workflow_service.py` (200 lines)
- `services/task_service.py` (150 lines)
- `handlers/tasks_menu.py` (100 lines)
- Update `models/thread.py` (+20 lines)

**Estimate:** 4-5 hours (up from 3-4)

---

## 📊 Use Case Example

### YouTube Video Analysis

```
Thread A: "Learning Python"
  │
  ├─ User: "Analyze this: https://youtube.com/..."
  │
  ├─ Bot: "🚀 Starting youtube_analysis workflow..."
  │   │
  │   └─► Camunda: Start Process (source_thread_id: "thread_a")
  │
  ├─ [Workflow executes]
  │   ├─ Extract transcript
  │   ├─ Create task: "Review timestamps"
  │   └─ Generate summary
  │
  ├─ Bot: "✅ Transcript extracted!"
  │   [Auto-delivered to Thread A]
  │
  ├─ Bot: "📋 New task: Review timestamps"
  │   [Notification via WebSocket]
  │   [Auto-switch to Thread A]
  │   [Task rendered in Thread A]
  │
  ├─ User: [Completes task]
  │
  └─ Bot: "✨ Analysis complete! Summary..."
      [Final result in Thread A]


Meanwhile, user can:
  └─ /tasks → See all tasks across all threads
  └─ Tap any task → Auto-switch to its thread
```

---

## ✅ Benefits

### User Experience
- ✅ **Context preservation**: Results appear where they make sense
- ✅ **No context loss**: Auto-switching keeps conversation coherent
- ✅ **Familiar UX**: Mimics Camunda Tasklist/Cockpit
- ✅ **Clean separation**: Threads (UI) + Workflows (logic)

### Technical
- ✅ **Scalable**: Multiple workflows per thread
- ✅ **Flexible**: Two relationship types (IS vs LAUNCHES)
- ✅ **Simple**: One binding variable (`source_thread_id`)
- ✅ **Robust**: Fallback to active thread if binding missing

### Product
- ✅ **Workflow visibility**: See which workflows running where
- ✅ **Task management**: All tasks in one view
- ✅ **Background jobs**: Long-running workflows don't block UI
- ✅ **Scheduled tasks**: Periodic results delivered to thread

---

## 📝 Documentation Updates

### Updated Documents:
1. **`docs/luka_bot.md`** - Main PRD
   - Section 6: Workflows Integration (completely rewritten)
   - Section 3: /tasks command (enhanced)
   - Phase 4 implementation plan (updated)

2. **`docs/CAMUNDA_THREAD_ARCHITECTURE.md`** - NEW
   - Detailed architecture document
   - Data flow diagrams
   - Implementation checklist
   - Use case examples

3. **`llm_bot/CAMUNDA_ARCHITECTURE_UPDATE.md`** - NEW (this doc)
   - Change summary
   - Migration guide

---

## 🚀 Next Steps

### Phase 4 Implementation (4-5 hours)

1. **Thread Model** (30 min)
   - Add `active_workflows` field
   - Add `workflow_results` field
   - Update serialization

2. **Camunda Client** (1 hour)
   - Copy from `bot_server`
   - Adapt for standalone
   - Add `source_thread_id` support

3. **Workflow Service** (1.5 hours)
   - `launch_workflow()` with thread binding
   - `deliver_result_to_thread()`
   - Thread-workflow management

4. **Task Service** (1 hour)
   - `fetch_user_tasks()`
   - `group_tasks_by_thread()`
   - `handle_task_notification()` with auto-switch
   - `render_task_in_thread()`

5. **/tasks Command** (1 hour)
   - Handler implementation
   - Task grouping UI
   - Callback handling
   - Auto-switch on tap

6. **Testing** (1 hour)
   - Launch workflow from thread
   - Verify task notification → auto-switch
   - Test result delivery
   - Test /tasks command

---

## 🎯 Success Criteria

- [x] Architecture documented
- [ ] Thread model extended
- [ ] Workflows launch with `source_thread_id`
- [ ] Tasks grouped by thread in `/tasks`
- [ ] Auto-switch on task notification
- [ ] Results delivered to source thread
- [ ] Multiple workflows per thread supported
- [ ] Mimics Camunda Tasklist/Cockpit UX

---

## 📚 References

- **Main PRD:** `docs/luka_bot.md`
- **Architecture Doc:** `docs/CAMUNDA_THREAD_ARCHITECTURE.md`
- **Thread Model:** `llm_bot/models/thread.py`
- **Reference Implementation:** `bot_server/services/camunda.py`

---

**Status:** ✅ Design Complete  
**Next:** Begin Phase 4 Implementation  
**Updated:** October 4, 2025

