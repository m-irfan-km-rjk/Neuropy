import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen
from kivy.animation import Animation


# Set soft pastel background color for the main window (Sensory-friendly)
Window.clearcolor = (0.92, 0.96, 0.98, 1)

# REQUIRED SCENARIOS (5 TOTAL)
SCENARIOS = [
    {
        "title": "Getting Ready for School",
        "steps": [
            {"text": "Brush Teeth", "icon": "assets/images/brushteeth.jpg"}, 
            {"text": "Wear Uniform", "icon": "assets/images/wearuniform.jpg"}, 
            {"text": "Eat Breakfast", "icon": "assets/images/eatbreakfast.jpg"}, 
            {"text": "Pack Bag", "icon": "assets/images/pack bag.jpg"}
        ]
    },
    {
        "title": "Going to the Shop",
        "steps": [
            {"text": "Carry Bag", "icon": "assets/images/carrybag.jpg"}, 
            {"text": "Take Money", "icon": "assets/images/take money.jpg"}, 
            {"text": "Buy Product", "icon": "assets/images/buy product.jpg"}, 
            {"text": "Collect Balance", "icon": "assets/images/collect balance.jpg"}
        ]
    },
    {
        "title": "Preparing for Bed",
        "steps": [
            {"text": "Change Clothes", "icon": "assets/images/change cloths.jpg"}, 
            {"text": "Brush Teeth", "icon": "assets/images/brushteeth.jpg"}, 
            {"text": "Read Book", "icon": "assets/images/reading book.jpg"}, 
            {"text": "Sleep", "icon": "assets/images/sleep.jpg"}
        ]
    },
    {
        "title": "Going to Playground",
        "steps": [
            {"text": "Wear Shoes", "icon": "assets/images/wear shoes.jpg"}, 
            {"text": "Take Water Bottle", "icon": "assets/images/take bottle.jpg"}, 
            {"text": "Go Outside", "icon": "assets/images/go outside.jpg"}, 
            {"text": "Play", "icon": "assets/images/play.jpg"}
        ]
    },
    {
        "title": "Doing Homework",
        "steps": [
            {"text": "Take Books", "icon": "assets/images/take book.png"}, 
            {"text": "Sit at Desk", "icon": "assets/images/sit at desk.png"}, 
            {"text": "Complete Work", "icon": "assets/images/complete work.png"}, 
            {"text": "Pack Books", "icon": "assets/images/pack books.jpg"}
        ]
    }
]

class StyledSlot(BoxLayout):
    """
    Custom container with rounded rectangle background used for timeline drop slots.
    Displays an image and a label strictly when populated by a successful Drop.
    """
    def __init__(self, bg_color, text="", **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=5, **kwargs)
        with self.canvas.before:
            self.bg_color_inst = Color(*bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[15])
        
        self.bind(pos=self.update_rect, size=self.update_rect)
        
        # Hidden by default until populated
        self.img = Image(source="", size_hint=(1, 0.7), allow_stretch=True, keep_ratio=True, opacity=0)
        self.add_widget(self.img)
        
        self.lbl = Label(text=text, color=(0.1, 0.1, 0.1, 1), font_size='22sp', bold=True, size_hint=(1, 0.3))
        self.lbl.halign = 'center'
        self.lbl.valign = 'middle'
        self.lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width - 20, inst.height)))
        self.add_widget(self.lbl)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def set_bg_color(self, color):
        self.bg_color_inst.rgba = color
        
    def set_task(self, text, icon_path):
        self.lbl.text = f"{text} ✔"
        self.lbl.color = (0.1, 0.4, 0.1, 1) # Dark green success text
        if icon_path:
            self.img.source = icon_path
            self.img.opacity = 1
            
    def reset(self, text):
        self.lbl.text = text
        self.lbl.color = (0.1, 0.1, 0.1, 1)
        self.img.source = ""
        self.img.opacity = 0


class DraggableTask(BoxLayout):
    """
    Represents a single task that child can drag and drop.
    Handles custom touch down/move/up events.
    """
    def __init__(self, text, icon="", **kwargs):
        # Sensory-friendly colors, large readable text (minimum 160x60 -> 200x140 for image support)
        super().__init__(orientation='vertical', size_hint=(None, None), size=(200, 140), **kwargs)
        
        with self.canvas.before:
            self.bg_color_inst = Color(1, 0.9, 0.7, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[15])
        self.bind(pos=self.update_rect, size=self.update_rect)
        
        if icon:
            self.add_widget(Image(source=icon, size_hint=(1, 0.65), allow_stretch=True, keep_ratio=True))
            
        lbl = Label(text=text, font_size='16sp', color=(0.1, 0.1, 0.1, 1), size_hint=(1, 0.35 if icon else 1))
        def _update_lbl_size(instance, value):
            instance.text_size = (instance.width - 20, instance.height)
        lbl.bind(size=_update_lbl_size)
        lbl.halign = 'center'
        lbl.valign = 'middle'
        self.add_widget(lbl)

        self.is_dragging = False
        self.disabled = False
        self.task_name = text
        self.icon_source = icon
        self.pos_hint_original = {}

    def glow(self, peak_color=(1, 0.2, 0.2, 1)):
        anim = Animation(rgba=peak_color, duration=0.3) + Animation(rgba=(1, 0.9, 0.7, 1), duration=0.3)
        anim.repeat = True
        anim.start(self.bg_color_inst)

    def stop_glow(self):
        Animation.cancel_all(self.bg_color_inst)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_touch_down(self, touch):
        if self.disabled:
             return False
             
        if self.collide_point(*touch.pos):
            self.is_dragging = True
            touch.grab(self)
            
            # Bring widget to front
            parent = self.parent
            if parent:
                parent.remove_widget(self)
                parent.add_widget(self)
            return True
            
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self and self.is_dragging:
            # Remove pos_hint to allow free horizontal/vertical dragging inside FloatLayout
            self.pos_hint = {} 
            self.center_x = touch.x
            self.center_y = touch.y
            return True
            
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self and self.is_dragging:
            self.is_dragging = False
            touch.ungrab(self)
            # Find the GameScreen parent (it is the parent of the parent floating layout)
            parent = self.parent
            while parent is not None:
                if hasattr(parent, 'handle_drop'):
                    parent.handle_drop(self)
                    return True
                parent = parent.parent
            
            # Fallback if somehow not found
            self.return_to_original()
            return True
            
        return super().on_touch_up(touch)

    def return_to_original(self):
        """ Safety fallback if dropped outside or logic fails """
        if self.pos_hint_original:
            self.pos_hint = self.pos_hint_original.copy()


class GameScreen(BoxLayout):
    """
    Main layout containing Scenario Label, Tasks Area, Drop Slots, and Feedback Label.
    """
    def __init__(self, level=2, return_menu_cb=None, **kwargs):
        super().__init__(**kwargs)
        self.level = level
        self.return_menu_cb = return_menu_cb
        self.failed_attempts = 0
        
        self.orientation = 'vertical'
        self.padding = 30
        self.spacing = 15
        
        # UI STRUCTURE REQUIREMENTS (Layout 15%, 40%, 25%, 10%)
        # 1. Top Section (15%) - Scenario Label and Home Button
        self.top_section = BoxLayout(size_hint=(1, 0.15), orientation='horizontal', padding=[0, 10, 0, 0])
        self.home_btn = Button(text="< Menu", size_hint_x=None, width=120, background_normal='', background_color=(0.65, 0.84, 0.65, 1), color=(0.1, 0.1, 0.1, 1), bold=True, font_size='20sp')
        if self.return_menu_cb:
            self.home_btn.bind(on_release=lambda x: self.return_menu_cb())
        else:
            self.home_btn.bind(on_release=self._go_home)
        self.scenario_lbl = Label(font_size='36sp', color=(0.1, 0.1, 0.1, 1), bold=True)
        self.top_section.add_widget(self.home_btn)
        self.top_section.add_widget(self.scenario_lbl)
        
        # 2. Middle Section (40%) - Draggable Task Area (FloatLayout for free movement)
        self.middle_section = FloatLayout(size_hint=(1, 0.40))
        
        # 3. Drop Section (25%) - 4 fixed slots in horizontal layout
        self.drop_section = BoxLayout(size_hint=(1, 0.25), orientation='horizontal', spacing=20)
        
        # 4. Feedback Section (10%) - Correct / Try Again / Scenario Complete 
        # Extra 10% comes from Box padding/spacing implicitly
        self.feedback_section = Label(size_hint=(1, 0.10), font_size='28sp', color=(0.1, 0.1, 0.1, 1), bold=True)
        
        self.add_widget(self.top_section)
        self.add_widget(self.middle_section)
        self.add_widget(self.drop_section)
        self.add_widget(self.feedback_section)
        
        # Create 4 static Drop Slots
        self.slots = []
        for i in range(4):
            slot = StyledSlot(bg_color=(0.8, 0.8, 0.8, 1), text=f"Step {i+1}")
            self.slots.append(slot)
            self.drop_section.add_widget(slot)
            
        # Internal Game Logic States
        self.current_scenario_idx = 0
        self.current_step_idx = 0
        self.tasks = []
        
        # Load the very first scenario
        Clock.schedule_once(self.load_current_scenario, 0.1)

    def load_current_scenario(self, dt=0):
        try:
            # Check Scenario Index Error
            if self.current_scenario_idx >= len(SCENARIOS):
                self.scenario_lbl.text = "All Scenarios Complete 🎉"
                # Clear areas
                self.middle_section.clear_widgets()
                for slot in self.slots:
                    slot.reset("")
                    slot.set_bg_color((0.8, 0.8, 0.8, 1))
                self.feedback_section.text = ""
                return

            scenario = SCENARIOS[self.current_scenario_idx]
            self.scenario_lbl.text = f"[{self.current_scenario_idx+1}/{len(SCENARIOS)}] Lvl {self.level}: {scenario['title']}"
            
            # State Reset Protection
            self.current_step_idx = 0
            self.failed_attempts = 0
            self.feedback_section.text = ""
            
            self.reset_slots()
            self.create_and_shuffle_tasks()
        except Exception as e:
            print(f"Error loading scenario: {e}")

    def reset_slots(self):
        # Reset drop slots safely wiping visual JPEGs
        for i, slot in enumerate(self.slots):
            slot.reset(f"Step {i+1}")
            slot.set_bg_color((0.85, 0.85, 0.85, 1))

    def create_and_shuffle_tasks(self):
        self.middle_section.clear_widgets()
        self.tasks = []
        
        try:
            scenario = SCENARIOS[self.current_scenario_idx]
            
            # Shuffle Safety (using copy of list)
            steps = list(scenario['steps'])
            random.shuffle(steps)
            
            # Positions spread out predictably
            hints = [
                {'center_x': 0.25, 'center_y': 0.75},
                {'center_x': 0.75, 'center_y': 0.75},
                {'center_x': 0.25, 'center_y': 0.25},
                {'center_x': 0.75, 'center_y': 0.25}
            ]
            random.shuffle(hints)
            
            for i, step_data in enumerate(steps):
                task = DraggableTask(text=step_data['text'], icon=step_data.get('icon', ''))
                task.pos_hint_original = hints[i].copy()
                task.pos_hint = hints[i].copy()
                
                self.tasks.append(task)
                self.middle_section.add_widget(task)
                
        except Exception as e:
            print(f"Error shuffling tasks: {e}")

    def play_level2_hint_sequence(self, dt=0):
        try:
            scenario = SCENARIOS[self.current_scenario_idx]
            correct_order = [s['text'] for s in scenario['steps']]
            
            task_map = {t.task_name: t for t in self.tasks}
            
            delay = 0.0
            for step_text in correct_order:
                t = task_map.get(step_text)
                if t:
                    # Blink target sequentially using Green pulse memory
                    Clock.schedule_once(lambda dt, task=t: task.glow(peak_color=(0.2, 0.8, 0.2, 1)), delay)
                    Clock.schedule_once(lambda dt, task=t: task.stop_glow(), delay + 1.0)
                    delay += 1.2
        except Exception as e:
            print(f"Error playing sequence: {e}")

    def handle_drop(self, task):
        """
        Validates the dropped task using collide_widget() immediately upon release
        """
        try:
            scenario = SCENARIOS[self.current_scenario_idx]
            correct_order = [s['text'] for s in scenario['steps']]
            
            dropped_on_slot = None
            dropped_slot_idx = -1
            
            # 1. Check if the dragged task collides with any drop slot
            for i, slot in enumerate(self.slots):
                if task.collide_widget(slot):
                    dropped_on_slot = slot
                    dropped_slot_idx = i
                    break
                    
            # 2. Invalid Collision
            if not dropped_on_slot:
                task.return_to_original()
                return
                
            # 3. Duplicate Drop / out-of-order drop checks
            # Enforce drop in successive sequential slots only 
            if dropped_slot_idx != self.current_step_idx:
                self.wrong_drop(task)
                return
                
            # Validation Logic
            if task.task_name == correct_order[self.current_step_idx]:
                self.correct_drop(task, dropped_on_slot)
            else:
                self.wrong_drop(task)
                
        except Exception as e:
            # Prevents crashing on unexpectedly unhandled layout drops
            print(f"Error handling drop: {e}")
            task.return_to_original()

    def correct_drop(self, task, slot):
        # Update UI: Populate the slot with the Dragged Object's Icon Graphic
        slot.set_task(task.task_name, task.icon_source)
        
        # Change slot UI to indicate success
        slot.set_bg_color((0.6, 0.9, 0.6, 1)) # Light pastel green
        
        # Disable original dragging widget and safely clear it
        task.disabled = True
        try:
            self.middle_section.remove_widget(task)
        except Exception:
            pass # Widget Removal Error handled safely
            
        self.feedback_section.text = "✔ Correct!"
        self.feedback_section.color = (0.2, 0.8, 0.2, 1)
        
        self.failed_attempts = 0
        for t in self.tasks:
            if hasattr(t, 'stop_glow'): t.stop_glow()
        
        # Move up internal step
        self.current_step_idx += 1
        
        # Check scenario complete
        if self.current_step_idx == 4:
            self.feedback_section.text = "🎉 Scenario Complete"
            self.feedback_section.color = (0.2, 0.2, 0.8, 1)
            self.current_scenario_idx += 1
            
            # Load next scenario smoothly
            Clock.schedule_once(self.load_current_scenario, 2.0)

    def wrong_drop(self, task=None):
        # Update Feedback "Try Again"
        self.feedback_section.text = "❌ Try Again"
        self.feedback_section.color = (0.8, 0.2, 0.2, 1)
        
        if self.level == 1:
            self.failed_attempts += 1
            if task: 
                task.return_to_original()
            
            if self.failed_attempts >= 3:
                scenario = SCENARIOS[self.current_scenario_idx]
                correct_order = [s['text'] for s in scenario['steps']]
                target_name = correct_order[self.current_step_idx]
                for t in self.tasks:
                    if hasattr(t, 'task_name') and t.task_name == target_name and not t.disabled:
                        if hasattr(t, 'glow'):
                            t.glow(peak_color=(1, 0.2, 0.2, 1))
        else:
            # Level 2 Sequence completely resets
            self.failed_attempts += 1
            self.current_step_idx = 0
            self.reset_slots()
            self.create_and_shuffle_tasks()
            
            # If they have failed 3 times in strict mode, show the full sequence order
            if self.failed_attempts >= 3:
                Clock.schedule_once(self.play_level2_hint_sequence, 0.5)

    def _go_home(self, *args):
        app = App.get_running_app()
        if app and app.root and hasattr(app.root, 'current'):
            app.root.current = 'games'

class RoutineGameScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        # Ensure correct background color is set when entering this screen
        Window.clearcolor = (0.92, 0.96, 0.98, 1)
        self.show_menu()

    def show_menu(self):
        self.clear_widgets()
        
        layout = BoxLayout(orientation='vertical', padding=[50, 100], spacing=40)
        
        lbl = Label(text="Routine Sequence Builder", font_size='48sp', color=(0.1, 0.1, 0.1, 1), bold=True, size_hint=(1, 0.3))
        layout.add_widget(lbl)
        
        btn_lvl1 = Button(text="Level 1 (With Hints & Forgiving Drops)", font_size='30sp', size_hint=(1, 0.2), background_normal='', background_color=(0.4, 0.8, 0.4, 1), bold=True)
        btn_lvl1.bind(on_release=lambda x: self.start_game(level=1))
        layout.add_widget(btn_lvl1)
        
        btn_lvl2 = Button(text="Level 2 (Strict Rules)", font_size='30sp', size_hint=(1, 0.2), background_normal='', background_color=(0.8, 0.4, 0.4, 1), bold=True)
        btn_lvl2.bind(on_release=lambda x: self.start_game(level=2))
        layout.add_widget(btn_lvl2)
        
        btn_home = Button(text="< Back to Hub", font_size='30sp', size_hint=(1, 0.2), background_normal='', background_color=(0.6, 0.6, 0.6, 1), bold=True)
        btn_home.bind(on_release=self._go_home)
        layout.add_widget(btn_home)
        
        self.add_widget(layout)
        
    def start_game(self, level):
        self.clear_widgets()
        self.add_widget(GameScreen(level=level, return_menu_cb=self.show_menu))
        
    def _go_home(self, *args):
        app = App.get_running_app()
        if app and app.root and hasattr(app.root, 'current'):
            app.root.current = 'games'

class RoutineApp(App):
    def build(self):
        return GameScreen()

if __name__ == '__main__':
    try:
        RoutineApp().run()
    except Exception as e:
        print(f"Application error: {e}")
