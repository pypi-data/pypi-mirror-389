from .txtcleanen import txtcleanen
import sys

class TxtCleanEn:
    def __call__(self, text):
        return txtcleanen(text)

sys.modules[__name__] = TxtCleanEn()