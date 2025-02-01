#Libraries
import pygame

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
              "YELLOW":(255,255,0)}

    FONT_LARGE = pygame.font.Font("8-BIT WONDER.TTF",32)
    FONT_MEDIUM = pygame.font.Font("8-BIT WONDER.TTF",28)
    FONT_SMALL = pygame.font.Font("8-BIT WONDER.TTF",18)

    #Load constant images
    BG_IMG = pygame.image.load("Background/background.png")

    def __init__(self):
        #Assign instance to class variable
        Game.instance = self

        #Available buttons
        self.buttons = {
            "MENU" : [
                Button("PLAY",self.FONT_MEDIUM, "WHITE", (140,300)),
                Button("OPTIONS",self.FONT_MEDIUM, "WHITE", (110,375)),
                Button("ARMOURY",self.FONT_MEDIUM, "WHITE", (95,450)),
                Button("HELP",self.FONT_MEDIUM, "WHITE", (140,525))],

            "BACK" : Button("BACK",self.FONT_MEDIUM, "WHITE", (10,500))
            }
        
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
        

    def text(self, message, font, color, pos):
        #Create text surface and rect 
        text_surface = font.render(message, True, (self.COLORS[color]))
          
        #Render text
        self.screen.blit(text_surface, pos)


    def set_screen_size(self, width):
        self.width = width
        self.screen = pygame.display.set_mode((self.width, self.height))

    
    def handle_background(self):
        #Increment position downwards
        self.BG_y += 0.5

        #Check if reached top edge of screen
        if self.BG_y >= 0:
            #Reset Y value to -600
            self.BG_y = self.BG_default_y

            
    def run(self):
        while self.running:
            #Resize screen for armoury state
            if self.current_state == "ARMOURY" and self.width != 800:
                self.set_screen_size(800)
                
            elif self.current_state != "ARMOURY" and self.width != 400:
                self.set_screen_size(400)

                
            #Executes events of current state
            self.process_events()

            #Display Backgrounds
            if self.current_state != "ARMOURY":
                self.screen.blit(self.BG_IMG, (0, self.BG_y))
                self.handle_background()
                
            else:
                self.screen.fill(self.COLORS["bg_color"])
            
            #Display Headings
            if self.current_state != "MENU" and self.current_state != "PLAY":
                    self.text(self.current_state,self.FONT_LARGE, "WHITE", (10,30))

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
        #Get Mouse coordinates
        self.mx, self.my = pygame.mouse.get_pos()

    def menu(self):
        #Menu logic
        self.text("COSMIC CONFLICT",self.FONT_MEDIUM, "YELLOW", (8,30))
        self.text("HIGHSCORE 0",self.FONT_SMALL, "WHITE", (100,100))

        #Load and display menu buttons
        for b in self.buttons["MENU"]:
            b.update()
       

    def play(self):
        #Play logic 
        pass
    
    def options(self):
        #Options logic 
        self.buttons["BACK"].update()
        
    def armoury(self):
        #Armoury logic
        self.buttons["BACK"].update()
        
        
    def help(self):
        #Help Logic
        self.buttons["BACK"].update()
        
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

#-----------------------------------------------------------------------------------------------------------------------------------------------
class Button():
    def __init__(self, message, font, color, pos):
        
        #Custom attributes
        self.message = message
        self.font = font
        self.color = color
        self.pos = pos

        #Default attributes 
        self.button_surface = font.render(message, True, (Game.instance.COLORS[color]))
        self.rect = self.button_surface.get_rect(topleft = (pos))
        
    def update(self):
        self.handle_button_press()
        self.render_button()

    def handle_button_press(self):
        #Default color if when not hovering over button
        self.button_surface = self.font.render(self.message, True, (Game.instance.COLORS[self.color]))

        #Check if mouse is hovering over button
        if self.rect.collidepoint(Game.instance.mx, Game.instance.my):

            #Highlight button different color for usability
            self.button_surface = self.font.render(self.message,False,(Game.instance.COLORS["YELLOW"]))

            #Check if user presses LMB
            if Game.instance.click:
                #Dynamically check if message is in self.states

                for key in Game.instance.states:
                    if self.message == key:
                        Game.instance.current_state = key
                    
                    #Return user to menu
                    elif self.message == "BACK":
                        Game.instance.current_state = "MENU"

    def render_button(self):
        Game.instance.screen.blit(self.button_surface, self.pos)

#-----------------------------------------------------------------------------------------------------------------------------------------------

g = Game()
g.run()

