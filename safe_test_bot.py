import os
import asyncio
import time
import random
from dataclasses import dataclass
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# =========================
# CONFIGURATION
# =========================

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

MIN_INTERVAL = 3          # minimum seconds between simulated messages
MAX_DURATION = 10 * 60 * 60   # maximum 10 hours
MAX_TARGETS = 1000        # simulated targets only


# =========================
# TEST STATE
# =========================

@dataclass
class TestState:
    running: bool = False
    started_at: float = 0
    sent: int = 0
    failed: int = 0
    total: int = 0
    task: asyncio.Task | None = None


states = {}


def get_state(chat_id: int) -> TestState:
    if chat_id not in states:
        states[chat_id] = TestState()
    return states[chat_id]


# =========================
# SIMULATED TARGETS
# =========================

def create_test_targets(count: int):
    count = max(1, min(count, MAX_TARGETS))
    return [f"TEST-TARGET-{i:04d}" for i in range(1, count + 1)]


# =========================
# MOCK MESSAGE
# =========================

async def simulate_message(target: str):
    """
    SAFE SIMULATION ONLY.

    This function does NOT:
    - send SMS
    - send OTP
    - make phone calls
    - contact WhatsApp
    - contact real users

    It only waits briefly and returns a simulated result.
    """

    await asyncio.sleep(0.05)

    # Simulated success/failure
    success = random.random() > 0.02
    return success


# =========================
# TEST WORKER
# =========================

async def run_test(chat_id: int, targets):
    state = get_state(chat_id)

    state.running = True
    state.started_at = time.time()
    state.sent = 0
    state.failed = 0
    state.total = 0

    try:
        index = 0

        while state.running:

            elapsed = time.time() - state.started_at

            # Hard 10-hour limit
            if elapsed >= MAX_DURATION:
                state.running = False
                break

            target = targets[index % len(targets)]

            success = await simulate_message(target)

            state.total += 1

            if success:
                state.sent += 1
            else:
                state.failed += 1

            index += 1

            # Required minimum interval
            await asyncio.sleep(MIN_INTERVAL)

    except asyncio.CancelledError:
        pass

    finally:
        state.running = False


# =========================
# /START
# =========================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 Safe Telegram Test Bot\n\n"
        "This bot performs simulation only.\n"
        "No real SMS, OTP, calls or WhatsApp messages are sent.\n\n"
        "Commands:\n"
        "/test 100 - start simulated test\n"
        "/stop - stop test\n"
        "/status - show live status\n"
        "/targets 100 - preview test targets\n"
    )

    await update.message.reply_text(text)


# =========================
# /TEST
# =========================

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    state = get_state(chat_id)

    if state.running:
        await update.message.reply_text(
            "⚠️ A test is already running.\n"
            "Use /status or /stop."
        )
        return

    count = 100

    if context.args:
        try:
            count = int(context.args[0])
        except ValueError:
            await update.message.reply_text(
                "❌ Example:\n/test 100"
            )
            return

    if count < 1:
        count = 1

    if count > MAX_TARGETS:
        await update.message.reply_text(
            f"❌ Maximum simulated targets: {MAX_TARGETS}"
        )
        return

    targets = create_test_targets(count)

    state.total = 0
    state.sent = 0
    state.failed = 0

    state.task = asyncio.create_task(
        run_test(chat_id, targets)
    )

    await update.message.reply_text(
        "🟢 Simulation started\n\n"
        f"🎯 Simulated targets: {count}\n"
        f"⏱ Interval: {MIN_INTERVAL} seconds\n"
        "⏳ Maximum duration: 10 hours\n\n"
        "Use /status for live statistics."
    )


# =========================
# /STOP
# =========================

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    state = get_state(chat_id)

    if not state.running:
        await update.message.reply_text(
            "ℹ️ No test is currently running."
        )
        return

    state.running = False

    if state.task and not state.task.done():
        state.task.cancel()

    await update.message.reply_text(
        "🛑 Simulation stopped.\n\n"
        f"Simulated messages: {state.total}\n"
        f"Successful: {state.sent}\n"
        f"Failed: {state.failed}"
    )


# =========================
# /STATUS
# =========================

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    state = get_state(chat_id)

    if state.started_at:
        elapsed = int(time.time() - state.started_at)
    else:
        elapsed = 0

    hours = elapsed // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60

    status = "🟢 RUNNING" if state.running else "🔴 STOPPED"

    await update.message.reply_text(
        "📊 TEST STATUS\n\n"
        f"Status: {status}\n"
        f"Runtime: {hours:02d}:{minutes:02d}:{seconds:02d}\n"
        f"Total simulated: {state.total}\n"
        f"Successful: {state.sent}\n"
        f"Failed: {state.failed}\n"
        f"Interval: {MIN_INTERVAL}s\n"
        f"Max duration: 10 hours"
    )


# =========================
# /TARGETS
# =========================

async def targets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = 100

    if context.args:
        try:
            count = int(context.args[0])
        except ValueError:
            count = 100

    count = max(1, min(count, MAX_TARGETS))

    targets = create_test_targets(count)

    preview = "\n".join(targets[:20])

    if count > 20:
        preview += f"\n... and {count - 20} more simulated targets"

    await update.message.reply_text(
        "🎯 SIMULATED TARGETS\n\n" + preview
    )


# =========================
# ERROR HANDLER
# =========================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print("Bot error:", context.error)


# =========================
# MAIN
# =========================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN environment variable is missing."
        )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start_command)
    )

    application.add_handler(
        CommandHandler("test", test_command)
    )

    application.add_handler(
        CommandHandler("stop", stop_command)
    )

    application.add_handler(
        CommandHandler("status", status_command)
    )

    application.add_handler(
        CommandHandler("targets", targets_command)
    )

    application.add_error_handler(error_handler)

    print("✅ Safe Telegram Test Bot is running...")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()