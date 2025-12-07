# sends outputs to slack / gmail
from __future__ import annotations

import logging
import os
from typing import Optional
from dotenv import load_dotenv

import requests

log = logging.getLogger(__name__)

load_dotenv()

SLACK_WEBHOOK_ENV = "MERLIN_SLACK_WEBHOOK_URL"


def send_slack_message(text: str, *, username: Optional[str] = None) -> None:
    """
    Post a simple text message to Slack using an incoming webhook.

    Set MERLIN_SLACK_WEBHOOK_URL in your environment.
    """
    url = os.getenv(SLACK_WEBHOOK_ENV)
    if not url:
        log.warning("Slack webhook not configured; skipping Slack notification.")
        return

    payload: dict = {"text": text}
    if username:
        payload["username"] = username

    try:
        resp = requests.post(url, json=payload, timeout=5)
        resp.raise_for_status()
    except Exception as e:
        log.error("Failed to send Slack message: %s", e)


def send_leaderboard_to_slack(leaderboard_text: str) -> None:
    """
    Convenience helper to send the leaderboard as a code block.
    #TODO: Update and format later
    """
    wrapped = f"```{leaderboard_text}```"
    send_slack_message(wrapped, username="Merlin VC Bot")
