# Chapter 3, Step 2: Robot Eyes
# The MacBook camera finds faces and draws a box around each one.
# Click the camera window and press Q to quit.

from pathlib import Path
import time

import cv2
import mediapipe as mp

CAMERA = 0   # if your iPhone's camera opens instead, change this to 1

FACE_MODEL = Path(__file__).parent / "blaze_face_short_range.tflite"
if not FACE_MODEL.exists():
    raise SystemExit("Missing the face model. Do Step 1 (download the AI models) first.")

options = mp.tasks.vision.FaceDetectorOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=str(FACE_MODEL)),
    running_mode=mp.tasks.vision.RunningMode.VIDEO,
    min_detection_confidence=0.6,      # how sure the AI must be before it says "face"
)
face_finder = mp.tasks.vision.FaceDetector.create_from_options(options)
camera = cv2.VideoCapture(CAMERA)

while True:
    ok, frame = camera.read()
    if not ok:
        print("Can't read the camera. See 'Camera won't open' in Troubleshooting.")
        break

    frame = cv2.flip(frame, 1)                       # mirror it, like a selfie
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)     # the AI wants colors in RGB order
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = face_finder.detect_for_video(image, int(time.monotonic() * 1000))

    for face in result.detections:
        box = face.bounding_box
        sure = face.categories[0].score               # 0.0 to 1.0
        cv2.rectangle(frame, (box.origin_x, box.origin_y),
                      (box.origin_x + box.width, box.origin_y + box.height), (0, 255, 0), 4)
        cv2.putText(frame, f"{sure:.0%} sure", (box.origin_x, box.origin_y - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.putText(frame, f"Faces: {len(result.detections)}", (30, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 4)
    cv2.imshow("Robot Eyes - press Q to quit", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
