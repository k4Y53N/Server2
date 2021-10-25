from .Connection import Connection
from PIL import Image, ImageDraw, ImageFont
from Adafruit_SSD1306 import SSD1306_128_32
from time import sleep, time, gmtime, strftime
from threading import Thread


class pyOLED:

    def __init__(self, connection: Connection) -> None:
        self.__connection = connection
        self.__display = SSD1306_128_32(rst=None, i2c_bus=1, gpio=1)
        self.__display.begin()
        self.__display.clear()
        self.__display.display()
        self.__server_activate_time = time()
        self.__client_activate_time = None
        self.__server_addr = self.__connection.get_server_address()
        self.__client_addr = None
        self.__delay = 1 / 4
        self.__time_fmt = '%H:%M:%S'
        self.__width = self.__display.width
        self.__height = self.__display.height
        self.__image = Image.new('1', (self.__width, self.__height))
        self.__font = ImageFont.load_default()
        self.__draw = ImageDraw.Draw(self.__image)
        self.__x_time_padding = self.__calc_padding('00:00:00')
        self.__thread = Thread(target=self.__loop, daemon=True)

    def activate(self):
        if self.__thread.is_alive():
            return

        try:
            self.__thread.start()
        except RuntimeError:
            self.__thread = Thread(target=self.__loop, daemon=True)
            self.__thread.start()

    def __loop(self):
        while self.__connection.is_connect():
            self.__update()
            self.__display.image(self.__image)
            self.__display.display()
            sleep(self.__delay)

        self.__close()

    def __update(self):
        t = time()
        client_address = self.__connection.get_client_address()

        if client_address != self.__client_addr:
            self.__client_activate_time = t
            self.__client_addr = client_address

        self.__draw_server(t)
        self.__draw_client(t)
        sleep(self.__delay)

    def __close(self):
        pass

    def __draw_server(self, nowtime: float):
        x = self.__calc_padding(self.__server_addr)
        self.__draw.text(
            (x, -2),
            self.__server_addr,
            fill=255,
            font=self.__font
        )
        s_uptime_txt = self.__calc_time(self.__server_activate_time, nowtime)
        self.__draw.text(
            (self.__x_time_padding, 6),
            s_uptime_txt,
            fill=255,
            font=self.__font
        )

    def __draw_client(self, nowtime: float):

        x = self.__calc_padding(f'{self.__client_addr}')
        self.__draw.text(
            (x, 14),
            f'{self.__client_addr}',
            fill=255,
            font=self.__font
        )

        c_uptime_txt = None
        if self.__client_addr:
            c_uptime_txt = self.__calc_time(
                self.__client_activate_time, nowtime)
        else:
            c_uptime_txt = self.__calc_time(0, 0)

        self.__draw.text(
            (self.__x_time_padding, 22),
            c_uptime_txt,
            fill=255,
            font=self.__font
        )

    def __calc_padding(self, text: str):
        return (self.__width - self.__draw.textsize(text)) / 2

    def __calc_time(self, t1: float, t2: float) -> str:
        if t1 > t2:
            t1, t2 = t2, t1
        return strftime(self.__time_fmt, gmtime(t2 - t1))

    def is_alive(self):
        return self.__thread.is_alive()
