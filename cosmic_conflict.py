#Libraries
import pygame, json, random, os
from os import path 

#Initialise all pygame modules
pygame.init()
#-----------------------------------------------------------------------------------------------------------------------------------------------

# Class to handle loading and storing high score data  
class Data():  
    hs_file = "highscore.txt"  # File to store the high score  

    def __init__(self):  
        # Initializes the Data object and loads high score data. 
        root = path.dirname(__file__)  # Gets the directory where cosmic_conflict.py is located  
        self.data_dir = path.join(root, "data")
        self.load_data()  

    def load_data(self):  
        # Loads high score data from the file or creates a new file if it doesn't exist 
        os.makedirs(self.data_dir, exist_ok=True)  # Creates 'data' folder if it doesn't exist
     
        try:  
            # Open and read the high score file  
            with open(path.join(self.data_dir, Data.hs_file), "r+") as f: 
                contents = f.read()
                if not contents.isdigit():
                    self.highscore = 0 # Default high-score to 0 if file is corrupt (contains strings)
                else:
                    self.highscore = int(contents)
        except:  
            # If file doesn't exist or error occurs, create new file in folder
            with open(path.join(self.data_dir, Data.hs_file), 'w'):  
                self.highscore = 0  
  
    def write_highscore(self):
        # Only update if current score is higher than highscore
        if Game.instance.player.score > self.highscore:
            self.highscore = Game.instance.player.score
            if self.highscore < 99999: # Prevent highscore overflows 
                with open(path.join(self.data_dir, Data.hs_file), "w") as f:
                    f.write(str(self.highscore))

class Cursor(pygame.sprite.Sprite):
    def __init__(self, picture_path):
        super().__init__()
        self.image = pygame.image.load(picture_path)
        self.rect = self.image.get_rect()
        pygame.mouse.set_visible(False) # Hide default mouse 

    def update(self):
        # Update position of sprite to follow mouse position
        self.rect.center = pygame.mouse.get_pos() 
        self.render()

    def render(self):
        Game.instance.screen.blit(self.image, self.rect)

class Game():
    #Define class variables
    instance = None
    GAME_OVER = False
    #Class level constants
    COLORS = {"bg_color":(38,33,56),
              "RED":(255,0,0),
              "WHITE":(255,255,255),
              "GREEN":(0,255,0),
              "YELLOW":(255,255,0),
              "ORANGE":(255, 180, 0)
              }
    

    FONT_LARGE = pygame.font.Font("assets/8-BIT WONDER.TTF",32)
    FONT_MEDIUM = pygame.font.Font("assets/8-BIT WONDER.TTF",28)
    FONT_SMALL = pygame.font.Font("assets/8-BIT WONDER.TTF",18)

    #Load constant images
    BG_IMG = {"BG" : pygame.image.load("assets/background/background.png"),
              "OVERLAY" : pygame.image.load("assets/background/bg_overlay.png")}
    

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
   
    # Default configuration for game settings
    CONFIG = {
        "music": True,
        "sound": True,
        "HUD": True,
        "wrapping" : False
        }

    # Pygame groups
    bullet_enemy_group = pygame.sprite.Group()
    bullet_player_group = pygame.sprite.Group()
    
    enemy_group = pygame.sprite.Group()
    player_group = pygame.sprite.Group()
    planet_group = pygame.sprite.Group()
    powerup_group = pygame.sprite.Group()
    effect_group = pygame.sprite.Group()

    GROUPS = [planet_group, enemy_group, bullet_player_group, bullet_enemy_group, player_group, powerup_group, effect_group      ]

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
            "HELP": [self.help,self.help_event_handler],
            "PAUSE": [self.pause, self.pause_event_handler]}


        # Default game control attributes
        self.current_state = "MENU"
        self.running = True
        self.click = False

        # Background attributes
        self.BG_default_y = -self.BG_IMG["BG"].get_height()/2
        self.BG_default_x = -self.BG_IMG["BG"].get_width()/3
        self.BG_y = self.BG_default_y
        self.BG_x = self.BG_default_x
        # Available buttons
        self.text_buttons = {
            "MENU" : [
                TextButton("PLAY", Game.FONT_MEDIUM, Game.COLORS["WHITE"], (140,300)),
                TextButton("OPTIONS", Game.FONT_MEDIUM, Game.COLORS["WHITE"], (110,375)),
                TextButton("ARMOURY", Game.FONT_MEDIUM, Game.COLORS["WHITE"], (95,450)),
                TextButton("HELP", Game.FONT_MEDIUM, Game.COLORS["WHITE"], (140,525))],

            "BACK" : TextButton("BACK", Game.FONT_MEDIUM, Game.COLORS["WHITE"], (10,525)),
            
            "OPTIONS": [
                    TextButton(
                        f"{setting} enabled" if Game.CONFIG[setting] else f"{setting} disabled",
                        Game.FONT_SMALL,
                        Game.COLORS["GREEN"] if Game.CONFIG[setting] else Game.COLORS["RED"],
                        (10, (100 + list(Game.CONFIG).index(setting) * 40))
                    )
                    for setting in Game.CONFIG],
            "PAUSE": [
                TextButton("PAUSED", Game.FONT_LARGE, Game.COLORS["YELLOW"], (105,165)),
                TextButton("RESUME ( P )", Game.FONT_MEDIUM, Game.COLORS["WHITE"], (55,250)),
        ]


            }

        # Horizontal pixel spacing width
        spacing = 130
        # Available image buttons
        self.image_buttons = {
            "ARMOURY": [ImageButton(img, f"SHIP{Game.SHIP_LIST.index(img) + 1}", ((Game.SHIP_LIST.index(img) * spacing), 130), "ship") for img in Game.SHIP_LIST],
            }
          
        self.selected_ship_description = Game.instance.SHIP_DATA.get("SHIP1")
      
        # Initialise default player ship
        self.player = Player("SHIP1")
        self.player_group.add(self.player)
        self.data = Data()
        self.cursor = Cursor("assets/misc/cursor.png")
        self.initialise_planets()
        self.initialise_hearts()
        self.initialise_bullets()

        # Wave System Attributes
        self.current_wave = 0
        self.wave_timer = 0  
        self.wave_duration = 0
        self.in_wave = False
        self.enemies_spawned = False
        
        self.last_spawn_time = 0
        self.spawn_interval = 1700 # ms
       
        self.waves = [
            self.wave_1, # Spawm Standard Enemies 
            self.wave_2  # Spawn 6 Diagonal Enemies
            ]
        

        self.WAVE_EVENT = pygame.USEREVENT + 0
        pygame.time.set_timer(self.WAVE_EVENT, 1000)
        
        self.POWER_UP = pygame.USEREVENT + 1
        pygame.time.set_timer(self.POWER_UP, 5000)

    def wave_1(self):        
        # Initial setup when wave starts
        if self.wave_timer == 0:
            self.wave_duration = 15  # seconds
        
        # Spawning logic
        current_time = pygame.time.get_ticks()
        if current_time - self.last_spawn_time >= self.spawn_interval:
            enemy = StandardEnemy()
            self.enemy_group.add(enemy)
            self.last_spawn_time = current_time
        
        # Completion conditions
        if self.wave_timer >= self.wave_duration:
            return True
        return False
    
    def wave_2(self):
        # Initial setup when wave starts
        if self.wave_timer == 0:
            self.wave_duration = 30  # seconds
        
            # Spawn formation 
            x, y = 30, 50
            x2, y2 = 200, -250
        
        if not self.enemies_spawned:
             # Left group
            for _ in range(3):
                enemy = DiagonalEnemy(x, y)
                y -= 100
                x += 85
                self.enemy_group.add(enemy)
            
            # Right group
            for _ in range(3):
                enemy = DiagonalEnemy(x2, y2)
                y2 -= 100
                x2 += 85
                self.enemy_group.add(enemy)
            
            self.enemies_spawned = True
        
        # Completion conditions
        if len(self.enemy_group) == 0 or self.wave_timer >= self.wave_duration:  
            return True
        return False

    # Create non-button text 
    def text(self, message, font, color, pos):
        #Create text surface and rect 
        text_surface = font.render(message, True, (self.COLORS[color]))
        # Render text
        self.screen.blit(text_surface, pos)

    def set_screen_size(self, width):
        self.width = width
        self.screen = pygame.display.set_mode((self.width, self.height))
    
    # Immersive background logic
    def move_background(self):
        self.BG_y += 0.5

        """
        key = pygame.key.get_pressed()
        # Check if the player is touching the bottom edge
        touching_bottom = self.player.rect.bottom > self.height

        # If 'S' is pressed and player is NOT touching the bottom edge then move up (-0.6)
        if key[pygame.K_s] and not touching_bottom:
            self.BG_y -= 0.6
        else:
            # In all other cases, move down by 0.5
            self.BG_y += 0.5
        # Handle other movement keys
        if key[pygame.K_d]:
            self.BG_x -= 0.5
        if key[pygame.K_w]:
            self.BG_y += 0.5
        if key[pygame.K_a]:
            self.BG_x += 0.5
    

        # Check if reached side edges
        if self.BG_x <= -800:
            self.BG_x = self.BG_default_x
      
        elif self.BG_x >= 0:
            self.BG_x = self.BG_default_x
        """
        # Check if reached top edge of screen
        if self.BG_y >= 0:
            #Reset Y value to -600
            self.BG_y = self.BG_default_y
    
    def global_UI_elements(self):
        # Display backgrounds for current states
        if self.current_state != "ARMOURY":
            self.screen.blit(self.BG_IMG["BG"], (self.BG_x, self.BG_y))
            self.move_background()       
        else:
            self.screen.fill(self.COLORS["bg_color"])
        # Display headings for current state
        if self.current_state != "MENU" and self.current_state != "PLAY" and self.current_state != "PAUSE":
            self.text(self.current_state,self.FONT_LARGE, "WHITE", (10,30))
        
    
    def initialise_planets(self):
        num_planets = 1
        for _ in range(num_planets):
            planet = Planet()
            self.planet_group.add(planet)
    
    def initialise_hearts(self): 

        num_hearts = self.player.lives  # Number of initial hearts corresponds to player's lives
        x_initial = 450  # Starting x coordinate for the first heart
        y_initial = 65   # Starting y coordinate for the first heart


        pos_x, pos_y = x_initial, y_initial

        for i in range(num_hearts):
            heart = Heart(pos_x, pos_y)  # Create a new heart object
            self.player.heart_stack.append(heart)  # Store the heart in the stack

            pos_x += 100  # Shift the x position of heart to the right for next heart
            
            # Every 3 hearts, reset x position and move down a row
            if (i + 1) % 3 == 0:
                pos_x = x_initial  # Reset x to initial position for a new row
                pos_y += 100  # Move hearts down to the next row
    
    def initialise_bullets(self): 
        num_bullets = self.player.ammo  # Number of initial bullets corresponds to player's ammo
        x_initial = 465  # Starting x coordinate for the first bullet
        y_initial = 470  # Starting y coordinate for the first bullet
        x_spacing, y_spacing = 40, 15

        pos_x, pos_y = x_initial, y_initial

        for i in range(num_bullets):
            bullet = Bullet(pos_x, pos_y, 0)  # Create a new bullet object
            self.player.bullet_stack.append(bullet)  # Store the bullet in the stack
            self.bullet_player_group.add(bullet)
            pos_y += y_spacing  # Shift the y position of the bullet downward for the next bullet

            # Every 6 bullets, reset y position and move right to form a new column
            if (i + 1) % 6 == 0:
                pos_y = y_initial  # Reset y to initial position for a new column
                pos_x += x_spacing  # Move bullets to the right to start a new column


    def run(self):
        while self.running:
            # Executes events of current state
            self.process_events()
            # Manages global UI elements
            self.global_UI_elements()
            # Executes logic of current state
            self.states[self.current_state][0]()
            # Render and update screen
            self.global_render()
            
        pygame.quit()
        
    def process_events(self):
         for event in pygame.event.get():
            # Global event handling
            if event.type == pygame.QUIT:
                self.running = False

            # State-specific event handling
            self.states[self.current_state][1](event)

    # Global rendering
    def global_render(self):
        pygame.display.update()
        self.clock.tick(60)

    def mouse_click_event(self, event):
        self.get_mouse_pos()
        
        # Check for LMB press
        self.click = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.click = True

    def get_mouse_pos(self):
        # Get mouse coordinates
        self.mx, self.my = pygame.mouse.get_pos()

    def display_HUD(self):
        if Game.CONFIG["HUD"] and self.width != 700:
            self.set_screen_size(700)
        
        self.screen.blit(Game.BG_IMG["OVERLAY"], (400, 0))
        
        self.text("LIVES", self.FONT_SMALL, "WHITE", (512, 15))
        self.text("HI SCORE", self.FONT_SMALL, "WHITE", (485, 215))
        self.text(str(self.data.highscore), self.FONT_LARGE, "ORANGE", (567, 260))
        self.text(str(self.player.score), self.FONT_SMALL, "WHITE", (575, 330))

        self.text("AMMO", self.FONT_SMALL, "WHITE", (500, 420))
        
        for bullet in self.player.bullet_stack:
            bullet.update()
        
        for heart in self.player.heart_stack:
            heart.update()
       
    def menu(self):
        # Menu logic
        self.text("COSMIC CONFLICT",self.FONT_MEDIUM, "YELLOW", (8,30))
        self.text(f"HIGH SCORE {self.data.highscore}",self.FONT_SMALL, "WHITE", (100,100))

        # Load and display menu buttons
        for button in self.text_buttons["MENU"]:
            button.update()
        #Update and render position of cursor
        self.cursor.update()
        
    def play(self):
        # Play logic 
        if self.GAME_OVER:
            self.player.kill()
        # Update and draw sprite groups

        for group in self.GROUPS:
            group.update()
       
        self.display_HUD()
        
    # Options Logic
    def options(self):
        #Options UI 
        for button in self.text_buttons["OPTIONS"]:
            button.update()
            
        
        self.text_buttons["BACK"].update()
        #Update and render position of cursor
        self.cursor.update()

    # Armoury Logic
    def armoury(self):
        # Armoury UI
        self.text("select ship", self.FONT_SMALL, "WHITE", (10,80))
        self.text_buttons["BACK"].update()
        # Display Ships
        for ship in self.image_buttons["ARMOURY"]:
            ship.update()
            
        # Resize screen for armoury state
        if self.current_state == "ARMOURY" and self.width != 800:
            self.set_screen_size(800)
        # Reset screen to default width 
        elif self.current_state != "ARMOURY" and self.width != 400:
            self.set_screen_size(400)
        #Update and render position of cursor
        self.cursor.update()
    # Help Logic
    def help(self):
        # Help UI
        self.text_buttons["BACK"].update()
        #Update and render position of cursor
        self.cursor.update()
    
    # Pause Logic
    def pause(self):
        if self.width != 400:
            self.set_screen_size(400)
        # Create semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))  # Semi-transparent black
        self.screen.blit(overlay, (0, 0))
        
        # Show pause UI using buttons from dictionary
        for button in self.text_buttons["PAUSE"]:
            button.update()
    
    def menu_event_handler(self, event):
        
        self.mouse_click_event(event)
    
    def play_event_handler(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
            self.current_state = "PAUSE"
            return
        if event.type == self.WAVE_EVENT:
            self.wave_timer += 1
    
            # If not in a wave, start the next one
            if not self.in_wave:
                if self.current_wave < len(self.waves):
                    self.in_wave = True
                    self.wave_timer = 0
                    self.enemies_spawned = False
                    self.last_spawn_time = pygame.time.get_ticks()
                   
            # Process current wave
            if self.in_wave:
                wave_completed = self.waves[self.current_wave]()
                
                if wave_completed:
                    self.in_wave = False
                    self.current_wave += 1
                    
                    if self.current_wave >= len(self.waves):
                        self.current_wave = 0  # Loop back to first wave
        
        if event.type == self.POWER_UP:

            if self.player.lives < 3:
                life = LifePowerUp()
                self.powerup_group.add(life)

    def options_event_handler(self, event):
        self.mouse_click_event(event)

    def armoury_event_handler(self, event):
        self.mouse_click_event(event)

    def help_event_handler(self, event):
        self.mouse_click_event(event)
    
    
    def pause_event_handler(self, event):
        # Handle key press to resume
        if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
            self.current_state = "PLAY"
        
        
                  

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
        self.max_lives = self.lives
        self.score = 0
        # Determine the correct ship image index based on selection
        index = list(Game.instance.SHIP_DATA).index(self.selected_ship)
        self.image = Player.PLAYER_SHIP_LIST[index]

        #Player ship defaults
        default_pos = (200,500)
        self.rect = self.image.get_rect(center=default_pos)
    
        self.previous_time = pygame.time.get_ticks()
        
        self.heart_stack = []
        self.bullet_stack = []

    def update(self):
        key = pygame.key.get_pressed()  # Returns tuple of bools for keys pressed
        self.handle_movement(key)
        self.shoot_bullet(key)
        self.render()

    def handle_movement(self, key):
        # Check for key press and movement based on wrapping setting
        if key[pygame.K_a]:  
            self.rect.x -= self.speed  

            if Game.instance.CONFIG["wrapping"]:  # Wrapping logic
                if self.rect.right < 0:  # If off-screen on the left side
                    self.rect.x = 400  # Wrap to right side
                    if key[pygame.K_w]:  # If pressing W, move to bottom
                        self.rect.y = Game.instance.height - (self.rect.height + 15)

            elif self.rect.x < 0:  # If wrapping is off, prevent moving past the left edge
                self.rect.x = 0  # Restrict player to left edge

        if key[pygame.K_d]:  
            self.rect.x += self.speed  

            if Game.instance.CONFIG["wrapping"]:  # Wrapping logic
                if self.rect.x > 400:  # If off-screen on the right side
                    self.rect.x = -self.rect.width  # Wrap to left side
                    if key[pygame.K_w]:  # If pressing W, move to bottom
                        self.rect.y = Game.instance.height - (self.rect.height + 15)

            elif self.rect.right > 400:  # If wrapping is off, prevent moving past the right edge
                self.rect.x = 400 - self.rect.width  # Restrict player to right edge

                    

        if key[pygame.K_w] and self.rect.y > 0: 
            self.rect.y -= self.speed
        if key[pygame.K_s] and self.rect.y < Game.instance.height - self.rect.height: 
            self.rect.y += self.speed

    def shoot_bullet(self, key):       
       # Check if the spacebar is pressed
        if key[pygame.K_SPACE] and self.ammo > 0:
            # Get the current time in milliseconds
            current_time = pygame.time.get_ticks()

            # Check if enough time has passed since the last shot 
            if current_time - self.previous_time > self.fire_rate:
                self.previous_time = current_time
               
                for pattern in Player.BULLET_PATTERNS[self.selected_ship]:
                    x, y, *direction = pattern  # Unpack tuple, direction is optional
                    bullet = Bullet(self.rect.x + x, self.rect.y + y, self.bullet_speed, True, *direction)
                    Game.instance.bullet_player_group.add(bullet)
                
                self.lose_bullet()

    def gain_bullet(self):
        if self.ammo < 30:
            self.ammo += 1
            # Determine initial position 
            x_initial, y_initial = 465, 470
            bullets_per_column = 6
            x_spacing, y_spacing = 40, 15  # Spacing between bullets
            
            # Determine position of the next bullet
            bullet_count = len(self.bullet_stack)
            col = bullet_count // bullets_per_column
            row = bullet_count % bullets_per_column

            x_new = x_initial + col * x_spacing
            y_new = y_initial + row * y_spacing

            # Add new bullet
            bullet = Bullet(x_new, y_new, 0)
            self.bullet_stack.append(bullet)

    def lose_bullet(self):
        if self.bullet_stack:
            self.bullet_stack.pop()  # Remove from stack
            self.ammo -= 1

    def gain_life(self):
        if self.lives < self.max_lives:
            # First increment lives (this matches the actual count we want to display)
            self.lives += 1
            
            # Clear and rebuild the entire heart stack to ensure proper positioning
            self.heart_stack = []  # Clear existing hearts
            
            # Grid layout parameters
            x_initial, y_initial = 450, 65  # Starting position
            hearts_per_row = 3  # Number of hearts per row
            x_spacing, y_spacing = 100, 30  # Spacing between hearts
            
            # Recreate all hearts with proper positions
            for i in range(self.lives):
                row = i // hearts_per_row
                col = i % hearts_per_row
                
                x_new = x_initial + col * x_spacing
                y_new = y_initial + row * y_spacing
                
                heart = Heart(x_new, y_new)
                self.heart_stack.append(heart)

    def lose_life(self):
        if self.heart_stack:
            self.heart_stack.pop()  # Remove from stack
            self.lives -= 1
        
        if self.lives == 0:
            Game.instance.GAME_OVER = True
        
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
            # Remove old player
            Game.instance.player_group.empty()
            Game.instance.player = Player(self.button_name)
            Game.instance.player_group.add(Game.instance.player)
            # Reinitialise player health, ammo
            Game.instance.initialise_hearts()
            Game.instance.initialise_bullets()

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
        
        elif 'enabled' in self.message:
            for setting in Game.instance.CONFIG:
                if setting in self.message:
                    # Disable setting if clicked
                    Game.instance.CONFIG[setting] = False
                    self.color = Game.instance.COLORS["RED"]
                    self.message = f"{setting} disabled"
        elif 'disabled' in self.message:
            for setting in Game.instance.CONFIG:
                if setting in self.message:
                    # Enable setting if clicked
                    Game.instance.CONFIG[setting] = True
                    self.color = Game.instance.COLORS["GREEN"]
                    self.message = f"{setting} enabled"

        Game.instance.click = False       

    def on_hover(self):
        #Highlight button different color for usability
        self.button_surface = self.font.render(self.message,False,(Game.instance.COLORS["YELLOW"]))

    def on_unhover(self):
        #Rest button to white when not hovering
        self.button_surface = self.font.render(self.message,False,(self.color))

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed, is_player=True, direction=None):
        super().__init__()
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = speed
        self.is_player = is_player # True by default
        
        # Assign appropriate bullet image based on ownership
        if not is_player:
            self.image = Game.instance.BULLET_LIST["enemy"]
        else:
            self.image = Game.instance.BULLET_LIST["player"]
    
            #Rotate image if direction is specified
            if self.direction == "NW":
                self.image = pygame.transform.rotate(self.image, 15) # Rotate 15 degrees anticlockwise
            elif self.direction == "NE":
                self.image = pygame.transform.rotate(self.image, -15) # Rotate 15 degrees clockwise
        
        # Set the bullet's rectangle for positioning and collision detection
        if self.speed != 0:
            self.rect = self.image.get_rect(
                center = ((x + Game.instance.player.rect.width//2), y)
                )
        else:
            self.rect = self.image.get_rect(
                center = (x, y)
                )
    
    def update(self):
        # Updates the bullet's position according to its trajectory
        self.handle_trajectory()
        self.handle_collision()
        self.render()
 
    def handle_trajectory(self):
        # Moves the bullet straight up
        if self.is_player:
            self.rect.y -= self.speed 
        else:
            """  
            key = pygame.key.get_pressed()

            if key[pygame.K_d]:
                self.rect.x -= 1
            if key[pygame.K_w]:
                self.rect.y += 1
            if key[pygame.K_a]:
                self.rect.x += 1
            """
            self.rect.y += self.speed 

        if self.rect.y < 0:
            self.kill()

        # Apply horizontal movement to bullets 
        if self.direction == "NW":
            self.rect.x -= 2  # Move left
       
        elif self.direction == "NE":
            self.rect.x += 2 # Move right
            
    
    def handle_collision(self):
        # Handles collision detection and interaction with enemies.
        if pygame.sprite.groupcollide(Game.instance.bullet_player_group, Game.instance.enemy_group, True, True):
            # Renew player's ammo upon a destroyed enemy
            Game.instance.player.score += 1
            print(f"Enemies killed: {Game.instance.player.score}")
            Game.instance.data.write_highscore()
            Game.instance.player.gain_bullet()
            Game.instance.player.gain_bullet()
        
        elif pygame.sprite.groupcollide(Game.instance.bullet_enemy_group, Game.instance.player_group, True, False):
            Game.instance.player.lose_life()

    def render(self):
        Game.instance.screen.blit(self.image, self.rect)
            
class Planet(pygame.sprite.Sprite):
    # Load all planet images once and store them in a class-level list
    PLANET_LIST = [pygame.image.load(f"assets/planets/planet_{i}.png") 
                   for i in range(1, 5)]
   
    def __init__(self):
        super().__init__()  # Initialize the sprite class
        self.counter = 0  # Track which planet image to use
        self.generate_planet()  # Generate the initial planet attributes

    def generate_planet(self):
        #Randomly generates new attributes for the planet instance
        
        self.angle = random.randint(0, 360)  # Random rotation angle
        self.speed = 1  # Set the falling speed of the planet
    
        # Randomly determine planet scale within the  range
        lower_scale, max_scale = 1.15, 1.8
        self.scale = random.uniform(lower_scale, max_scale)
        
        # Rotate and scale the planet image
        self.image = pygame.transform.rotozoom(
            Planet.PLANET_LIST[self.counter], self.angle, self.scale
        ).convert_alpha()
        
        # Set random position at the top of the screen
        self.pos_x = random.randint(-50, 400 - (self.image.get_width()))
        self.pos_y = -self.image.get_height()

        # Get the image rectangle and set its position
        self.rect = self.image.get_rect(center=(self.pos_x, self.pos_y))
        
    def update(self):
        self.handle_movement()
        self.render()
  
    def render(self):
        Game.instance.screen.blit(self.image, (self.pos_x, self.pos_y))

    def handle_movement(self):
        """
        key = pygame.key.get_pressed()
       
         # Check if the player is touching the bottom edge
        touching_bottom = Game.instance.player.rect.bottom >= Game.instance.height

        if key[pygame.K_s] and not touching_bottom:
            self.pos_y -= self.speed
        else:
            self.pos_y += self.speed

        # Moves the planet downward and regenerates it when off-screen.
        if self.pos_y >= -self.rect.height:
           
            if key[pygame.K_a]: 
                self.pos_x +=  self.speed
            if key[pygame.K_w]: 
                self.pos_y +=  self.speed
            if key[pygame.K_d]: 
                self.pos_x -=  self.speed
            """
        self.pos_y += self.speed

        # If the planet moves below the screen, regenerate it
        if self.pos_y > Game.instance.height + self.rect.height:
            self.counter += 1  # Cycle to the next planet image

            # Loop back to the first image if we reach the end of the list
            if self.counter == len(Planet.PLANET_LIST):
                self.counter = 0

            self.generate_planet()  # Generate a new planet

class Enemy(pygame.sprite.Sprite):
    def __init__(self, image_list, speed, bullet_speed, shoot_interval, pos_x, pos_y):
        super().__init__()
        self.speed = speed
        self.bullet_speed = bullet_speed
        
        self.shoot_interval = shoot_interval
        self.next_shot_time = pygame.time.get_ticks() + self.shoot_interval
        
        self.image_list = image_list
        self.image = random.choice(self.image_list)
        self.rect = self.image.get_rect(center=(pos_x, pos_y))
        
    
    def update(self):
        self.handle_behavior()
        '''Logic to be extended by child classes'''
        
    def handle_behavior(self):
        self.render()
        self.collision_with_player()
        self.despawn_if_offscreen()
        #self.move_relative_to_player()
        self.shoot_bullet()
   
    def collision_with_player(self):
        if pygame.sprite.groupcollide(Game.instance.player_group, Game.instance.enemy_group, True, True):
            Game.instance.GAME_OVER = True

    def despawn_if_offscreen(self):
        if self.rect.y >= Game.instance.height + 10:
            self.kill()
            Game.instance.player.lose_life()

    def shoot_bullet(self):
        current_time = pygame.time.get_ticks() 
       
        if current_time >= self.next_shot_time and not Game.instance.GAME_OVER:
            enemy_bullet = Bullet(self.rect.x-5, self.rect.bottom, self.bullet_speed, False)
            Game.instance.bullet_enemy_group.add(enemy_bullet)
            
            self.next_shot_time = current_time + self.shoot_interval  # Reset shot timer

    def kill(self):
        explosion = Explosion(self.rect.center) # Spawn at center of enemy position
        Game.instance.effect_group.add(explosion)  #  Add to effect group 
        super().kill()

    def render(self):
        Game.instance.screen.blit(self.image, self.rect)
    """
    def move_relative_to_player(self):
        key = pygame.key.get_pressed()
        if key[pygame.K_d]:
            self.rect.x -= 1
        if key[pygame.K_w]:
            self.rect.y += 1
        if key[pygame.K_a]:
            self.rect.x += 1
    """

class StandardEnemy(Enemy):
    ENEMY_IMG = [pygame.image.load(f"assets/enemy/standard/alien{i}.png") for i in range(1,7)]

    def __init__(self):
        speed = random.randint(3, 5)
        bullet_speed = 6
        pos_x = random.randint(30, 370)
        pos_y = -100
        
        # Individual fire timing
        shoot_interval = random.randint(850, 1100)  # Each enemy shoots at random intervals
        super().__init__(StandardEnemy.ENEMY_IMG, speed, bullet_speed, shoot_interval, pos_x, pos_y)
    
    def update(self):
        super().update()
        self.rect.y += self.speed
              
class DiagonalEnemy(Enemy):
    ENEMY_IMG = [pygame.image.load(f"assets/enemy/diagonal/diagonal_alien{i}.png") for i in range(1, 2)]
 

    def __init__(self, x, y):
        self.speed_x = 4
        speed = 2
        bullet_speed = 6
        shoot_interval = 1200

        super().__init__(DiagonalEnemy.ENEMY_IMG, speed, bullet_speed, shoot_interval, x, y)

    def update(self):
        super().handle_behavior()
        # Diagonal Movement
        self.rect.y += self.speed
        self.rect.x -= self.speed_x
        
        # Inverse speeds when touches wall
        if self.rect.x < 390:
            if self.rect.x  < 0:
                self.speed_x *= -1
            if self.rect.x + self.rect.width > 400:
                self.speed_x *= -1

class Heart(pygame.sprite.Sprite):
    HEART_IMG = [pygame.image.load(f"assets/misc/heart{i}.png") for i in range(1,3)]
    def __init__(self, x, y):
        super().__init__()
        self.pos_x = x
        self.pos_y = y
        self.image = Heart.HEART_IMG[0]
        self.rect = self.image.get_rect(center = ((self.pos_x, self.pos_y)))
    
    def update(self):
        self.render()
    
    def render(self):
        Game.instance.screen.blit(self.image, self.rect)

class PowerUp(pygame.sprite.Sprite): 
    def __init__(self, image):
        super().__init__()
        # Set random position at the top of the screen
        self.pos_x, self.pos_y = random.randint(0, 400), -50
        self.speed = 7
        self.image = image
        self.rect = self.image.get_rect(center=(self.pos_x, self.pos_y))
        
        self.alpha = 255  # Full opacity
        self.pulsing_down = True  # Track whether we are fading out or in

    def handle_behavior(self):
        self.render()
        self.collision_with_player()
        self.despawn_if_offscreen()
        self.move()

    def update(self):
        self.handle_behavior()
        
    def collision_with_player(self):
        if pygame.sprite.spritecollide(self, Game.instance.player_group, False):
            self.apply_effect()
            self.kill()

    def despawn_if_offscreen(self):
        if self.rect.y >= Game.instance.height + 10:
            self.kill()

    def move(self):
        #Move downards
        self.rect.y += self.speed

    def pulse(self):
         # Pulsing effect by changing transparency
        if self.pulsing_down:
            self.alpha -= 10  # Fade out
            if self.alpha <= 85:  
                self.pulsing_down = False
        else:
            self.alpha += 10  # Fade in
            if self.alpha >= 255:  # Fully visible
                self.pulsing_down = True
        
        self.image.set_alpha(self.alpha)

    def render(self):
        self.pulse()
        Game.instance.screen.blit(self.image, self.rect)
        
    def apply_effect(self):
        """To be implemented by child classes"""
        pass

class LifePowerUp(PowerUp):
    POWERUP_IMG = pygame.image.load(f"assets/misc/heart1.png")
    
    def __init__(self):
       
        super().__init__(LifePowerUp.POWERUP_IMG)
    
    def apply_effect(self):
        Game.instance.player.gain_life()
    
    def update(self):
        super().update()

class Animation(pygame.sprite.Sprite):
    def __init__(self, frames, pos):
        super().__init__()
        self.frames = frames  # list of images
        self.frame_duration = 5  # time per frame (ms)
        self.current_frame = 0 # index to access
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.timer = 0  # track time elapsed

    def update(self):
        self.timer += 1
        
        if self.timer >= self.frame_duration:
            self.timer = 0
            self.current_frame += 1
            if self.current_frame < len(self.frames):
                self.image = self.frames[self.current_frame]
            else:
                self.kill()  # remove the animation when it's done
      
        self.render()

    def render(self):
        Game.instance.screen.blit(self.image, self.rect)
        
class Explosion(Animation):
    EXP_IMG = [pygame.image.load(f"assets/explosion/exp{i}.png") for i in range (1,9)]
   
    def __init__(self, pos):
        
        super().__init__(Explosion.EXP_IMG, pos)
      
game = Game()
game.run()
