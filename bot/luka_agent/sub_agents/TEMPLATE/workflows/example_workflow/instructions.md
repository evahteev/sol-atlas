# Example Workflow Instructions

**Workflow:** example_workflow
**Description:** Multi-step guided process demonstrating workflow structure
**Type:** Interactive

---

## Workflow Execution Rules

**CRITICAL:**
1. Execute steps in exact numerical order (1, 2, 3...)
2. Wait for user response when `<ask>` tag is used
3. Save progress after each `<checkpoint>` tag
4. Allow user to skip optional steps
5. Require approval at major milestones

---

## Step 1: Initialize

**Goal:** Gather context and setup workspace

**Actions:**
1. Check if user provided context data
2. Load any reference data if needed
3. Initialize output file from template

**User Interaction:**

<ask response="user_goal">
What would you like to accomplish with this workflow?

Please describe:
1. Your main objective
2. Any constraints or requirements
3. Desired outcome
</ask>

<wait>Wait for user response before continuing</wait>

**Process Response:**
- Store `user_goal` = user's response
- Parse objective, constraints, outcome
- Adapt subsequent steps based on context

**Conditional Logic:**

<check if="user_goal includes specific domain">
  <action>Load domain-specific data from data.csv</action>
  <action>Adjust approach for specialized context</action>
</check>

<check if="user_goal is vague">
  <ask response="clarification">
    Could you elaborate on:
    - What specifically you're trying to achieve
    - Who this is for
    - Any specific requirements
  </ask>
</check>

**Output:**
<checkpoint>
  <save-to-template>
    ## Workflow Context

    **Objective:** {user_goal.objective}
    **Constraints:** {user_goal.constraints}
    **Desired Outcome:** {user_goal.outcome}
    **Date:** {date}
  </save-to-template>

  <show-user>Display saved context</show-user>

  <ask-approval>
    Does this accurately capture your objective?
    [a] Approve and continue
    [e] Edit the context
    [r] Restart from beginning
  </ask-approval>
</checkpoint>

---

## Step 2: Execute Main Process

**Goal:** Core workflow logic - adapt to your specific use case

**Approach Selection:**

<ask response="approach">
How would you like to proceed?

1. **Guided Mode** - I'll walk you through each part step-by-step
2. **Express Mode** - Answer key questions, I'll generate everything
3. **Collaborative Mode** - We'll build this together iteratively

Enter 1-3:
</ask>

<wait>Wait for user selection</wait>

---

### Step 2a: Guided Mode (if approach == 1)

**Goal:** Walk user through detailed process

**Sub-steps:**

<substep n="2a-1" name="Part A">
  <action>Guide user through first component</action>

  <ask response="part_a">
    Let's start with [Component A].

    Question 1: [Specific question]
    Question 2: [Specific question]
  </ask>

  <process>
    - Validate responses
    - Generate content for Part A
    - Show to user
  </process>

  <checkpoint>
    <save-to-template section="Part A">
      ## Part A: {part_a.title}

      {generated_content}
    </save-to-template>

    <ask-approval>
      [a] Approve
      [e] Edit
      [s] Skip for now
    </ask-approval>
  </checkpoint>
</substep>

<substep n="2a-2" name="Part B">
  [Similar structure for Part B]
</substep>

<substep n="2a-3" name="Part C">
  [Similar structure for Part C]
</substep>

---

### Step 2b: Express Mode (if approach == 2)

**Goal:** Quick generation with minimal interaction

<ask response="express_answers">
Let me ask a few key questions, then I'll generate everything:

1. [Key question 1]
2. [Key question 2]
3. [Key question 3]
4. [Key question 4]
5. [Key question 5]
</ask>

<wait>Wait for all answers</wait>

<action>
Generate all content based on express_answers:
- Part A
- Part B
- Part C
- Supporting sections
</action>

<checkpoint>
  <save-to-template>
    [Generated complete content]
  </save-to-template>

  <show-user>Display complete generated content</show-user>

  <ask-approval>
    Review the generated content above.

    [a] Approve all
    [e] Edit specific sections
    [r] Regenerate with different approach
  </ask-approval>
</checkpoint>

---

### Step 2c: Collaborative Mode (if approach == 3)

**Goal:** Iterative co-creation

<iterate cycles="3-5">
  <cycle n="{i}">
    <ask response="cycle_input">
      Cycle {i}: What aspect should we work on?

      Current progress:
      - Part A: {status_a}
      - Part B: {status_b}
      - Part C: {status_c}

      What would you like to add/refine?
    </ask>

    <action>Generate or refine based on cycle_input</action>

    <checkpoint>
      <save-to-template>
        [Updated content]
      </save-to-template>

      <ask-continue>
        [a] Continue with another cycle
        [f] Finalize and move to Step 3
      </ask-continue>
    </checkpoint>
  </cycle>
</iterate>

---

## Step 3: Review and Finalize

**Goal:** Final review, polish, and save

**Actions:**
1. Show complete workflow output
2. Offer final edits
3. Run validation checklist (if configured)
4. Save final version

**Complete Output:**

<action>Compile all sections into final document</action>

<show-user>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORKFLOW COMPLETE - FINAL OUTPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{complete_document}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
</show-user>

**Validation (Optional):**

<check if="checklist.md exists">
  <action>Load validation checklist</action>

  <ask response="validation">
    Let's validate against the checklist:

    {checklist_items}

    Does everything check out?
    [y] Yes, looks good
    [n] No, let me make adjustments
  </ask>

  <check if="validation == 'n'">
    <ask response="adjustments">What needs adjustment?</ask>
    <action>Make requested changes</action>
    <goto>Restart validation</goto>
  </check>
</check>

**Final Save:**

<checkpoint final="true">
  <save-to-file path="{output.default_file}">
    {complete_document}
  </save-to-file>

  <show-user>
    ✅ Workflow complete!

    Saved to: {output.default_file}

    **Summary:**
    - Steps completed: {steps_completed}/{total_steps}
    - Time taken: {elapsed_time}
    - Output size: {document_size} chars

    **Next Steps:**
    - Review the document
    - Share with stakeholders
    - Implement recommendations
  </show-user>
</checkpoint>

---

## Error Handling

### User Abandons Workflow

**Trigger:** User says "stop", "cancel", "quit"

**Action:**
```
<ask response="save_draft">
Would you like to save your progress as a draft?
[y] Yes, save progress
[n] No, discard everything
</ask>

<check if="save_draft == 'y'">
  <save-to-file path="{output_folder}/draft-{date}.md">
    {current_progress}
  </save-to-file>

  <show-user>
    Draft saved to: {output_folder}/draft-{date}.md
    You can resume later by loading this draft.
  </show-user>
</check>

<exit gracefully="true"/>
```

### Invalid User Input

**Trigger:** Response doesn't match expected format

**Action:**
```
<handle-error>
  <show-user>
    I didn't understand that response.

    Expected: {expected_format}
    You entered: {user_response}

    Please try again:
  </show-user>

  <retry question="previous_question" max_attempts="3"/>

  <check if="attempts >= 3">
    <action>Provide example</action>
    <action>Offer help</action>
  </check>
</handle-error>
```

---

## Advanced Features

### YOLO Mode

**Description:** Skip all confirmations, auto-generate everything

**Activation:**
```
User: "y" or "yolo" at any checkpoint
```

**Behavior:**
- Auto-approve all checkpoints
- No user interaction except initial questions
- Fast completion

### Party Mode

**Description:** Creative, playful approach

**Activation:**
```
User: "p" or "party" at any checkpoint
```

**Behavior:**
- Use creative language
- Add humor and personality
- More experimental outputs

### Advanced Elicitation

**Description:** Deep questioning to extract detailed requirements

**Activation:**
```
User: "a" or "advanced" at any checkpoint
```

**Behavior:**
- Load advanced elicitation techniques
- Ask probing follow-up questions
- Build comprehensive context

---

## Integration Points

### Invoke Another Workflow

```xml
<invoke-workflow path="other_workflow">
  <pass-data>
    <variable name="context">{user_goal}</variable>
    <variable name="previous_output">{step_2_output}</variable>
  </pass-data>
</invoke-workflow>
```

### Invoke a Task

```xml
<invoke-task id="create_doc">
  <pass-variable name="document_type">report</pass-variable>
  <pass-variable name="topic">{user_goal.objective}</pass-variable>
</invoke-task>
```

### Switch to Specialist Agent

```xml
<check if="user_needs_specialist">
  <ask response="switch">
    This might be better handled by our [Specialist Agent].
    Would you like me to switch you over?
    [y] Yes, switch
    [n] No, continue here
  </ask>

  <check if="switch == 'y'">
    <switch-to-agent id="specialist_agent">
      <pass-context>{workflow_context}</pass-context>
    </switch-to-agent>
  </check>
</check>
```

---

## Notes for Developers

**When Creating Your Own Workflow:**

1. **Start Simple:** Begin with 3-5 clear steps
2. **Be Specific:** Provide exact questions and expected responses
3. **Checkpoint Often:** Save progress after major sections
4. **Handle Errors:** Plan for unclear input and user abandonment
5. **Test Iteratively:** Try the workflow yourself first

**File Structure:**
```
workflows/my_workflow/
├── workflow.yaml       # Configuration
├── instructions.md     # THIS FILE - Execution steps
├── template.md         # Output template (optional)
├── checklist.md        # Validation checklist (optional)
└── data.csv           # Reference data (optional)
```

**Tags Reference:**
- `<ask>` - Ask user a question (MUST wait for response)
- `<check if="">` - Conditional logic
- `<action>` - Perform an action
- `<checkpoint>` - Save progress and get approval
- `<save-to-template>` - Save to output file
- `<invoke-workflow>` - Call another workflow
- `<invoke-task>` - Call a task
- `<goto>` - Jump to another step
- `<wait>` - Explicit wait for user
- `<iterate>` - Loop through items

---

**This is an example workflow structure. Adapt for your agent's specific needs.**
