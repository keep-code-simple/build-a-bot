# Chapter 4, Step 5: watch the AI think
# The camera shows a live score for every enrolled person: how sure is the AI that this is them?
# The AI is never 100% sure. It gives scores, and OUR rule decides when that is sure enough.
# Click the camera window and press Q to quit.
#
#   python calibrate_faces.py

import cv2

from bridge import faces
from bridge.settings import load_config

GREEN, YELLOW, GRAY, WHITE = (0, 255, 0), (0, 255, 255), (160, 160, 160), (255, 255, 255)


def main():
    rules = load_config().get("faces", {})
    sure_enough = rules.get("sure_enough", faces.SURE_ENOUGH)
    beat_second_by = rules.get("beat_second_by", faces.BEAT_SECOND_BY)

    details, samples = faces.load_people()
    if not details:
        raise SystemExit("Nobody is enrolled yet. Run:  python enroll_face.py")
    engine = faces.FaceEngine()
    camera = faces.open_camera(rules.get("camera", 0))
    print(f"Rule: say a name if the best score is at least {sure_enough} "
          f"and beats second place by {beat_second_by}.")

    while True:
        ok, frame = camera.read()
        if not ok:
            print("Can't read the camera. See 'Camera won't open' in Troubleshooting.")
            break
        frame = cv2.flip(frame, 1)
        found = engine.find_faces(frame)
        scores = {who: 0.0 for who in details}
        answer = None

        if found:
            numbers = engine.embedding(frame, found[0])
            scores = faces.all_scores(numbers, samples, engine.compare)
            answer = faces.decide(scores, sure_enough, beat_second_by)
            x, y, w, h = faces.box(found[0])
            cv2.rectangle(frame, (x, y), (x + w, y + h), GREEN, 4)

        # one score bar per person
        for row, (who, score) in enumerate(scores.items()):
            top = 40 + row * 60
            color = GREEN if who == answer else GRAY
            cv2.putText(frame, f"{details[who]['name']}: {score:.2f}", (30, top),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)
            cv2.rectangle(frame, (30, top + 10), (30 + int(max(score, 0) * 400), top + 26), color, -1)
            line = 30 + int(sure_enough * 400)           # the "sure enough" line
            cv2.line(frame, (line, top + 4), (line, top + 32), WHITE, 3)

        if answer is None:
            verdict = "No face"
        elif answer == faces.FRIEND:
            verdict = "Not sure -> friend"
        else:
            verdict = "It's " + details[answer]["name"] + "!"
        cv2.putText(frame, verdict, (30, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 1.4, YELLOW, 4)
        cv2.imshow("Watch the AI think - press Q to quit", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
