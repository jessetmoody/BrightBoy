# pantilthat emulator
# Jesse Moody, 11/27/2020

class Pantilthat:
    def __init__(self):
        # public
        self.WS2812 = 1
        self.GRBW = 2

        # private
        self._panAngle = 0
        self._tiltAngle = 0
        self._lightMode = ''
        self._lightType = ''

    def light_mode(self, *args):
        self._lightMode = args[0]
        return

    def light_type(self, *args):
        self._lightType = args[0]
        return

    def pan(self, angle):
        self._panAngle = angle
        print(f'servo panned {self._panAngle} degrees')

    def tilt(self, angle):
        self._tiltAngle = angle
        print(f'servo tilted {self._tiltAngle} degrees')

    def set_all(self, one, two, three, four): # TODO: Change parameter var names to better match their actual fn
        print(f'Ring light levels set')

    def show(self):
        print(f'Ring light levels activated (ON)')

    def get_pan(self):
        return self._panAngle

    def get_tilt(self):
        return self._tiltAngle
