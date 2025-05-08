# In-App Notification Examples

This document shows examples of how various notifications would appear in the application's user interface.

## Hospital Registration Notification

When a hospital approves a user's registration, the user will receive the following notification:

### Notification Bell (Unread Badge)

```
 🔔 (1)
```

### Notification Panel

```
━━━━━━━━━━━━━━━━━━ Notifications ━━━━━━━━━━━━━━━━━━

📋 Hospital Registration Approved           NEW
────────────────────────────────────────────────
Your registration with St. Nicholas Hospital Lagos 
has been approved. You can now book appointments 
and access services.

5 minutes ago
────────────────────────────────────────────────

[Mark all as read]                 [Delete read]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Mobile View

```
┌─────────────────────────────────┐
│           Notifications         │
├─────────────────────────────────┤
│ 📋 Hospital Registration        │
│ Approved                    NEW │
│                                 │
│ Your registration with St.      │
│ Nicholas Hospital Lagos has     │
│ been approved. You can now book │
│ appointments and access         │
│ services.                       │
│                                 │
│ 5 minutes ago                   │
└─────────────────────────────────┘
```

## Clinical Note Notification

When a new clinical note is added to a patient's record, they will receive:

### Notification Bell (Unread Badge)

```
 🔔 (2)
```

### Notification Panel

```
━━━━━━━━━━━━━━━━━━ Notifications ━━━━━━━━━━━━━━━━━━

📝 Progress Note Finalized                 NEW
────────────────────────────────────────────────
Your progress note has been finalized and is 
ready for review.

10 minutes ago
────────────────────────────────────────────────

📋 Hospital Registration Approved           
────────────────────────────────────────────────
Your registration with St. Nicholas Hospital Lagos 
has been approved. You can now book appointments 
and access services.

2 hours ago
────────────────────────────────────────────────

[Mark all as read]                 [Delete read]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Test Results Notification

When test results become available:

### Notification Panel

```
━━━━━━━━━━━━━━━━━━ Notifications ━━━━━━━━━━━━━━━━━━

🔬 Test Results Available                  NEW
────────────────────────────────────────────────
Your blood test results are now available.

Just now
────────────────────────────────────────────────

📝 Progress Note Finalized                  
────────────────────────────────────────────────
Your progress note has been finalized and is 
ready for review.

10 minutes ago
────────────────────────────────────────────────

📋 Hospital Registration Approved           
────────────────────────────────────────────────
Your registration with St. Nicholas Hospital Lagos 
has been approved. You can now book appointments 
and access services.

2 hours ago
────────────────────────────────────────────────

[Mark all as read]                 [Delete read]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Frontend Implementation Details

When implementing the notification UI, it should:

1. Show a count of unread notifications on the bell icon
2. Display notifications in reverse chronological order (newest first)
3. Highlight unread notifications with a visual indicator (e.g., "NEW" tag, bold text, or background color)
4. Show relative time for recent notifications ("Just now", "5 minutes ago")
5. Show action buttons for marking notifications as read and deleting read notifications
6. Allow clicking on a notification to:
   - Mark it as read
   - Navigate to the relevant section of the app (when applicable)

Each notification type can have a specific icon that helps users quickly identify the category:
- 📋 Hospital-related notifications
- 🔬 Test results notifications
- 📝 Clinical notes/medical records notifications
- 💊 Prescription notifications
- 📅 Appointment notifications
- 💰 Payment notifications 