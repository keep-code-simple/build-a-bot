# Chapter 4, Step 2: set up the cloud (a parent runs this ONCE)
# It makes config.json with two secret topic names and tells you what to type into the phone.
#
#   python setup_cloud.py                first-time setup
#   python setup_cloud.py --new-topics   a topic leaked? Make two new ones.
#   python setup_cloud.py --show         print the phone instructions again
#
# config.json is PRIVATE. It is in .gitignore and must never be put on GitHub.

import argparse
import json
import os
import secrets

from bridge import cloud
from bridge.settings import CONFIG_FILE, EXAMPLE_FILE


def make_topic():
    """A topic name nobody can guess: "bab-" plus 22 random letters and numbers."""
    return "bab-" + secrets.token_urlsafe(16)


def build_config(example, old=None):
    """Start from the example settings, keep any old settings, and put in two fresh topics."""
    config = dict(example)
    config.update(old or {})
    config["to_robot_topic"] = make_topic()
    config["from_robot_topic"] = make_topic()
    return config


def save(config, config_file=CONFIG_FILE):
    with open(config_file, "w") as file:
        json.dump(config, file, indent=2)
        file.write("\n")
    os.chmod(config_file, 0o600)          # only this Mac user can read it


def phone_instructions(config):
    server = config["ntfy_server"].rstrip("/")
    return f"""
📱 ON THE IPHONE OR IPAD: make a Shortcut called "Tell the robot"

   1. Shortcuts app -> + -> name it:  Tell the robot
   2. Add action:  Ask for Input   (Text)   Prompt:  What should the robot say?
   3. Add action:  Get Contents of URL
        URL:           {server}/
        Method:        POST
        Request Body:  JSON
          topic    (Text) = {config["to_robot_topic"]}
          message  (Text) = Provided Input   (pick it from the variables)

🔔 TO GET THE ROBOT'S TEXTS: install the free ntfy app (or open {server}/app)
   and subscribe to this topic:
        {config["from_robot_topic"]}

🔒 These two names are passwords. Anyone who knows them can talk to your robot.
   Don't post them, screenshot them or put them on GitHub.
   If one leaks, run:  python setup_cloud.py --new-topics
"""


def main():
    parser = argparse.ArgumentParser(description="Make the private config.json for the Talking Robot.")
    parser.add_argument("--new-topics", action="store_true", help="replace both secret topics")
    parser.add_argument("--show", action="store_true", help="print the phone instructions again")
    args = parser.parse_args()

    example = json.loads(EXAMPLE_FILE.read_text())
    old = json.loads(CONFIG_FILE.read_text()) if CONFIG_FILE.exists() else None

    if args.show:
        if not old or not cloud.is_real_topic(old.get("to_robot_topic")):
            raise SystemExit("There is no config.json yet. Run:  python setup_cloud.py")
        print(phone_instructions(old))
        return

    if old and not args.new_topics:
        print("config.json already exists, so I left it alone.")
        print("  See the phone instructions again:  python setup_cloud.py --show")
        print("  Make two NEW secret topics:        python setup_cloud.py --new-topics")
        return

    if old:
        print("This replaces BOTH secret topics. Your other settings are kept.")
        print("The phone Shortcut and the ntfy app will need the new names.")
        if input("Type yes to go ahead: ").strip().lower() != "yes":
            print("Nothing changed.")
            return

    config = build_config(example, old)
    save(config)
    print("✅ Wrote config.json with two new secret topics.")
    print(phone_instructions(config))


if __name__ == "__main__":
    main()
