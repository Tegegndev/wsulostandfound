# WSU Lost & Found Telegram Bot

A Telegram bot that helps Wolaita Sodo University (WSU) community members report and find lost items. Users can post lost or found items, browse listings, search by keyword, and contact item owners — all through Telegram.

## Screenshot

![WSU Lost & Found Bot Screenshot](https://github.com/user-attachments/assets/03985e5d-4d24-40e1-b9db-9c7fe465539a)

## Features

- **User Registration** — new users share their phone number to register before using the bot
- **Channel Membership Gate** — users must join the official channel to access bot features
- **Post Lost / Found Items** — guided multi-step flow to submit a lost or found item for admin review
- **Admin Moderation** — every submission is sent to the admin for approval or rejection before it appears publicly
- **Channel Publishing** — approved posts are automatically published to the Telegram channel with a "Contact Owner" deep-link button
- **Browse Listings** — paginated list of active items (5 per page) with Prev/Next navigation
- **Keyword Search** — search across item names and descriptions
- **Multilingual Support** — English (`en`), Amharic (`am`), and Afaan Oromoo (`om`)
- **Language Preference** — users can change their preferred language; the setting is persisted in the database

## Bot Commands

| Command | Description |
|---|---|
| `/start` | Start the bot, register, or view the main menu |
| `/list` | Browse all active lost & found items (paginated) |
| `/search <keyword>` | Search items by keyword |
| `/post_lost` | Submit a lost item report |
| `/post_found` | Submit a found item report |

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12+ |
| Telegram API | [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) (`telebot`) |
| Database | [Supabase](https://supabase.com/) (PostgreSQL) |
| Package Manager | [uv](https://github.com/astral-sh/uv) |

## Project Structure

```
wsulostandfound/
├── main.py                  # Entry point — creates and starts the bot
├── database.py              # Supabase client and all DB helpers
├── helpers.py               # Shared utilities (formatting, membership check, etc.)
├── localization.py          # i18n loader and get_text() helper
├── utils.py                 # In-memory state management (user states, pending posts)
├── handlers/
│   ├── command_handlers.py  # /start, /list, /search, /post_lost, /post_found
│   ├── callback_handlers.py # Inline button callbacks (language, admin actions, pagination)
│   └── message_handlers.py  # Free-text message handler (multi-step flows)
├── services/
│   ├── list_service.py      # Paginated item listing
│   ├── menu_service.py      # Main menu and join-channel prompt
│   ├── post_service.py      # Submit post to admin for review
│   └── report_service.py    # Error reporting to admin
└── locales/
    ├── en.json              # English strings
    ├── am.json              # Amharic strings
    └── om.json              # Afaan Oromoo strings
```

## Database Schema

Two tables are required in your Supabase project:

**`botusers`**

| Column | Type | Notes |
|---|---|---|
| `telegram_id` | bigint | Primary key |
| `username` | text | Telegram username (optional) |
| `first_name` | text | Telegram first name (optional) |
| `phone_number` | text | Collected on registration |
| `language` | text | User's preferred language code (default `en`) |

**`items`**

| Column | Type | Notes |
|---|---|---|
| `id` | bigint | Auto-increment primary key |
| `item_name` | text | Short title of the item |
| `description` | text | Detailed description |
| `type` | text | `lost` or `found` |
| `status` | text | `active` or other |
| `user_telegram_id` | bigint | FK → `botusers.telegram_id` |
| `item_image` | text | Optional image file ID |
| `telegram_message_id` | bigint | Optional channel message ID |

## Setup

### Prerequisites

- Python 3.12 or later
- A [Telegram bot token](https://core.telegram.org/bots#botfather) from BotFather
- A [Supabase](https://supabase.com/) project with the tables above

### 1. Clone the repository

```bash
git clone https://github.com/Tegegndev/wsulostandfound.git
cd wsulostandfound
```

### 2. Install dependencies

Using `uv` (recommended):

```bash
uv sync
```

Or with `pip`:

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `TELEGRAM_TOKEN` | Bot token from BotFather |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon/service key |
| `CHANNEL_USERNAME` | Telegram channel username (e.g. `@mychannel`) |
| `ADMIN_ID` | Telegram user ID of the bot admin |

### 4. Run the bot

```bash
python main.py
```

Press **Ctrl+C** to stop.

## How It Works

1. A user sends `/start` — the bot checks channel membership and registration.
2. New users are prompted to share their phone number to complete registration.
3. From the main menu users can list items, search, or start a post flow.
4. During a post flow the user provides a title and description; the submission is forwarded to the admin.
5. The admin receives an inline keyboard with **Approve** / **Reject** buttons.
6. On approval the item is saved to the database and posted to the channel with a "Contact Owner" button.
7. Any Telegram user can tap "Contact Owner" — this starts the bot with a deep link that reveals the owner's contact info.

## License

This project is open source. See the repository for license details.
