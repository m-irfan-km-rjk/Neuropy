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
import win32com.client

# Import modules and models
from modules.emotion_ai import EmotionAI
from models import init_db, Event, AACCategory, AACButton
from games import GamesHubScreen, EmotionSelectionScreen, EmotionPracticeScreen, MemoryMatchScreen, RoutineGameScreen, SmartBubbleAppScreen

# Set window background color
Window.clearcolor = get_color_from_hex("#FDFCF0")

# --- Custom Widgets ---

from kivy.uix.widget import Widget
from kivy.graphics import Ellipse, Triangle, Quad

def _get_emoji_font():
    """Helper to get the path to a font that supports emojis on Windows, or default."""
    import os
    if os.path.exists("C:/Windows/Fonts/seguiemj.ttf"):
        return "C:/Windows/Fonts/seguiemj.ttf"
    elif os.path.exists("C:/Windows/Fonts/seguihis.ttf"):
        return "C:/Windows/Fonts/seguihis.ttf" 
    return "Roboto" # Fallback

def _create_emoji_label(text, font_size, **kwargs):
    lbl = Label(text=text, font_size=font_size, font_name=_get_emoji_font(), **kwargs)
    return lbl
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

        if icon_data.endswith('.png') or icon_data.endswith('.jpg') or icon_data.endswith('.jpeg'):
            img = KivyImage(source=icon_data, allow_stretch=True, keep_ratio=True)
            parent_widget.add_widget(img)
        else:
            icon_widget = _create_emoji_label(icon_data, font_size='80sp')
            parent_widget.add_widget(icon_widget)

class AACScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sentence = []
        try:
            self.speaker = win32com.client.Dispatch("SAPI.SpVoice")
        except Exception as e:
            print(f"Failed to load SAPI: {e}")
            self.speaker = None

    def on_enter(self):
        self.load_aac_data()

    def load_aac_data(self):
        app = App.get_running_app()
        categories = app.db.query(AACCategory).all()
        
        self.ids.category_list.clear_widgets()
        self.ids.aac_grid.clear_widgets()

        # Add "All" category at top
        all_btn = Button(text="All", size_hint_y=None, height=70, font_size='22sp', bold=True)
        all_btn.background_normal = ''
        all_btn.background_color = [0, 0, 0, 0]
        # Draw soft rounded bg
        with all_btn.canvas.before:
            Color(*get_color_from_hex("#FFFFFF"))
            rc1 = RoundedRectangle(pos=all_btn.pos, size=all_btn.size, radius=[15,])
            Color(*get_color_from_hex("#B0BEC5"))
            ln1 = Line(rounded_rectangle=(all_btn.x, all_btn.y, all_btn.width, all_btn.height, 15), width=1)
        all_btn.bind(pos=lambda w, *a: setattr(rc1, 'pos', w.pos) or setattr(ln1, 'rounded_rectangle', (w.x, w.y, w.width, w.height, 15)),
                     size=lambda w, *a: setattr(rc1, 'size', w.size) or setattr(ln1, 'rounded_rectangle', (w.x, w.y, w.width, w.height, 15)))
        all_btn.color = get_color_from_hex("#455A64")
        all_btn.bind(on_release=lambda x: self.filter_buttons(None))
        self.ids.category_list.add_widget(all_btn)

        for cat in categories:
            btn = Button(
                text=cat.name,
                font_name=_get_emoji_font(),
                size_hint_y=None, height=70, font_size='22sp', bold=True)
            btn.background_normal = ''
            btn.background_color = [0, 0, 0, 0]
            with btn.canvas.before:
                Color(*get_color_from_hex(cat.color or "#E0F7FA"))
                rc2 = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[15,])
                Color(0, 0, 0, 0.1)
                ln2 = Line(rounded_rectangle=(btn.x, btn.y, btn.width, btn.height, 15), width=1)
            btn.bind(pos=lambda w, *a, r=rc2, l=ln2: setattr(r, 'pos', w.pos) or setattr(l, 'rounded_rectangle', (w.x, w.y, w.width, w.height, 15)),
                     size=lambda w, *a, r=rc2, l=ln2: setattr(r, 'size', w.size) or setattr(l, 'rounded_rectangle', (w.x, w.y, w.width, w.height, 15)))
            btn.color = get_color_from_hex("#333333")
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
            # We use ButtonBehavior with a clean BoxLayout for perfect alignment
            class AACGridItem(ButtonBehavior, BoxLayout): pass
            
            box = AACGridItem(orientation='vertical', padding=[15, 20, 15, 10], spacing=10, size_hint_y=None, height=190)
            with box.canvas.before:
                # Slight drop shadow via offset faint rects
                Color(0.85, 0.88, 0.9, 0.8)
                sh1 = RoundedRectangle(pos=(box.x + 2, box.y - 2), size=box.size, radius=[20,])
                Color(1, 1, 1, 1)
                bg1 = RoundedRectangle(pos=box.pos, size=box.size, radius=[20,])
                Color(0.9, 0.9, 0.9, 1)
                bdr = Line(rounded_rectangle=(box.x, box.y, box.width, box.height, 20), width=1.2)
                
            def upd_box(w, _pos, s1=sh1, b1=bg1, l1=bdr):
                s1.pos = (w.x + 2, w.y - 2); s1.size = w.size
                b1.pos = w.pos; b1.size = w.size
                l1.rounded_rectangle = (w.x, w.y, w.width, w.height, 20)
            box.bind(pos=upd_box, size=upd_box)
            
            # Icon handling
            if btn_data.image_path and (btn_data.image_path.endswith('.png') or btn_data.image_path.endswith('.jpg')):
                icon_widget = KivyImage(source=btn_data.image_path, size_hint_y=0.7)
            else:
                icon_widget = Label(text=btn_data.image_path or '🗣️',
                                    font_size='56sp', color=[0,0,0,1], size_hint_y=0.7, font_name=_get_emoji_font())
            
            box.add_widget(icon_widget)
            box.add_widget(Label(text=btn_data.label, font_size='22sp', bold=True, color=get_color_from_hex("#333333"), size_hint_y=0.3))
            
            box.bind(on_release=lambda x, b=btn_data: self.add_to_sentence(b))
            self.ids.aac_grid.add_widget(box)

    def add_to_sentence(self, btn_data):
        self.sentence.append(btn_data)
        label = Label(text=btn_data.label, size_hint_x=None, width=130, font_size='20sp',
                      color=get_color_from_hex("#1565C0"), bold=True)

        # Draw chip premium background
        with label.canvas.before:
            Color(*get_color_from_hex("#E3F2FD"))
            chip_rect = RoundedRectangle(pos=label.pos, size=label.size, radius=[18,])
            Color(*get_color_from_hex("#64B5F6"))
            chip_line = Line(rounded_rectangle=(label.x, label.y, label.width, label.height, 18), width=1.5)

        def _update_chip(widget, *args, r=chip_rect, l=chip_line):
            r.pos = widget.pos
            r.size = widget.size
            l.rounded_rectangle = (widget.x, widget.y, widget.width, widget.height, 18)

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
        if hasattr(self, 'speaker') and self.speaker:
            try:
                # 1 = SVSFlagsAsync (Plays speech without freezing application)
                self.speaker.Speak(text, 1)
            except Exception as e:
                print(f"TTS error: {e}")

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
                icon_widget = _create_emoji_label(ev.icon_path or '📅', font_size='40sp', size_hint_x=0.1, color=[0,0,0,1])
            
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

        if not title or not start or not end or not icon:
            self._show_error("Please fill in title, start time, end time, and an icon/emoji.")
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
                icon_widget = _create_emoji_label(ev.icon_path or '📅', font_size='50sp', size_hint_x=0.2, color=[0,0,0,1])
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
        sm.add_widget(GamesHubScreen(name='games'))
        sm.add_widget(MemoryMatchScreen(name='memory_match'))
        sm.add_widget(RoutineGameScreen(name='routine_builder'))
        sm.add_widget(SmartBubbleAppScreen(name='smart_bubble_pop'))
        
        return sm

    def seed_data(self):
        # ---------------------------------------------------------------
        # AAC CATEGORIES & BUTTONS
        # Reseed if the DB is empty OR if it only has the old minimal data
        # (fewer than 10 buttons means it's the old 6-button seed).
        # ---------------------------------------------------------------
        existing_btn_count = self.db.query(AACButton).count()
        if existing_btn_count < 10:
            # Wipe old sparse data so we can insert the full vocabulary
            self.db.query(AACButton).delete()
            self.db.query(AACCategory).delete()
            self.db.commit()

            # ── 1. Needs & Requests ──────────────────────────────────────
            cat_needs = AACCategory(name='Needs', color='#FFCDD2')
            # ── 2. Food & Drinks ─────────────────────────────────────────
            cat_food = AACCategory(name='Food & Drinks', color='#C8E6C9')
            # ── 3. Feelings ───────────────────────────────────────────────
            cat_feelings = AACCategory(name='Feelings', color='#BBDEFB')
            # ── 4. People ─────────────────────────────────────────────────
            cat_people = AACCategory(name='People', color='#E1BEE7')
            # ── 5. Places ─────────────────────────────────────────────────
            cat_places = AACCategory(name='Places', color='#B2EBF2')
            # ── 6. Actions ────────────────────────────────────────────────
            cat_actions = AACCategory(name='Actions', color='#DCEDC8')
            # ── 7. Body ───────────────────────────────────────────────────
            cat_body = AACCategory(name='Body', color='#FFE0B2')
            # ── 8. Questions ──────────────────────────────────────────────
            cat_questions = AACCategory(name='Questions', color='#F8BBD0')
            # ── 9. Responses ──────────────────────────────────────────────
            cat_responses = AACCategory(name='Responses', color='#FFF9C4')
            # ── 10. School ───────────────────────────────────────────────
            cat_school = AACCategory(name='School', color='#CFD8DC')
            # ── 11. Health & Self-Care ────────────────────────────────────
            cat_health = AACCategory(name='Health', color='#D7CCC8')
            # ── 12. Quick Phrases ─────────────────────────────────────────
            cat_phrases = AACCategory(name='Quick Phrases', color='#FFCCBC')

            self.db.add_all([
                cat_needs, cat_food, cat_feelings, cat_people, cat_places,
                cat_actions, cat_body, cat_questions, cat_responses,
                cat_school, cat_health, cat_phrases
            ])
            self.db.commit()

            buttons = [
                # ── Needs & Requests ──────────────────────────────────────
                AACButton(label='Hungry',    speech_text='I am hungry',          image_path='🍔', category=cat_needs),
                AACButton(label='Thirsty',   speech_text='I am thirsty',         image_path='🥤', category=cat_needs),
                AACButton(label='Tired',     speech_text='I am tired',           image_path='😴', category=cat_needs),
                AACButton(label='Toilet',    speech_text='I need to use the toilet', image_path='🚽', category=cat_needs),
                AACButton(label='Help',      speech_text='I need help',          image_path='🙋', category=cat_needs),
                AACButton(label='More',      speech_text='I want more',          image_path='➕', category=cat_needs),
                AACButton(label='Stop',      speech_text='Please stop',          image_path='🛑', category=cat_needs),
                AACButton(label='Go Away',   speech_text='Please go away',       image_path='👋', category=cat_needs),
                AACButton(label='Pain',      speech_text='I am in pain',         image_path='😣', category=cat_needs),
                AACButton(label='Cold',      speech_text='I am cold',            image_path='🥶', category=cat_needs),
                AACButton(label='Hot',       speech_text='I am hot',             image_path='🥵', category=cat_needs),
                AACButton(label='Quiet',     speech_text='Please be quiet',      image_path='🤫', category=cat_needs),

                # ── Food & Drinks ─────────────────────────────────────────
                AACButton(label='Water',     speech_text='I want water',         image_path='💧', category=cat_food),
                AACButton(label='Milk',      speech_text='I want milk',          image_path='🥛', category=cat_food),
                AACButton(label='Juice',     speech_text='I want juice',         image_path='🧃', category=cat_food),
                AACButton(label='Apple',     speech_text='I want an apple',      image_path='🍎', category=cat_food),
                AACButton(label='Banana',    speech_text='I want a banana',      image_path='🍌', category=cat_food),
                AACButton(label='Bread',     speech_text='I want bread',         image_path='🍞', category=cat_food),
                AACButton(label='Toast',     speech_text='I want toast',         image_path='assets/icons/toast.png', category=cat_food),
                AACButton(label='Rice',      speech_text='I want rice',          image_path='🍚', category=cat_food),
                AACButton(label='Cookie',    speech_text='I want a cookie',      image_path='🍪', category=cat_food),
                AACButton(label='Pizza',     speech_text='I want pizza',         image_path='🍕', category=cat_food),
                AACButton(label='Eggs',      speech_text='I want eggs',          image_path='🥚', category=cat_food),
                AACButton(label='Chicken',   speech_text='I want chicken',       image_path='🍗', category=cat_food),
                AACButton(label='Noodles',   speech_text='I want noodles',       image_path='🍜', category=cat_food),
                AACButton(label='Ice Cream', speech_text='I want ice cream',     image_path='🍦', category=cat_food),
                AACButton(label='Cereal',    speech_text='I want cereal',        image_path='🥣', category=cat_food),
                AACButton(label='Sandwich',  speech_text='I want a sandwich',    image_path='🥪', category=cat_food),

                # ── Feelings ──────────────────────────────────────────────
                AACButton(label='Happy',     speech_text='I feel happy',         image_path='assets/emotions/happy.png',   category=cat_feelings),
                AACButton(label='Sad',       speech_text='I feel sad',           image_path='assets/emotions/sad.png',     category=cat_feelings),
                AACButton(label='Angry',     speech_text='I feel angry',         image_path='assets/emotions/angry.png',   category=cat_feelings),
                AACButton(label='Scared',    speech_text='I feel scared',        image_path='assets/emotions/fear.png',    category=cat_feelings),
                AACButton(label='Surprised', speech_text='I feel surprised',     image_path='assets/emotions/surprise.png',category=cat_feelings),
                AACButton(label='Disgusted', speech_text='I feel disgusted',     image_path='assets/emotions/disgust.png', category=cat_feelings),
                AACButton(label='Calm',      speech_text='I feel calm',          image_path='😌', category=cat_feelings),
                AACButton(label='Excited',   speech_text='I feel excited',       image_path='🤩', category=cat_feelings),
                AACButton(label='Bored',     speech_text='I feel bored',         image_path='😑', category=cat_feelings),
                AACButton(label='Confused',  speech_text='I feel confused',      image_path='😕', category=cat_feelings),
                AACButton(label='Nervous',   speech_text='I feel nervous',       image_path='😰', category=cat_feelings),
                AACButton(label='Proud',     speech_text='I feel proud',         image_path='😊', category=cat_feelings),

                # ── People ────────────────────────────────────────────────
                AACButton(label='Mum',       speech_text='Mum',                  image_path='👩', category=cat_people),
                AACButton(label='Dad',       speech_text='Dad',                  image_path='👨', category=cat_people),
                AACButton(label='Teacher',   speech_text='Teacher',              image_path='🧑‍🏫', category=cat_people),
                AACButton(label='Doctor',    speech_text='Doctor',               image_path='🧑‍⚕️', category=cat_people),
                AACButton(label='Friend',    speech_text='My friend',            image_path='🧑', category=cat_people),
                AACButton(label='Baby',      speech_text='Baby',                 image_path='👶', category=cat_people),
                AACButton(label='Me',        speech_text='Me',                   image_path='🙋', category=cat_people),
                AACButton(label='You',       speech_text='You',                  image_path='👉', category=cat_people),
                AACButton(label='Sister',    speech_text='My sister',            image_path='👧', category=cat_people),
                AACButton(label='Brother',   speech_text='My brother',           image_path='👦', category=cat_people),
                AACButton(label='Grandma',   speech_text='Grandma',              image_path='👵', category=cat_people),
                AACButton(label='Grandpa',   speech_text='Grandpa',              image_path='👴', category=cat_people),

                # ── Places ────────────────────────────────────────────────
                AACButton(label='Home',      speech_text='I want to go home',    image_path='🏠', category=cat_places),
                AACButton(label='School',    speech_text='School',               image_path='🏫', category=cat_places),
                AACButton(label='Hospital',  speech_text='Hospital',             image_path='🏥', category=cat_places),
                AACButton(label='Park',      speech_text='I want to go to the park', image_path='🌳', category=cat_places),
                AACButton(label='Toilet',    speech_text='The toilet',           image_path='🚽', category=cat_places),
                AACButton(label='Bedroom',   speech_text='My bedroom',           image_path='🛏️', category=cat_places),
                AACButton(label='Kitchen',   speech_text='The kitchen',          image_path='🍳', category=cat_places),
                AACButton(label='Car',       speech_text='The car',              image_path='🚗', category=cat_places),
                AACButton(label='Store',     speech_text='The store',            image_path='🛒', category=cat_places),
                AACButton(label='Playground',speech_text='The playground',       image_path='🎡', category=cat_places),

                # ── Actions ───────────────────────────────────────────────
                AACButton(label='Eat',       speech_text='I want to eat',        image_path='🍽️', category=cat_actions),
                AACButton(label='Drink',     speech_text='I want to drink',      image_path='🥤', category=cat_actions),
                AACButton(label='Sleep',     speech_text='I want to sleep',      image_path='😴', category=cat_actions),
                AACButton(label='Play',      speech_text='I want to play',       image_path='🎮', category=cat_actions),
                AACButton(label='Read',      speech_text='I want to read',       image_path='📖', category=cat_actions),
                AACButton(label='Watch TV',  speech_text='I want to watch TV',   image_path='📺', category=cat_actions),
                AACButton(label='Walk',      speech_text='I want to walk',       image_path='🚶', category=cat_actions),
                AACButton(label='Sit',       speech_text='I want to sit down',   image_path='🪑', category=cat_actions),
                AACButton(label='Stand',     speech_text='I want to stand up',   image_path='🧍', category=cat_actions),
                AACButton(label='Wash',      speech_text='I want to wash',       image_path='🚿', category=cat_actions),
                AACButton(label='Draw',      speech_text='I want to draw',       image_path='✏️', category=cat_actions),
                AACButton(label='Dance',     speech_text='I want to dance',      image_path='💃', category=cat_actions),
                AACButton(label='Sing',      speech_text='I want to sing',       image_path='🎵', category=cat_actions),
                AACButton(label='Go Out',    speech_text='I want to go outside', image_path='🌤️', category=cat_actions),

                # ── Body ──────────────────────────────────────────────────
                AACButton(label='Head',      speech_text='My head hurts',        image_path='🤕', category=cat_body),
                AACButton(label='Tummy',     speech_text='My tummy hurts',       image_path='🤢', category=cat_body),
                AACButton(label='Arm',       speech_text='My arm hurts',         image_path='💪', category=cat_body),
                AACButton(label='Leg',       speech_text='My leg hurts',         image_path='🦵', category=cat_body),
                AACButton(label='Mouth',     speech_text='My mouth hurts',       image_path='👄', category=cat_body),
                AACButton(label='Eyes',      speech_text='My eyes hurt',         image_path='👁️', category=cat_body),
                AACButton(label='Ear',       speech_text='My ear hurts',         image_path='👂', category=cat_body),
                AACButton(label='Hand',      speech_text='My hand hurts',        image_path='✋', category=cat_body),
                AACButton(label='Foot',      speech_text='My foot hurts',        image_path='🦶', category=cat_body),
                AACButton(label='Hurts',     speech_text='It hurts here',        image_path='🩹', category=cat_body),

                # ── Questions ─────────────────────────────────────────────
                AACButton(label='What?',     speech_text='What is that?',        image_path='❓', category=cat_questions),
                AACButton(label='Where?',    speech_text='Where are we going?',  image_path='🗺️', category=cat_questions),
                AACButton(label='Who?',      speech_text='Who is that?',         image_path='🧐', category=cat_questions),
                AACButton(label='When?',     speech_text='When is it?',          image_path='⏰', category=cat_questions),
                AACButton(label='Why?',      speech_text='Why?',                 image_path='🤔', category=cat_questions),
                AACButton(label='How?',      speech_text='How do I do this?',    image_path='💡', category=cat_questions),
                AACButton(label='Can I?',    speech_text='Can I have a turn?',   image_path='🙏', category=cat_questions),
                AACButton(label='What next?',speech_text='What do I do next?',   image_path='➡️', category=cat_questions),

                # ── Responses ─────────────────────────────────────────────
                AACButton(label='Yes',       speech_text='Yes',                  image_path='✅', category=cat_responses),
                AACButton(label='No',        speech_text='No',                   image_path='❌', category=cat_responses),
                AACButton(label='Maybe',     speech_text='Maybe',                image_path='🤷', category=cat_responses),
                AACButton(label='I don\'t know', speech_text='I do not know',    image_path='😶', category=cat_responses),
                AACButton(label='Please',    speech_text='Please',               image_path='🙏', category=cat_responses),
                AACButton(label='Thank You', speech_text='Thank you',            image_path='😊', category=cat_responses),
                AACButton(label='Sorry',     speech_text='I am sorry',           image_path='😔', category=cat_responses),
                AACButton(label='OK',        speech_text='OK',                   image_path='👍', category=cat_responses),
                AACButton(label='Finished',  speech_text='I am finished',        image_path='🏁', category=cat_responses),
                AACButton(label='Again',     speech_text='Can we do it again?',  image_path='🔄', category=cat_responses),

                # ── School ────────────────────────────────────────────────
                AACButton(label='Book',      speech_text='I want the book',      image_path='📚', category=cat_school),
                AACButton(label='Pencil',    speech_text='I need a pencil',      image_path='✏️', category=cat_school),
                AACButton(label='Drawing',   speech_text='I want to draw',       image_path='🎨', category=cat_school),
                AACButton(label='Counting',  speech_text='Let us count',         image_path='🔢', category=cat_school),
                AACButton(label='Spelling',  speech_text='Let us do spelling',   image_path='🔤', category=cat_school),
                AACButton(label='Break',     speech_text='I need a break',       image_path='☕', category=cat_school),
                AACButton(label='Circle Time',speech_text='It is circle time',   image_path='⭕', category=cat_school),
                AACButton(label='Computer',  speech_text='I want to use the computer', image_path='💻', category=cat_school),
                AACButton(label='Art',       speech_text='I want to do art',     image_path='🖌️', category=cat_school),
                AACButton(label='Music',     speech_text='I want music',         image_path='🎶', category=cat_school),

                # ── Health & Self-Care ────────────────────────────────────
                AACButton(label='Medicine',   speech_text='I need my medicine',  image_path='💊', category=cat_health),
                AACButton(label='Wash Hands', speech_text='I need to wash my hands', image_path='🧼', category=cat_health),
                AACButton(label='Bath',       speech_text='I want a bath',       image_path='🛁', category=cat_health),
                AACButton(label='Brush Teeth',speech_text='I need to brush my teeth', image_path='assets/icons/toothbrush.png', category=cat_health),
                AACButton(label='Haircut',    speech_text='I need a haircut',    image_path='✂️', category=cat_health),
                AACButton(label='Doctor',     speech_text='I need to see the doctor', image_path='🧑‍⚕️', category=cat_health),
                AACButton(label='Sick',       speech_text='I feel sick',         image_path='🤒', category=cat_health),
                AACButton(label='Tissues',    speech_text='I need tissues',      image_path='🤧', category=cat_health),

                # ── Quick Phrases ─────────────────────────────────────────
                AACButton(label='I want...',       speech_text='I want',               image_path='👉', category=cat_phrases),
                AACButton(label='I need...',       speech_text='I need',               image_path='🙋', category=cat_phrases),
                AACButton(label='I feel...',       speech_text='I feel',               image_path='💬', category=cat_phrases),
                AACButton(label='Can I have?',     speech_text='Can I have',           image_path='🙏', category=cat_phrases),
                AACButton(label='Please help me',  speech_text='Please help me',       image_path='🆘', category=cat_phrases),
                AACButton(label='I don\'t like',   speech_text='I do not like this',   image_path='👎', category=cat_phrases),
                AACButton(label='I don\'t understand', speech_text='I do not understand', image_path='😕', category=cat_phrases),
                AACButton(label='I\'m done',       speech_text='I am done',            image_path='🏁', category=cat_phrases),
                AACButton(label='Look at me',      speech_text='Please look at me',    image_path='👀', category=cat_phrases),
                AACButton(label='Wait please',     speech_text='Please wait',          image_path='✋', category=cat_phrases),
                AACButton(label='That\'s mine',    speech_text='That is mine',         image_path='☝️', category=cat_phrases),
                AACButton(label='Share please',    speech_text='Can we share please?', image_path='🤝', category=cat_phrases),
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
