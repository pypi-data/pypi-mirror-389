EZTimer
A simple and intuitive Python timer library for measuring elapsed time with comprehensive pause/resume functionality.

Installation
pip install py-eztimer

## Quick Start

from eztimer import EZTimer
import time

# Basic usage
timer = EZTimer()
timer.start()

# Do some work...
time.sleep(1.5)

print(f"Elapsed time: {timer.get_elapsed_time():.2f} seconds")

# Pause/resume functionality
timer.pause()
time.sleep(1)  # This won't be counted
timer.resume()
time.sleep(0.5)

print(f"Total time: {timer.get_elapsed_time():.2f} seconds")

# Reset and restart
timer.restart()

## API Reference

start()
Start the timer. If already running, has no effect.

pause()
Pause the timer, freezing the current elapsed time.

resume()
Resume a paused timer, continuing from where it left off.

get_elapsed_time() -> float
Get the total elapsed time in seconds.

reset()
Completely reset the timer to zero.

restart()
Reset the timer and immediately start counting again.

## Examples

Benchmarking Code Execution

from eztimer import EZTimer

timer = EZTimer()
timer.start()

# Your code to benchmark
result = sum(i*i for i in range(1000000))

elapsed = timer.get_elapsed_time()
print(f"Computation took {elapsed:.4f} seconds")

Timing with Pauses

from eztimer import EZTimer
import time

timer = EZTimer()
timer.start()

# First operation
time.sleep(0.5)
timer.pause()

# User interaction (not timed)
input("Press Enter to continue...")

timer.resume()
# Second operation
time.sleep(0.3)

print(f"Active time: {timer.get_elapsed_time():.2f} seconds")

## License
MIT