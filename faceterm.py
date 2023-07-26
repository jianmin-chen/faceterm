from PIL import Image
from sys import argv, exit
import numpy as np
import curses, cv2, math, pyaudio, threading, time, wave

DEBUG = True


class Screen:
    """Wrapper around curses."""

    # Using built in colors
    colors = {
        (0, 0, 0): [1, "COLOR_BLACK"],
        (0, 0, 255): [2, "COLOR_BLUE"],
        (0, 100, 100): [3, "COLOR_CYAN"],
        (0, 255, 0): [4, "COLOR_GREEN"],
        (255, 0, 255): [5, "COLOR_MAGENTA"],
        (255, 0, 0): [6, "COLOR_RED"],
        (255, 255, 255): [7, "COLOR_WHITE"],
        (255, 255, 0): [8, "COLOR_YELLOW"],
    }

    def __init__(self):
        self.screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(False)
        if curses.has_colors():
            curses.start_color()
            for color in Screen.colors.values():
                curses.init_pair(
                    color[0], getattr(curses, color[1]), curses.COLOR_BLACK
                )
        self.rows, self.cols = self.screen.getmaxyx()

    def refresh(self):
        self.screen.refresh()

    def cleanup(self):
        self.screen.keypad(False)
        curses.echo()
        curses.nocbreak()
        curses.curs_set(False)
        curses.endwin()


class VideoRecorder:
    def __init__(self, color: bool):
        self.open = True
        self.device_index = 0
        self.fps = 6
        self.fourcc = "MJPG"
        self.frame_size = (640, 480)
        self.video_cap = cv2.VideoCapture(self.device_index)
        self.frame_counts = 1
        self.start_time = time.time()
        self.color = color

    def draw(self, screen: Screen, frame: np.ndarray):
        """
        Draw frame as ASCII pixel image.
        """

        # Originally used this. Not clear enough what you were looking at, so I decided to try out some libraries to do the grunt work for me
        img = Image.fromarray(np.uint8(frame) * 255)
        gray = img.convert("L")
        width, height = gray.size
        screen_width = curses.COLS - 1
        screen_height = min(curses.LINES, math.floor(screen_width * height / width))
        resized = gray.resize((screen_width, screen_height))
        pixels = list(resized.getdata())
        possible_chars = ["-", "#", "<", ">", "|", "&", "@", "$", "%", "*", "!"]
        art = [possible_chars[pixel // 25] for pixel in pixels]
        updated = "".join(art)
        size = len(updated)
        final = [
            updated[index : index + screen_width]
            for index in range(0, size, screen_width)
        ]

        screen.refresh()

        if not self.color:
            for row in range(screen_height):
                screen.screen.addstr(row, 0, final[row])
            return

        # So you want color
        def distance(c1, c2):
            (r1, g1, b1) = c1
            (r2, g2, b2) = c2
            return math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)

        def find(pixel):
            """
            Find closest color in color pairs to pixel.
            """

            closest = min(
                Screen.colors.keys(), key=lambda color: distance(color, pixel)
            )
            return Screen.colors[closest][0]

        resized = img.resize((screen_width, screen_height)).getdata()
        for row in range(screen_height):
            for col in range(screen_width):
                screen.screen.addstr(
                    row,
                    col,
                    art[row * screen_width + col],
                    curses.color_pair(find(resized[row * screen_width + col])),
                )

    def record(self, screen: Screen):
        """
        Records video headlessly.
        """

        while self.open:
            ret, video_frame = self.video_cap.read()
            if ret:
                self.draw(screen, video_frame)
                self.frame_counts += 1
                time.sleep(0.16)
            elif not ret or not self.open:
                break

    def stop(self):
        """
        Stops recording video.
        """

        if self.open:
            self.open = False
            self.video_cap.release()
            cv2.destroyAllWindows()

    def start(self, screen: Screen):
        """
        Starts recording video through a thread.
        """

        video_thread = threading.Thread(target=self.record, args=(screen,))
        video_thread.start()


class AudioRecorder:
    def __init__(self):
        self.open = True
        self.rate = 44100
        self.frames_per_buffer = 1024
        self.channels = 2
        self.format = pyaudio.paInt16
        self.audio = pyaudio.PyAudio()
        self.audio_filename = "test.wav"
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.frames_per_buffer,
        )
        self.audio_frames = []

    def record(self):
        """
        Records audio headlessly.
        """

        self.stream.start_stream()
        while self.open:
            data = self.stream.read(self.frames_per_buffer)
            self.audio_frames.append(data)
            if not self.open:
                break

    def stop(self):
        """
        Stops recording audio.
        """

        if self.open:
            self.open = False
            self.stream.stop_stream()
            self.stream.close()
            self.audio.terminate()

            if DEBUG:
                print("Saving audio file for debugging")
                with wave.open(self.audio_filename, "wb") as wavefile:
                    wavefile.setnchannels(self.channels)
                    wavefile.setsampwidth(self.audio.get_sample_size(self.format))
                    wavefile.setframerate(self.rate)
                    wavefile.write(b"".join(self.audio_frames))

    def start(self):
        """
        Starts recording audio through a thread.
        """

        audio_thread = threading.Thread(target=self.record)
        audio_thread.start()


screen: Screen = None
video_thread: VideoRecorder = None
audio_thread: AudioRecorder = None


def start_video_recording(screen, color=False):
    global video_thread
    video_thread = VideoRecorder(color)
    video_thread.start(screen)


def start_audio_recording():
    global audio_thread
    audio_thread = AudioRecorder()
    audio_thread.start()


def stop_recording():
    screen.cleanup()
    video_thread.stop()
    audio_thread.stop()


if __name__ == "__main__":
    try:
        screen = Screen()
        if "--color" in argv:
            start_video_recording(screen, True)
        else:
            start_video_recording(screen)
        start_audio_recording()
    except KeyboardInterrupt:
        stop_recording()
        if video_thread:
            video_thread.join()
        if audio_thread:
            audio_thread.join()
        print("Done")
        exit(0)
    except Exception as e:
        print("There was an error?", e)
        exit(-1)
