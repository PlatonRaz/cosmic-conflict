#Libraries
import pygame, json

#Initialise all pygame modules
pygame.init()

#-----------------------------------------------------------------------------------------------------------------------------------------------

class Game():
    #Define class variables
    instance = None
    
    #Class level constants
    COLORS = {"bg_color":(38,33,56),
              "RED":(255,0,0),
              "WHITE":(255,255,255),
              "GREEN":(0,255,0),
              "YELLOW":(255,255,0)
              }
    

    FONT_LARGE = pygame.font.Font("8-BIT WONDER.TTF",32)
    FONT_MEDIUM = pygame.font.Font("8-BIT WONDER.TTF",28)
    FONT_SMALL = pygame.font.Font("8-BIT WONDER.TTF",18)

    #Load constant images
    BG_IMG = pygame.image.load("Background/background.png")

    #Load JSON file that stores game text
    def load_json_text(filename):
        with open(filename, "r") as file:
            return json.load(file)  
        
    #Dynamically load all ships for armoury
    SHIP_LIST = [pygame.image.load(f"Player Ships/ship{i}.png") for i in range(1,7)] 

    SHIP_DATA = load_json_text("game_text.json")

    def __init__(self):
        #Assign instance to class variable
        Game.instance = self
        #Window dimensions
        self.width = 400
        self.height = 600

        #Screen initialisation
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        
        #Game states
        self.states = {
            "MENU": [self.menu, self.menu_event_handler],
            "PLAY": [self.play,self.play_event_handler],
            "OPTIONS": [self.options,self.options_event_handler],
            "ARMOURY": [self.armoury,self.armoury_event_handler],
            "HELP": [self.help,self.help_event_handler]}

        #Default game control attributes
        self.current_state = "MENU"
        self.running = True
        self.click = False

        #Background attributes
        self.BG_default_y = -self.BG_IMG.get_height()/2
        self.BG_y = self.BG_default_y

        #Available buttons
        self.text_buttons = {
            "MENU" : [
                TextButton("PLAY",self.FONT_MEDIUM, "WHITE", (140,300)),
                TextButton("OPTIONS",self.FONT_MEDIUM, "WHITE", (110,375)),
                TextButton("ARMOURY",self.FONT_MEDIUM, "WHITE", (95,450)),
                TextButton("HELP",self.FONT_MEDIUM, "WHITE", (140,525))],

            "BACK" : TextButton("BACK",self.FONT_MEDIUM, "WHITE", (10,500))
            }

        #Horizontal pixel spacing width
        spacing = 130
        #Available image buttons
        self.image_buttons = {
            "ARMOURY": [ImageButton(img, f"SHIP{Game.SHIP_LIST.index(img) + 1}", ((Game.SHIP_LIST.index(img) * spacing), 130)) for img in Game.SHIP_LIST],
            }
        self.selected_ship_description = ""
    # Retrieve text from JSON based on category and key
    def get_text(self, category, key):
        return Game.SHIP_DATA.get(category, {}).get(key, "No description available.")
        
    #Create non-button text 
    def text(self, message, font, color, pos):
        #Create text surface and rect 
        text_surface = font.render(message, True, (self.COLORS[color]))
        #Render text
        self.screen.blit(text_surface, pos)

    def set_screen_size(self, width):
        self.width = width
        self.screen = pygame.display.set_mode((self.width, self.height))

    #Immersive background logic
    def move_background(self):
        #Increment position downwards
        self.BG_y += 0.5
        #Check if reached top edge of screen
        if self.BG_y >= 0:
            #Reset Y value to -600
            self.BG_y = self.BG_default_y
    
    def global_UI_elements(self):
        #Display backgrounds for current states
        if self.current_state != "ARMOURY":
            self.screen.blit(self.BG_IMG, (0, self.BG_y))
            self.move_background()
        else:
            self.screen.fill(self.COLORS["bg_color"])
        #Display headings for current state
        if self.current_state != "MENU" and self.current_state != "PLAY":
            self.text(self.current_state,self.FONT_LARGE, "WHITE", (10,30))

    def run(self):
        while self.running:
            #Executes events of current state
            self.process_events()
            #Manages global UI elements
            self.global_UI_elements()
            #Executes logic of current state
            self.states[self.current_state][0]()
            #Render and update screen
            self.global_render()
            
        pygame.quit()
        
    def process_events(self):
         for event in pygame.event.get():
            #Global event handling
            if event.type == pygame.QUIT:
                self.running = False

            #State-specific event handling
            self.states[self.current_state][1](event)

    #Global rendering
    def global_render(self):
        pygame.display.update()
        self.clock.tick(60)

    def mouse_click_event(self, event):
        self.get_mouse_pos()
        
        #Check for LMB press
        self.click = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.click = True

    def get_mouse_pos(self):
        #Get mouse coordinates
        self.mx, self.my = pygame.mouse.get_pos()

    def menu(self):
        #Menu logic
        self.text("COSMIC CONFLICT",self.FONT_MEDIUM, "YELLOW", (8,30))
        self.text("HIGHSCORE 0",self.FONT_SMALL, "WHITE", (100,100))

        #Load and display menu buttons
        for button in self.text_buttons["MENU"]:
            button.update()
       

    def play(self):
        #Play logic 
        pass
    
    #Options Logic
    def options(self):
        #Options UI 
        self.text_buttons["BACK"].update()
            #Options Logic

    #Armoury Logic
    def armoury(self):
        #Armoury UI
        self.text("select ship", self.FONT_SMALL, "WHITE", (10,80))
        self.text_buttons["BACK"].update()
        #Display Ships
        for ship in self.image_buttons["ARMOURY"]:
            ship.update()
            
        #Resize screen for armoury state
        if self.current_state == "ARMOURY" and self.width != 800:
            self.set_screen_size(800)
        #Reset screen to default width 
        elif self.current_state != "ARMOURY" and self.width != 400:
            self.set_screen_size(400)
        
    #Help Logic
    def help(self):
        #Help UI
        self.text_buttons["BACK"].update()
        
    def menu_event_handler(self, event):
        self.mouse_click_event(event)
    
    def play_event_handler(self, event):
        pass
    
    def options_event_handler(self, event):
        self.mouse_click_event(event)

    def armoury_event_handler(self, event):
        self.mouse_click_event(event)

    def help_event_handler(self, event):
        self.mouse_click_event(event)

class Button():
    def __init__(self, pos):
        #Custom attributes
        self.pos = pos

    def update(self):
        self.handle_button_press()
        self.render_button()

    def handle_button_press(self):
        #On_unhover() logic implemented by child classes
        self.on_unhover()
        #Check if mouse is hovering over button
        if self.button_rect.collidepoint(Game.instance.mx, Game.instance.my):
            #On_hover() logic implemented by child classes
            self.on_hover()
            #Check if user presses LMB
            if Game.instance.click:
                #On_click() logic implemented by child classes
                self.on_click() 

    def render_button(self):
        #Display button on-screen
        Game.instance.screen.blit(self.button_surface, self.pos)

class ImageButton(Button):
    def __init__(self, img, button_name, pos):
        super().__init__(pos)
        #Default attributes
        self.button_surface = img
        self.button_rect = self.button_surface.get_rect(topleft = pos)
        self.button_name = button_name
   
    def on_hover(self):
        #Increase transparency of surface
        self.button_surface.set_alpha(100)
        #Set ship description to correct ship attribute dictionary
        Game.instance.selected_ship_description = Game.instance.SHIP_DATA.get(self.button_name)
        self.draw_ship_description()
   
    # Display the selected ship's description
    def draw_ship_description(self):
        x,y = 10, 300
        for key, value in Game.instance.selected_ship_description.items():
            ship_text = f"{key}  {value}"
            Game.instance.text(ship_text, Game.instance.FONT_SMALL, "WHITE", (x, y))
            y += 30
    

    def on_click(self):
        pass
    

    def on_unhover(self):
        self.button_surface.set_alpha(255)
    

class TextButton(Button):
    def __init__(self, message, font, color, pos):
        super().__init__(pos)
        #Default attributes
        self.message = message
        self.font = font
        self.color = color
        self.button_surface = self.font.render(self.message,False,(Game.instance.COLORS["WHITE"]))
        self.button_rect = self.button_surface.get_rect(topleft = (pos))
    
    def on_click(self):
        #Dictionary lookup
        if self.message in Game.instance.states:
            Game.instance.current_state = self.message
        elif self.message == "BACK":
            Game.instance.current_state = "MENU"

    def on_hover(self):
        #Highlight button different color for usability
        self.button_surface = self.font.render(self.message,False,(Game.instance.COLORS["YELLOW"]))

    def on_unhover(self):
        #Rest button to white when not hovering
        self.button_surface = self.font.render(self.message,False,(Game.instance.COLORS["WHITE"]))

g = Game()
g.run()

