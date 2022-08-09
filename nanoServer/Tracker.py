from typing import List, Iterable, Union


class Box:
    def __init__(self, bbox: List):
        self.x1 = bbox[0]
        self.y1 = bbox[1]
        self.x2 = bbox[2]
        self.y2 = bbox[3]
        self.class_id = bbox[4]
        self.id = 0
        self.gen = 0


class IDGenerator:
    def __init__(self):
        self.id_map = {}

    def get(self, class_id: int) -> int:
        id_count = self.id_map.get(class_id, 0) + 1
        self.id_map[class_id] = id_count
        return id_count

    def reset(self):
        self.id_map.clear()


class Tracker:
    def __init__(self, iou_threshold: float, generation_limit=3):
        self.iou_threshold = iou_threshold
        self.tracked: List[Box] = []
        self.id_generator = IDGenerator()
        self.generation_limit = generation_limit

    def __str__(self):
        s = ''
        for box in self.tracked:
            s += f'x1:{box.x1}, y1:{box.y1}, x2:{box.x2}, y2:{box.y2}, id:{box.id}, gen:{box.gen}' + '\n'
        s += '-----------------------------\n'
        return s

    def get(self):
        return [box for box in self.tracked if box.gen == 0]

    def update(self, boxes: Iterable):
        if len(self.tracked) == 0:
            self.add_all_boxes(boxes)
            return
        tracked = []
        for box in boxes:
            box = Box(box)
            match_box = self.pop_match_box(box)
            if match_box is None:
                box.id = self.id_generator.get(box.class_id)
                tracked.append(box)
            else:
                box.id = match_box.id
                tracked.append(box)

        self.filtrate_generation()
        self.tracked.extend(tracked)

    def pop_match_box(self, box: Box) -> Union[Box, None]:
        max_iou_score = 0
        exist_box_id = 0
        for index, exist_box in enumerate(self.tracked):
            if box.class_id != exist_box.class_id:
                continue
            iou_score = self.calc_iou(box, exist_box)
            if iou_score > max_iou_score:
                max_iou_score = iou_score
                exist_box_id = index
        if max_iou_score >= self.iou_threshold:
            return self.tracked.pop(exist_box_id)

        return None

    def calc_iou(self, box1: Box, box2: Box) -> float:
        if box1.class_id != box2.class_id:
            return 0.0

        x_left = max(box1.x1, box2.x1)
        y_top = max(box1.y1, box2.y1)
        x_right = min(box1.x2, box2.x2)
        y_bottom = min(box1.y2, box2.y2)

        if x_right < x_left or y_bottom < y_top:
            return 0.0

        inter_area = (x_right - x_left) * (y_bottom - y_top)
        box1_area = (box1.x2 - box1.x1) * (box1.y2 - box1.y1)
        box2_area = (box2.x2 - box2.x1) * (box2.y2 - box2.y1)

        return inter_area / (box1_area + box2_area - inter_area)

    def reset(self):
        self.tracked.clear()
        self.id_generator.reset()

    def add_all_boxes(self, boxes):
        for box in boxes:
            box = Box(box)
            box.id = self.id_generator.get(box.class_id)
            self.tracked.append(box)

    def filtrate_generation(self):
        for box in self.tracked:
            box.gen += 1
            if box.gen > self.generation_limit:
                self.tracked.remove(box)
