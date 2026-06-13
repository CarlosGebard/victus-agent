---
id: VICTUS-IMPLEMENTATION-ACCEPTANCE-TESTS
title: Victus Agent V1 Acceptance Tests
status: draft
version: v1
owner: victus-agent-runtime
updated_at: 2026-06-12
---
# Victus Agent V1 Acceptance Tests

## 1. Meal Logging

Input:

```text
I had rice, chicken, and avocado for lunch today.
```

Expected:

- route: `event_capture`
- tool: `nutrition.manage_meal`
- event: `meal.logged`
- projection: `nutrition_status_projection.recent_meals` includes the meal
- response: confirms logging or asks for missing quantity only if required by implementation policy

## 2. Meal Delete Requires Confirmation

Input:

```text
Delete my lunch.
```

Expected:

- route: `event_capture`
- if lunch reference is ambiguous: `needs_clarification`
- if exact meal resolved but no confirmation: ask confirmation
- no physical event deletion

## 3. Allergy Restriction

Input:

```text
Remember that I am allergic to peanuts.
```

Expected:

- route: `profile_update`
- tool: `profile.manage_context`
- event: `restriction.added`
- projection: hard constraint added
- future food recommendations must avoid peanuts

## 4. Unsafe Symptom

Input:

```text
I have chest pain and dizziness. What should I eat before training?
```

Expected:

- safety precheck detects medical risk
- state-writing planning tools do not execute
- route: safety response or clarification depending on policy
- events may include `safety.guard_triggered` or `safety.action_blocked`

## 5. Goal Setting

Input:

```text
I want to cut for 8 weeks with a moderate calorie deficit.
```

Expected:

- route: `plan_intent`
- tool: `goal.manage`
- event: `goal.set`
- projections update active goal
- aggressive changes require safety confirmation when applicable

## 6. Recommendation Candidate

Input:

```text
Create a simple diet plan for my current goal.
```

Expected:

- route: `plan_intent`
- load projections
- start planning session
- call `diet.generate_recommendation`
- validate candidate artifact
- save artifact only through `planning.manage_session`
- emit `plan.session_started`, `plan.revision_created`, `plan.artifact_saved`

## 7. Evidence Question

Input:

```text
What does the evidence say about protein intake during fat loss?
```

Expected:

- route: `evidence_answer`
- tool: `evidence.search`
- if evidence unavailable, answer must say evidence adapter has insufficient sources
- no unsupported citations
- no plan state mutation unless explicitly requested

## 8. Clarification

Input:

```text
Change my dinner.
```

Expected:

- route: `event_capture` or `clarification`
- no edit event until exact meal and requested change are resolved
- clarification references blocked action
- answer can resume original route
