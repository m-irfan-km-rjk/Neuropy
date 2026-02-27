import random
from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Ellipse, RoundedRectangle, Line, Rectangle, Triangle, PushMatrix, PopMatrix, Translate, InstructionGroup
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.utils import get_color_from_hex
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import BooleanProperty

# Sensory-friendly pastel colors
COLORS = {
    "bg": get_color_from_hex("#F9FBFA"),
    "btn": get_color_from_hex("#D6EAF8"),
    "btn_border": get_color_from_hex("#AED6F1"),
    "text": get_color_from_hex("#2C3E50"),
    "bubble_base": get_color_from_hex("#E8DAEF"),
    "bubble_border": get_color_from_hex("#D2B4DE"),
    "bubble_correct": get_color_from_hex("#D5F5E3"),
    "feedback_correct": get_color_from_hex("#27AE60"),
    "feedback_wrong": get_color_from_hex("#E67E22")
}


# --- GAME DATA ---

STAGES = {
    "stage1": {
        "title": "Symbol Identification",
        "questions": [
            {"instruction": "Pop the RED ball", "correct": "🔴", "options": ["🔴", "🔵", "🟢", "🟡"]},
            {"instruction": "Pop the TRIANGLE", "correct": "▲", "options": ["▲", "●", "■", "▬"]},
            {"instruction": "Pop the BIG shape", "correct": "<big>●", "options": ["<big>●", "●", "■", "▲"]},
            {"instruction": "Pop the GREEN shape", "correct": "🟢", "options": ["🟢", "🟦", "🔺", "🟣"]},
            {"instruction": "Pop the STAR", "correct": "⭐", "options": ["⭐", "■", "●", "▲"]}
        ]
    },
    "stage2": {
        "title": "Letter Orientation",
        "questions": [
            {"instruction": "Pop the letter p", "correct": "p", "options": ["p", "q", "b", "d"]},
            {"instruction": "Pop the letter b", "correct": "b", "options": ["b", "d", "p", "q"]},
            {"instruction": "Pop the letter d", "correct": "d", "options": ["d", "b", "q", "p"]},
            {"instruction": "Pop number 6", "correct": "6", "options": ["6", "9", "8", "0"]},
            {"instruction": "Pop number 9", "correct": "9", "options": ["9", "6", "8", "0"]}
        ]
    },
    "stage3": {
        "title": "Emotion Recognition",
        "questions": [
            {"instruction": "Pop the HAPPY face", "correct": "😊", "options": ["😊", "😡", "😢", "😨"]},
            {"instruction": "Pop the ANGRY face", "correct": "😡", "options": ["😡", "😊", "😢", "😲"]},
            {"instruction": "Pop the SAD face", "correct": "😢", "options": ["😢", "😊", "😡", "😨"]},
            {"instruction": "Pop the SURPRISED face", "correct": "😲", "options": ["😲", "😊", "😡", "😢"]},
            {"instruction": "Pop the SCARED face", "correct": "😨", "options": ["😨", "😊", "😡", "😢"]}
        ]
    }
}


# --- UI COMPONENTS ---

class MenuButton(ButtonBehavior, BoxLayout):
    """Large, rounded soft colored button for Main Menu"""
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = 120
        self.padding = 20

        with self.canvas.before:
            Color(*COLORS["btn"])
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[20])
            Color(*COLORS["btn_border"])
            self.line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, 20), width=2)

        self.bind(pos=self._update_graphics, size=self._update_graphics)

        self.add_widget(Label(text=text, font_size='28sp', bold=True, color=COLORS["text"]))

    def _update_graphics(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.line.rounded_rectangle = (self.x, self.y, self.width, self.height, 20)

class Bubble(ButtonBehavior, Label):
    """Circular bubble widget that floats gently"""
    is_correct = BooleanProperty(False)
    
    def __init__(self, text, is_correct, **kwargs):
        super().__init__(**kwargs)
        self.raw_text = text
        self.text = ""
        self.is_correct = is_correct
        self.color = COLORS["text"]
        
        # Determine if it needs a larger font size
        if "<big>" in text:
            self.font_size = '90sp'
            text = text.replace("<big>", "")
        else:
            self.font_size = '40sp'
        
        # Load Windows Segoe UI Emoji font to ensure emoji support
        from kivy.core.text import LabelBase
        import os
        if os.path.exists("C:/Windows/Fonts/seguiemj.ttf"):
            self.font_name = "C:/Windows/Fonts/seguiemj.ttf"
            
        self.size_hint = (None, None)
        self.size = (160, 160)
        self.halign = 'center'
        self.valign = 'middle'
        self.disabled = False
        
        self.bg_color_inst = None
        
        with self.canvas.before:
            self.bg_color_inst = Color(*COLORS["bubble_base"])
            self.ellipse = Ellipse(pos=self.pos, size=self.size)
            Color(*COLORS["bubble_border"])
            self.line = Line(ellipse=(self.x, self.y, self.width, self.height), width=1.5)

        self.bind(pos=self._update_graphics, size=self._update_graphics)
        self.bind(size=self._update_text_size)
        
        # Determine if it's an image path
        if text.endswith(".png") or text.endswith(".jpg"):
            from kivy.uix.image import Image
            img = Image(source=text, pos_hint={'center_x': 0.5, 'center_y': 0.5}, size_hint=(0.7, 0.7))
            self.add_widget(img)
        else:
            self.text = text
            
    def _update_text_size(self, *args):
        self.text_size = (self.width - 20, self.height)

    def _update_graphics(self, *args):
        self.ellipse.pos = self.pos
        self.ellipse.size = self.size
        self.line.ellipse = (self.x, self.y, self.width, self.height)
        
    def set_correct_style(self):
        self.bg_color_inst.rgba = COLORS["bubble_correct"]

    def play_wrong_animation(self):
        """Gentle shake animation, sensory friendly"""
        anim = Animation(x=self.x - 10, duration=0.05) + \
               Animation(x=self.x + 10, duration=0.05) + \
               Animation(x=self.x, duration=0.05)
        anim.start(self)
        
    def play_float_animation(self):
        """Removed because 'y' animation fights 'pos_hint' updates and breaks clicks in FloatLayout."""
        pass


# --- SCREENS ---

class BubbleMainMenu(Screen):
    """Stage selection screen"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        with self.canvas.before:
            Color(*COLORS["bg"])
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        layout = BoxLayout(orientation='vertical', padding=40, spacing=30)
        
        # Header
        header = BoxLayout(size_hint_y=None, height=80, padding=[0, 0, 0, 20])
        back_btn = Button(text="< Home", size_hint_x=None, width=120, 
                          background_normal='', background_color=COLORS["btn_border"], 
                          color=COLORS["text"], bold=True, font_size='20sp')
        back_btn.bind(on_release=self._go_home)
        
        title = Label(text="Smart Bubble Pop", font_size='42sp', bold=True, color=COLORS["text"])
        
        header.add_widget(back_btn)
        header.add_widget(title)
        layout.add_widget(header)
        
        # Subtitle
        layout.add_widget(Label(text="Choose a practice stage:", font_size='24sp', color=COLORS["text"], size_hint_y=None, height=40))

        # Menu Options
        btn1 = MenuButton("1. Symbol Identification")
        btn1.bind(on_release=lambda x: self.load_stage("stage1"))
        
        btn2 = MenuButton("2. Letter Orientation")
        btn2.bind(on_release=lambda x: self.load_stage("stage2"))
        
        btn3 = MenuButton("3. Emotion Recognition")
        btn3.bind(on_release=lambda x: self.load_stage("stage3"))
        
        layout.add_widget(btn1)
        layout.add_widget(btn2)
        layout.add_widget(btn3)
        
        # Spacer
        layout.add_widget(Label())
        
        self.add_widget(layout)

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def load_stage(self, stage_id):
        app = App.get_running_app()
        if hasattr(app, 'bubble_game'):
            app.bubble_game.start_game(stage_id)
            self.manager.current = 'bubble_game'
            
    def _go_home(self, *args):
        app = App.get_running_app()
        app.root.current = 'games'

class BubbleGameStage(Screen):
    """Main gameplay screen displaying bubbles and validating answers"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        with self.canvas.before:
            Color(*COLORS["bg"])
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.main_layout = BoxLayout(orientation='vertical')
        
        # Top Header (Back btn, Progress, Score)
        self.header = BoxLayout(size_hint_y=None, height=70, padding=10)
        self.back_btn = Button(text="< Menu", size_hint_x=None, width=100, 
                          background_normal='', background_color=COLORS["btn_border"], 
                          color=COLORS["text"], bold=True, font_size='18sp')
        self.back_btn.bind(on_release=self.return_to_menu)
        
        self.progress_lbl = Label(font_size='20sp', color=COLORS["text"], bold=True)
        self.score_lbl = Label(text="Score: 0", font_size='20sp', color=COLORS["text"], bold=True, size_hint_x=None, width=120)
        
        self.header.add_widget(self.back_btn)
        self.header.add_widget(self.progress_lbl)
        self.header.add_widget(self.score_lbl)
        
        # Stage Title
        self.stage_title_lbl = Label(size_hint_y=None, height=50, font_size='28sp', color=COLORS["text"], bold=True)
        
        # Instruction
        self.instruction_lbl = Label(size_hint_y=None, height=80, font_size='32sp', color=COLORS["text"], bold=True)
        
        # Game Area (FloatLayout for random bubble placement)
        self.game_area = FloatLayout()
        
        # Feedback Label
        self.feedback_lbl = Label(size_hint_y=None, height=80, font_size='36sp', bold=True)
        
        self.main_layout.add_widget(self.header)
        self.main_layout.add_widget(self.stage_title_lbl)
        self.main_layout.add_widget(self.instruction_lbl)
        self.main_layout.add_widget(self.game_area)
        self.main_layout.add_widget(self.feedback_lbl)
        
        self.add_widget(self.main_layout)
        
        # State
        self.current_stage = None
        self.current_q_idx = 0
        self.score = 0
        self.bubbles = []
        self.is_processing = False

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def return_to_menu(self, *args):
        self.manager.current = 'bubble_menu'

    def start_game(self, stage_id):
        # Prevent crash if invalid state
        if stage_id not in STAGES:
            return
            
        self.current_stage = STAGES[stage_id]
        self.stage_title_lbl.text = f"Stage: {self.current_stage['title']}"
        self.current_q_idx = 0
        self.score = 0
        self.score_lbl.text = f"Score: {self.score}"
        self.feedback_lbl.text = ""
        self.load_question()

    def load_question(self):
        self.is_processing = False
        self.feedback_lbl.text = ""
        
        # Question index overflow protection
        if self.current_q_idx >= 5 or self.current_q_idx >= len(self.current_stage["questions"]):
            self.show_completion()
            return
            
        self.progress_lbl.text = f"Question {self.current_q_idx + 1} of 5"
        
        question = self.current_stage["questions"][self.current_q_idx]
        self.instruction_lbl.text = question["instruction"]
        
        # Safely remove old widgets
        try:
            self.game_area.clear_widgets()
        except:
            pass
            
        self.bubbles = []
        
        # Randomization safety (use copy)
        options = list(question["options"])
        random.shuffle(options)
        
        # Preset safe floating positions around center to avoid overlap 
        positions = [
            {'center_x': 0.3, 'center_y': 0.75},
            {'center_x': 0.7, 'center_y': 0.75},
            {'center_x': 0.3, 'center_y': 0.35},
            {'center_x': 0.7, 'center_y': 0.35}
        ]
        random.shuffle(positions)
        
        for i, opt in enumerate(options):
            is_correct = (opt == question["correct"])
            b = Bubble(text=opt, is_correct=is_correct)
            b.pos_hint = positions[i]
            b.bind(on_release=self.on_bubble_tap)
            self.game_area.add_widget(b)
            self.bubbles.append(b)
            
            # Start subtle float
            b.play_float_animation()

    def on_bubble_tap(self, instance):
        # 1. Protection against Rapid multiple taps or late taps
        if self.is_processing or instance.disabled:
            return
            
        if instance.is_correct:
            self.is_processing = True
            
            # Update Score
            self.score += 10
            self.score_lbl.text = f"Score: {self.score}"
            
            # Update UI gently
            instance.set_correct_style()
            self.feedback_lbl.text = "Good Job! ✔️"
            self.feedback_lbl.color = COLORS["feedback_correct"]
            
            # Disable all
            for b in self.bubbles:
                b.disabled = True
                
            # Auto advance
            self.current_q_idx += 1
            Clock.schedule_once(lambda dt: self.load_question(), 1.5)
            
        else:
            # Gentle feedback, no penalization
            instance.play_wrong_animation()
            self.feedback_lbl.text = "Try Again"
            self.feedback_lbl.color = COLORS["feedback_wrong"]


    def show_completion(self):
        try:
            self.game_area.clear_widgets()
        except:
            pass
            
        self.instruction_lbl.text = ""
        self.feedback_lbl.text = "Stage Complete 🎉"
        self.feedback_lbl.color = COLORS["text"]
        
        Clock.schedule_once(lambda dt: self.return_to_menu(), 2.5)


class SmartBubbleAppScreen(Screen):
    """Wrapper that acts as the entrypoint screen for the main app routing"""
    def on_enter(self):
        self.clear_widgets()
        # Reset color
        Window.clearcolor = (1, 1, 1, 1)
        
        sm = ScreenManager()
        
        menu_screen = BubbleMainMenu(name='bubble_menu')
        game_screen = BubbleGameStage(name='bubble_game')
        
        sm.add_widget(menu_screen)
        sm.add_widget(game_screen)
        
        App.get_running_app().bubble_game = game_screen
        
        self.add_widget(sm)


class BubbleAppWrapper(App):
    """Standalone launcher for testing"""
    def build(self):
        Window.clearcolor = (1, 1, 1, 1)
        sm = ScreenManager()
        menu = BubbleMainMenu(name='bubble_menu')
        game = BubbleGameStage(name='bubble_game')
        sm.add_widget(menu)
        sm.add_widget(game)
        self.bubble_game = game
        return sm

if __name__ == '__main__':
    BubbleAppWrapper().run()
