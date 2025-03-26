# NIT Needs Telegram Bot

This is a Telegram bot designed to help users post and manage requests, such as "for sale," "requested," "lost and found," "questions," and more. The bot integrates with a channel to ensure users are subscribed before interacting with the bot. It also provides administrators with the ability to review and approve or reject requests from users. The bot can handle various user requests, notify admins when requests are pending for too long, and send bulk messages to all users.

---

### Features

- **User Interaction**:
  - Users can post requests related to "for sale," "requested," "lost and found," "questions," and more.
  - Users must join the associated Telegram channel to use the bot.
  - Requests are sent to admins for approval, after which they are either posted to the channel or rejected.
  
- **Admin Panel**:
  - Admins can view and approve or reject user requests.
  - Admin roles are defined to categorize the requests they handle.
  - Admins are notified if a request goes unprocessed for over an hour.

- **Broadcasting**:
  - Admins can broadcast messages to all users.

- **Timed Actions**:
  - User requests have a time limit; if no message is sent within a given time, the request will be canceled.
  
- **Multi-faceted Request Handling**:
  - Categories include: "for sale," "requested," "questions," "lost and found," "roommates," etc.
  - Admins can manage each category with a specific set of actions.

---

### Installation

To run this bot, you need Python 3.6 or higher.

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/nit-needs-bot.git
   cd nit-needs-bot
