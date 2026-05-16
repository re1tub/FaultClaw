"""FaultClaw Telegram bot interface.

Commands
--------
/verify    — run full pipeline on the correct 4-bit adder (normal mode)
/breakdown — run Breakdown Mode (exhaustive 16×16 sweep) on the correct adder
/buggy     — run normal mode against the buggy adder DUT (carry hardwired to 0)

Requires TELEGRAM_BOT_TOKEN in .env (or the environment).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure the project root is on sys.path regardless of where this script is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from agents.spec_reader import parse_spec
from agents.test_generator import DesignSpec, generate_test_suite
from agents.verification_judge import run_verification
from memory.store import save_run

load_dotenv()

_SPEC_PATH = Path("samples/adder_4bit.v")


# ---------------------------------------------------------------------------
# Pipeline runner
# ---------------------------------------------------------------------------

def _run_pipeline(breakdown: bool = False, buggy: bool = False) -> dict:
    spec_dict = parse_spec(_SPEC_PATH)
    spec = DesignSpec.from_dict(spec_dict)
    suite = generate_test_suite(spec, breakdown=breakdown)
    report = run_verification(suite, buggy=buggy)
    save_run(
        design_name=report["design_name"],
        mode=report["mode"],
        total_tests=report["total_tests"],
        tests_passed=report["tests_passed"],
        tests_failed=report["tests_failed"],
        failed_tests=report["failed_tests"],
    )
    return report


def _format_report(report: dict) -> str:
    header = (
        f"*FaultClaw — {report['design_name']}*\n"
        f"Mode: `{report['mode']}` | DUT: `{report['dut']}`\n"
        f"Tests: {report['total_tests']} | "
        f"✅ {report['tests_passed']} passed | "
        f"❌ {report['tests_failed']} failed\n"
        f"Coverage: {report['coverage_pct']}%"
    )

    if not report["failed_tests"]:
        return header + "\n\n✅ All tests passed."

    failures = report["failed_tests"]
    shown = failures[:5]
    lines = [header, "\n*Failures:*"]
    for f in shown:
        inp = f["inputs"]
        lines.append(
            f"• `{f['id']}` "
            f"a={inp['a']}, b={inp['b']} → "
            f"expected `{f['expected']}`, got `{f['actual']}`\n"
            f"  _{f['failure_explanation']}_"
        )
    if len(failures) > 5:
        lines.append(f"_…and {len(failures) - 5} more failures_")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

async def cmd_verify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Running verification on `adder_4bit.v`…", parse_mode="Markdown")
    try:
        report = _run_pipeline()
        await update.message.reply_text(_format_report(report), parse_mode="Markdown")
    except Exception as exc:
        await update.message.reply_text(f"❌ Error: {exc}")


async def cmd_breakdown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Running *Breakdown Mode* (256 tests)…", parse_mode="Markdown")
    try:
        report = _run_pipeline(breakdown=True)
        await update.message.reply_text(_format_report(report), parse_mode="Markdown")
    except Exception as exc:
        await update.message.reply_text(f"❌ Error: {exc}")


async def cmd_buggy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Running against *buggy adder* DUT…", parse_mode="Markdown")
    try:
        report = _run_pipeline(buggy=True)
        await update.message.reply_text(_format_report(report), parse_mode="Markdown")
    except Exception as exc:
        await update.message.reply_text(f"❌ Error: {exc}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not set. Add it to your .env file."
        )

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("verify", cmd_verify))
    app.add_handler(CommandHandler("breakdown", cmd_breakdown))
    app.add_handler(CommandHandler("buggy", cmd_buggy))

    print("FaultClaw bot is running. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
