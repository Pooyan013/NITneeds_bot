# NIT Needs Telegram Bot

**NIT Needs** is a Telegram bot that helps users post and manage various requests. Categories include "For Sale," "Requested," "Questions," "Lost & Found," and more. The bot ensures users are subscribed to the related channel and allows admins to review, approve, or reject requests. It also supports broadcasting messages and timed actions for user requests.

---

### Features

* **User Interaction**:

  * Users can submit requests in multiple categories.
  * Joining the related Telegram channel is required to interact with the bot.
  * Requests are sent to admins for approval or rejection.

* **Admin Panel**:

  * Admins can view and manage user requests.
  * Admin roles determine which categories they handle.
  * Admins receive notifications if a request remains pending for over an hour.

* **Broadcasting**:

  * Admins can send messages, photos, or videos to all users.

* **Timed Actions**:

  * User requests have a time limit. If no message is sent in time, the request will be canceled.

* **Advanced Request Handling**:

  * Categories include "For Sale," "Requested," "Questions," "Lost & Found," "Roommates," etc.
  * Admins can manage each category with specific actions.

---

### Installation

Requires **Python 3.6+**.

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/nit-needs-bot.git
   cd nit-needs-bot
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the bot**:

   ```bash
   python bot/main.py
   ```

