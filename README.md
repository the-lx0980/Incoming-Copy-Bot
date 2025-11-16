# 📇 Copy UserBot 📇

A **UserBot** is just a Telegram account you control with code—here, with Pyrogram. This Copy UserBot grabs media from any channels you choose and automatically forwards it all to one destination channel or group. It skips duplicates and keeps an eye on Telegram’s flood limits so you don’t have to.

## ✅ Why Use a UserBot?
- Looks and acts like a regular user, so it can join any channel.
- Gets into private channels and groups where normal bots aren’t allowed.
- Doesn’t need admin rights in source channels—just being a member works.
- Handles all types of media: videos, docs, audio, you name it.
- You can tweak everything in Python, so you’re in control.

## ⚙️ How Does the Copy UserBot Work?
1. Log in with your Telegram account using a session string.
2. Join or add the UserBot to every source channel (no admin rights needed).
3. Set your destination channel by running `/add_chat <channel_id>` (make sure the UserBot is an admin there).
4. The bot watches for new media and forwards it when it spots something.
5. It uses MongoDB to remember what’s already been forwarded, so nothing gets sent twice.

This setup is perfect if you want to back up channel media, manage content across channels, or just automate forwarding.

---
## 🧩 Commands (Admin Only)
- `/start` — shows start message and user bot commands
- `/stats` — see how many files got forwarded, how many were duplicates, and how much is stored
- `/cleardb` — clears the database
- `/add_chat <channel_id>` — set the destination channel (the bot checks if it’s a member)
- `/delete_chat` — remove the saved destination channel
- `/show_chat` — see which channel is set as the destination and its status

---

## 🎯 Quick Setup
- Add your UserBot to any source channel where media comes in.
- Set the destination with:
  ```
  /add_chat <channel_id>
  ```
- Make sure the UserBot is in the destination channel and has permission to post.
- That’s it. From now on, any media that shows up in a source channel gets copied over—no extra work.

---

## ⚙️ What You’ll Need
Set these variables:
```
API_ID       - Telegram API ID (get it from https://my.telegram.org)
API_HASH     - Telegram API Hash (from the same place)
SESSION      - Your Pyrogram User Session String
DB_URL       - MongoDB Database URL
ADMINS       - List of admin user IDs, separated by commas (like 12345,67890)
```

### ⚠️ Heads Up
Every time you add a new destination channel or change where you’re forwarding with `/add_chat`, you need to run:
```
/cleardb
```
#### 📝 Why bother with `/cleardb`?
The bot keeps a list of every forwarded media’s `file_unique_id` to spot duplicates. If you switch the destination channel:
- The old duplicate list matches the previous channel, not the new one.
- The bot might think new files are “duplicates” and not send them.
- That means real files get skipped.

Running `/cleardb` wipes the old IDs so your bot starts fresh and forwards everything it should.

### 🧬 How the Bot Spots Duplicates
Your UserBot has a three-step system to make sure nothing gets sent twice:

#### 1️⃣ Telegram’s `file_unique_id`
Every media file on Telegram gets a unique ID. Even if two people send the same file, it’s got the same ID. The bot uses this to check for duplicates.

#### 2️⃣ MongoDB Storage
Every forwarded file’s ID goes into the database. This way, the bot remembers what it’s already sent—even after a restart.

#### 📌 What Happens When a File Shows Up?
1. The bot grabs the file’s `file_unique_id`
2. Looks it up in MongoDB—if it’s already there, it skips the file
3. If not, it forwards the file
4. Then saves the ID to MongoDB

## 👨‍💻 Developer
- by: **[@lx0980](https://github.com/lx0980)**
