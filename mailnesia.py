import re
import time
import html
import requests

# Travian seems to send the same activation code, even if you re-send

BASE_URL = "https://mailnesia.com"
TIMEOUT = 15
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; otp-fetcher/1.0)"}

# One <tr> per email in the inbox; the id attribute is the email id.
ROW_RE = re.compile(r'<tr[^>]*\bid="(\d+)"[^>]*class="emailheader"[^>]*>(.*?)</tr>', re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")


def _get(url: str) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    except requests.RequestException as exc:
        print(f"Request failed for {url}: {exc}")
        return None
    if not resp.ok:
        print(f"Failed to fetch {url}, status code: {resp.status_code}")
        return None
    return resp.text


def _row_text(row_html: str) -> str:
    return html.unescape(TAG_RE.sub(" ", row_html)).lower()


def _extract_code(email_html: str) -> str | None:
    # Preferred: the code inside the activation link.
    m = re.search(r"activationCode=(\d{6})", email_html)
    if m:
        return m.group(1)
    # Fallback: a standalone 6-digit number in the visible text.
    text = html.unescape(TAG_RE.sub(" ", email_html))
    m = re.search(r"(?<!\d)(\d{6})(?!\d)", text)
    return m.group(1) if m else None


def get_verification_code(username: str, sender_keyword: str = "travian",
                          retries: int = 4, delay: int = 10) -> str | None:
    """
    Retrieve a 6-digit activation code from the most recent matching email
    in a public Mailnesia inbox.

    Args:
        username: Local part of the Mailnesia address (e.g. 'amandaangeli2n14'
                  for amandaangeli2n14@mailnesia.com).
        sender_keyword: Case-insensitive text that must appear in the inbox row
                        (sender or subject). Default 'travian'.
        retries: Number of attempts to fetch the mailbox.
        delay: Base delay in seconds; attempt n waits delay * n before retrying.

    Returns:
        The 6-digit code, or None if not found after all retries.
    """
    mailbox_url = f"{BASE_URL}/mailbox/{username}"
    keyword = sender_keyword.lower()

    for attempt in range(1, retries + 1):
        mailbox_html = _get(mailbox_url)
        if mailbox_html is not None:
            matching_ids = [
                int(email_id)
                for email_id, row in ROW_RE.findall(mailbox_html)
                if keyword in _row_text(row)
            ]

            if matching_ids:
                # Highest id = most recent email.
                for email_id in sorted(matching_ids, reverse=True):
                    email_html = _get(f"{mailbox_url}/{email_id}")
                    if email_html is None:
                        continue
                    code = _extract_code(email_html)
                    if code:
                        return code
                    print(f"No activation code found in email {email_id}")
            else:
                print(f"No '{sender_keyword}' emails found in mailbox, attempt {attempt}/{retries}")

        if attempt < retries:
            wait = delay * attempt
            print(f"Retrying in {wait}s...")
            time.sleep(wait)

    return None


if __name__ == "__main__":
    import sys

    username = sys.argv[1] if len(sys.argv) > 1 else "amandaangeli2n14"
    code = get_verification_code(username)
    if code:
        print(f"Found activation code: {code}")
    else:
        print("No activation code found after retries")
