class DetectResult:
    def __init__(self, boxes=None, scores=None, classes=None):
        if boxes is None:
            boxes = []
        if scores is None:
            scores = []
        if classes is None:
            classes = []
        self.boxes = boxes
        self.classes = classes
        self.scores = scores
