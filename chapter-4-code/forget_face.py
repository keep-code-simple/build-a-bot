# Chapter 4, Step 5: forget a face
# Your face is yours. This deletes every trace of a person: their numbers and their details.
#
#   python forget_face.py "Kid 1"      forget one person
#   python forget_face.py --everyone   forget everybody

import argparse
import shutil

from bridge import faces


def main():
    parser = argparse.ArgumentParser(description="Delete a person from the robot's memory.")
    parser.add_argument("name", nargs="?", help='the name they were enrolled with, like "Kid 1"')
    parser.add_argument("--everyone", action="store_true", help="forget everybody")
    args = parser.parse_args()

    if args.everyone:
        shutil.rmtree(faces.FACES, ignore_errors=True)
        faces.PEOPLE_FILE.unlink(missing_ok=True)
        print("🧹 Forgot everyone. The faces folder and people.json are gone.")
    elif not args.name:
        details, _ = faces.load_people()
        names = ", ".join(info["name"] for info in details.values()) or "nobody"
        print(f"I know: {names}")
        print('To forget someone:  python forget_face.py "their name"')
    elif faces.forget_person(args.name):
        print(f"🧹 Forgot {args.name}. Their numbers and details are deleted.")
    else:
        print(f"I don't know anyone called {args.name}.")


if __name__ == "__main__":
    main()
