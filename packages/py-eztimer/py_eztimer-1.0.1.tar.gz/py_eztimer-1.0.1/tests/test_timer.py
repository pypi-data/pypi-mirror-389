import time
import unittest
from eztimer import EZTimer

class TestEZTimer(unittest.TestCase):
    
    def test_basic_timing(self):
        timer = EZTimer()
        timer.start()
        time.sleep(0.1)
        elapsed = timer.get_elapsed_time()
        self.assertGreaterEqual(elapsed, 0.1)
    
    def test_pause_resume(self):
        timer = EZTimer()
        timer.start()
        time.sleep(0.1)
        timer.pause()
        paused_time = timer.get_elapsed_time()
        time.sleep(0.1)  # This shouldn't count
        timer.resume()
        time.sleep(0.1)
        total_time = timer.get_elapsed_time()
        
        self.assertGreaterEqual(total_time, 0.2)
        self.assertLess(total_time, 0.25)  # Should be ~0.2s
    
    def test_reset(self):
        timer = EZTimer()
        timer.start()
        time.sleep(0.1)
        timer.reset()
        self.assertEqual(timer.get_elapsed_time(), 0)

if __name__ == "__main__":
    unittest.main()