import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen


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

class StyledLabel(Label):
    """
    Custom Label with rounded rectangle background used for slots and tasks.
    Ensures safe drawing on size updates.
    """
    def __init__(self, bg_color, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self.bg_color_inst = Color(*bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[15])
        
        self.bind(pos=self.update_rect, size=self.update_rect)
        self.color = (0.1, 0.1, 0.1, 1) # Dark text for readability
        self.halign = 'center'
        self.valign = 'middle'
        self.bind(size=self._update_text_size)

    def _update_text_size(self, *args):
        self.text_size = (self.width - 20, self.height)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def set_bg_color(self, color):
        self.bg_color_inst.rgba = color


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
        self.pos_hint_original = {}

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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 30
        self.spacing = 15
        
        # UI STRUCTURE REQUIREMENTS (Layout 15%, 40%, 25%, 10%)
        # 1. Top Section (15%) - Scenario Label and Home Button
        self.top_section = BoxLayout(size_hint=(1, 0.15), orientation='horizontal', padding=[0, 10, 0, 0])
        self.home_btn = Button(text="< Home", size_hint_x=None, width=120, background_normal='', background_color=(0.65, 0.84, 0.65, 1), color=(0.1, 0.1, 0.1, 1), bold=True, font_size='20sp')
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
            slot = StyledLabel(bg_color=(0.8, 0.8, 0.8, 1), text=f"Step {i+1}", font_size='22sp', bold=True)
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
                    slot.text = ""
                    slot.set_bg_color((0.8, 0.8, 0.8, 1))
                self.feedback_section.text = ""
                return

            scenario = SCENARIOS[self.current_scenario_idx]
            self.scenario_lbl.text = f"Scenario: {scenario['title']}"
            
            # State Reset Protection
            self.current_step_idx = 0
            self.feedback_section.text = ""
            
            self.reset_slots()
            self.create_and_shuffle_tasks()
        except Exception as e:
            print(f"Error loading scenario: {e}")

    def reset_slots(self):
        # Reset drop slots safely
        for i, slot in enumerate(self.slots):
            slot.text = f"Step {i+1}"
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
                self.wrong_drop()
                return
                
            # Validation Logic
            if task.task_name == correct_order[self.current_step_idx]:
                self.correct_drop(task, dropped_on_slot)
            else:
                self.wrong_drop()
                
        except Exception as e:
            # Prevents crashing on unexpectedly unhandled layout drops
            print(f"Error handling drop: {e}")
            task.return_to_original()

    def correct_drop(self, task, slot):
        # Update UI: Change slot text and add tick
        slot.text = f"{task.task_name} ✔"
        
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
        
        # Move up internal step
        self.current_step_idx += 1
        
        # Check scenario complete
        if self.current_step_idx == 4:
            self.feedback_section.text = "🎉 Scenario Complete"
            self.feedback_section.color = (0.2, 0.2, 0.8, 1)
            self.current_scenario_idx += 1
            
            # Load next scenario smoothly
            Clock.schedule_once(self.load_current_scenario, 2.0)

    def wrong_drop(self):
        # Update Feedback "Try Again"
        self.feedback_section.text = "❌ Try Again"
        self.feedback_section.color = (0.8, 0.2, 0.2, 1)
        
        # Reset specific local step tracker
        self.current_step_idx = 0
        
        # Reset UI
        self.reset_slots()
        
        # Safely reshuffle everything again
        self.create_and_shuffle_tasks()

    def _go_home(self, *args):
        app = App.get_running_app()
        if app and app.root and hasattr(app.root, 'current'):
            app.root.current = 'games'


class RoutineGameScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        # Ensure correct background color is set when entering this screen
        Window.clearcolor = (0.92, 0.96, 0.98, 1)
        self.add_widget(GameScreen())


class RoutineApp(App):
    def build(self):
        return GameScreen()

if __name__ == '__main__':
    try:
        RoutineApp().run()
    except Exception as e:
        print(f"Application error: {e}")
