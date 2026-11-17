from gpio_buttons import ButtonListener, RELEASED

buttons = ButtonListener([4, 17, 27, 22])

@buttons.pressed(4)
def play(pin):
    print("play/pause")

buttons.on(27, lambda pin: print("27 up"), RELEASED)
buttons.on_any(lambda pin: print(f"{pin} pressed"))

buttons.start()      # non-blocking; main thread is free
...
buttons.stop()