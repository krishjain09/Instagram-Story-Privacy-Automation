# 🚀 Instagram Story Privacy Automation

> Because sometimes you want only a few people to see your story... without screaming **"YOU ARE IN MY CLOSE FRIENDS LIST"** 🟢

---

## 🤔 The Problem

Hope Instagram someday adds a feature like:

> **"Share Story Only With Selected People"**

Now you'll probably say:

> "Bro, Instagram already lets you hide your story from everyone except selected people."

And yes, technically you can do that.

But imagine you're someone with **500+ followers**.

Let's say you want only **5–10 people** to see a particular story.

Your workflow becomes:

1. Open Story Privacy Settings.
2. Hide story from hundreds of followers.
3. Post the story.
4. Go back later.
5. Unhide everyone again.
6. Repeat next time.

Bro... that's painful 😭

And then someone says:

> "Just use Close Friends."

Sure.

But sometimes you don't want the green ring.

The moment someone sees a Close Friends story, they instantly know:

> "Oh, I was specifically added to a special list."

Sometimes you want the story to look completely normal while still controlling who can see it.

That's where this project comes in.

---

## 🎯 Why I Built This

I got tired of:

- Clicking hundreds of followers manually.
- Repeating the same privacy settings every time.
- Opening Story Settings again and again.
- Accidentally forgetting to restore settings.

So I built a tool that helps automate the repetitive workflow.

Because life is too short for 700 checkbox clicks 💀

## 🎥 Demo

Watch the project in action:

[![Watch Demo]](https://res.cloudinary.com/dpd1i7viz/video/upload/v1780500463/Instagram-Story-Privacy-Automation_wxa1vx.mp4)

The demo covers:

- Installation
- Login flow
- CAPTCHA handling
- 2FA handling
- Story privacy workflow
- Troubleshooting

---

## 📦 Requirements

- Python 3.9+
- Windows / Linux / macOS
- Google Chrome / Chromium
- Internet connection

---

## ⚙️ Installation

### 1. Clone Repository

```bash
git clone https://github.com/krishjain09/Instagram-Story-Privacy-Automation.git
cd Instagram-Story-Privacy-Automation
```

### 2. Install Dependencies

```bash
pip install playwright
```

### 3. Install Browser

```bash
playwright install chromium
```

### 4. Run

```bash
python insta-new-feature.py
```

---

## 🚀 How It Works

### Step 1

Run the script.

```bash
python insta-new-feature.py
```

### Step 2

Enter your Instagram credentials.

```text
Enter Instagram Username/Email:
Enter Instagram Password:
```

### Step 3

The browser opens automatically.

```text
[→] Opening Instagram Login window...
[→] Typing username...
[→] Typing password...
[→] Submitting form...
```

### Step 4

Instagram may ask for:

- CAPTCHA
- Image verification
- Security challenge
- 2FA code

Complete them manually.

---

### Step 5

Press ENTER in terminal.

```text
👉 Press ENTER after you are fully logged in
```

---

### Step 6

The script continues.

```text
[✓] Resuming session...
[→] Navigating to Story Privacy page...
```

---

### Step 7

Choose an operation.

```text
[1] Hide story from ALL users
[2] Unhide story for ALL users
[q] Quit
```

Example:

```text
Enter choice: 1
```

---

### Step 8

Wait for completion.

```text
✓ Total Actions Run : 250
– Skipped (Correct) : 0
✗ Action Failures   : 0
```

Boom 🚀

Now your story visibility settings are updated.

---

## 🖥️ Example Terminal Output

```text
=======================================================
Instagram Story Privacy Automation
=======================================================

==================================================
INSTAGRAM CREDENTIALS REQUIRED
==================================================

Enter Instagram Username/Email: test_user
Enter Instagram Password (hidden):

[→] Opening Instagram Login window...
[→] Locating login elements...
[→] Typing username...
[→] Typing password...
[→] Submitting form...

╔══════════════════════════════════════════════════╗
⚠️ ACTION REQUIRED
╚══════════════════════════════════════════════════╝

1. Complete CAPTCHA
2. Complete 2FA
3. Wait for Home Feed
4. Press ENTER

[✓] Resuming script...

[→] Navigating to target...
Waiting for UI...

Select Process Mode:

[1] Hide story from ALL users
[2] Unhide story for ALL users
[q] Quit

Enter choice: 1

[→] Processing...

✓ Total Actions Run : 250
– Skipped (Correct) : 0
✗ Action Failures   : 0
```

## ⭐ If You Found This Useful

Give the repository a star ⭐

It helps more developers discover the project.

---

Made with ☕, Python, Playwright, and pure frustration from clicking hundreds of checkboxes.
