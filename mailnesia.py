import requests2
import re
import time
import requests

# Travian seems to send the same activation code, even if you re-send

def get_verification_code(username: str, retries: int = 4, delay: int = 10) -> str | None:
    """
    Retrieve a 6-digit activation code from the most recent Travian email in a Mailnesia inbox.

    Args:
        username (str): The username part of the Mailnesia email address (e.g., 'amandaangeli2n1').
        retries (int): Number of times to retry fetching the mailbox (default: 4).
        delay (int): Base delay in seconds between retries (default: 10).

    Returns:
        str: The 6-digit activation code if found, otherwise None.
    """
    # Define the base URL and mailbox URL
    mailbox_url = f"https://mailnesia.com/mailbox/{username}"

    # Regex pattern to match href attributes with email IDs
    id_pattern = rf'href="/mailbox/{username}/(\d+)"'  # Use raw string
    # Regex pattern to identify Travian emails in the inbox
    travian_pattern = r'Travian.*?<td>.*?' + re.escape(f"{username}@mailnesia.com")

    # Retry loop to handle email delivery delays
    for attempt in range(retries):
        if attempt > 0:
            time.sleep(delay * attempt)  # Wait based on the retry attempt (10s, 20s, etc.)

        # Fetch the mailbox page
        response = requests.get(mailbox_url)
        if not response.ok:
            print(f"Failed to fetch mailbox, status code: {response.status_code}")
            continue

        mailbox_content = response.text

        # Find all email IDs and check for Travian emails
        email_entries = re.finditer(rf'<tr id="\d+" class="emailheader".*?</tr>', mailbox_content, re.DOTALL)

        travian_ids = []

        for entry in email_entries:
            entry_content = entry.group(0)
            if re.search(travian_pattern, entry_content, re.DOTALL):
                id_match = re.search(id_pattern, entry_content)
                if id_match:
                    travian_ids.append(int(id_match.group(1)))

        if not travian_ids:
            print(f"No Travian emails found in mailbox, attempt {attempt + 1}")
            continue

        # Sort IDs in descending order (most recent first)
        travian_ids.sort(reverse=True)
        most_recent_id = travian_ids[0]

        # Fetch the most recent Travian email
        email_url = f"https://mailnesia.com/mailbox/{username}/{most_recent_id}"
        email_response = requests.get(email_url)
        if not email_response.ok:
            print(f"Failed to fetch email {most_recent_id}, status code: {email_response.status_code}")
            continue

        email_content = email_response.text

        # Extract the activation code from the Travian URL
        code_match = re.search(r'activationCode=(\d{6})', email_content)
        if code_match:
            return code_match.group(1)  # Return the 6-digit activation code

        print(f"No activation code found in email {most_recent_id}, attempt {attempt + 1}")

    return None  # Return None if no code is found after all retries


# Example usage
if __name__ == "__main__":
    username = "amandaangeli2n14"  # Replace with a username (will be used as an email. For example: amandaangeli2n14@mailnesia.com

    code = get_verification_code(username)
    if code:
        print(f"Found activation code: {code}")
    else:
        print("No activation code found after retries")
