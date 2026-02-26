import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import StringProperty, ObjectProperty, BooleanProperty
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle
from kivy.uix.image import Image as KivyImage
import random
from datetime import datetime, timedelta
import os
from pathlib import Path

# Import modules and models
from modules.emotion_ai import EmotionAI
from modules.camera import CameraCapture
from models import init_db, Event, AACCategory, AACButton

# Set window background color
Window.clearcolor = get_color_from_hex("#FDFCF0")

# --- Custom Widgets ---

class Confetti(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self.pos_hint = {'x': 0, 'y': 0}
        
    def start(self):
        for _ in range(50):
            self.add_particle()
            
    def add_particle(self):
        with self.canvas:
            color = Color(random.random(), random.random(), random.random(), 1)
            size = random.randint(10, 20)
            rect = Rectangle(pos=(random.randint(0, Window.width), Window.height), size=(size, size))
            
        anim_pos = Animation(pos=(rect.pos[0], 0), duration=random.uniform(1, 3), t='out_bounce')
        anim_alpha = Animation(a=0, duration=random.uniform(1, 3))
        
        def cleanup(*args):
            if rect in self.canvas.children:
                self.canvas.remove(rect)
            if color in self.canvas.children:
                self.canvas.remove(color)
            
        anim_pos.bind(on_complete=cleanup)
        anim_pos.start(rect)
        anim_alpha.start(color)

# --- Screens ---

class DashboardScreen(Screen):
    def on_enter(self):
        self.update_info()
        Clock.schedule_interval(self.update_time, 1)

    def on_leave(self):
        Clock.unschedule(self.update_time)

    def update_time(self, dt):
        now = datetime.now()
        self.ids.clock_label.text = now.strftime('%I:%M %p')
        self.ids.date_label.text = now.strftime('%A, %B %d')
        # Refresh now/next every minute
        if now.second == 0:
            self.update_now_next()

    def update_info(self):
        self.update_time(0)
        self.update_now_next()

    def update_now_next(self):
        app = App.get_running_app()
        now = datetime.now()
        
        current_event = app.db.query(Event).filter(Event.start_time <= now, Event.end_time >= now).first()
        next_event = app.db.query(Event).filter(Event.start_time > now).order_by(Event.start_time).first()

        self.set_icon_or_text(self.ids.now_icon, current_event.icon_path if current_event else '📍')
        self.ids.now_title.text = current_event.title if current_event else 'Free Time'

        self.set_icon_or_text(self.ids.next_icon, next_event.icon_path if next_event else '✅')
        self.ids.next_title.text = next_event.title if next_event else 'All Done!'

    def set_icon_or_text(self, parent_widget, icon_data):
        """Helper to set either an image or emoji text in a BoxLayout container"""
        parent_widget.clear_widgets()
        
        if not icon_data:
            icon_data = "📍"

        if icon_data.endswith('.png') or icon_data.endswith('.jpg'):
            img = KivyImage(source=icon_data, allow_stretch=True, keep_ratio=True)
            parent_widget.add_widget(img)
        else:
            lbl = Label(text=icon_data, font_size='80sp')
            parent_widget.add_widget(lbl)

class AACScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sentence = []
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)

    def on_enter(self):
        self.load_aac_data()

    def load_aac_data(self):
        app = App.get_running_app()
        categories = app.db.query(AACCategory).all()
        
        self.ids.category_list.clear_widgets()
        self.ids.aac_grid.clear_widgets()

        # Add "All" category
        all_btn = Button(text="All", size_hint_y=None, height=60, bold=True)
        all_btn.bind(on_release=lambda x: self.filter_buttons(None))
        self.ids.category_list.add_widget(all_btn)

        for cat in categories:
            btn = Button(text=cat.name, size_hint_y=None, height=60,
                        background_normal='', background_color=get_color_from_hex(cat.color or "#E0F7FA"),
                        color=[0,0,0,1], bold=True)
            btn.bind(on_release=lambda x, c=cat: self.filter_buttons(c.id))
            self.ids.category_list.add_widget(btn)

        self.filter_buttons(None)

    def filter_buttons(self, category_id):
        app = App.get_running_app()
        self.ids.aac_grid.clear_widgets()
        
        query = app.db.query(AACButton)
        if category_id:
            query = query.filter(AACButton.category_id == category_id)
        
        buttons = query.all()
        for btn_data in buttons:
            btn = Button(size_hint_y=None, height=180)
            btn.background_normal = ''
            btn.background_color = [1, 1, 1, 1]
            
            layout = BoxLayout(orientation='vertical', padding=10)
            
            # Icon handling
            if btn_data.image_path and (btn_data.image_path.endswith('.png') or btn_data.image_path.endswith('.jpg')):
                icon_widget = KivyImage(source=btn_data.image_path, size_hint_y=0.65)
            else:
                icon_widget = Label(text=btn_data.image_path or '🗣️',
                                    font_size='48sp', color=[0,0,0,1], size_hint_y=0.65)
            
            layout.add_widget(icon_widget)
            layout.add_widget(Label(text=btn_data.label, font_size='20sp', bold=True, color=[0,0,0,1], size_hint_y=0.3))
            
            btn.add_widget(layout)
            btn.bind(on_release=lambda x, b=btn_data: self.add_to_sentence(b))
            self.ids.aac_grid.add_widget(btn)

    def add_to_sentence(self, btn_data):
        self.sentence.append(btn_data)
        label = Label(text=btn_data.label, size_hint_x=None, width=110,
                      color=[0.2,0.2,0.2,1], bold=True)

        # Draw chip background, bound to label pos/size so it moves correctly
        with label.canvas.before:
            chip_color = Color(1, 0.95, 0.8, 1)
            chip_rect = RoundedRectangle(pos=label.pos, size=label.size, radius=[10,])

        def _update_chip(widget, *args, r=chip_rect):
            r.pos = widget.pos
            r.size = widget.size

        label.bind(pos=_update_chip, size=_update_chip)
        self.ids.sentence_display.add_widget(label)
        self.speak(btn_data.speech_text)

    def speak_sentence(self):
        if not self.sentence: return
        full_text = " ".join([b.speech_text for b in self.sentence])
        self.speak(full_text)

    def clear_sentence(self):
        self.sentence = []
        self.ids.sentence_display.clear_widgets()

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

class AdminScreen(Screen):
    def on_enter(self):
        self.load_admin_events()

    def load_admin_events(self):
        app = App.get_running_app()
        events = app.db.query(Event).order_by(Event.start_time).all()
        self.ids.admin_event_list.clear_widgets()

        for ev in events:
            row = BoxLayout(size_hint_y=None, height=80, padding=10, spacing=10)
            with row.canvas.before:
                Color(0.9, 0.9, 0.9, 1)
                Rectangle(pos=row.pos, size=row.size)
            
            # Icon handling
            if ev.icon_path and (ev.icon_path.endswith('.png') or ev.icon_path.endswith('.jpg')):
                icon_widget = KivyImage(source=ev.icon_path, size_hint_x=0.1)
            else:
                icon_widget = Label(text=ev.icon_path or '📅', font_size='30sp', size_hint_x=0.1, color=[0,0,0,1])
            
            row.add_widget(icon_widget)
            info = BoxLayout(orientation='vertical', size_hint_x=0.7)
            info.add_widget(Label(text=ev.title, bold=True, color=[0,0,0,1], halign='left', text_size=(300, 30)))
            info.add_widget(Label(text=f"{ev.start_time.strftime('%H:%M')} - {ev.end_time.strftime('%H:%M')}", 
                                color=[0.5,0.5,0.5,1], halign='left', text_size=(300, 30)))
            row.add_widget(info)
            
            del_btn = Button(text="Delete", size_hint_x=0.2, background_color=[1,0,0,1])
            del_btn.bind(on_release=lambda x, e=ev: self.delete_event(e))
            row.add_widget(del_btn)
            
            self.ids.admin_event_list.add_widget(row)

    def add_task(self):
        title = self.ids.task_title.text.strip()
        start = self.ids.start_hour.text.strip()
        end = self.ids.end_hour.text.strip()
        icon = self.ids.task_icon.text.strip()

        if not title or not start or not end:
            self._show_error("Please fill in title, start time, and end time.")
            return

        try:
            today = datetime.now().date()
            s_time = datetime.combine(today, datetime.strptime(start, '%H:%M').time())
            e_time = datetime.combine(today, datetime.strptime(end, '%H:%M').time())
            if e_time <= s_time:
                self._show_error("End time must be after start time.")
                return
            
            app = App.get_running_app()
            new_ev = Event(title=title, start_time=s_time, end_time=e_time,
                           icon_path=icon or '📅')
            app.db.add(new_ev)
            app.db.commit()
            
            self.ids.task_title.text = ""
            self.ids.start_hour.text = ""
            self.ids.end_hour.text = ""
            self.ids.task_icon.text = ""
            self.load_admin_events()
        except ValueError:
            self._show_error("Invalid time format. Use HH:MM (e.g. 08:30)")
        except Exception as e:
            self._show_error(f"Unexpected error: {e}")

    def _show_error(self, message):
        """Show a simple error popup to the user."""
        content = BoxLayout(orientation='vertical', padding=20, spacing=15)
        content.add_widget(Label(text=message, font_size='18sp', color=[0.2,0.2,0.2,1],
                                 halign='center', text_size=(350, None)))
        close_btn = Button(text="OK", size_hint_y=None, height=50,
                           background_normal='', background_color=get_color_from_hex("#7B1FA2"),
                           color=[1,1,1,1], bold=True)
        content.add_widget(close_btn)
        popup = Popup(title='⚠️ Oops!', content=content,
                      size_hint=(None, None), size=(400, 230),
                      title_color=[0.2,0.2,0.2,1])
        close_btn.bind(on_release=popup.dismiss)
        popup.open()

    def delete_event(self, event):
        app = App.get_running_app()
        app.db.delete(event)
        app.db.commit()
        self.load_admin_events()

class SchedulerScreen(Screen):
    def on_enter(self):
        self.load_timeline()

    def load_timeline(self):
        app = App.get_running_app()
        now = datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0)
        end_of_day = now.replace(hour=23, minute=59, second=59)

        events = app.db.query(Event).filter(
            Event.start_time >= start_of_day,
            Event.start_time <= end_of_day
        ).order_by(Event.start_time).all()

        self.ids.timeline_list.clear_widgets()

        for ev in events:
            is_past = ev.end_time < now
            is_current = ev.start_time <= now <= ev.end_time
            
            bg_hex = "#E8F5E9" if is_current else "#FFFFFF"
            card = BoxLayout(size_hint_y=None, height=120, padding=15, spacing=20)

            with card.canvas.before:
                bg_c = Color(*get_color_from_hex(bg_hex))
                bg_r = Rectangle(pos=card.pos, size=card.size)
                if is_current:
                    bdr_c = Color(*get_color_from_hex("#4CAF50"))
                    bdr_l = Line(rectangle=(card.x, card.y, card.width, card.height), width=2)

            # Bind canvas instructions to card position/size so they update on scroll
            if is_current:
                def _upd(w, *a, r=bg_r, l=bdr_l):
                    r.pos = w.pos; r.size = w.size
                    l.rectangle = (w.x, w.y, w.width, w.height)
            else:
                def _upd(w, *a, r=bg_r):
                    r.pos = w.pos; r.size = w.size
            card.bind(pos=_upd, size=_upd)

            card.opacity = 0.6 if is_past else 1.0
            
            time_box = BoxLayout(orientation='vertical', size_hint_x=0.2)
            time_box.add_widget(Label(text=ev.start_time.strftime('%I:%M'), bold=True, color=[0,0,0,1], font_size='20sp'))
            time_box.add_widget(Label(text=ev.start_time.strftime('%p'), color=[0.4,0.4,0.4,1], font_size='14sp'))
            card.add_widget(time_box)
            
            # Icon handling
            if ev.icon_path and (ev.icon_path.endswith('.png') or ev.icon_path.endswith('.jpg')):
                icon_widget = KivyImage(source=ev.icon_path, size_hint_x=0.2)
            else:
                icon_widget = Label(text=ev.icon_path or '📅', font_size='50sp', size_hint_x=0.2)
            card.add_widget(icon_widget)
            
            info = BoxLayout(orientation='vertical', size_hint_x=0.6)
            title_text = ev.title
            if is_current: title_text += " (NOW)"
            elif is_past: title_text += " (DONE)"
            
            info.add_widget(Label(text=title_text, bold=True, color=[0,0,0,1], font_size='24sp', halign='left', text_size=(400, 40)))
            info.add_widget(Label(text=f"Until {ev.end_time.strftime('%I:%M %p')}", color=[0.5,0.5,0.5,1], halign='left', text_size=(400, 30)))
            card.add_widget(info)
            
            self.ids.timeline_list.add_widget(card)

# --- Emotion Screens (Existing) ---

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
        App.get_running_app().root.current = 'emotion_selection'
    
    def return_to_selection(self):
        self.go_back()

class AutismLearningHubApp(App):
    def build(self):
        # Load the KV file
        Builder.load_file('layout.kv')

        # Database Initialization
        db_path = os.path.join(os.getcwd(), 'neuropi.db')
        self.db = init_db(db_path)
        self.seed_data()

        # Modules
        self.emotion_ai = EmotionAI()
        
        # UI
        sm = ScreenManager()
        sm.add_widget(DashboardScreen(name='dashboard'))
        sm.add_widget(AACScreen(name='aac'))
        sm.add_widget(SchedulerScreen(name='scheduler'))
        sm.add_widget(AdminScreen(name='admin'))
        sm.add_widget(EmotionSelectionScreen(name='emotion_selection'))
        sm.add_widget(EmotionPracticeScreen(name='emotion_practice'))
        
        return sm

    def seed_data(self):
        # Seed AAC Categories and Buttons if empty
        if not self.db.query(AACCategory).first():
            cat_needs = AACCategory(name='Needs', color='#FFCDD2')
            cat_food = AACCategory(name='Food', color='#C8E6C9')
            cat_feelings = AACCategory(name='Feelings', color='#BBDEFB')
            self.db.add_all([cat_needs, cat_food, cat_feelings])
            self.db.commit()

            buttons = [
                AACButton(label='Hungry', speech_text='I am hungry', image_path='🍔', category=cat_needs),
                AACButton(label='Thirsty', speech_text='I am thirsty', image_path='🥤', category=cat_needs),
                AACButton(label='Toast', speech_text='I want toast', image_path='assets/icons/toast.png', category=cat_food),
                AACButton(label='Apple', speech_text='Apple', image_path='�', category=cat_food),
                AACButton(label='Happy', speech_text='I feel happy', image_path='assets/emotions/happy.png', category=cat_feelings),
                AACButton(label='Sad', speech_text='I feel sad', image_path='assets/emotions/sad.png', category=cat_feelings),
            ]
            self.db.add_all(buttons)
            self.db.commit()

        # Seed some Events if empty
        if not self.db.query(Event).first():
            today = datetime.now().replace(hour=0, minute=0, second=0)
            events = [
                Event(title="Breakfast", start_time=today.replace(hour=8, minute=0), 
                      end_time=today.replace(hour=8, minute=30), icon_path="assets/icons/toast.png"),
                Event(title="School Bus", start_time=today.replace(hour=8, minute=30), 
                      end_time=today.replace(hour=9, minute=0), icon_path="assets/icons/bus.png"),
                Event(title="Brushing Teeth", start_time=today.replace(hour=20, minute=0), 
                      end_time=today.replace(hour=20, minute=15), icon_path="assets/icons/toothbrush.png"),
            ]
            self.db.add_all(events)
            self.db.commit()

if __name__ == '__main__':
    AutismLearningHubApp().run()
