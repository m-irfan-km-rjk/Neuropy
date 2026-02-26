from pathlib import Path
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image as KivyImage
from kivy.properties import StringProperty, ObjectProperty
from kivy.graphics import Color
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
from kivy.app import App

from modules.camera import CameraCapture

class Confetti(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self.pos_hint = {'x': 0, 'y': 0}
        
    def start(self):
        import random
        from kivy.animation import Animation
        from kivy.graphics import Rectangle
        from kivy.core.window import Window
        
        colors = [(1, 0.4, 0.4, 1), (1, 0.8, 0.2, 1), (0.4, 0.9, 0.5, 1), 
                  (0.4, 0.7, 1, 1), (0.9, 0.5, 1, 1), (1, 0.6, 0.2, 1)]
                  
        for _ in range(50):
            x = random.uniform(0, Window.width)
            y = Window.height + random.uniform(0, 60)
            size = random.randint(10, 20)
            col = random.choice(colors)
            
            with self.canvas:
                Color(*col)
                p = Rectangle(pos=(x, y), size=(size, size))
                
            anim = Animation(
                pos=(x + random.uniform(-80, 80), -30),
                duration=random.uniform(1.4, 3.0),
                t='in_quad'
            )
            anim.start(p)

class EmotionCard(ButtonBehavior, BoxLayout):
    emotion_name = StringProperty()
    emotion_emoji = StringProperty()
    emotion_color = ObjectProperty()
    emotion_image = StringProperty()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = (200, 250)
        self.padding = 20
        self.spacing = 10
        with self.canvas.before:
            self.bg_color = Color(*self.emotion_color)
            from kivy.graphics import RoundedRectangle
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[15,])
        self.bind(pos=self.update_rect, size=self.update_rect)
        
        # Icon handling
        if self.emotion_image and Path(self.emotion_image).exists():
            icon_widget = KivyImage(source=self.emotion_image, size_hint_y=0.6)
        else:
            icon_widget = Label(text=self.emotion_emoji, font_size='80sp', size_hint_y=0.6)
            
        self.add_widget(icon_widget)
        self.add_widget(Label(text=self.emotion_name, font_size='24sp', bold=True, color=(1, 1, 1, 1), size_hint_y=0.4))
    
    def update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def on_release(self):
        app = App.get_running_app()
        practice_screen = app.root.get_screen('emotion_practice')
        practice_screen.set_target_emotion(self.emotion_name)
        app.root.current = 'emotion_practice'

class EmotionSelectionScreen(Screen):
    def on_enter(self):
        container = self.ids.emotion_cards_container
        container.clear_widgets()
        emotions_data = [
            ('Happy', '😊', get_color_from_hex("#FFD700"), "assets/emotions/happy.png"),
            ('Sad', '😢', get_color_from_hex("#4169E1"), "assets/emotions/sad.png"),
            ('Angry', '😠', get_color_from_hex("#DC143C"), "assets/emotions/angry.png"),
            ('Surprise', '😲', get_color_from_hex("#FF69B4"), "assets/emotions/surprise.png"),
            ('Fear', '😨', get_color_from_hex("#9370DB"), "assets/emotions/fear.png"),
            ('Neutral', '😐', get_color_from_hex("#808080"), "assets/emotions/neutral.png"),
        ]
        for name, emoji, color, img in emotions_data:
            container.add_widget(EmotionCard(emotion_name=name, emotion_emoji=emoji, emotion_color=color, emotion_image=img))

class EmotionPracticeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.camera = None
        self.emotion_update_event = None
        self.target_emotion = None
        self.success_shown = False
        
    def set_target_emotion(self, emotion):
        self.target_emotion = emotion
        self.success_shown = False
        
    def on_enter(self):
        if self.target_emotion:
            self.ids.target_emotion_label.text = f"Show me: {self.target_emotion}"
        self.ids.next_button.opacity = 0
        self.ids.next_button.disabled = True
        if self.camera is None:
            self.setup_camera()
        Clock.schedule_once(lambda dt: self.camera.start(), 0.5)
        self.emotion_update_event = Clock.schedule_interval(self.update_emotion, 0.2)
    
    def setup_camera(self):
        self.camera = CameraCapture(camera_index=0, fps=30)
        self.ids.camera_container.add_widget(self.camera)
    
    def update_emotion(self, dt):
        if not self.camera or not self.camera.is_running: return
        frame = self.camera.get_frame()
        if frame is None: return
        app = App.get_running_app()
        result = app.emotion_ai.predict(frame)
        self.provide_feedback(result)
    
    def provide_feedback(self, result):
        if not result['face_detected']:
            self.ids.feedback_label.text = "No face detected"
            return
        
        detected = result['emotion']
        if detected == self.target_emotion and result['confidence'] > 0.4:
            self.ids.feedback_label.text = f"Perfect! You showed {self.target_emotion}!"
            if not self.success_shown:
                self.success_shown = True
                self.show_confetti()
                self.ids.next_button.opacity = 1
                self.ids.next_button.disabled = False
        else:
            self.ids.feedback_label.text = f"Detected: {detected}"

    def show_confetti(self):
        c = Confetti()
        self.add_widget(c)
        c.start()
        Clock.schedule_once(lambda dt: self.remove_widget(c), 3)
    
    def go_back(self):
        self.camera.stop()
        if self.emotion_update_event: Clock.unschedule(self.emotion_update_event)
        App.get_running_app().root.current = 'games'
    
    def return_to_selection(self):
        self.go_back()
