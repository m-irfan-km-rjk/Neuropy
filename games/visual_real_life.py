import random
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.graphics import Color, RoundedRectangle, Line, Rectangle
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.behaviors import ButtonBehavior
from kivy.animation import Animation
from kivy.utils import get_color_from_hex

COLORS = {
    "bg": get_color_from_hex("#FDFCF0"),
    "top_panel": get_color_from_hex("#E8F5E9"),
    "btn_bg": get_color_from_hex("#BBDEFB"),
    "btn_border": get_color_from_hex("#90CAF9"),
    "text": get_color_from_hex("#2C3E50"),
    "selected": get_color_from_hex("#FFD54F")
}

Window.clearcolor = (0.92, 0.96, 0.98, 1)

def _get_emoji_font():
    if os.path.exists("C:/Windows/Fonts/seguiemj.ttf"): return "C:/Windows/Fonts/seguiemj.ttf"
    if os.path.exists("C:/Windows/Fonts/seguihis.ttf"): return "C:/Windows/Fonts/seguihis.ttf"
    return "Roboto"

def create_ui_icon(image_path, fallback_text, font_size='50sp', **kwargs):
    have_image = bool(image_path and isinstance(image_path, str) and (image_path.endswith('.png') or image_path.endswith('.jpg') or image_path.endswith('.jpeg')))
    if have_image:
        if os.path.isfile(image_path):
            try:
                return Image(source=image_path, allow_stretch=True, keep_ratio=True, **kwargs)
            except:
                pass
    # If not a valid file path, force the fallback Emoji
    lbl = Label(text=str(fallback_text), font_size=font_size, font_name=_get_emoji_font(), color=(0,0,0,1), **kwargs)
    # Give it bounding so it doesn't bleed if it's long text
    lbl.bind(size=lbl.setter('text_size'))
    lbl.halign = 'center'
    lbl.valign = 'middle'
    return lbl

# ---------------- DOMAIN DATA ----------------
DOMAINS = {
    "counting": {
        "items": [
            {"icon": "🍌", "image": "assets/images/grocery/banana.png"},
            {"icon": "🍎", "image": "assets/images/grocery/apple.png"},
            {"icon": "🧸", "image": "assets/images/home/teddy.png"},
            {"icon": "🍓", "image": "assets/images/grocery/strawberry.png"},
            {"icon": "⚽", "image": "assets/images/home/ball.png"},
            {"icon": "🚗", "image": "assets/images/home/car.png"},
            {"icon": "📚", "image": "assets/images/school/book.png"}
        ]
    },
    "comparison": {
        "items": [
            {"icon": "🚗", "image": "assets/images/home/car.png"},
            {"icon": "🍓", "image": "assets/images/grocery/strawberry.png"},
            {"icon": "🎈", "image": "assets/images/home/balloon.png"},
            {"icon": "🚲", "image": "assets/images/home/bicycle.png"},
            {"icon": "🐶", "image": "assets/images/home/dog.png"}
        ]
    },
    "money": {
        "items": [
            {"name": "Candy", "icon": "🍬", "image": "assets/images/grocery/candy.png", "price": 10},
            {"name": "Notebook", "icon": "📘", "image": "assets/images/school/notebook.png", "price": 20},
            {"name": "Toy", "icon": "🧸", "image": "assets/images/home/teddy.png", "price": 50},
            {"name": "Milk", "icon": "🥛", "image": "assets/images/grocery/milk.png", "price": 30},
            {"name": "Backpack", "icon": "🎒", "image": "assets/images/school/backpack.png", "price": 100}
        ],
        "coins": [{"icon": "🪙", "image": "assets/images/10.jpg", "val": 10, "label": "Rs.10"}, 
                  {"icon": "💵", "image": "assets/images/20.jpg", "val": 20, "label": "Rs.20"}, 
                  {"icon": "💰", "image": "assets/images/50.jpg", "val": 50, "label": "Rs.50"},
                  {"icon": "💳", "image": "assets/images/100.jpg", "val": 100, "label": "Rs.100"},
                  {"icon": "🏦", "image": "assets/images/500.jpg", "val": 500, "label": "Rs.500"}]
    },
    "daily": {
        "questions": [
            {"scene": "🌧️", "scene_img": "assets/images/scenes/rain.png", "target": "☂️", "options": ["☂️", "🧢", "🎒", "🏃"]},
            {"scene": "☀️", "scene_img": "assets/images/scenes/sun.png", "target": "🧢", "options": ["☂️", "🧢", "🧤", "🧥"]},
            {"scene": "🏫", "scene_img": "assets/images/scenes/school.png", "target": "🎒", "options": ["🎒", "🎮", "📺", "🛌"]},
            {"scene": "🍽️", "scene_img": "assets/images/scenes/dinner.png", "target": "🥪", "options": ["🥪", "⚽", "🚗", "🛁"]},
            {"scene": "🥶", "scene_img": "assets/images/scenes/cold.png", "target": "🧥", "options": ["🧥", "🩳", "🧊", "🍦"]},
            {"scene": "🤕", "scene_img": "assets/images/scenes/hurt.png", "target": "🩹", "options": ["🩹", "🎮", "⚽", "🍭"]},
            {"scene": "🦷", "scene_img": "assets/images/scenes/teeth.png", "target": "🪥", "options": ["🪥", "👟", "🎩", "🎒"]}
        ]
    },
    "safety": {
        "questions": [
            {"scene": "🚦🔴", "target": "🧍 Stop", "options": ["🧍 Stop", "🏃 Run", "🚶 Walk", "🚗 Drive"]},
            {"scene": "🔥", "target": "🚫 Stay Away", "options": ["🚫 Stay Away", "✋ Touch", "🔥 Play", "🏃 Run"]},
            {"scene": "🔪", "target": "🚫 Don't Touch", "options": ["🚫 Don't Touch", "✋ Play", "🔪 Grab", "🏃 Run"]},
            {"scene": "🚦🟢", "target": "🚶 Walk", "options": ["🚶 Walk", "🧍 Stop", "🛌 Sleep", "🍽️ Eat"]},
            {"scene": "🔌", "target": "🚫 Don't Touch", "options": ["🚫 Don't Touch", "🔌 Plug", "💧 Water", "🏃 Run"]},
            {"scene": "🐕 (Angry)", "target": "🚶 Walk Away", "options": ["🚶 Walk Away", "✋ Pet", "🏃 Run", "🗣️ Yell"]},
            {"scene": "🏊 (No Adult)", "target": "🧍 Wait", "options": ["🧍 Wait", "🏊 Swim", "🏃 Run", "💦 Jump"]}
        ]
    }
}

# ---------------- UI WIDGETS ----------------

class StyledDropZone(StackLayout):
    """
    Acts as the basket/payment zone.
    Stacks dropped items neatly using a StackLayout instead of random scattering.
    """
    def __init__(self, bg_color, title="Drop Area", expected_type="", expected_val=0, **kwargs):
        super().__init__(orientation='lr-tb', padding=20, spacing=15, **kwargs)
        self.expected_type = expected_type
        self.expected_val = expected_val
        self.current_items = []
        
        with self.canvas.before:
            self.bg_color_inst = Color(*bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[15])
            
            Color(0.8, 0.8, 0.8, 1)
            self.line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, 15), width=2, dash_length=10, dash_offset=5)
            
        self.bind(pos=self.update_rect, size=self.update_rect)
        
        self.title_lbl = Label(text=title, size_hint=(1, None), height=50, font_size='24sp', color=(0.4, 0.4, 0.4, 1), bold=True, font_name=_get_emoji_font())
        self.add_widget(self.title_lbl)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.line.rounded_rectangle = (self.x, self.y, self.width, self.height, 15)

    def set_bg_color(self, color):
        self.bg_color_inst.rgba = color
        
    def glow(self):
        anim = Animation(rgba=(1, 0.8, 0.3, 1), duration=0.3) + Animation(rgba=self.bg_color_inst.rgba, duration=0.3)
        anim.repeat = True
        anim.start(self.bg_color_inst)

    def stop_glow(self):
        Animation.cancel_all(self.bg_color_inst)

class DraggableTask(BoxLayout):
    """
    The drag/drop items without duplicated labeling. 
    Can be picked up mathematically from the StackLayout or MiddleSection FloatLayout.
    """
    def __init__(self, text="", icon="", image_path="", value=1, main_layout=None, domain="daily", **kwargs):
        # Base dimensions mapping to domain dynamics
        if domain == "money":
            dims = (190, 125) # Expanded size for higher legibility, still mathematically avoiding 4-row vertical overlap
        elif domain == "counting":
            dims = (110, 110) # Small squares for massive grid counts (11+ items) avoiding overlaps
        else:
            dims = (140, 140)
            
        super().__init__(orientation='vertical', size_hint=(None, None), size=dims, **kwargs)
        self.main_layout = main_layout
        self.domain = domain
        self.task_name = text or icon
        self.icon = icon
        self.value = value
        
        with self.canvas.before:
            self.bg_color_inst = Color(1, 0.9, 0.7, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[15])
        self.bind(pos=self.update_rect, size=self.update_rect)
        
        has_text = bool(text and text != icon)
        
        # Maximize graphic scaling depending on domain padding needed
        # 0.75 allocation leaves 25% explicitly for text, completely preventing font overflow outside of the box
        img_alloc = 0.75 if has_text else 1.0
        img = create_ui_icon(image_path, icon if icon else text, font_size='70sp' if domain != 'counting' else '50sp', size_hint=(1, img_alloc))
        self.add_widget(img)
            
        if has_text:
            lbl = Label(text=str(text), font_size='22sp' if domain != 'counting' else '18sp', color=(0.1, 0.1, 0.1, 1), size_hint=(1, 1.0 - img_alloc), bold=True)
            self.add_widget(lbl)

        self.is_dragging = False
        self.disabled = False
        self.pos_hint_original = {}
        self.original_parent = None

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_touch_down(self, touch):
        if self.disabled:
             return False
        if self.collide_point(*touch.pos):
            self.is_dragging = True
            touch.grab(self)
            
            # Record where we came from exactly
            if not self.original_parent:
                self.original_parent = self.parent
                
            # If inside the stack layout, we must pop it out to drag it globally
            if self.parent and self.main_layout:
                # Need to map global coords back into float space so it doesnt blink
                abs_pos = self.to_window(self.x, self.y)
                parent_to_detach_from = self.parent
                
                # If we are pulling it out of the DropZone stack
                if hasattr(parent_to_detach_from, 'current_items') and self in parent_to_detach_from.current_items:
                    parent_to_detach_from.current_items.remove(self)
                    
                parent_to_detach_from.remove_widget(self)
                self.size_hint = (None, None)
                self.pos_hint = {}
                self.pos = abs_pos
                self.main_layout.add_widget(self)
                
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self and self.is_dragging:
            self.pos_hint = {} 
            self.center_x = touch.x
            self.center_y = touch.y
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self and self.is_dragging:
            self.is_dragging = False
            touch.ungrab(self)
            
            # Parent hierarchy bubbling to trigger GameScreen drop validation
            parent = self.parent
            while parent is not None:
                if hasattr(parent, 'handle_drop'):
                    parent.handle_drop(self)
                    return True
                parent = parent.parent
            
            self.return_to_original()
            return True
        return super().on_touch_up(touch)

    def return_to_original(self):
        # Either map back to Float layout position...
        if self.pos_hint_original and self.main_layout:
            if self.parent != self.main_layout:
                if self.parent: self.parent.remove_widget(self)
                self.main_layout.add_widget(self)
            self.pos_hint = self.pos_hint_original.copy()

    def glow(self, peak_color=(1, 0.4, 0.4, 1)):
        # Provide stark highlighting via passed color
        anim = Animation(rgba=peak_color, duration=0.3) + Animation(rgba=(1, 0.9, 0.7, 1), duration=0.3)
        anim.repeat = True
        anim.start(self.bg_color_inst)

    def stop_glow(self):
        Animation.cancel_all(self.bg_color_inst)



class TapTask(ButtonBehavior, BoxLayout):
    def __init__(self, text, icon, image_path="", is_correct=False, **kwargs):
        super().__init__(orientation='vertical', size_hint=(None, None), size=(300, 200), **kwargs)
        self.is_correct = is_correct
        self.text = text
        
        with self.canvas.before:
            self.bg_color_inst = Color(0.85, 0.95, 1, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[15])
            Color(0.5, 0.5, 0.8, 1)
            self.line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, 15), width=2)
            
        self.bind(pos=self.update_rect, size=self.update_rect)
        
        img = create_ui_icon(image_path, icon if icon else text, font_size='40sp', size_hint=(1, 0.65))
        self.add_widget(img)
        
        if len(str(text)) > 4 and "🚗" not in str(text) and "🍓" not in str(text):
            lbl = Label(text=str(text), font_size='18sp', font_name=_get_emoji_font(), color=(0.1, 0.1, 0.1, 1), size_hint=(1, 0.35))
            self.add_widget(lbl)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.line.rounded_rectangle = (self.x, self.y, self.width, self.height, 15)
        
    def glow(self, peak_color=(1, 0.8, 0.3, 1)):
        anim = Animation(rgba=peak_color, duration=0.3) + Animation(rgba=(0.85, 0.95, 1, 1), duration=0.3)
        anim.repeat = True
        anim.start(self.bg_color_inst)

    def stop_glow(self):
        Animation.cancel_all(self.bg_color_inst)


# ---------------- MAIN SCREEN ARCHITECTURE ----------------

class GameScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 30
        self.spacing = 15
        
        self.top_section = BoxLayout(size_hint=(1, 0.15), orientation='horizontal', padding=[0, 10, 0, 0])
        self.home_btn = Button(text="< Menu", size_hint_x=None, width=120, background_normal='', background_color=(0.65, 0.84, 0.65, 1), color=(0.1, 0.1, 0.1, 1), bold=True, font_size='20sp')
        self.home_btn.bind(on_release=self._go_home)
        self.scenario_lbl = Label(font_size='36sp', color=(0.1, 0.1, 0.1, 1), bold=True, font_name=_get_emoji_font(), markup=True)
        
        self.top_section.add_widget(self.home_btn)
        self.top_section.add_widget(self.scenario_lbl)
        
        # Absolute Middle Section to hold floating drags
        self.middle_section = FloatLayout(size_hint=(1, 0.70))
        
        self.feedback_section = Label(size_hint=(1, 0.15), font_size='36sp', color=(0.1, 0.1, 0.1, 1), bold=True, font_name=_get_emoji_font())
        
        self.add_widget(self.top_section)
        self.add_widget(self.middle_section)
        self.add_widget(self.feedback_section)
        
        self.current_q_idx = 0
        self.level_active = 1
        self.tasks = []
        self.drop_zone = None
        self.failed_attempts = 0
        self.question_history = []

    def start_session(self, explicit_level=1):
        self.current_q_idx = 0
        self.level_active = explicit_level
        self.question_history = []
        self.load_current_question()

    def load_current_question(self, dt=0):
        try:
            if self.current_q_idx >= 10: # Auto advance after 10 questions in a block
                self.scenario_lbl.text = "All Challenges Complete! 🎉"
                self.middle_section.clear_widgets()
                self.feedback_section.text = f"You crushed Level {self.level_active}!"
                self.feedback_section.color = (0.2, 0.2, 0.8, 1)
                
                # Auto increment and return home or next Level
                if self.level_active < 5:
                    btn_next_lvl = Button(text=f"Start Level {self.level_active + 1} >", size_hint=(None, None), size=(300, 80), pos_hint={'center_x':0.5, 'center_y':0.5}, background_normal='', background_color=(0.2, 0.8, 0.2, 1), font_size='24sp', bold=True)
                    btn_next_lvl.bind(on_release=lambda x: self.start_session(self.level_active + 1))
                    self.middle_section.add_widget(btn_next_lvl)
                return

            self.q_data = self.generate_question_for_level(self.level_active)
            self.scenario_lbl.text = f"[{self.current_q_idx+1}/10] Lvl {self.level_active}:   {self.q_data['instruction']}"
            
            self.failed_attempts = 0
            self.feedback_section.text = ""
            self.middle_section.clear_widgets()
            self.tasks = []
            
            if self.q_data["type"] == "drag":
                self.build_drag_domain()
            else:
                self.build_tap_domain()
                
        except Exception as e:
            print(f"Error loading question: {e}")

    def generate_question_for_level(self, level):
        """Map levels directly to domains exactly requested by the User"""
        if level == 1: domain = "counting"
        elif level == 2: domain = "comparison"
        elif level == 3: domain = "daily"
        elif level == 4: domain = "money"
        else: domain = "safety"
            
        data = DOMAINS[domain]
        q = {"domain": domain}
        
        while True:
            if domain == "counting":
                item = random.choice(data["items"])
                qty = random.randint(2, 6)
                q.update({"type": "drag", "instruction": f"Pick {qty} [size=70sp]{item['icon']}[/size]", "target_qty": qty, "item": item})
            
            elif domain == "comparison":
                is_more = random.choice([True, False])
                opt1 = random.randint(1, 4)
                opt2 = random.randint(5, 8)
                item = random.choice(data["items"])
                opts = [item['icon'] * opt1, item['icon'] * opt2]
                correct = opts[1] if is_more else opts[0]
                q.update({"type": "tap", "instruction": f"Tap the box with {'MORE' if is_more else 'LESS'}", "options": opts, "correct": correct})
                
            elif domain == "money":
                item = random.choice(data["items"])
                q.update({"type": "drag", "instruction": f"Pay Rs.{item['price']} for [size=70sp]{item['icon']}[/size]", "target_val": item['price'], "item": item})
                
            elif domain == "daily": # Cause effect reasoning
                question = random.choice(data["questions"])
                q.update({"type": "drag", "instruction": f"What do you need? [size=70sp]{question['scene']}[/size]", "target_single": question["target"], "options": question["options"]})

            elif domain == "safety":
                question = random.choice(data["questions"])
                q.update({"type": "tap", "instruction": f"What to do? [size=55sp]{question['scene']}[/size]", "options": question["options"], "correct": question["target"]})
                
            # Anti-Repetition logic
            inst = q["instruction"]
            if self.question_history.count(inst) < 2:
                # To prevent immediate back-to-back duplicates entirely
                if len(self.question_history) == 0 or self.question_history[-1] != inst:
                    self.question_history.append(inst)
                    return q

    def build_drag_domain(self):
        domain = self.q_data["domain"]
        
        # 1. Provide Visual Basket (Half the screen, horizontally aligned)
        lbl_hint = ""
        if domain == "counting":
            self.drop_zone = StyledDropZone(bg_color=(0.95, 0.95, 0.95, 1), title="Basket 🧺", expected_type="count", expected_val=self.q_data["target_qty"])
        elif domain == "money":
            self.drop_zone = StyledDropZone(bg_color=(0.95, 0.95, 0.95, 1), title="Shop Counter 🏪", expected_type="sum", expected_val=self.q_data["target_val"])
        elif domain == "daily":
            self.drop_zone = StyledDropZone(bg_color=(0.95, 0.95, 0.95, 1), title=f"Action Box 📦", expected_type="single", expected_val=self.q_data["target_single"])

        self.drop_zone.size_hint = (0.45, 0.55)
        self.drop_zone.pos_hint = {'right': 0.95, 'center_y': 0.5}
        self.middle_section.add_widget(self.drop_zone)

        # 2. Build draggable items visually onto the LEFT side explicitly in a mathematical grid
        items_to_generate = []
        
        if domain == "counting":
            item = self.q_data["item"]
            num_draggable = self.q_data["target_qty"] + random.randint(2, 5)
            for i in range(num_draggable):
                items_to_generate.append(DraggableTask(text="", icon=item["icon"], image_path=item.get("image", ""), value=1, main_layout=self.middle_section, domain=domain))
        elif domain == "money":
            target_val = self.q_data["target_val"]
            coins_def = sorted(DOMAINS["money"]["coins"], key=lambda x: x['val'], reverse=True)
            
            # 1. Calculate and guarantee the exact change notes exist in the pool
            guaranteed_coins = []
            remaining = target_val
            for c in coins_def:
                while remaining >= c['val']:
                    guaranteed_coins.append(c)
                    remaining -= c['val']
            
            # 2. Pad the remainder of the 7-slot grid randomly
            pool = DOMAINS["money"]["coins"] * 3
            random.shuffle(pool)
            
            final_coins = guaranteed_coins.copy()
            for c in pool:
                if len(final_coins) >= 7:
                    break
                final_coins.append(c)
                
            random.shuffle(final_coins)
            
            for i in range(7):
                c = final_coins[i]
                items_to_generate.append(DraggableTask(text=c.get("label", str(c['val'])), icon=c["icon"], image_path=c.get("image", ""), value=c['val'], main_layout=self.middle_section, domain=domain))
        elif domain == "daily":
            opts = list(self.q_data["options"])
            random.shuffle(opts)
            for o in opts:
                items_to_generate.append(DraggableTask(text=o, icon=o, image_path="", value=1, main_layout=self.middle_section, domain=domain))

        total = len(items_to_generate)
        
        # Domain-aware layout spacing that perfectly complements their explicit rectangular shapes
        if domain == "money":
            cols = 2
            start_x, space_x = 0.12, 0.28   # Narrowed origin pulling grid away from DropZone
            start_y, space_y = 0.85, 0.24   # Stable tight vertical spanning 4 rows exactly
        elif domain == "counting":
            if total <= 6:
                cols = 2
                start_x, space_x = 0.15, 0.22
                start_y, space_y = 0.85, 0.28
            else:
                cols = 3
                start_x, space_x = 0.08, 0.15
                start_y, space_y = 0.85, 0.23
        else: # Daily
            cols = 2
            start_x, space_x = 0.10, 0.25
            start_y, space_y = 0.80, 0.30
            
        for i, task in enumerate(items_to_generate):
            col = i % cols
            row = i // cols
            
            px = start_x + (col * space_x)
            py = start_y - (row * space_y)
            
            # constrain py firmly to prevent physics dropping off screen bottom edge
            py = max(0.12, py)
            
            task.pos_hint_original = {'center_x': px, 'center_y': py}
            task.pos_hint = task.pos_hint_original.copy()
            self.tasks.append(task)
            self.middle_section.add_widget(task)


    def build_tap_domain(self):
        opts = list(self.q_data["options"])
        random.shuffle(opts)
        
        num_opts = len(opts)
        for i, opt in enumerate(opts):
            is_correct = (opt == self.q_data["correct"])
            t = TapTask(text=opt, icon=opt, image_path="", is_correct=is_correct)
            t.bind(on_release=self.on_tap_task)
            
            # Clean layouting directly overriding random jitter
            if num_opts == 2:
                t.pos_hint = {'center_x': 0.3 if i==0 else 0.7, 'center_y': 0.5}
            else:
                t.pos_hint = {'center_x': 0.3 if i%2==0 else 0.7, 'center_y': 0.7 if i<2 else 0.3}
                
            self.middle_section.add_widget(t)
            self.tasks.append(t)

    def handle_drop(self, task):
        try:
            # 1. Validate collision over drop zone explicitly
            if not task.collide_widget(self.drop_zone):
                task.return_to_original()
                return
                
            # 2. Add to Drop Zone list and visually stack into the box
            self.drop_zone.current_items.append(task)
            
            # REPARENT to StackLayout: Perfect visibility mapping!
            if task.parent:
                task.parent.remove_widget(task)
            self.drop_zone.add_widget(task)
            # Remove pos_hint constraints since it is now natively ordered by StackLayout
            task.pos_hint = {}
            task.size_hint = (None, None)
            
            # 3. Process Logic Checks against the expected
            items = self.drop_zone.current_items
            target_type = self.drop_zone.expected_type
            target_val = self.drop_zone.expected_val
            
            success = False
            failed = False
            fail_msg = "❌ Try Again"
            
            if target_type == "count":
                if len(items) == target_val: success = True
                elif len(items) > target_val: 
                    failed = True
                    fail_msg = "❌ Too many items!"
                else: # Incremental feedback
                    self.feedback_section.text = f"Placed {len(items)}. {target_val - len(items)} more to go!"
                    self.feedback_section.color = (0.2, 0.5, 0.8, 1)
            
            elif target_type == "sum":
                total = sum(i.value for i in items)
                if total == target_val: success = True
                elif total > target_val:
                    failed = True
                    fail_msg = "❌ Too much money!"
                else: # Incremental feedback
                    self.feedback_section.text = f"Added Rs.{total}. Need Rs.{target_val - total} more!"
                    self.feedback_section.color = (0.2, 0.5, 0.8, 1)
            
            elif target_type == "single":
                if len(items) == 1:
                    if items[0].task_name == target_val: success = True
                    else:
                        failed = True
                        fail_msg = "❌ Incorrect object!"

            if success:
                self.correct_action()
            elif failed:
                self.wrong_action(fail_msg)
                
        except Exception as e:
            print(f"Error handling drop: {e}")
            task.return_to_original()

    def on_tap_task(self, instance):
        if instance.is_correct:
            self.correct_action()
        else:
            self.wrong_action("❌ Try Again")

    def correct_action(self):
        self.feedback_section.text = "✔ Correct! Awesome!"
        self.feedback_section.color = (0.2, 0.8, 0.2, 1)
        
        # Lock UI
        if self.q_data["type"] == "drag":
            if self.drop_zone:
                self.drop_zone.set_bg_color((0.6, 0.9, 0.6, 1))
                if hasattr(self.drop_zone, 'stop_glow'): self.drop_zone.stop_glow()
            for t in self.tasks: t.disabled = True
        else:
            for t in self.tasks:
                 if hasattr(t, 'stop_glow'): t.stop_glow()
                 t.disabled = True
        
        self.current_q_idx += 1
        
        # Schedule auto advance requested by user
        Clock.schedule_once(self.load_current_question, 1.5)
        
    def wrong_action(self, msg):
        self.failed_attempts += 1
        self.feedback_section.text = msg
        self.feedback_section.color = (0.8, 0.2, 0.2, 1)
        
        # Revert items from Basket automatically
        if self.q_data["type"] == "drag":
            for t in list(self.drop_zone.current_items):
                t.return_to_original()
            self.drop_zone.current_items = []
                
        if self.failed_attempts >= 3:
            self.trigger_hint()

    def trigger_hint(self):
        self.feedback_section.text = "Hint! Look for the glowing area 👀"
        self.feedback_section.color = (0.8, 0.6, 0.1, 1)
        
        if self.q_data["type"] == "drag":
            # Rectified Level Hints: Highlight exact draggable Target Options instead of generic glowing drop boxes
            # Passes highly contrasting RED highlight for extreme visibility
            if self.q_data["domain"] == "daily":
                for t in self.tasks:
                    if hasattr(t, 'task_name') and t.task_name == self.q_data["target_single"] and t.parent == self.middle_section:
                        if hasattr(t, 'glow'): t.glow(peak_color=(1, 0.2, 0.2, 1))
            elif self.q_data["domain"] == "counting":
                target_icon = self.q_data["item"]["icon"]
                need = self.q_data["target_qty"] - len(self.drop_zone.children) if self.drop_zone else self.q_data["target_qty"]
                glowing = 0
                for t in self.tasks:
                    if hasattr(t, 'icon') and t.icon == target_icon and t.parent == self.middle_section:
                        if hasattr(t, 'glow'): t.glow(peak_color=(0.1, 0.9, 0.2, 1)) # Bright contrast Green
                        glowing += 1
                        if glowing >= need: break
            else:
                if hasattr(self.drop_zone, 'glow'): self.drop_zone.glow()
        else:
            for t in self.tasks:
                if hasattr(t, 'is_correct') and t.is_correct and hasattr(t, 'glow'): 
                    t.glow(peak_color=(0.1, 0.9, 0.2, 1))

    def _go_home(self, *args):
        app = App.get_running_app()
        if app and app.root and hasattr(app.root, 'current'):
            app.root.current = 'games'


class VRLMenuScreen(Screen):
    """Refined Menu with Level Selector"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*COLORS["bg"])
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        layout = BoxLayout(orientation='vertical', padding=40, spacing=30)
        
        header = BoxLayout(size_hint_y=None, height=80, padding=[0, 0, 0, 20])
        back_btn = Button(text="< Home", size_hint_x=None, width=120, background_normal='', background_color=COLORS["btn_border"], color=COLORS["text"], bold=True, font_size='20sp')
        back_btn.bind(on_release=self._go_home)
        title = Label(text="Visual Real-Life", font_size='42sp', bold=True, color=COLORS["text"])
        header.add_widget(back_btn)
        header.add_widget(title)
        layout.add_widget(header)

        layout.add_widget(Label(text="Choose Your Lesson Level:", font_size='26sp', color=COLORS["text"], size_hint_y=None, height=40))

        # Level Selector specific explicitly to User requirements
        self.lvl_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=80, spacing=15)
        self.lvl_buttons = []
        domain_labels = ["Counting", "Comparison", "Daily Logic", "Money", "Safety"]
        
        for lvl in range(1, 6):
            btn = Button(text=f"Lvl {lvl}\n{domain_labels[lvl-1]}", halign='center', background_normal='', background_color=COLORS['btn_bg'], color=COLORS['text'], bold=True)
            btn.bind(on_release=lambda instance, l=lvl: self.select_level(l))
            self.lvl_buttons.append(btn)
            self.lvl_box.add_widget(btn)
            
        layout.add_widget(self.lvl_box)
        self.selected_level = 1
        self.select_level(1)

        btn_start_box = BoxLayout(size_hint_y=None, height=120, padding=20)
        btn_start = Button(text="Start Challenge >", background_normal='', background_color=(0.3, 0.8, 0.3, 1), font_size='28sp', bold=True)
        btn_start.bind(on_release=lambda x: self.start_game())
        btn_start_box.add_widget(btn_start)
        
        layout.add_widget(Label()) # Spacer
        layout.add_widget(btn_start_box)
        self.add_widget(layout)

    def select_level(self, level):
        self.selected_level = level
        for i, b in enumerate(self.lvl_buttons):
            b.background_color = COLORS["selected"] if i+1 == level else COLORS["btn_bg"]

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def _go_home(self, *args):
        app = App.get_running_app()
        if hasattr(app, 'root') and app.root:
            app.root.current = 'games'

    def start_game(self):
        self.manager.current = 'vrl_game'
        game_screen = self.manager.get_screen('vrl_game')
        game_screen.children[0].start_session(explicit_level=self.selected_level)


class VisualRealLifeAppScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        Window.clearcolor = (0.92, 0.96, 0.98, 1)
        sm = ScreenManager()
        menu_screen = VRLMenuScreen(name='vrl_menu')
        game_screen = Screen(name='vrl_game')
        game_screen.add_widget(GameScreen())
        sm.add_widget(menu_screen)
        sm.add_widget(game_screen)
        self.add_widget(sm)

if __name__ == '__main__':
    class TestApp(App):
        def build(self):
            Window.size = (1024, 768)
            return VisualRealLifeAppScreen()
    TestApp().run()
