import time

class EZTimer:
    """
    EZTimer - A simple and intuitive timer class for measuring elapsed time 
    \nwith comprehensive pause/resume functionality. Perfect for benchmarking code, 
    \ntracking operation durations, or measuring execution times with precision 
    \nand flexibility across various use cases and applications.
    """
    
    def __init__(self):
        """
        Initialize a new EZTimer instance. Creates a fresh timer with zero 
        \nelapsed time. The timer starts in a stopped state and will only 
        \nbegin counting after the start() method is explicitly called.
        \nTimer state is managed internally with start_time and elapsed_time.
        """
        self.start_time = None
        self.elapsed_time = 0
    
    def start(self):
        """
        Start the timer and begin counting elapsed time. If the timer is 
        \nalready running, this method has no effect. Sets the internal 
        \nstart_time to the current system time using time.time() for 
        \naccurate time measurement from the moment of invocation.
        """
        self.start_time = time.time()
    
    def pause(self):
        """
        Pause the timer and freeze the current elapsed time measurement. 
        \nThe accumulated time up to the pause moment is saved, and the 
        \ntimer stops counting until resume() is called. If the timer is 
        \nalready paused, this method has no additional effect.
        """
        if self.start_time is not None:
            self.elapsed_time += time.time() - self.start_time
            self.start_time = None
    
    def resume(self):
        """
        Resume a paused timer and continue counting time from where it 
        \nwas stopped. The timer continues accumulating time while 
        \npreserving previously elapsed duration. If the timer is already 
        \nrunning, this method has no effect on the current measurement.
        """
        if self.start_time is None:
            self.start_time = time.time()
    
    def get_elapsed_time(self):
        """
        Retrieve the total elapsed time measured by the timer in seconds. 
        \nReturns the cumulative time including both running and paused 
        \nperiods. The time is calculated with sub-second precision and 
        \nrepresents the actual duration the timer has been active.
        """
        if self.start_time is not None:
            return self.elapsed_time + (time.time() - self.start_time)
        return self.elapsed_time
    
    def reset(self):
        """
        Completely reset the timer to its initial state. Clears all 
        \naccumulated time and stops the timer if it's running. After 
        \nreset, the timer will have zero elapsed time and requires 
        \na new call to start() to begin measuring time again.
        """
        self.start_time = None
        self.elapsed_time = 0

    def restart(self):
        """
        Reset the timer to zero and immediately start counting again 
        \nin a single operation. This is equivalent to calling reset() 
        \nfollowed by start(), but performed atomically for convenience 
        \nand to ensure no time gap between reset and start operations.
        """
        self.start_time = time.time()
        self.elapsed_time = 0

print("EZTimer loaded successfully!")

## Example
# my_timer = EZTimer()
# my_timer.start()
# input("Press ENTER when you're ready.")
# print(f"Time passed: {my_timer.get_elapsed_time():.2f} seconds.")