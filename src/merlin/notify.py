from __future__ import annotations

import logging
import os
from typing import Optional, Iterable, Any

import requests

log = logging.getLogger(__name__)

SLACK_WEBHOOK_ENV = "MERLIN_SLACK_WEBHOOK_URL"


def send_slack_message(text: str, *, username: Optional[str] = None) -> None:
    """
    Post a simple text message to Slack using an incoming webhook.

    Set MERLIN_SLACK_WEBHOOK_URL in your environment or .env.
    """
    url = os.getenv(SLACK_WEBHOOK_ENV)
    if not url:
        log.warning("Slack webhook not configured; skipping Slack notification.")
        return

    payload: dict[str, Any] = {"text": text}
    if username:
        payload["username"] = username

    try:
        resp = requests.post(url, json=payload, timeout=5)
        resp.raise_for_status()
    except Exception as e:
        log.error("Failed to send Slack message: %s", e)


def _format_results_for_slack(results: Iterable[Any]) -> str:
    """
    Builds human readable message for Slack
    """

    # --- Merlin Intro Message ---
    intro = (
        "Greetings, mortals :male_mage:\n"
        "I, *Merlin the Venture Wizard*, have gazed deeply into my crystal ball :crystal_ball:\n"
        "consulted ancient scrolls :scroll: of market wisdom,\n"
        "and conjured visions of the most promising companies in the realm.\n\n"
        "Behold… the ventures that shimmer with arcane potential :magic_wand:\n\n"
    )

    lines: list[str] = [intro]

    # --- Per-company details ---
    for idx, r in enumerate(results):
        name = getattr(r, "name", "Unknown Company")

        # URL
        raw_url = getattr(r, "url", "") or getattr(r, "website_url", "")
        url_display = ""
        if raw_url:
            if not raw_url.startswith(("http://", "https://")):
                raw_url = "https://" + raw_url
            url_display = f" – <{raw_url}|{raw_url.replace('https://','')}>"

        # Company Header
        lines.append(f"*{name}*{url_display}")

        # Description
        desc = getattr(r, "description", "") or ""
        if desc:
            lines.append(desc.strip())
        lines.append("")  # blank line

        # Founders
        founders = getattr(r, "founders", None)
        if founders is None:
            enrichment = getattr(r, "enrichment", None)
            if enrichment:
                founders = getattr(enrichment, "founders", None)

        if founders:
            lines.append("• *Founders:*")
        for f in founders:
            fname = getattr(f, "name", "") or "Founder"
            linkedin = getattr(f, "linkedin", "") or getattr(f, "linkedin_url", "")

            # Collect all emails
            primary = getattr(f, "email", None)
            email_list = getattr(f, "emails", None)

            emails = []
            if primary:
                emails.append(primary)
            if email_list:
                # email_list should already be deduped, but we dedupe again just in case
                for e in email_list:
                    if e and e not in emails:
                        emails.append(e)

            # Build parts
            parts = [fname]
            if linkedin:
                parts.append(f"<{linkedin}|LinkedIn>")
            if emails:
                parts.append(" | ".join(emails))

            lines.append("   – " + " — ".join(parts))


            lines.append("")

        # Scores
        scores = getattr(r, "scores", None)
        if scores:
            lines.append(f"• *Score:* {scores.total:0.2f}")
            lines.append(
                f"   Team: {scores.team:0.2f} | Market: {scores.market:0.2f} | Funding: {scores.funding:0.2f}"
            )

        DIVIDER = "────────────────────────────────────────────────────────"

        if idx < len(results) - 1:
            lines.append(DIVIDER + "\n")



    return "\n".join(lines).rstrip()


def send_results_to_slack(results: Iterable[Any]) -> None:
    """
    Sends the wizard intro + formatted company results to Slack,
    but ONLY for companies with total score >= 75.
    """
    results = list(results)

    # Filter by score threshold
    filtered = []
    for r in results:
        scores = getattr(r, "scores", None)
        if scores and scores.total >= 80:
            filtered.append(r)

    # If nothing qualifies, send a friendly message
    if not filtered:
        send_slack_message(
            "Merlin gazed deeply into the crystal ball…\n"
            "But alas, no companies scored above *75* today. :crystal_ball:",
            username="Merlin VC Bot"
        )
        return

    # Format only those companies
    text = _format_results_for_slack(filtered)
    if not text:
        log.warning("No text generated for Slack; skipping.")
        return

    send_slack_message(text, username="Merlin VC Bot")
