"""
games/memory_match.py
=====================
Memory Match – An autism-friendly tile-flip game for the Neuropy Kivy app.
Features calm colors, predictable slow animations, large tiles, and gentle feedback.
"""

import random
import math
from functools import partial

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle, Line, Rectangle, Ellipse, Triangle, Quad
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.utils import get_color_from_hex
from kivy.app import App
from kivy.properties import StringProperty, BooleanProperty

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))

def draw_shape(canvas_group, shape, color_hex, cx, cy, radius):
    """Draws a cognitive-friendly shape using precise Canvas instructions."""
    r, g, b = hex_to_rgb(color_hex)
    canvas_group.add(Color(r, g, b, 1))
    
    if shape == "circle":
        canvas_group.add(Ellipse(pos=(cx - radius, cy - radius), size=(radius*2, radius*2)))
        
    elif shape == "square":
        sq = radius * 1.8
        canvas_group.add(RoundedRectangle(pos=(cx - sq/2, cy - sq/2), size=(sq, sq), radius=[10]))
        
    elif shape == "triangle":
        # Upward pointing triangle
        x0, y0 = cx, cy + radius
        x1, y1 = cx - radius*0.866, cy - radius*0.5
        x2, y2 = cx + radius*0.866, cy - radius*0.5
        canvas_group.add(Triangle(points=[x0, y0, x1, y1, x2, y2]))
        
    elif shape == "diamond":
        x0, y0 = cx, cy + radius
        x1, y1 = cx - radius*0.8, cy
        x2, y2 = cx, cy - radius
        x3, y3 = cx + radius*0.8, cy
        canvas_group.add(Quad(points=[x0, y0, x1, y1, x2, y2, x3, y3]))
        
    elif shape == "star":
        _draw_star(canvas_group, cx, cy, radius, radius*0.4, 5, r, g, b)
        
    elif shape == "cross":
        w = radius * 0.6
        canvas_group.add(RoundedRectangle(pos=(cx - w/2, cy - radius), size=(w, radius*2), radius=[5]))
        canvas_group.add(RoundedRectangle(pos=(cx - radius, cy - w/2), size=(radius*2, w), radius=[5]))
        
    elif shape == "ring":
        # Render ring as a thick circle line
        canvas_group.add(Line(circle=(cx, cy, radius*0.75), width=radius*0.25))
        
    elif shape == "hexagon":
        points = []
        for i in range(6):
            angle = math.pi / 2 + i * (math.pi / 3)
            points.extend([cx + radius*math.cos(angle), cy + radius*math.sin(angle)])
        for i in range(6):
            x1 = points[i*2]
            y1 = points[i*2+1]
            x2 = points[((i+1)%6)*2]
            y2 = points[((i+1)%6)*2+1]
            canvas_group.add(Triangle(points=[cx, cy, x1, y1, x2, y2]))

def _draw_star(canvas_group, cx, cy, outer_r, inner_r, points_count, r, g, b):
    verts = []
    for i in range(points_count * 2):
        radius = outer_r if i % 2 == 0 else inner_r
        angle  = math.pi / 2 + i * math.pi / points_count
        verts.extend([cx + radius * math.cos(angle), cy + radius * math.sin(angle)])
    n = points_count * 2
    for i in range(n):
        x1 = verts[i * 2]
        y1 = verts[i * 2 + 1]
        x2 = verts[((i + 1) % n) * 2]
        y2 = verts[((i + 1) % n) * 2 + 1]
        canvas_group.add(Triangle(points=[cx, cy, x1, y1, x2, y2]))


# --- Shapes Database ---
SHAPES = [
    ("circle",   "#FF8A80"), # Soft Red
    ("square",   "#82B1FF"), # Soft Blue
    ("triangle", "#B9F6CA"), # Soft Green
    ("diamond",  "#FFE57F"), # Soft Yellow
    ("star",     "#FFD180"), # Soft Orange
    ("cross",    "#B388FF"), # Soft Purple
    ("ring",     "#80CBC4"), # Teal
    ("hexagon",  "#F8BBD0"), # Soft Pink
]

# --- Colors ---
BG_COLOR         = get_color_from_hex("#EAF7F0") # soft mint
TILE_BACK_COLOR  = get_color_from_hex("#C8E6C9") # soft green 
TILE_BACK_BORDER = get_color_from_hex("#A5D6A7")
TILE_FRONT_COLOR = get_color_from_hex("#FFFFFF") # clean white
TILE_FRONT_BORDER= get_color_from_hex("#E0E0E0")
TEXT_COLOR       = get_color_from_hex("#2E7D32") # calm green text

# --- Animation Speeds ---
FLIP_DUR   = 0.5
MATCH_DUR  = 1.0
PREVIEW_DUR= 3.0

# --- Feedback Messages ---
MATCH_MSGS  = ["Great match!", "Well done!", "Nice job!", "You found it!"]
MISS_MSGS   = ["Let's try again.", "Good effort!"]

CONFETTI_COUNT = 40

class TileButton(ButtonBehavior, BoxLayout):
    shape_name = StringProperty("")
    shape_col  = StringProperty("#FFFFFF")
    revealed   = BooleanProperty(False)
    
    def __init__(self, shape_name, shape_col, **kwargs):
        super().__init__(**kwargs)
        self.shape_name = shape_name
        self.shape_col  = shape_col
        self.size_hint = (1, 1)
        self._showing_front = False
        self.is_wrong = False
        self.is_hint = False
        
        from kivy.graphics import InstructionGroup
        self.draw_group = InstructionGroup()
        self.canvas.add(self.draw_group)

        self.bind(pos=self._redraw, size=self._redraw)
        Clock.schedule_once(self._redraw, 0)

    def _redraw(self, *args):
        self.draw_group.clear()
        if self._showing_front:
            self._draw_front()
        else:
            self._draw_back()

    def _draw_back(self):
        w, h = self.width, self.height
        
        self.draw_group.add(Color(0, 0, 0, 0.05)) # softer shadow
        self.draw_group.add(RoundedRectangle(pos=(self.x + 2, self.y - 2), size=(w, h), radius=[16]))
        self.draw_group.add(Color(*TILE_BACK_COLOR))
        self.draw_group.add(RoundedRectangle(pos=self.pos, size=self.size, radius=[16]))
        
        if getattr(self, 'is_hint', False):
            self.draw_group.add(Color(*get_color_from_hex("#FFD700"))) # Gold border
            self.draw_group.add(Line(rounded_rectangle=(self.x, self.y, w, h, 16), width=6))
        else:
            self.draw_group.add(Color(*TILE_BACK_BORDER))
            self.draw_group.add(Line(rounded_rectangle=(self.x, self.y, w, h, 16), width=2))
            
        if not hasattr(self, '_lbl'):
            self._lbl = Label(
                text="?",
                font_name="Roboto",
                font_size=min(self.width, self.height) * 0.4,
                bold=True, color=(1, 1, 1, 0.8),
                size_hint=(None, None), size=self.size, pos=self.pos,
            )
            self.add_widget(self._lbl)
        else:
            self._lbl.text = "?"
            self._lbl.color = (1, 1, 1, 0.8)
            self._lbl.pos  = self.pos
            self._lbl.size = self.size
            self._lbl.font_size = min(self.width, self.height) * 0.4
            self._lbl.opacity = 1

    def _draw_front(self):
        w, h = self.width, self.height
        
        self.draw_group.add(Color(0, 0, 0, 0.05))
        self.draw_group.add(RoundedRectangle(pos=(self.x + 2, self.y - 2), size=(w, h), radius=[16]))
        self.draw_group.add(Color(*TILE_FRONT_COLOR))
        self.draw_group.add(RoundedRectangle(pos=self.pos, size=self.size, radius=[16]))
        
        if getattr(self, 'is_wrong', False):
            self.draw_group.add(Color(*get_color_from_hex("#E53935"))) # Red border
            self.draw_group.add(Line(rounded_rectangle=(self.x, self.y, w, h, 16), width=8))
        else:
            self.draw_group.add(Color(*TILE_FRONT_BORDER))
            border_w = 4 if self.revealed else 2
            self.draw_group.add(Line(rounded_rectangle=(self.x, self.y, w, h, 16), width=border_w))

        if hasattr(self, '_lbl'):
            self._lbl.opacity = 0

        # Draw actual shape
        cx, cy = self.center_x, self.center_y
        radius = min(w, h) * 0.28
        draw_shape(self.draw_group, self.shape_name, self.shape_col, cx, cy, radius)

    def flip_to_front(self, on_done=None):
        if self._showing_front: return
        half1 = Animation(size_hint_x=0.01, duration=FLIP_DUR/2, t='in_quad')
        def _switch(*a):
            self._showing_front = True
            self._redraw()
            half2 = Animation(size_hint_x=1.0, duration=FLIP_DUR/2, t='out_quad')
            if on_done: half2.bind(on_complete=lambda *a: on_done())
            half2.start(self)
        half1.bind(on_complete=_switch)
        half1.start(self)

    def flip_to_back(self, on_done=None):
        if not self._showing_front: return
        half1 = Animation(size_hint_x=0.01, duration=FLIP_DUR/2, t='in_quad')
        def _switch(*a):
            self._showing_front = False
            self._redraw()
            half2 = Animation(size_hint_x=1.0, duration=FLIP_DUR/2, t='out_quad')
            if on_done: half2.bind(on_complete=lambda *a: on_done())
            half2.start(self)
        half1.bind(on_complete=_switch)
        half1.start(self)

    def mark_matched(self):
        self.revealed = True
        self._redraw()
        pulse = (Animation(size_hint_x=1.05, size_hint_y=1.05, duration=0.3) +
                 Animation(size_hint_x=1.0,  size_hint_y=1.0,  duration=0.3))
        pulse.start(self)

    def mark_wrong(self):
        self.is_wrong = True
        self._redraw()
        pulse = (Animation(size_hint_x=0.95, size_hint_y=0.95, duration=0.1) +
                 Animation(size_hint_x=1.0,  size_hint_y=1.0,  duration=0.1))
        pulse.start(self)

    def clear_wrong(self):
        if getattr(self, 'is_wrong', False):
            self.is_wrong = False
            self._redraw()

    def on_press(self):
        # Only gentle bounce on press, logic handles flip
        if not self.revealed and not self._showing_front:
            a = Animation(size_hint_x=0.95, size_hint_y=0.95, duration=0.1)
            a += Animation(size_hint_x=1.0,  size_hint_y=1.0,  duration=0.1)
            a.start(self)


class MemoryMatchGame(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding     = [20, 20, 20, 20]
        self.spacing     = 20
        with self.canvas.before:
            Color(*BG_COLOR)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        self._tiles_up   = []
        self._locked     = False
        self._matches    = 0
        self._consecutive_misses = 0
        self._hinted_tile = None
        self._started    = False
        self._level      = 1 # 1: 3x2, 2: 4x3, 3: 4x4
        self._cols       = 3
        self._rows       = 2

        self._build_ui()
        self._new_game()

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def _build_ui(self):
        # 1. Top Bar
        title_bar = BoxLayout(size_hint_y=None, height=60, spacing=20)

        back_btn = Button(text="< Home", size_hint_x=None, width=140,
            background_normal='', background_color=get_color_from_hex("#A5D6A7"),
            color=TEXT_COLOR, bold=True, font_size='20sp')
        back_btn.bind(on_release=self._go_home)
        title_bar.add_widget(back_btn)

        self._title_lbl = Label(text="MEMORY MATCH", font_size='36sp', bold=True, color=TEXT_COLOR)
        title_bar.add_widget(self._title_lbl)

        restart_btn = Button(text="Restart", size_hint_x=None, width=140,
            background_normal='', background_color=get_color_from_hex("#A5D6A7"),
            color=TEXT_COLOR, bold=True, font_size='20sp')
        restart_btn.bind(on_release=lambda *a: self._new_game())
        title_bar.add_widget(restart_btn)
        self.add_widget(title_bar)
        
        # 2. Controls Bar (Level Only!)
        controls_bar = BoxLayout(size_hint_y=None, height=50, spacing=15)
        # Empty space left
        controls_bar.add_widget(Label(text="", size_hint_x=1))
        
        level_box = BoxLayout(spacing=10, size_hint_x=None, width=400)
        level_box.add_widget(Label(text="Grid:", color=TEXT_COLOR, font_size='18sp', bold=True, size_hint_x=None, width=80))
        self._level_btns = {}
        for lvl, name in [(1, "3x2"), (2, "4x3"), (3, "4x4")]:
            btn = Button(text=name, bold=True, font_size='16sp', background_normal='',
                background_color=get_color_from_hex("#66BB6A") if lvl == self._level else get_color_from_hex("#C8E6C9"),
                color=(1,1,1,1) if lvl == self._level else TEXT_COLOR)
            btn.bind(on_release=partial(self._set_level, lvl))
            self._level_btns[lvl] = btn
            level_box.add_widget(btn)
        controls_bar.add_widget(level_box)
        
        # Empty space right
        controls_bar.add_widget(Label(text="", size_hint_x=1))
        
        self.add_widget(controls_bar)

        # 3. Progress Bar (Stars)
        progress_wrap = BoxLayout(size_hint_y=None, height=50, spacing=10)
        self._progress_lbl = Label(text="Progress: ", font_size='24sp', color=TEXT_COLOR, bold=True, halign='center', markup=True)
        progress_wrap.add_widget(self._progress_lbl)
        self.add_widget(progress_wrap)

        # 4. Grid Area (Large interaction area)
        board_wrap = BoxLayout(padding=[10, 10])
        # Add a subtle background to the board
        with board_wrap.canvas.before:
            Color(1, 1, 1, 0.5)
            self._board_rect = RoundedRectangle(pos=board_wrap.pos, size=board_wrap.size, radius=[24])
        board_wrap.bind(pos=lambda w, *a: setattr(self._board_rect, 'pos', w.pos), size=lambda w, *a: setattr(self._board_rect, 'size', w.size))

        self._grid = GridLayout(spacing=20, padding=20) # 20px spacing
        board_wrap.add_widget(self._grid)
        self.add_widget(board_wrap)

        # 5. Friendly Feedback Label
        self._info_lbl = Label(text="", font_size='28sp', bold=True, color=TEXT_COLOR, size_hint_y=None, height=60, halign='center')
        self.add_widget(self._info_lbl)

    def _set_level(self, lvl, *args):
        self._level = lvl
        for k, btn in self._level_btns.items():
            btn.background_color = get_color_from_hex("#66BB6A") if k == lvl else get_color_from_hex("#C8E6C9")
            btn.color = (1,1,1,1) if k == lvl else TEXT_COLOR
        self._new_game()

    def _new_game(self):
        self._tiles_up   = []
        self._locked     = True # Lock during preview
        self._matches    = 0
        self._consecutive_misses = 0
        self._hinted_tile = None
        self._started    = False
        
        if self._level == 1:
            self._cols, self._rows = 3, 2
        elif self._level == 2:
            self._cols, self._rows = 4, 3
        else:
            self._cols, self._rows = 4, 4

        self._grid.cols = self._cols
        self._grid.rows = self._rows
        
        total = self._cols * self._rows
        self._num_pairs = total // 2
        
        self._update_progress()
        self._grid.clear_widgets()

        available = SHAPES[:]
        random.shuffle(available)
        chosen = available[:self._num_pairs]

        deck = chosen * 2
        random.shuffle(deck)

        self._all_tiles = []

        for shape, col in deck:
            tile = TileButton(shape_name=shape, shape_col=col)
            tile.bind(on_release=self._on_tile_press)
            self._grid.add_widget(tile)
            self._all_tiles.append(tile)

        self._info_lbl.text = "Get ready..."
        self._info_lbl.color = TEXT_COLOR
        
        # Preview Mode
        Clock.schedule_once(self._start_preview, 0.5)

    def _start_preview(self, dt):
        for t in self._all_tiles:
            t.flip_to_front()
        self._info_lbl.text = "Memorize the tiles!"
        Clock.schedule_once(self._end_preview, PREVIEW_DUR)

    def _end_preview(self, dt):
        for t in self._all_tiles:
            t.flip_to_back()
        self._locked = False
        self._info_lbl.text = "Can you find a match?"

    def _update_progress(self):
        # We can use standard star char which usually renders fine: ★ or ☆
        stars = "★ " * self._matches
        empty = "☆ " * (self._num_pairs - self._matches)
        
        # In case ★ or ☆ don't render, we can use simple dots: ● ○
        # But ★ is very standard in system unicode fonts on Windows compared to emojis.
        # Let's use simple shapes to be completely safe: [ X ] for empty, [ O ] for matched?
        # Actually ★ and ☆ should render perfectly on Arial/Roboto.
        self._progress_lbl.text = f"Progress: {stars}{empty}"

    def _on_tile_press(self, tile, *args):
        if self._locked: return
        if tile.revealed or tile in self._tiles_up: return

        tile.flip_to_front()
        self._tiles_up.append(tile)

        if getattr(self, '_hinted_tiles', None):
            for t in self._hinted_tiles:
                t.is_hint = False
                t._redraw()
            self._hinted_tiles = []

        if len(self._tiles_up) == 2:
            self._locked = True
            Clock.schedule_once(self._check_pair, FLIP_DUR + 0.1)

    def _check_pair(self, *args):
        t1, t2 = self._tiles_up

        if t1.shape_name == t2.shape_name:
            self._handle_match(t1, t2)
        else:
            self._consecutive_misses = getattr(self, '_consecutive_misses', 0) + 1
            t1.mark_wrong()
            t2.mark_wrong()
            self._info_lbl.text = random.choice(MISS_MSGS)
            self._info_lbl.color = get_color_from_hex("#E53935") # More visible red
            Clock.schedule_once(lambda dt: self._flip_back_and_hint(t1, t2), MATCH_DUR)

    def _flip_back_and_hint(self, t1, t2):
        self._flip_back(t1, t2)
        
        # Immediately display a hint if they've failed 3 times
        if getattr(self, '_consecutive_misses', 0) >= 3 and self._matches < self._num_pairs:
            # Find an unrevealed pair
            unrevealed = [t for t in self._all_tiles if not t.revealed]
            if len(unrevealed) >= 2:
                target_shape = unrevealed[0].shape_name
                pair = [t for t in unrevealed if t.shape_name == target_shape][:2]
                
                self._hinted_tiles = pair
                for t in pair:
                    t.is_hint = True
                    t._redraw()
                    pulse = (Animation(size_hint_x=1.05, size_hint_y=1.05, duration=0.4) +
                             Animation(size_hint_x=1.0,  size_hint_y=1.0,  duration=0.4))
                    pulse.start(t)

    def _handle_match(self, t1, t2):
        self._consecutive_misses = 0
        t1.mark_matched()
        t2.mark_matched()
        self._matches += 1
        self._info_lbl.text = random.choice(MATCH_MSGS)
        self._info_lbl.color = get_color_from_hex("#4CAF50") # Nice green indicator
        
        self._tiles_up = []
        self._locked   = False
        self._update_progress()

        if self._matches >= self._num_pairs:
            Clock.schedule_once(self._show_win, 0.8)

    def _flip_back(self, t1, t2, *args):
        t1.clear_wrong()
        t2.clear_wrong()
        t1.flip_to_back()
        t2.flip_to_back()
        self._tiles_up = []
        self._locked   = False
        self._info_lbl.text = "Keep going!"
        self._info_lbl.color = TEXT_COLOR

    def _show_win(self, *args):
        self._launch_confetti()

        content = BoxLayout(orientation='vertical', padding=30, spacing=20)
        content.add_widget(Label(text="You did it!", font_size='48sp', bold=True, color=TEXT_COLOR, size_hint_y=None, height=60))
        content.add_widget(Label(text="You matched them all!", font_size='28sp', color=TEXT_COLOR, size_hint_y=None, height=40))
        
        stars_row = BoxLayout(size_hint_y=None, height=80)
        stars_row.add_widget(Label(text="★ ★ ★", font_size='60sp', color=get_color_from_hex("#FBC02D")))
        content.add_widget(stars_row)

        btn_row = BoxLayout(spacing=20, size_hint_y=None, height=70)
        play_again = Button(text="Play Again", bold=True, font_size='24sp', background_normal='', background_color=get_color_from_hex("#66BB6A"), color=(1,1,1,1))
        
        home_btn = Button(text="< Home", bold=True, font_size='24sp', background_normal='', background_color=get_color_from_hex("#A5D6A7"), color=TEXT_COLOR)
        
        btn_row.add_widget(play_again)
        btn_row.add_widget(home_btn)
        content.add_widget(btn_row)

        popup = Popup(title='', content=content, size_hint=(None, None), size=(500, 400), separator_height=0, background_color=get_color_from_hex("#F1F8E9"))
        
        play_again.bind(on_release=lambda *a: (popup.dismiss(), self._new_game()))
        home_btn.bind(on_release=lambda *a: (popup.dismiss(), self._go_home(None)))
        
        popup.open()

    def _launch_confetti(self):
        from kivy.uix.widget import Widget
        confetti = Widget(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        self.add_widget(confetti)

        colors = [(1, 0.4, 0.4, 1), (1, 0.8, 0.2, 1), (0.4, 0.9, 0.5, 1), (0.4, 0.7, 1, 1), (0.9, 0.5, 1, 1), (1, 0.6, 0.2, 1)]
        for _ in range(CONFETTI_COUNT):
            x = random.uniform(0, self.width)
            y = self.height + random.uniform(0, 100)
            size = random.randint(15, 25)
            col = random.choice(colors)
            with confetti.canvas:
                Color(*col)
                p = Rectangle(pos=(x, y), size=(size, size))
            anim = Animation(pos=(x + random.uniform(-100, 100), -50), duration=random.uniform(2.0, 4.0), t='in_quad')
            anim.start(p)

        Clock.schedule_once(lambda *a: self.remove_widget(confetti), 4.5)

    def _go_home(self, *args):
        app = App.get_running_app()
        app.root.current = 'games'

class MemoryMatchScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        with self.canvas.before:
            Color(*BG_COLOR)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda w, *a: setattr(self.bg_rect, 'pos', w.pos), size=lambda w, *a: setattr(self.bg_rect, 'size', w.size))
        
        game = MemoryMatchGame()
        self.add_widget(game)

    def on_leave(self):
        self.clear_widgets()
