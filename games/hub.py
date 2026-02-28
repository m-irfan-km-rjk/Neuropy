from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle, Line, Rectangle
from kivy.utils import get_color_from_hex
from kivy.app import App

class GamesHubScreen(Screen):
    """
    Landing screen that shows available games.
    """

    def on_enter(self):
        self._build()

    def _build(self):
        self.clear_widgets()
        root = BoxLayout(orientation='vertical', padding=30, spacing=20)

        # Background
        with self.canvas.before:
            Color(*get_color_from_hex("#E8F5E9"))
            bg_rect = Rectangle(pos=self.pos, size=self.size)
        
        def _upd_bg(w, *a):
            bg_rect.pos = w.pos
            bg_rect.size = w.size
            
        self.bind(pos=_upd_bg, size=_upd_bg)

        # Header
        header = BoxLayout(size_hint_y=None, height=70, spacing=14)
        back_btn = Button(
            text="🏠 Home", size_hint_x=None, width=130,
            background_normal='', background_color=get_color_from_hex("#A5D6A7"),
            color=(1,1,1,1), bold=True, font_size='17sp'
        )
        back_btn.bind(on_release=lambda *a: setattr(App.get_running_app().root, 'current', 'dashboard'))
        header.add_widget(back_btn)
        header.add_widget(Label(
            text="🎮  Games", font_size='34sp', bold=True,
            color=get_color_from_hex("#2E7D32")
        ))
        root.add_widget(header)

        root.add_widget(Label(
            text="Choose an activity!",
            font_size='20sp', color=get_color_from_hex("#555555"),
            size_hint_y=None, height=36
        ))

        # Game cards grid
        grid = GridLayout(cols=2, spacing=24, padding=10, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        # Emotion Practice card
        em_card = self._make_game_card(
            icon="😊",
            title="Emotion Practice",
            desc="Practice your expressions",
            bg_hex="#E6F2FF",
            border_hex="#AEC6CF",
        )
        em_card.bind(on_release=lambda *a: setattr(App.get_running_app().root, 'current', 'emotion_selection'))
        grid.add_widget(em_card)

        # Memory Match card
        mm_card = self._make_game_card(
            icon="🃏",
            title="Memory Match",
            desc="Flip tiles & find pairs",
            bg_hex="#DCEDC8",
            border_hex="#8BC34A",
        )
        mm_card.bind(on_release=lambda *a: setattr(App.get_running_app().root, 'current', 'memory_match'))
        grid.add_widget(mm_card)

        # Routine Builder card
        rb_card = self._make_game_card(
            icon="📅",
            title="Routine Builder",
            desc="Practice daily steps",
            bg_hex="#FFF9C4",
            border_hex="#FFF176",
        )
        rb_card.bind(on_release=lambda *a: setattr(App.get_running_app().root, 'current', 'routine_builder'))
        grid.add_widget(rb_card)

        # Smart Bubble Pop card
        sb_card = self._make_game_card(
            icon="🫧",
            title="Smart Bubble Pop",
            desc="Pop the right symbols",
            bg_hex="#E8DAEF",
            border_hex="#D2B4DE",
        )
        sb_card.bind(on_release=lambda *a: setattr(App.get_running_app().root, 'current', 'smart_bubble_pop'))
        grid.add_widget(sb_card)

        # Visual Real-Life card
        vrl_card = self._make_game_card(
            icon="🌍",
            title="Visual Real-Life",
            desc="Practice real-world skills",
            bg_hex="#E3F2FD",
            border_hex="#90CAF9",
        )
        vrl_card.bind(on_release=lambda *a: setattr(App.get_running_app().root, 'current', 'visual_real_life'))
        grid.add_widget(vrl_card)

        root.add_widget(grid)
        self.add_widget(root)

    def _make_game_card(self, icon, title, desc, bg_hex, border_hex):
        class ButtonBehaviorBox(ButtonBehavior, BoxLayout): pass
        
        card = ButtonBehaviorBox(
            orientation='vertical', padding=20, spacing=10,
            size_hint_y=None, height=200
        )
        with card.canvas.before:
            Color(*get_color_from_hex(bg_hex))
            rr = RoundedRectangle(pos=card.pos, size=card.size, radius=[22])
            Color(*get_color_from_hex(border_hex))
            brd = Line(rounded_rectangle=(card.x, card.y, card.width, card.height, 22), width=2.5)
        def _upd(w, *a):
            rr.pos  = w.pos;  rr.size = w.size
            brd.rounded_rectangle = (w.x, w.y, w.width, w.height, 22)
        card.bind(pos=_upd, size=_upd)

        card.add_widget(Label(text=icon,  font_size='54sp', size_hint_y=0.5))
        card.add_widget(Label(text=title, font_size='20sp', bold=True,
                              color=get_color_from_hex("#2E7D32"), size_hint_y=0.25))
        card.add_widget(Label(text=desc,  font_size='14sp',
                              color=get_color_from_hex("#555555"), size_hint_y=0.25))
        return card
