# Chapter 3, Step 4: AI Door Greeter
# When the camera sees a face, tell the Arduino "F".
# When the face has been gone for a while, tell it "N".
# Click the camera window and press Q to quit.

from pathlib import Path
import glob
import time

import cv2
import mediapipe as mp
import serial

CAMERA = 0                 # if your iPhone's camera opens instead, change this to 1
STAY_GONE_SECONDS = 2      # how long the face must be gone before the robot resets


def connect_to_arduino():
    ports = (glob.glob("/dev/cu.usbmodem*") + glob.glob("/dev/cu.usbserial*")
             + glob.glob("/dev/cu.wchusbserial*"))
    if not ports:
        raise SystemExit("No Arduino found. Is the USB cable plugged in?")
    try:
        arduino = serial.Serial(ports[0], 9600)
    except serial.SerialException:
        raise SystemExit("The Arduino is busy. Close the Serial Monitor, then try again.")
    print("Connected to the Arduino on", ports[0])
    time.sleep(2)          # the Arduino restarts when we connect, so give it a moment
    return arduino


FACE_MODEL = Path(__file__).parent / "blaze_face_short_range.tflite"
if not FACE_MODEL.exists():
    raise SystemExit("Missing the face model. Do Step 1 (download the AI models) first.")

options = mp.tasks.vision.FaceDetectorOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=str(FACE_MODEL)),
    running_mode=mp.tasks.vision.RunningMode.VIDEO,
    min_detection_confidence=0.6,
)
face_finder = mp.tasks.vision.FaceDetector.create_from_options(options)
arduino = connect_to_arduino()
camera = cv2.VideoCapture(CAMERA)

greeted = False            # have we already said hi to this face?
last_seen = 0.0            # when did we last see a face?

while True:
    ok, frame = camera.read()
    if not ok:
        print("Can't read the camera. See 'Camera won't open' in Troubleshooting.")
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = face_finder.detect_for_video(image, int(time.monotonic() * 1000))
    now = time.monotonic()

    if result.detections:                            # a face is here
        last_seen = now
        if not greeted:
            arduino.write(b"F")                      # tell the Arduino: say hi!
            print("Face! Sent F")
            greeted = True
    elif greeted and now - last_seen > STAY_GONE_SECONDS:
        arduino.write(b"N")                          # tell the Arduino: nobody here
        print("Gone. Sent N")
        greeted = False

    for face in result.detections:
        box = face.bounding_box
        cv2.rectangle(frame, (box.origin_x, box.origin_y),
                      (box.origin_x + box.width, box.origin_y + box.height), (0, 255, 0), 4)

    status = "Greeted!" if greeted else "Waiting for a face..."
    cv2.putText(frame, status, (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 4)
    cv2.imshow("AI Door Greeter - press Q to quit", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

arduino.write(b"N")        # leave the robot in its waiting screen
arduino.close()
camera.release()
cv2.destroyAllWindows()
