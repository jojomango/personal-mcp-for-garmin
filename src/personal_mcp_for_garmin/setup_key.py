"""Save your Garmin Personal API key. Run it yourself in a terminal:

    uv run personal-mcp-for-garmin-setup

Create the key at https://connect.garmin.com/app/settings/personalApiToken (it is shown only once).
It is verified with Garmin first, then saved to ~/.config/personal-mcp-for-garmin/personal_api_key
with permissions 600. The key stays on this computer.
"""

from __future__ import annotations

import getpass

from .api import KEY_PAGE, GarminAPIError, PersonalAPI, save_api_key


def main() -> None:
    print(f"Create a Personal API key at {KEY_PAGE}")
    print("Reminder: the key is for your own use only. Never share it or commit it to git.\n")
    key = getpass.getpass("Paste your Garmin Personal API key (input is hidden): ").strip()
    if not key:
        print("Nothing entered; cancelled.")
        return
    try:
        PersonalAPI(key).request("/userprofile-service/userprofile/settings")
    except GarminAPIError as e:
        print(f"❌ Verification failed: {e}")
        raise SystemExit(1)
    path = save_api_key(key)
    print(f"✅ Key verified and saved to {path}")


if __name__ == "__main__":
    main()
