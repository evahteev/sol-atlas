# Example Task: Create Document

**Task ID:** `create_doc`
**Description:** Guide user through creating a structured document
**Elicit:** Yes (requires user interaction)
**Type:** Interactive workflow

---

## Task Configuration

```yaml
task:
  id: "create_doc"
  name: "Create Document"
  description: "Guide user through creating a structured document"
  author: "luka_agent"
  elicit: true  # Requires user interaction

  # Variables that can be passed when invoking
  variables:
    document_type: "Document type (report, proposal, guide, etc.)"
    topic: "Main topic or subject"
    audience: "Target audience"

  # Output configuration
  output:
    default_file: "documents/{document_type}-{topic}-{date}.md"
    template: "sub_agents/[AGENT_ID]/templates/document_template.md"
```

---

## Execution Steps

### Step 1: Gather Context

**Goal:** Understand what document the user wants to create

**Actions:**
1. Ask user what type of document they want to create
2. If not specified, present options:
   - Report (analysis, findings, recommendations)
   - Proposal (pitch, project plan, business proposal)
   - Guide (how-to, tutorial, documentation)
   - Summary (meeting notes, article summary)
   - Other (user specifies)

**User Interaction:**
```
Agent: "What type of document would you like to create?"
Options: report, proposal, guide, summary, other

User: [Responds with choice]
```

**Store:**
- `document_type` = user's choice
- `topic` = main subject

**Next:** Step 2

---

### Step 2: Define Scope

**Goal:** Determine document scope and key sections

**Actions:**
1. Ask about the main topic/subject
2. Ask about target audience
3. Ask about key points to cover
4. Determine document structure

**User Interaction:**
```
Agent: "Let's define the scope:
1. What's the main topic?
2. Who is the audience?
3. What key points should we cover?"

User: [Provides answers]
```

**Store:**
- `topic` = main topic
- `audience` = target audience
- `key_points` = list of key points

**Next:** Step 3

---

### Step 3: Generate Outline

**Goal:** Create document outline for user review

**Actions:**
1. Based on document_type, generate appropriate structure
2. Include key_points in relevant sections
3. Present outline to user
4. Get feedback and iterate

**Example Output:**
```markdown
# [Topic] - [Document Type]

## Executive Summary
- Overview
- Key findings/recommendations

## Introduction
- Background
- Purpose
- Audience

## Main Content
[Sections based on key_points]

## Conclusion
- Summary
- Next steps

## Appendix (if needed)
```

**User Interaction:**
```
Agent: [Shows outline]
"Does this structure work for you?
 [a] Approve and continue
 [e] Edit sections
 [r] Regenerate with different approach"

User: [Chooses option]
```

**Conditional:**
- If `e` (edit): Go to Step 3a (Edit Outline)
- If `r` (regenerate): Go to Step 2
- If `a` (approve): Go to Step 4

---

### Step 3a: Edit Outline (Optional)

**Goal:** Refine outline based on user feedback

**Actions:**
1. Ask what sections to add/remove/modify
2. Update outline
3. Show updated version
4. Return to Step 3 for approval

---

### Step 4: Generate Content

**Goal:** Create document content section by section

**Actions:**
1. For each section in outline:
   - Generate content
   - Show to user
   - Get approval or edits
2. Save progress after each section

**User Interaction:**
```
Agent: [Generates section]
"
## Introduction

[Generated content...]

Does this section work?
[a] Approve and continue to next section
[e] Edit this section
[s] Skip this section for now"

User: [Chooses option]
```

**Template Output:**
- After each approved section, save to output file
- Show progress: "Completed 2/5 sections"

**Next:** Repeat for all sections, then Step 5

---

### Step 5: Review and Finalize

**Goal:** Final review and save complete document

**Actions:**
1. Show complete document
2. Offer final edits
3. Save to output file
4. Provide document summary

**User Interaction:**
```
Agent: "Here's your complete document:

[Full document content]

Options:
[a] Approve and save
[e] Make final edits
[c] Cancel and save as draft"

User: [Chooses option]
```

**Final Output:**
- Save document to: `documents/{document_type}-{topic}-{date}.md`
- Confirm location and file name

---

## Error Handling

### User Abandons Mid-Task

**Detection:** User says "stop", "cancel", "nevermind"

**Action:**
1. Confirm abandonment: "Would you like to save progress as a draft?"
2. If yes: Save current state
3. If no: Discard progress
4. Exit task gracefully

### User Provides Unclear Input

**Detection:** Response is vague or ambiguous

**Action:**
1. Clarify: "I want to make sure I understand. Do you mean..."
2. Provide examples
3. Repeat question with more context

---

## Usage in Agent

To invoke this task from an agent:

```markdown
User: "Help me create a report"

Agent: [Recognizes need for structured document creation]
"I can guide you through creating a structured report. Let me start the document creation workflow..."

[Invokes: create_doc task]
[Follows steps 1-5]
```

In system_prompt.md:
```markdown
### Creating Documents

When user wants to create a structured document, use the create_doc task:

**Trigger keywords:**
- "create document"
- "write report"
- "make proposal"
- "draft guide"

**Usage:**
Invoke: create_doc task
Let task guide the interaction
```

---

## Notes

- **Elicit flag:** This task requires user interaction at each step
- **Save progress:** Use template-output tags after major sections
- **Flexible:** Allow user to skip, edit, regenerate at any point
- **Transparent:** Always show what you're doing and why

---

**This is an example task structure. Adapt for your agent's specific needs.**
