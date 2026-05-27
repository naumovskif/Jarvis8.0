# Quick Test Instructions

## The Real Issue

When you redirect output to a file with `> jarvis_crash.log 2>&1`, the output is **buffered** - you can't see it in the terminal, so it looks like JARVIS is hanging. But it's actually working fine and printing to the log file.

## How to Actually Capture the Error

### Option 1: Run Normally and Let It Crash (Easiest)

Just run JARVIS normally and when it crashes, the error will be printed to the console:

```bash
python main.py
```

Use it until it crashes, then you'll see the error message in the terminal.

### Option 2: Run and Save Crash Log

Use the debug script which is better at capturing errors:

```bash
python run_jarvis_debug.py
```

When it crashes, the error will appear on screen. You can then:
1. Copy it from terminal
2. Or press Ctrl+C to exit and check for a `jarvis_crash.log` file

### Option 3: PowerShell Transcript (Captures Everything)

```powershell
Start-Transcript -Path "jarvis_log.txt" -Append
python main.py
# Use JARVIS, let it crash
# Press Ctrl+C
Stop-Transcript
```

Then open `jarvis_log.txt` to see the full transcript.

---

## Key Point

**JARVIS is working fine.** The "INITIALISING" message you see is normal - it means JARVIS is waiting for input. It's not actually hanging.

The actual crash happens when you **talk to it** during a conversation.

---

## What to Do Now

1. Run: `python main.py`
2. Wait for "🎤 Mic started"
3. Say something to JARVIS
4. Let it respond
5. When it crashes, copy the error from the terminal
6. Paste it in your next message

That's it!

