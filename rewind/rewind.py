import sqlite3
import os
import curses
from curses import wrapper
import io
from PIL import Image
import locale

locale.setlocale(locale.LC_ALL, "")

config_dir = os.path.expanduser("~/.config/rewind")
db_path = os.path.join(config_dir, "screenshots.db")
config_path = os.path.join(config_dir, "config.yaml")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()


def search_screenshots(query, timestamp=None):
    if timestamp:
        cursor.execute(
            """
            SELECT id, text, timestamp FROM screenshots 
            WHERE LOWER(text) LIKE LOWER(?) AND timestamp = ?
        """,
            ("%" + query + "%", timestamp),
        )
    else:
        cursor.execute(
            """
            SELECT id, text, timestamp FROM screenshots 
            WHERE LOWER(text) LIKE LOWER(?)
        """,
            ("%" + query + "%",),
        )
    return cursor.fetchall()


def get_screenshot_image(id):
    cursor.execute(
        """
        SELECT image FROM screenshots WHERE id=?
    """,
        (id,),
    )
    result = cursor.fetchone()
    if result:
        return result[0]
    return None


def get_all_timestamps():
    cursor.execute("""
        SELECT DISTINCT timestamp FROM screenshots ORDER BY timestamp
    """)
    return [row[0] for row in cursor.fetchall()]


class SearchApp:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.results = []
        self.selected_index = 0
        self.query = ""
        self.timestamps = get_all_timestamps()
        self.timeline_index = len(self.timestamps) - 1 if self.timestamps else 0
        self.timeline_mode = False
        self.init_curses()

    def init_curses(self):
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_RED, -1)
        curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_CYAN)
        self.stdscr.keypad(True)

    def search(self):
        if self.timeline_mode:
            self.results = search_screenshots(
                self.query, self.timestamps[self.timeline_index]
            )
        else:
            self.results = search_screenshots(self.query)
        self.selected_index = 0

    def draw_rounded_box(self, y, x, height, width, title="", color_pair=0):
        max_y, max_x = self.stdscr.getmaxyx()

        # Top left
        self.stdscr.addch(y, x, "╭", color_pair)

        # Top right
        if x + width < max_x:
            self.stdscr.addch(y, x + width - 1, "╮", color_pair)

        # Bottom left
        if y + height < max_y:
            self.stdscr.addch(y + height - 1, x, "╰", color_pair)

        # Bottom right
        if y + height < max_y and x + width < max_x:
            self.stdscr.addch(y + height - 1, x + width - 1, "╯", color_pair)

        # Horizontal lines
        self.stdscr.addstr(y, x + 1, "─" * (min(width - 2, max_x - x - 1)), color_pair)
        if y + height < max_y:
            self.stdscr.addstr(
                y + height - 1, x + 1, "─" * (min(width - 2, max_x - x - 1)), color_pair
            )

        # Vertical lines
        for i in range(1, min(height - 1, max_y - y - 1)):
            self.stdscr.addch(y + i, x, "│", color_pair)
            if x + width < max_x:
                self.stdscr.addch(y + i, x + width - 1, "│", color_pair)

        # Title
        if title:
            self.stdscr.addstr(y, x + 2, f" {title} ", color_pair)

    def display(self):
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()

        # Header
        self.draw_rounded_box(0, 0, 3, width, "Rewind Search", curses.color_pair(1))
        self.stdscr.addstr(1, 2, "Search: ", curses.color_pair(1) | curses.A_BOLD)
        self.stdscr.addstr(1, 10, self.query[: width - 11])

        # Results
        results_height = height - 6 if not self.timeline_mode else height - 8
        self.draw_rounded_box(
            3, 0, results_height, width, "Search Results", curses.color_pair(2)
        )
        for idx, result in enumerate(self.results[: results_height - 2]):
            if idx == self.selected_index:
                self.stdscr.attron(curses.color_pair(5) | curses.A_BOLD)
            id_str = f"{result[0]:3d}"
            timestamp = result[2][:19]
            text = self.clean_and_truncate_text(result[1], width - 50)
            self.stdscr.addnstr(
                idx + 4, 2, f"{id_str} | {timestamp} | {text}", width - 4
            )
            if idx == self.selected_index:
                self.stdscr.attroff(curses.color_pair(5) | curses.A_BOLD)

        if not self.results:
            self.stdscr.addstr(4, 2, "No results found.", curses.color_pair(2))

        # Timeline
        if self.timeline_mode:
            self.display_timeline(height - 5, 0, width)

        # Footer
        help_text = "←→: Timeline | Enter: Open | Tab: Toggle Timeline | Esc: Exit"
        self.draw_rounded_box(height - 3, 0, 3, width, "", curses.color_pair(1))
        self.stdscr.addnstr(height - 2, 2, help_text, width - 4, curses.color_pair(1))

        self.stdscr.refresh()

    def display_timeline(self, y, x, width):
        if not self.timestamps:
            self.stdscr.addstr(y, x, "No timeline data", curses.color_pair(3))
            return

        timeline_width = width - 2
        self.stdscr.addstr(y, x, "─" * timeline_width, curses.color_pair(3))

        if len(self.timestamps) > 1:
            step = timeline_width / (len(self.timestamps) - 1)
            pos = int(self.timeline_index * step)
        else:
            pos = 0

        self.stdscr.addch(y, x + pos, "●", curses.color_pair(4) | curses.A_BOLD)

        current_timestamp = self.timestamps[self.timeline_index][:19]
        timestamp_str = f"[{current_timestamp}]"
        start_x = max(0, x + pos - len(timestamp_str) // 2)
        start_x = min(start_x, width - len(timestamp_str) - 1)
        self.stdscr.addstr(y + 1, start_x, timestamp_str, curses.color_pair(4))

    def clean_and_truncate_text(self, text, max_width):
        cleaned_text = " ".join(text.split())
        return cleaned_text[:max_width]

    def open_image(self):
        if self.results:
            id = self.results[self.selected_index][0]
            image_data = get_screenshot_image(id)
            if image_data:
                image = Image.open(io.BytesIO(image_data))
                image.show()

    def run(self):
        while True:
            self.display()
            try:
                key = self.stdscr.get_wch()
            except curses.error:
                continue

            if isinstance(key, str):
                if ord(key) == 27:  # Escape
                    break
                elif key in ("\n", "\r"):  # Enter
                    self.open_image()
                elif key == "\t":  # Tab
                    self.timeline_mode = not self.timeline_mode
                    self.search()
                else:
                    self.query += key
                    self.search()
            elif isinstance(key, int):
                if key in (curses.KEY_BACKSPACE, 127):
                    self.query = self.query[:-1]
                    self.search()
                elif key == curses.KEY_UP:
                    if not self.timeline_mode:
                        self.selected_index = max(0, self.selected_index - 1)
                elif key == curses.KEY_DOWN:
                    if not self.timeline_mode:
                        self.selected_index = min(
                            len(self.results) - 1, self.selected_index + 1
                        )
                elif key == curses.KEY_LEFT:
                    if self.timeline_mode:
                        self.timeline_index = max(0, self.timeline_index - 1)
                        self.search()
                elif key == curses.KEY_RIGHT:
                    if self.timeline_mode:
                        self.timeline_index = min(
                            len(self.timestamps) - 1, self.timeline_index + 1
                        )
                        self.search()


def main(stdscr):
    app = SearchApp(stdscr)
    app.run()


if __name__ == "__main__":
    wrapper(main)
