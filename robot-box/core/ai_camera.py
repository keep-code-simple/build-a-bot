# The Raspberry Pi AI Camera has its own little AI chip (a Sony IMX500).
# The chip can find people, pets and things, or body poses, all by itself,
# and hands the Pi the answer together with each picture. The Pi stays cool.
# It can NOT find hands or faces. The Pi's own processor does those (see vision.py).
#
# NOT TESTED YET: this file was written from the Raspberry Pi examples without a real
# AI Camera on the desk. If something here is wrong, the debug overlay and the log will say so.

from pathlib import Path

MODELS = Path("/usr/share/imx500-models")       # put there by: sudo apt install imx500-all
MODEL_FILES = {
    "detect": MODELS / "imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk",
    "pose": MODELS / "imx500_network_higherhrnet_coco.rpk",
}
HOW_SURE = 0.5


def is_plugged_in():
    """True if the camera on this Pi is the AI Camera and its models are installed."""
    if not MODEL_FILES["detect"].exists():
        return False
    try:
        from picamera2 import Picamera2
        return any("imx500" in str(camera.get("Model", "")).lower()
                   for camera in Picamera2.global_camera_info())
    except Exception:
        return False


class AIChip:
    def __init__(self, kind):
        from picamera2.devices import IMX500
        self.kind = kind
        self.chip = IMX500(str(MODEL_FILES[kind]))      # sends the model to the camera's chip
        self.camera_number = self.chip.camera_num
        self.labels = getattr(self.chip.network_intrinsics, "labels", None) or []

    def results(self, metadata, picam, mirrored=False):
        outputs = self.chip.get_outputs(metadata, add_batch=True)
        if outputs is None:                             # the chip is still loading its model
            return {}
        width, height = picam.camera_configuration()["main"]["size"]
        if self.kind == "pose":
            return {"poses": self._poses(outputs, width, height, mirrored)}
        return {"objects": self._objects(outputs, metadata, picam, width, height, mirrored)}

    def _objects(self, outputs, metadata, picam, width, height, mirrored):
        boxes, scores, classes = outputs[0][0], outputs[1][0], outputs[2][0]
        found = []
        for box, score, number in zip(boxes, scores, classes):
            if score < HOW_SURE:
                continue
            x, y, w, h = self.chip.convert_inference_coords(box, metadata, picam)   # in screen pixels
            x, y, w, h = x / width, y / height, w / width, h / height               # now 0.0 to 1.0
            if mirrored:
                x = 1 - x - w
            name = self.labels[int(number)] if int(number) < len(self.labels) else str(int(number))
            found.append((name, float(score), (x, y, w, h)))
        return found

    def _poses(self, outputs, width, height, mirrored):
        from picamera2.devices.imx500.postprocess_highernet import postprocess_higherhrnet
        keypoints, scores, boxes = postprocess_higherhrnet(
            outputs=outputs, img_size=(height, width), img_w_pad=(0, 0), img_h_pad=(0, 0),
            detection_threshold=HOW_SURE, network_postprocess=True)
        poses = []
        for person in keypoints:                        # 17 body points per person: x, y, how sure
            points = [(p[0] / width, p[1] / height) for p in person.reshape(-1, 3)]
            poses.append([(1 - x, y) for x, y in points] if mirrored else points)
        return poses
