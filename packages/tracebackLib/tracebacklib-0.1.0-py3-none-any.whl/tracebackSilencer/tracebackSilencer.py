from Packages.AnsiCoolFORMATING import foregroundColors, textFormating
from Packages.customTraceback import customTraceback
class Silencer:
    def __init__(self):
        self.debugM = False
    @staticmethod #wdym
    def traceback(name, value, tb, line):
        pass
    customTraceback.setTraceBack(traceback)
    def debug(self, dm, resetTb=False):
        self.debugM = dm
        if resetTb:
            customTraceback.Reset()

            lines = f.read()
        ix = 0
        ib = 0
        for l in lines.splitlines():
            try:
                ix += 1
                exec(l)
            except:
                try:
                    eval(l)
                except Exception as e:
                    if self.debugM:
                        print(f"ERROR: {e}")
                        ib += 1
        if self.debugM:
            print("DEBUG REPORT:")
            print(f"Traced {ib} of {ix} lines.")
