import sys
import traceback

#---Actual Code---#
def customtraceback(exc_type, exc_value, exc_tb):
    line = traceback.format_exception(exc_type, exc_value, exc_tb)[1].strip()[:-19]
    i = 0
    while not line[i:][0] == " ":
        i = i-1
        if i < -25:
            break
    i = i+1
    try:
        line = int(line[i:])
    except Exception:
        pass
    tbf(name=str(exc_type.__name__), value=str(exc_value), tb=traceback.format_tb(exc_tb)[0].strip(), line=str(line))
def default_traceback(name, value, tb, line):
    if name == "BaseException":
        print(value)
    elif not value.strip():
        print(f"{name}")
    else:
        print(f"{name}: {value}")
def traceBackExample(name, value, tb, line):
    print(f"{name}: {value}, at {line}")
    print(tb)
tbf = default_traceback
def setTraceBack(function):
    global tbf
    sys.excepthook = customtraceback
    if not callable(function):
        tbf = default_traceback
        raise BaseException(f"ArgumentException: \"{function}\" is not callable")
    tbf = function
def Reset():
    sys.excepthook = sys.__excepthook__
def help():
    setTraceBack(traceBackExample)
    print(f"\033[91m\033[4mCustomTraceBack\033[0m")
    print(f"\033[91mUSAGE:\033[0m")
    print(f"\033[91mCustomTraceBack.setTraceBack(tracebackfunction)\033[0m")
    print(f"\033[91m(tracebackfunction is a function)\033[0m")
    print(f"EXAMPLE:")
    print(f"def traceBackExample(name, value, tb, line):")
    print("    print(f\"{name}: {value}, at {line}\")")
    print("    print(tb)")
    print("CustomTraceBack.setTraceBack(traceBackExample)")
    print("Lets run the example:")
    raise Exception(f"traceback")
sys.excepthook = customtraceback