# Chapter 3, Bonus: Age Guesser
# The camera finds each face, then a second AI guesses how old that person looks.
# It only picks an age GROUP (like 25-32), and it is often wrong. That's part of the fun!
# No Arduino needed. Click the camera window and press Q to quit.

from pathlib import Path
import time

import cv2
import mediapipe as mp
import numpy as np

CAMERA = 0      # if your iPhone's camera opens instead, change this to 1
SMOOTHING = 0.9 # closer to 1 = the guess changes more slowly (less flicker)

# The age AI can only answer with one of these 8 groups
AGE_GROUPS = ["0-2", "4-6", "8-12", "15-20", "25-32", "38-43", "48-53", "60+"]

FACE_MODEL = Path(__file__).parent / "blaze_face_short_range.tflite"
AGE_MODEL = Path(__file__).parent / "age_googlenet.onnx"
if not FACE_MODEL.exists():
    raise SystemExit("Missing the face model. Do Step 1 (download the AI models) first.")
if not AGE_MODEL.exists():
    raise SystemExit("Missing the age model. Download it with:\n"
                     "curl -L -O https://github.com/onnx/models/raw/main/validated/vision/"
                     "body_analysis/age_gender/models/age_googlenet.onnx")


def guess_age(frame, box):
    """Cuts the face out of the picture and returns 8 scores, one for each age group."""
    height, width = frame.shape[:2]
    # Take a bit more than the box, so the AI also sees hair and chin
    pad = int(box.width * 0.3)
    left, top = max(box.origin_x - pad, 0), max(box.origin_y - pad, 0)
    right = min(box.origin_x + box.width + pad, width)
    bottom = min(box.origin_y + box.height + pad, height)
    if right <= left or bottom <= top:
        return None
    face = frame[top:bottom, left:right]
    # The age AI wants a 224x224 picture with these color numbers subtracted
    blob = cv2.dnn.blobFromImage(face, 1.0, (224, 224), (104, 117, 123))
    age_ai.setInput(blob)
    return age_ai.forward()[0]


options = mp.tasks.vision.FaceDetectorOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=str(FACE_MODEL)),
    running_mode=mp.tasks.vision.RunningMode.VIDEO,
    min_detection_confidence=0.6,      # how sure the AI must be before it says "face"
)
face_finder = mp.tasks.vision.FaceDetector.create_from_options(options)
age_ai = cv2.dnn.readNetFromONNX(str(AGE_MODEL))
camera = cv2.VideoCapture(CAMERA)

smooth_scores = []      # one running average of the 8 scores for each face on screen

while True:
    ok, frame = camera.read()
    if not ok:
        print("Can't read the camera. See 'Camera won't open' in Troubleshooting.")
        break

    frame = cv2.flip(frame, 1)                       # mirror it, like a selfie
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)     # the AI wants colors in RGB order
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = face_finder.detect_for_video(image, int(time.monotonic() * 1000))

    # Go through the faces from left to right, so each one keeps its own average
    faces = sorted(result.detections, key=lambda face: face.bounding_box.origin_x)
    if len(faces) != len(smooth_scores):
        smooth_scores = [None] * len(faces)          # someone came or left: start over

    for i, face in enumerate(faces):
        box = face.bounding_box
        scores = guess_age(frame, box)
        if scores is None:
            continue
        # Mix the new guess into the average so the label doesn't jump around
        if smooth_scores[i] is None:
            smooth_scores[i] = scores
        else:
            smooth_scores[i] = SMOOTHING * smooth_scores[i] + (1 - SMOOTHING) * scores
        best = int(np.argmax(smooth_scores[i]))
        sure = smooth_scores[i][best]                 # 0.0 to 1.0

        cv2.rectangle(frame, (box.origin_x, box.origin_y),
                      (box.origin_x + box.width, box.origin_y + box.height), (0, 255, 0), 4)
        cv2.putText(frame, f"Age {AGE_GROUPS[best]}? ({sure:.0%} sure)",
                    (box.origin_x, box.origin_y - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.putText(frame, f"Faces: {len(faces)}", (30, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 4)
    cv2.imshow("Age Guesser - press Q to quit", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
