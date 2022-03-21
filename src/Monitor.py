from PIL import Image, ImageDraw, ImageFont
from Adafruit_SSD1306 import SSD1306_128_32
from time import time, gmtime, strftime
from .RepeatTimer import RepeatTimer
from threading import Lock


class Monitor(RepeatTimer):
    def __init__(self):
        RepeatTimer.__init__(self, name='Monitor')
        self.displayer = SSD1306_128_32(rst=None, i2c_bus=1, gpio=1)
        self.width = self.displayer.width
        self.height = self.displayer.height
        self.image = Image.new('1', (self.width, self.height))
        self.font = ImageFont.load_default()
        self.draw = ImageDraw.Draw(self.image)
        self.rows = ['', '']
        self.row_init_times = [0., 0.]
        self.time_fmt = '%H:%M:%S'
        self.timeX_padding = self.calc_padding('00:00:00')
        self.lock = Lock()

    def init_phase(self):
        self.displayer.begin()
        self.displayer.image(self.image)
        self.displayer.clear()
        self.displayer.display()

    def execute_phase(self):
        self.update()
        self.displayer.image(self.image)
        self.displayer.display()

    def close_phase(self):
        self.displayer.clear()
        self.displayer.display()
        self.displayer.reset()

    def update(self):
        self.draw.rectangle((0, 0, self.width, self.height), fill=0)
        y = -2
        with self.lock:
            for row, r_time in zip(self.rows, self.row_init_times):
                if not row:
                    row = 'None'
                    r_time = 0
                self.draw.text(
                    (self.calc_padding(row), y),
                    row,
                    fill=255,
                    font=self.font
                )
                y += 8
                time_string = self.get_time_string(r_time, time()) if r_time else self.get_time_string(0, 0)
                self.draw.text(
                    (self.calc_padding(time_string), y),
                    time_string,
                    fill=255,
                    font=self.font
                )
                y += 8

    def calc_padding(self, text: str):
        return (self.width - self.draw.textsize(text)[0]) / 2

    def get_time_string(self, t1: float, t2: float) -> str:
        if t1 > t2:
            t1, t2 = t2, t1
        return strftime(self.time_fmt, gmtime(t2 - t1))

    def set_row_string(self, index: int, row_str: str):
        index = int(index % len(self.rows))
        if row_str is None:
            row_str = ''
        with self.lock:
            self.rows[index] = row_str
            self.row_init_times[index] = time()
