from utils.util import nowait
from Connection import Connection
from PIL import Image, ImageDraw, ImageFont
from Adafruit_SSD1306 import SSD1306_128_32
from time import sleep, time, gmtime, strftime
from threading import Thread


# def calc_padding(img_w, msg_size): return (img_w - msg_size) / 2


class pyOLED:

    def __init__(self, connection: Connection) -> None:
        self.__connection = connection
        self.__server_activate_time = time()
        self.__client_activate_time = None()
        self.__server_addr = self.__connection.get_server_address()
        self.__client_addr = None
        self.__display = SSD1306_128_32(rst=None, i2c_bus=1, gpio=1)
        self.__display.begin()
        self.__display.clear()
        self.__display.display()
        self.__delay = 1/4
        self.__time_fmt = '%H:%M:%S'
        self.__x_time_padding = self.__calc_padding('00:00:00')
        self.__width = self.__display.width
        self.__height = self.__display.height
        self.__font = ImageFont.load_default()
        self.__image = Image.new('1', (self.__width, self.__height))
        self.__draw = ImageDraw.Draw(self.__image)
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



        
# class pioled:
#     def __init__(self):
#         self.__disp = Adafruit_SSD1306.SSD1306_128_32(rst=None, i2c_bus=1, gpio=1)
#         self.__disp.begin()
#         self.__disp.clear()
#         self.__disp.display()
#         self.__width = self.__disp.width
#         self.__height = self.__disp.height
#         self.__font = ImageFont.load_default()
#         self.__img = Image.new('1', (self.__width, self.__height))
#         self.__draw = ImageDraw.Draw(self.__img)
#         self.__thread = threading.Thread(target=self.__oled_loop, daemon=True)
#         self.__is_show_oled = True
#         self.__oled_delay = 1
#         self.__uptime = None
#         self.__server_address = None
#         self.__client_address = None
#         self.__client_uptime = None
#         self.time_Xpading = cal_padding(self.__width, self.__draw.textsize('00:00:00')[0])
#         self.sip_Xpading = 0
#         self.cip_Xpading = cal_padding(self.__width, self.__draw.textsize('None')[0])

#     def start(self, address: str):
#         self.__server_address = address
#         self.__uptime = time.time()
#         self.sip_Xpading = cal_padding(self.__width, self.__draw.textsize(address)[0])
#         try:
#             if not self.__thread.is_alive():
#                 self.__thread.start()
#         except RuntimeError:
#             self.__thread = threading.Thread(target=self.__oled_loop, daemon=True)
#             self.__thread.start()

#     def __oled_loop(self):
#         self.__is_show_oled = True
#         while self.__is_show_oled:
#             self.__set_content()
#             self.__disp.image(self.__img)
#             self.__disp.display()
#             time.sleep(self.__oled_delay)

#     def __set_content(self):
#         t = int(time.time())
#         self.__draw.rectangle((0, 0, self.__width, self.__height), outline=0, fill=0)
#         self.__draw.text((self.sip_Xpading, -2), self.__server_address, fill=255, font=self.__font)
#         suptime = time.strftime('%H:%M:%S', time.gmtime(t - self.__uptime))
#         self.__draw.text((self.time_Xpading, 6), suptime, fill=255, font=self.__font)

#         if self.__client_address:
#             self.__draw.text((self.cip_Xpading, 14), self.__client_address, fill=255, font=self.__font)
#             cuptime = time.strftime('%H:%M:%S', time.gmtime(t - self.__client_uptime))
#             self.__draw.text((self.time_Xpading, 22), cuptime, fill=255, font=self.__font)
#         else:
#             self.__draw.text((self.cip_Xpading, 14), 'None', fill=255, font=self.__font)
#             cuptime = time.strftime('%H:%M:%S', time.gmtime(0))
#             self.__draw.text((self.time_Xpading, 22), cuptime, fill=255, font=self.__font)

#     def reset(self):
#         self.__client_address = None
#         self.__client_uptime = None
#         self.cip_Xpading = cal_padding(self.__width, self.__draw.textsize('None')[0])

#     def set_client(self, address: str):
#         self.__client_address = address
#         self.__client_uptime = time.time()
#         self.cip_Xpading = cal_padding(self.__width, self.__draw.textsize(address)[0])

#     def close(self):
#         self.__is_show_oled = False
#         self.__disp.clear()
#         self.__disp.display()
#         self.__thread.join(1)
