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
    

    FONT_LARGE = pygame.font.Font("assets/8-BIT WONDER.TTF",32)
    FONT_MEDIUM = pygame.font.Font("assets/8-BIT WONDER.TTF",28)
    FONT_SMALL = pygame.font.Font("assets/8-BIT WONDER.TTF",18)

    #Load constant images
    BG_IMG = pygame.image.load("assets/background/background.png")

    #Load JSON file that stores game text
    def load_json_text(filename):
        with open(filename, "r") as file:
            return json.load(file)  
        
    #Dynamically load all ships for armoury
    SHIP_LIST = [pygame.image.load(f"assets/playerships/ship{i}.png") for i in range(1,7)] 
    
    #Load bullet types for player/enemy
    BULLET_LIST = {"player" : pygame.image.load("assets/bullets/player_bullet.png"), 
                   "enemy" : pygame.image.load("assets/bullets/enemy_bullet.png")}
    
    SHIP_DATA = load_json_text("data/game_text.json")

    #Define pygame groups
    bullet_group = pygame.sprite.Group()
    enemy_group = pygame.sprite.Group()

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

            "BACK" : TextButton("BACK",self.FONT_MEDIUM, "WHITE", (10,525))
            }

        #Horizontal pixel spacing width
        spacing = 130
        #Available image buttons
        self.image_buttons = {
            "ARMOURY": [ImageButton(img, f"SHIP{Game.SHIP_LIST.index(img) + 1}", ((Game.SHIP_LIST.index(img) * spacing), 130), "ship") for img in Game.SHIP_LIST],
            }
          
        self.selected_ship_description = Game.instance.SHIP_DATA.get("SHIP1")
      
        #Initialise default player ship
        self.player = Player("SHIP1")
   
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
        self.player.update()
       
        #Update and draw sprite groups
        self.bullet_group.draw(self.screen)
        self.bullet_group.update()

    
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

class Player(pygame.sprite.Sprite):
    #Dynamically load player ships with correct hitbox size
    PLAYER_SHIP_LIST = [pygame.image.load(f"assets/playerships/player{i}.png") for i in range(1,7)] 

    BULLET_PATTERNS = {
                "SHIP1": [(0, 0)],
                "SHIP2": [(0, 0)],
                "SHIP3": [(-25, 0, 'NW'), (25, 0, 'NE')],
                "SHIP4": [(-35, 0), (35, 0)],
                "SHIP5": [(0, 0), (-35, 25, 'NW'), (35, 25, 'NE')],
                "SHIP6": [(0, 0)]
            }
    
    def __init__(self, selected_ship):
        super().__init__()
        #Player ship attributes
        self.selected_ship = selected_ship
        self.speed = Game.instance.selected_ship_description["speed"] // 10
        self.ammo = Game.instance.selected_ship_description["ammo"]
        self.lives = Game.instance.selected_ship_description["lives"]
        self.type = Game.instance.selected_ship_description["type"]
        self.fire_rate = Game.instance.selected_ship_description["fire rate"] * 10
        self.bullet_speed = Game.instance.selected_ship_description["bullet speed"]
        
        # Determine the correct ship image index based on selection
        index = list(Game.instance.SHIP_DATA).index(self.selected_ship)
        self.image = Player.PLAYER_SHIP_LIST[index]

        #Player ship defaults
        default_pos = (200,500)
        self.rect = self.image.get_rect(center=default_pos)
    
        self.previous_time = pygame.time.get_ticks()

    def update(self):
        key = pygame.key.get_pressed()  # Returns tuple of bools for keys pressed
        self.handle_movement(key)
        self.shoot_bullet(key)
        self.render()

    def handle_movement(self, key):
        #Check for key press and if within screen bounds
        if key[pygame.K_a]: 
            self.rect.x -= self.speed  
            if self.rect.x < -self.rect.width:  # Off the left edge
                self.rect.x = Game.instance.width  # Reappear on the right
     
        if key[pygame.K_d]: 
            self.rect.x += self.speed
            if self.rect.x > Game.instance.width:  # Off the right edge
                self.rect.x = -self.rect.width  # Reappear on the left
      
        if key[pygame.K_w] and self.rect.y > 0: 
            self.rect.y -= self.speed
        if key[pygame.K_s] and self.rect.y < Game.instance.height - self.rect.width: 
            self.rect.y += self.speed

    def shoot_bullet(self, key):       
       # Check if the spacebar is pressed
        if key[pygame.K_SPACE]:
            # Get the current time in milliseconds
            current_time = pygame.time.get_ticks()

            # Check if enough time has passed since the last shot 
            if current_time - self.previous_time > self.fire_rate:
                self.previous_time = current_time
               
                for pattern in Player.BULLET_PATTERNS[self.selected_ship]:
                    x, y, *direction = pattern  # Unpack tuple, direction is optional
                    bullet = Bullet(self.rect.x + x, self.rect.y + y, self.bullet_speed, True, *direction)
                    Game.instance.bullet_group.add(bullet)

                self.ammo -= 1
                    
               
    def render(self):
        Game.instance.screen.blit(self.image, self.rect)  # Draw player sprite


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
    def __init__(self, img, button_name, pos, on_click_action=None):
        super().__init__(pos)
        #Default attributes
        self.button_surface = img
        self.button_rect = self.button_surface.get_rect(topleft=pos)
        self.button_name = button_name
        self.on_click_action = on_click_action
   
    def on_hover(self):
        #Increase transparency of surface
        self.button_surface.set_alpha(100)
        #Set ship description to correct ship attribute dictionary
        if self.on_click_action == "ship":
            Game.instance.selected_ship_description = Game.instance.SHIP_DATA.get(self.button_name)
            self.draw_ship_description()

    def on_unhover(self):
        self.button_surface.set_alpha(255)
    
    # Display the selected ship's description
    def draw_ship_description(self):
        x,y = 10, 300
        for key, value in Game.instance.selected_ship_description.items():
            ship_text = f"{key}  {value}"
            Game.instance.text(ship_text, Game.instance.FONT_SMALL, "WHITE", (x, y))
            y += 30
    

    def on_click(self):
        if self.on_click_action == "ship":
            print(Game.instance.SHIP_DATA.get(self.button_name))
            Game.instance.player = Player(self.button_name)
    
class TextButton(Button):
    def __init__(self, message, font, color, pos):
        super().__init__(pos)
        #Default attributes
        self.message = message
        self.font = font
        self.color = color
        self.button_surface = self.font.render(self.message,False,(Game.instance.COLORS["WHITE"]))
        self.button_rect = self.button_surface.get_rect(topleft=(pos))
    
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

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed, is_player=True, direction=None):
        super().__init__()
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = speed
        self.is_player = is_player # True by default

        if not is_player:
            self.image = Game.instance.BULLET_LIST["enemy"]
        else:
            self.image = Game.instance.BULLET_LIST["player"]
    
            #Rotate image if direction is specified
            if self.direction == "NW":
                self.image = pygame.transform.rotate(self.image, 15) # Rotate 15 degrees anticlockwise
            elif self.direction == "NE":
                self.image = pygame.transform.rotate(self.image, -15) # Rotate 15 degrees clockwise
        
        
        self.rect = self.image.get_rect(center = ((x + Game.instance.player.rect.width//2), y))
    
    def update(self):
        self.handle_trajectory()
    
    def handle_trajectory(self):
        # Moves the bullet straight up
        self.rect.y -= self.speed 
       
        # Apply horizontal movement to bullets 
        if self.direction == "NW":
            self.rect.x -= 2  # Move left
       
        elif self.direction == "NE":
            self.rect.x += 2 # Move right
            
    
    def handle_collision(self):
        if pygame.sprite.groupcollide(Game.instance.bullet_group, Game.instance.enemy_group, True, True):
            Game.instance.player.ammo += 2


g = Game()
g.run()
