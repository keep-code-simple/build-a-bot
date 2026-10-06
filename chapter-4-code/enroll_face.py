# Chapter 4, Step 5: teach the robot a face
# ASK FIRST: only add people who say yes.
#
# What gets saved: 20 lists of 128 numbers in faces/, and a name and catchphrase in people.json.
# What never gets saved: photos. Nothing leaves this Mac.
#
#   python enroll_face.py

import time

import cv2

from bridge import faces, protocol
from bridge.settings import load_config

SAMPLES = 20
SECONDS_BETWEEN = 0.6
POSES = ["Look straight at me", "Turn a little LEFT", "Turn a little RIGHT", "Big smile!"]


def ask_details():
    name = input("Name to show on the screen (10 letters or fewer fits best): ").strip()
    if not name:
        raise SystemExit("No name, no enrolling.")
    if input(f"Did {name} say YES to the robot learning their face? (yes/no) ").strip().lower() != "yes":
        raise SystemExit("OK! The robot only learns faces of people who say yes.")
    say_as = input(f"How should I SAY it? Spell it the way it sounds (Return = {name}): ").strip() or name
    catchphrase = input("Catchphrase (16 letters fits the screen), like 'Legend is here!': ").strip()
    while True:
        try:
            tune = protocol.read_tune(input("Theme tune, up to 8 notes (C D E F G A B C2), like 'C E G C2': "))
            break
        except ValueError as problem:
            print("  ", problem)
    return {"name": name, "say_as": say_as, "catchphrase": catchphrase, "tune": tune}


def collect_samples(camera_number):
    engine = faces.FaceEngine()
    camera = faces.open_camera(camera_number)
    samples = []
    last_sample = 0
    print("📷 Click the camera window. Press Q to give up.")

    while len(samples) < SAMPLES:
        ok, frame = camera.read()
        if not ok:
            print("Can't read the camera. See 'Camera won't open' in Troubleshooting.")
            break
        frame = cv2.flip(frame, 1)
        found = engine.find_faces(frame)
        pose = POSES[len(samples) * len(POSES) // SAMPLES]
        message = pose

        if len(found) == 0:
            message = "I can't see a face"
        elif len(found) > 1:
            message = "One face at a time, please!"
        else:
            x, y, w, h = faces.box(found[0])
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 4)
            if w < 120:
                message = "Come a bit closer"
            elif time.monotonic() - last_sample > SECONDS_BETWEEN:
                samples.append(engine.embedding(frame, found[0])[0])   # 128 numbers. No photo!
                last_sample = time.monotonic()

        cv2.putText(frame, message, (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 255, 255), 4)
        cv2.putText(frame, f"{len(samples)} of {SAMPLES}", (30, 130),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 0), 3)
        cv2.imshow("Enroll a face - press Q to give up", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()
    return samples


def main():
    config = load_config()
    info = ask_details()
    samples = collect_samples(config.get("faces", {}).get("camera", 0))
    if len(samples) < SAMPLES:
        raise SystemExit("Stopped early, so nothing was saved.")
    who = faces.make_id(info["name"])
    faces.save_person(who, info, samples)
    print(f"✅ Saved {len(samples)} face fingerprints for {info['name']}. No photos were kept.")
    print("Next:  python calibrate_faces.py")


if __name__ == "__main__":
    main()
