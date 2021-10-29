from .Connection import Connection
from PIL import Image, ImageDraw, ImageFont
from Adafruit_SSD1306 import SSD1306_128_32
from time import sleep, time, gmtime, strftime
from threading import Thread


class PyOLED:

    def __init__(self, connection: Connection) -> None:
        self.__connection = connection
        self.__display = SSD1306_128_32(rst=None, i2c_bus=1, gpio=1)
        self.__display.begin()
        self.__display.clear()
        self.__display.display()
        self.__server_activate_time = time()
        self.__client_activate_time = None
        self.__server_addr = self.__connection.get_server_address()
        self.__client_addr = self.__connection.get_client_address()
        self.__delay = 1 / 4
        self.__time_fmt = '%H:%M:%S'
        self.__width = self.__display.width
        self.__height = self.__display.height
        self.__image = Image.new('1', (self.__width, self.__height))
        self.__font = ImageFont.load_default()
        self.__draw = ImageDraw.Draw(self.__image)
        self.__x_time_padding = self.__calc_padding('00:00:00')
        self.__thread = Thread(target=self.__loop)

    def activate(self):
        if self.__thread.is_alive():
            return

        try:
            self.__thread.start()
        except RuntimeError:
            self.__thread = Thread(target=self.__loop)
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
        self.__draw.rectangle((0, 0, self.__width, self.__height), fill=0)
        client_address = self.__connection.get_client_address()

        if client_address != self.__client_addr:
            self.__client_activate_time = t
            self.__client_addr = client_address

        self.__draw_server(t)
        self.__draw_client(t)
        sleep(self.__delay)

    def __close(self):
        self.__display.clear()
        self.__display.display()
        self.__display.reset()

    def __draw_server(self, now_time: float):
        server_address_str = ':'.join((self.__server_addr[0], self.__server_addr[1]))
        x = self.__calc_padding(server_address_str)
        self.__draw.text(
            (x, -2),
            server_address_str,
            fill=255,
            font=self.__font
        )
        s_uptime_txt = self.__calc_time(self.__server_activate_time, now_time)
        self.__draw.text(
            (self.__x_time_padding, 6),
            s_uptime_txt,
            fill=255,
            font=self.__font
        )

    def __draw_client(self, now_time: float):
        if self.__client_addr:
            client_address_str = ':'.join((self.__client_addr[0], self.__client_addr[1]))
            c_uptime_txt = self.__calc_time(self.__client_activate_time, now_time)
        else:
            client_address_str = 'None'
            c_uptime_txt = self.__calc_time(0, 0)

        x = self.__calc_padding(client_address_str)
        self.__draw.text(
            (x, 14),
            client_address_str,
            fill=255,
            font=self.__font
        )

        self.__draw.text(
            (self.__x_time_padding, 22),
            c_uptime_txt,
            fill=255,
            font=self.__font
        )

    def __calc_padding(self, text: str):
        return (self.__width - self.__draw.textsize(text)[0]) / 2

    def __calc_time(self, t1: float, t2: float) -> str:
        if t1 > t2:
            t1, t2 = t2, t1
        return strftime(self.__time_fmt, gmtime(t2 - t1))

    def is_alive(self):
        return self.__thread.is_alive()
