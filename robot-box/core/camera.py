# The box's camera. Three kinds, and they all work the same way:
#   camera.read()  -> the newest picture (colors in BGR order, mirrored like a selfie), or None
#   camera.close()
# On the Pi it's the Pi camera (Picamera2). With --desktop it's the Mac's camera (OpenCV).
# The tests use a pretend camera that plays back pictures we give it.

import cv2


class DesktopCamera:
    has_ai = False                        # a normal camera: no AI chip inside

    def __init__(self, number=0, width=1280, height=720):
        self.capture = cv2.VideoCapture(number)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if not self.capture.isOpened():
            raise SystemExit("Can't open the camera. Is another program using it?")

    def read(self):
        ok, frame = self.capture.read()
        return cv2.flip(frame, 1) if ok else None

    def close(self):
        self.capture.release()


class PiCamera:
    """The Raspberry Pi camera. If it's the AI Camera, its chip does some of the seeing."""

    def __init__(self, width=1280, height=720, log=print):
        from . import ai_camera           # Pi-only parts are imported here, so the Mac never needs them
        self.width, self.height, self.log = width, height, log
        self.ai_camera = ai_camera
        self.has_ai = ai_camera.is_plugged_in()
        self.ai = None                    # the AI chip's current model (None on a normal camera)
        self.ai_kind = None
        self.picam = None
        self.metadata = None
        self._start("detect" if self.has_ai else None)

    def _start(self, ai_kind):
        from picamera2 import Picamera2
        if self.picam is not None:
            self.picam.stop()
            self.picam.close()
        self.ai = self.ai_camera.AIChip(ai_kind) if ai_kind else None
        self.ai_kind = ai_kind
        self.picam = Picamera2(self.ai.camera_number) if self.ai else Picamera2()
        # "RGB888" sounds backwards, but it gives pictures in BGR order, which is what OpenCV uses
        settings = self.picam.create_preview_configuration(
            main={"size": (self.width, self.height), "format": "RGB888"})
        self.picam.start(settings, show_preview=False)

    def use_ai(self, ai_kind):
        """Switch the AI chip between "detect" (people and things) and "pose". This is slow!"""
        if self.has_ai and ai_kind != self.ai_kind:
            self.log(f"Loading the AI Camera's {ai_kind} model. This can take a while...")
            self._start(ai_kind)

    def read(self):
        request = self.picam.capture_request()
        try:
            frame = request.make_array("main")
            self.metadata = request.get_metadata()
        finally:
            request.release()
        return cv2.flip(frame, 1)

    def ai_seen(self):
        """What the AI chip found in the newest picture: {"objects": [...]} or {"poses": [...]}."""
        if self.ai is None or self.metadata is None:
            return {}
        return self.ai.results(self.metadata, self.picam, mirrored=True)

    def close(self):
        self.picam.stop()
        self.picam.close()


class FakeCamera:
    """A pretend camera for tests: it shows the same pictures over and over."""
    has_ai = False

    def __init__(self, frames):
        self.frames = list(frames)
        self.count = 0

    def read(self):
        frame = self.frames[self.count % len(self.frames)]
        self.count += 1
        return None if frame is None else frame.copy()

    def close(self):
        pass


def open_camera(desktop, config, log=print):
    settings = config.get("camera", {})
    width, height = settings.get("width", 1280), settings.get("height", 720)
    if desktop:
        return DesktopCamera(settings.get("number", 0), width, height)
    return PiCamera(width, height, log)
