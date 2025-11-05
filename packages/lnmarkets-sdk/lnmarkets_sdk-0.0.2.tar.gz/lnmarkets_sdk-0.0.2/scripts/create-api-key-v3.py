#!/usr/bin/env python3

"""
Simple browser automation script for creating API keys on LN Markets environment
"""

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


@dataclass
class ApiCredentials:
    """API credentials data structure"""

    key: str
    name: str
    passphrase: str
    secret: str


# Default configuration
config = {
    "base_url": "https://app.lnmarkets.com",
    "email": "test@gmail.com",
    "headless": True,
    "password": "Anypassword123",
}


def authenticate_user(page: Page) -> None:
    """Authenticate user (register or login)"""
    page.goto(f"{config['base_url']}/en/register/credentials")
    page.get_by_placeholder("Email").fill(config["email"])
    page.get_by_placeholder("Password").fill(config["password"])
    page.locator("form").get_by_role("button", name="Register").click()

    try:
        page.wait_for_url(f"{config['base_url']}/en/welcome", timeout=1000)
    except Exception:
        page.goto(f"{config['base_url']}/en/login/credentials")
        page.get_by_placeholder("Enter your login or email").fill(config["email"])
        page.get_by_placeholder("Enter your password").fill(config["password"])
        page.locator("form").get_by_role("button", name="Login").click()
        page.wait_for_url(f"{config['base_url']}/en/futures", timeout=1000)


def remove_all_api_keys(page: Page) -> None:
    """Remove all existing API keys"""
    page.wait_for_selector('tbody[data-slot="table-body"]', timeout=1000)

    while page.locator('tbody button:has-text("Remove")').count() > 0:
        page.locator('tbody button:has-text("Remove")').first.click()
        page.wait_for_timeout(500)


def create_new_api_key(page: Page) -> ApiCredentials:
    """Create new API key"""
    page.goto(f"{config['base_url']}/en/user/api/v3/create")

    # Get auto-generated values
    api_passphrase = page.locator(
        'label:has-text("Passphrase") + div input[data-slot="form-control"]'
    ).input_value()

    api_key_name = page.locator(
        'label:has-text("Name") + div input[data-slot="form-control"]'
    ).input_value()

    # Select permissions and create key
    page.get_by_role("button", name="Select all").click()
    page.get_by_role("button", name="Create").click()

    # Get generated credentials
    api_key = page.locator('label:has-text("Key") + div input[readonly]').input_value()

    api_secret = page.locator(
        'label:has-text("Secret") + div input[readonly]'
    ).input_value()

    return ApiCredentials(
        key=api_key,
        name=api_key_name,
        passphrase=api_passphrase,
        secret=api_secret,
    )


def write_to_env_file(credentials: ApiCredentials) -> None:
    """Write credentials to .env file"""
    env_content = f"""# LN Markets API V3 Credentials
LNM_API_KEY_V3={credentials.key}
LNM_API_SECRET_V3={credentials.secret}
LNM_API_PASSPHRASE_V3={credentials.passphrase}
LNM_API_NAME_V3={credentials.name}
"""
    env_path = Path.cwd() / ".env"

    try:
        # Check if file exists and append to it
        if env_path.exists():
            existing_content = env_path.read_text()

            # Only write if the credentials aren't already there
            if "LNM_API_KEY_V3=" in existing_content:
                # Replace existing credentials
                pattern = r"# LN Markets API V3 Credentials\s*LNM_API_KEY_V3=.*\s*LNM_API_SECRET_V3=.*\s*LNM_API_PASSPHRASE_V3=.*\s*LNM_API_NAME_V3=.*"
                updated_content = re.sub(pattern, env_content.strip(), existing_content)
                env_path.write_text(updated_content)
            else:
                env_path.write_text(existing_content + "\n" + env_content)
        else:
            # File doesn't exist, create new one
            env_path.write_text(env_content)

        print("✅ Credentials written to .env file")
    except Exception as e:
        print(f"❌ Error writing to .env file: {e}")
        raise


def create_api_key() -> None:
    """Main function"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config["headless"])
        page = browser.new_page()

        try:
            print("🔑 Creating API key...")
            authenticate_user(page)
            page.goto(f"{config['base_url']}/en/user/api/v3")
            remove_all_api_keys(page)
            credentials = create_new_api_key(page)
            write_to_env_file(credentials)

            print("✅ API key created successfully")
        finally:
            browser.close()


def main() -> None:
    """Entry point for the script"""
    try:
        create_api_key()
        sys.exit(0)
    except Exception as error:
        print(f"Error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
