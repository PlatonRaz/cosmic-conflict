# Import required libraries
import pygame  # Main game library
import json    # For reading JSON files
import random  # For random number generation
import os      # For file system operations
from os import path  # For path manipulations

# initialise all pygame modules
pygame.init()
#-----------------------------------------------------------------------------------------------------------------------------------------------

class Data():
    """
    Handles loading and storing high score data.
    Uses a text file to persist high scores between game sessions.
    """
    hs_file = "highscore.txt"  # File to store the high score  

    def __init__(self):  
        """
        initialises the Data object and loads high score data.
        Creates data directory if it doesn't exist.
        """
        root = path.dirname(__file__)  # Gets the directory where the script is located  
        self.data_dir = path.join(root, "data")  # Path to data directory
        self.load_data()  # Load existing high score

    def load_data(self):  
        """
        Loads high score data from file.
        Creates new file with default high score (0) if file doesn't exist.
        Handles corrupt data (non-integer values) by resetting to 0.
        """
        os.makedirs(self.data_dir, exist_ok=True)  # Creates 'data' folder if it doesn't exist
     
        try:  
            # Try to open and read the high score file  
            with open(path.join(self.data_dir, Data.hs_file), "r+") as f: 
                contents = f.read()
                if not contents.isdigit():  # Check if content is a valid number
                    self.highscore = 0  # Default to 0 if file is corrupt
                else:
                    self.highscore = int(contents)  # Store valid high score
        except (FileNotFoundError, ValueError):  
            # If file doesn't exist or error occurs, create new file
            with open(path.join(self.data_dir, Data.hs_file), 'w') as f:  
                self.highscore = 0  # initialise with default value
  
    def write_highscore(self):
        """
        Updates high score file if current score exceeds stored high score.
        Prevents overflow by capping high score at 99999.
        """
        if Game.instance.player.score > self.highscore:
            self.highscore = Game.instance.player.score
            if self.highscore < 99999:  # Prevent overflow
                with open(path.join(self.data_dir, Data.hs_file), "w") as f:
                    f.write(str(self.highscore))  # Write new high score

class Cursor(pygame.sprite.Sprite):
    """
    Custom cursor class that replaces the default system cursor.
    Tracks and renders at mouse position.
    """
    def __init__(self, picture_path):
        """
        initialises cursor with custom image and hides default cursor.
        
        Args:
            picture_path (str): Path to cursor image file
        """
        super().__init__()
        self.image = pygame.image.load(picture_path)  # Load cursor image
        self.rect = self.image.get_rect()  # Get image rectangle
        pygame.mouse.set_visible(False)  # Hide default mouse cursor

    def update(self):
        """Updates cursor position to follow mouse and renders it."""
        self.rect.center = pygame.mouse.get_pos()  # Track mouse position
        self.render()

    def render(self):
        """Draws cursor at current mouse position."""
        Game.instance.screen.blit(self.image, self.rect)

class Game():
    """
    Main game class that manages the game state, assets, and core loop.
    Implements a state machine for different game screens.
    """
    
    # Class variables (shared across all instances)
    instance = None  # Singleton instance reference
    GAME_OVER = False  # Global game over flag
    
    # Color constants
    COLORS = {
        "bg_color": (38, 33, 56),  # Background color
        "RED": (255, 0, 0),
        "WHITE": (255, 255, 255),
        "GREEN": (0, 255, 0),
        "YELLOW": (255, 255, 0),
        "ORANGE": (255, 180, 0)
    }
    
    # Font assets
    FONT_LARGE = pygame.font.Font("assets/8-BIT WONDER.TTF", 32)
    FONT_MEDIUM = pygame.font.Font("assets/8-BIT WONDER.TTF", 28)
    FONT_SMALL = pygame.font.Font("assets/8-BIT WONDER.TTF", 18)

    # Background images
    BG_IMG = {
        "BG": pygame.image.load("assets/background/background.png"),
        "OVERLAY": pygame.image.load("assets/background/bg_overlay.png")
    }
    
    @staticmethod
    def load_json_text(filename):
        """
        Helper method to load JSON data from file.
        
        Args:
            filename (str): Path to JSON file
            
        Returns:
            dict: Parsed JSON data
        """
        with open(filename, "r") as file:
            return json.load(file)  
        
    # Game assets
    SHIP_LIST = [pygame.image.load(f"assets/playerships/ship{i}.png") for i in range(1,7)]  # Player ship options
    BULLET_LIST = {
        "player": pygame.image.load("assets/bullets/player_bullet.png"), 
        "enemy": pygame.image.load("assets/bullets/enemy_bullet.png")
    }
    
    # Game data loaded from files
    SHIP_DATA = load_json_text("data/ship_data.json")  # Ship attributes
    GAME_TEXT = load_json_text("data/game_text.json")  # Help text
    
    # Default game configuration
    CONFIG = {
        "music": True,    # Music enabled
        "sound": True,    # Sound effects enabled
        "HUD": True,      # Show HUD
        "wrapping": False # Screen wrapping enabled
    }

    # Sprite groups
    bullet_enemy_group = pygame.sprite.Group()
    bullet_player_group = pygame.sprite.Group()
    enemy_group = pygame.sprite.Group()
    player_group = pygame.sprite.Group()
    planet_group = pygame.sprite.Group()
    powerup_group = pygame.sprite.Group()
    effect_group = pygame.sprite.Group()
    
    # All groups in one list for easy clearing
    GROUPS = [planet_group, enemy_group, bullet_player_group, 
              bullet_enemy_group, player_group, powerup_group, effect_group]

    def __init__(self):
        """initialises game window, assets, and game state."""
        Game.instance = self  # Set singleton instance
        
        # Window dimensions
        self.width = 400
        self.height = 600

        # Screen setup
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()  # For controlling frame rate
       
        # Game control attributes
        self.current_state = "MENU"  # Starting state
        self.running = True          # Main game loop flag
        self.click = False           # Mouse click state

        # Background positioning
        self.BG_default_y = -self.BG_IMG["BG"].get_height()/2
        self.BG_default_x = -self.BG_IMG["BG"].get_width()/3
        self.BG_y = self.BG_default_y
        self.BG_x = self.BG_default_x
       
        # Game state handlers dictionary
        # Maps state names to their update and event handler methods
        self.states = {
            "MENU": [self.menu, self.menu_event_handler],
            "PLAY": [self.play, self.play_event_handler],
            "OPTIONS": [self.options, self.options_event_handler],
            "ARMOURY": [self.armoury, self.armoury_event_handler],
            "HELP": [self.help, self.help_event_handler],
            "PAUSE": [self.pause, self.pause_event_handler]
        }
      
        # Text buttons organized by screen
        self.text_buttons = {
            "PAUSE": [
                TextButton("PAUSED", Game.FONT_LARGE, Game.COLORS["YELLOW"], (105, 165)),
                TextButton("RESUME ( P )", Game.FONT_MEDIUM, Game.COLORS["WHITE"], (55, 325)),
                TextButton("EXIT ( ESC )", Game.FONT_MEDIUM, Game.COLORS["WHITE"], (65, 400))],

            "MENU": [
                TextButton("PLAY", Game.FONT_MEDIUM, Game.COLORS["WHITE"], (140, 300)),
                TextButton("OPTIONS", Game.FONT_MEDIUM, Game.COLORS["WHITE"], (110, 375)),
                TextButton("ARMOURY", Game.FONT_MEDIUM, Game.COLORS["WHITE"], (95, 450)),
                TextButton("HELP", Game.FONT_MEDIUM, Game.COLORS["WHITE"], (140, 525))],

            "BACK": TextButton("BACK", Game.FONT_MEDIUM, Game.COLORS["WHITE"], (10, 530)),
            
           "OPTIONS": [
                TextButton(
                    f"{setting} enabled" if Game.CONFIG[setting] else f"{setting} disabled",
                    Game.FONT_SMALL,
                    Game.COLORS["GREEN"] if Game.CONFIG[setting] else Game.COLORS["RED"],
                    (10, 100 + list(Game.CONFIG).index(setting) * 40)
                )
                for setting in Game.CONFIG]
        }

        # Image buttons (ship selection in armoury)
        spacing = 130  # Horizontal spacing between ship buttons
        self.image_buttons = {
            "ARMOURY": [
                ImageButton(img, f"SHIP{Game.SHIP_LIST.index(img) + 1}", 
                          ((Game.SHIP_LIST.index(img) * spacing), 130), "ship") 
                for img in Game.SHIP_LIST
            ]
        }
          
        # Initialise with first ship's description
        self.selected_ship_description = Game.instance.SHIP_DATA.get("SHIP1")
      
        # Initialise player with default ship
        self.player = Player("SHIP1")
        self.player_group.add(self.player)
        self.data = Data()  # High score handler
        self.cursor = Cursor("assets/misc/cursor.png")  # Custom cursor
        
        # Initialise game objects
        self.initialise_planets()
        self.initialise_hearts()
        self.initialise_bullets()

        # Wave system attributes
        self.current_wave = 0  # Current wave index
        self.wave_timer = 0    # Time elapsed in current wave  
        self.wave_duration = 0 # Duration of current wave
        self.in_wave = False   # Wave active flag
        self.enemies_spawned = False  # Enemy spawn flag
        self.total_waves_completed = 0  # Total waves completed
        
        self.last_spawn_time = 0  # Last enemy spawn time
        self.spawn_interval = 1700  # ms between spawns
       
        # Wave definitions (methods to call for each wave)
        self.waves = [
            self.wave_1,  # Standard enemies 
            self.wave_2   # Diagonal enemies
        ]
        
        # Custom events
        self.WAVE_EVENT = pygame.USEREVENT + 0  # Wave timer event
        pygame.time.set_timer(self.WAVE_EVENT, 1000)  # Trigger every second
        
        self.POWER_UP = pygame.USEREVENT + 1  # Powerup spawn event
        pygame.time.set_timer(self.POWER_UP, 5000)  # Trigger every 5 seconds

        # Pause system attributes
        self.pause_data = {
            'start_time': 0,      # When pause started
            'total_paused': 0,    # Total paused time
            'is_paused': False    # Pause state flag
        }

    # Wave definitions ----------------------------------------------------------
    def wave_1(self):        
        """
        First wave - spawns standard enemies at intervals.
        Runs for 15 seconds.
        """
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
            # Clean up any off-screen enemies
            for enemy in self.enemy_group:
                if enemy.rect.y < 0:
                    enemy.kill()
            return True  # Wave complete
        return False
    
    def wave_2(self):
        """
        Second wave - spawns diagonal enemies in formation.
        Runs until all enemies defeated or 30 seconds elapsed.
        """
        # Initial setup when wave starts
        if self.wave_timer == 0:
            self.wave_duration = 30  # seconds
        
            # Formation positions
            x, y = 30, 50    # Left group start position
            x2, y2 = 200, -250  # Right group start position
        
        if not self.enemies_spawned:
            # Spawn left group (3 enemies)
            for _ in range(3):
                enemy = DiagonalEnemy(x, y)
                y -= 100  # Move up for next enemy
                x += 85  # Move right for next enemy
                self.enemy_group.add(enemy)
            
            # Spawn right group (3 enemies)
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

    # Helper methods ------------------------------------------------------------
    def text(self, message, font, color, pos):
        """
        Helper method to render text.
        
        Args:
            message (str): Text to display
            font (pygame.Font): Font to use
            color (str): Key from COLORS dictionary
            pos (tuple): (x,y) screen position
        """
        text_surface = font.render(message, True, self.COLORS[color])
        self.screen.blit(text_surface, pos)

    def set_screen_size(self, width):
        """Resizes game window while maintaining height."""
        self.width = width
        self.screen = pygame.display.set_mode((self.width, self.height))
    
    def move_background(self):
        """Animates background scrolling effect."""
        self.BG_y += 0.5

        # Reset background position when scrolled off screen
        if self.BG_y >= 0:
            self.BG_y = self.BG_default_y
    
    def global_UI_elements(self):
        """Renders UI elements common to all screens."""
        # Background handling
        if self.current_state != "ARMOURY" and self.current_state != "HELP":
            self.screen.blit(self.BG_IMG["BG"], (self.BG_x, self.BG_y))
            self.move_background()       
        else:
            self.screen.fill(self.COLORS["bg_color"])  # Solid bg for some screens
        
        # Screen title
        if self.current_state != "MENU" and self.current_state != "PLAY" and self.current_state != "PAUSE":
            self.text(self.current_state, self.FONT_LARGE, "WHITE", (10, 20))
    
    def initialise_planets(self):
        """Creates initial planet objects."""
        num_planets = 1
        for _ in range(num_planets):
            planet = Planet()
            self.planet_group.add(planet)
    
    def initialise_hearts(self): 
        """Creates heart UI elements based on player lives."""
        num_hearts = self.player.lives  
        x_initial, y_initial = 450, 65  # Starting position
        
        pos_x, pos_y = x_initial, y_initial

        # Arrange hearts in grid
        for i in range(num_hearts):
            heart = Heart(pos_x, pos_y)  
            self.player.heart_stack.append(heart)  

            pos_x += 100  # Move right
            
            # New row after every 3 hearts
            if (i + 1) % 3 == 0:
                pos_x = x_initial
                pos_y += 100
    
    def initialise_bullets(self): 
        """Creates bullet UI elements based on player ammo."""
        num_bullets = self.player.ammo  
        x_initial, y_initial = 465, 470  # Starting position
        x_spacing, y_spacing = 40, 15  # Spacing between bullets

        pos_x, pos_y = x_initial, y_initial

        # Arrange bullets in columns
        for i in range(num_bullets):
            bullet = Bullet(pos_x, pos_y, 0)  # 0 speed for UI bullets
            self.player.bullet_stack.append(bullet) 
            self.bullet_player_group.add(bullet)
            pos_y += y_spacing  # Move down

            # New column after every 6 bullets
            if (i + 1) % 6 == 0:
                pos_y = y_initial
                pos_x += x_spacing

    # Core game loop ------------------------------------------------------------
    def run(self):
        """Main game loop."""
        while self.running:
            self.process_events()  # Handle input/events
            self.global_UI_elements()  # Render common UI
            self.states[self.current_state][0]()  # Update current state
            self.global_render()  # Update display
            
        pygame.quit()  # Clean up on exit
        
    def process_events(self):
        """Processes events for current game state."""
        for event in pygame.event.get():
            # Global event handling
            if event.type == pygame.QUIT:
                self.running = False

            # State-specific event handling
            self.states[self.current_state][1](event)

    def global_render(self):
        """Updates display and controls frame rate."""
        pygame.display.update()
        self.clock.tick(60)  # 60 FPS

    # Input handling ------------------------------------------------------------
    def mouse_click_event(self, event):
        """Handles mouse click events."""
        self.get_mouse_pos()
        
        # Check for left mouse button press
        self.click = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.click = True

    def get_mouse_pos(self):
        """Gets current mouse position."""
        self.mx, self.my = pygame.mouse.get_pos()

    # Game screens --------------------------------------------------------------
    def display_HUD(self):
        """Displays heads-up display during gameplay."""
        if Game.CONFIG["HUD"] and self.width != 700:
            self.set_screen_size(700)  # Expand screen for HUD
        
        self.screen.blit(Game.BG_IMG["OVERLAY"], (400, 0))  # HUD background
        
        # Render HUD elements
        self.text("LIVES", self.FONT_SMALL, "WHITE", (512, 15))
        self.text("HI SCORE", self.FONT_SMALL, "WHITE", (485, 215))
        self.text(str(self.data.highscore), self.FONT_LARGE, "ORANGE", (567, 260))
        self.text(str(self.player.score), self.FONT_SMALL, "WHITE", (575, 330))
        self.text("AMMO", self.FONT_SMALL, "WHITE", (500, 420))
        
        # Update UI elements
        for bullet in self.player.bullet_stack:
            bullet.update()
        
        for heart in self.player.heart_stack:
            heart.update()

    def reset_game_state(self):
        """Resets all game state for new game."""
        self.GAME_OVER = False
        self.current_wave = 0
        self.wave_timer = 0
        self.in_wave = False
        self.enemies_spawned = False
        
        # Clear all sprite groups
        for group in self.GROUPS:
            group.empty()
        
        # Reinitialise player
        self.player = Player(self.player.selected_ship)  # Keep selected ship
        self.player_group.add(self.player)
        
        # Reinitialise UI
        self.initialise_hearts()
        self.initialise_bullets()
        self.initialise_planets()

    def menu(self):
        """Renders main menu screen."""
        if self.width != 400:
            self.set_screen_size(400)  # Ensure correct size
            
        # Menu text
        self.text("COSMIC CONFLICT", self.FONT_MEDIUM, "YELLOW", (8, 30))
        self.text(f"HIGH SCORE {self.data.highscore}", self.FONT_SMALL, "WHITE", (100, 100))

        # Menu buttons
        for button in self.text_buttons["MENU"]:
            button.update()
            
        self.cursor.update()  # Render custom cursor
    
    def game_over_screen(self): 
        """Displays game over screen."""
        self.player.kill()
        # Semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 90))  
        self.screen.blit(overlay, (0, 0))
        
        # Game over text
        self.text("GAME OVER", self.FONT_LARGE, "YELLOW", (55, 80))
        self.text("Play Again ( SPACE )", self.FONT_SMALL, "WHITE", (55, 150))
        self.text("Exit ( ESC )", self.FONT_SMALL, "WHITE", (115, 185))   
   
    def play(self):
        """Main gameplay update method."""
        # Update all sprite groups
        for group in self.GROUPS:
            group.update()
       
        self.display_HUD()  # Render HUD
        
        # Show game over screen if needed
        if self.GAME_OVER:
            self.game_over_screen()

    def options(self):
        """Renders options screen."""
        # Options buttons
        for button in self.text_buttons["OPTIONS"]:
            button.update()
            
        self.text_buttons["BACK"].update()  # Back button
        self.cursor.update()  # Render cursor

    def armoury(self):
        """Renders ship selection screen."""
        self.text("select ship", self.FONT_SMALL, "WHITE", (10, 80))
        self.text_buttons["BACK"].update()
        
        # Ship selection buttons
        for ship in self.image_buttons["ARMOURY"]:
            ship.update()
            
        # Adjust screen size for armoury
        if self.current_state == "ARMOURY" and self.width != 800:
            self.set_screen_size(800)
        elif self.current_state != "ARMOURY" and self.width != 400:
            self.set_screen_size(400)
            
        self.cursor.update()

    def help(self):
        """Renders help/instructions screen."""
        self.text_buttons["BACK"].update()
        
        # Adjust screen size for help
        if self.current_state == "HELP" and self.width != 610:
            self.set_screen_size(610)
        elif self.current_state != "HELP" and self.width != 400:
            self.set_screen_size(400) 
       
        # Display help text from JSON
        help_data = self.GAME_TEXT["help_text"]
        y_offset = 65  # Starting Y position
        
        # Render each section
        for section in help_data:
            # Section title
            self.text(section["title"], self.FONT_MEDIUM, "YELLOW", (10, y_offset))
            y_offset += 40
            
            # Section content
            for line in section["content"]:
                self.text(line, self.FONT_SMALL, "GREEN", (20, y_offset))
                y_offset += 30
            
            y_offset += 20  # Section spacing

        self.cursor.update()
    
    def pause(self):
        """Handles pause screen functionality."""
        # Record pause start time
        if not self.pause_data['is_paused']:
            self.pause_data['start_time'] = pygame.time.get_ticks()
            self.pause_data['is_paused'] = True
       
        if self.width != 400:
            self.set_screen_size(400)
       
        # Semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))  
        self.screen.blit(overlay, (0, 0))
        
        # Pause screen buttons
        for button in self.text_buttons["PAUSE"]:
            button.update()

    # Event handlers ------------------------------------------------------------
    def menu_event_handler(self, event):
        """Handles events for menu screen."""
        self.mouse_click_event(event)
    
    def play_event_handler(self, event):
        """Handles events for gameplay screen."""
        if event.type == pygame.KEYDOWN:
            # Game over controls
            if event.key == pygame.K_ESCAPE and self.GAME_OVER:
                self.reset_game_state()
                self.current_state = "MENU"
           
            if event.key == pygame.K_SPACE and self.GAME_OVER:
                self.reset_game_state()

            # Pause game
            elif event.key == pygame.K_p and not self.GAME_OVER:
                self.current_state = "PAUSE"
                return

        # Wave system events
        if event.type == self.WAVE_EVENT:
            self.wave_timer += 1
    
            # Start new wave if none active
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
                    self.total_waves_completed += 1
                    
                    # Loop waves
                    if self.current_wave >= len(self.waves):
                        self.current_wave = 0
        
        # Powerup spawn event
        if event.type == self.POWER_UP and not self.GAME_OVER:
            if self.player.lives < 3:
                life = LifePowerUp()
                self.powerup_group.add(life)

    def options_event_handler(self, event):
        """Handles events for options screen."""
        self.mouse_click_event(event)

    def armoury_event_handler(self, event):
        """Handles events for armoury screen."""
        self.mouse_click_event(event)

    def help_event_handler(self, event):
        """Handles events for help screen."""
        self.mouse_click_event(event)
    
    def pause_event_handler(self, event):
        """Handles events for pause screen."""
        # Resume game
        if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
            self.current_state = "PLAY"
            self.pause_data['total_paused'] = pygame.time.get_ticks() - self.pause_data['start_time']
            self.pause_data['is_paused'] = False

        # Exit to menu
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.reset_game_state()
            self.current_state = "MENU"
            self.pause_data['is_paused'] = False

# Player class ------------------------------------------------------------------
class Player(pygame.sprite.Sprite):
    """
    Player ship class with movement, shooting, and health systems.
    Handles different ship types with varying stats.
    """
    
    # Player ship images with proper hitboxes
    PLAYER_SHIP_LIST = [pygame.image.load(f"assets/playerships/player{i}.png") for i in range(1,7)] 

    # Bullet firing patterns for each ship type
    BULLET_PATTERNS = {
        "SHIP1": [(0, 0)],  # Single center bullet
        "SHIP2": [(0, 0)],  # Single center bullet
        "SHIP3": [(-25, 0, 'NW'), (25, 0, 'NE')],  # Two angled bullets
        "SHIP4": [(-35, 0), (35, 0)],  # Two side bullets
        "SHIP5": [(0, 0), (-35, 25, 'NW'), (35, 25, 'NE')],  # Three bullets
        "SHIP6": [(0, 0)]  # Single center bullet
    }
    
    def __init__(self, selected_ship):
        """
        initialises player with selected ship type.
        
        Args:
            selected_ship (str): Ship ID (e.g. "SHIP1")
        """
        super().__init__()
        # Load ship stats from data
        self.selected_ship = selected_ship
        self.speed = Game.instance.selected_ship_description["speed"] // 10
        self.ammo = Game.instance.selected_ship_description["ammo"]
        self.lives = Game.instance.selected_ship_description["lives"]
        self.type = Game.instance.selected_ship_description["type"]
        self.fire_rate = Game.instance.selected_ship_description["fire rate"] * 10
        self.bullet_speed = Game.instance.selected_ship_description["bullet speed"]
        self.max_lives = self.lives
        self.score = 0
        
        # Get correct ship image
        index = list(Game.instance.SHIP_DATA).index(self.selected_ship)
        self.image = Player.PLAYER_SHIP_LIST[index]

        # Initial position
        default_pos = (200, 500)
        self.rect = self.image.get_rect(center=default_pos)
    
        self.previous_time = pygame.time.get_ticks()  # For firing cooldown
        
        self.heart_stack = []  # Life UI elements
        self.bullet_stack = []  # Ammo UI elements

    def update(self):
        """Updates player state each frame."""
        key = pygame.key.get_pressed()  # Get keyboard state
        self.handle_movement(key)
        self.shoot_bullet(key)
        self.render()

    def handle_movement(self, key):
        """Handles player movement based on input."""
        # Left movement
        if key[pygame.K_a]:  
            self.rect.x -= self.speed  

            # Wrapping logic if enabled
            if Game.instance.CONFIG["wrapping"]:  
                if self.rect.right < 0:  # Off left edge
                    self.rect.x = 400  # Wrap to right
                    if key[pygame.K_w]:  # Move to bottom if pressing up
                        self.rect.y = Game.instance.height - (self.rect.height + 15)

            # Standard boundary check
            elif self.rect.x < 0:  
                self.rect.x = 0  

        # Right movement
        if key[pygame.K_d]:  
            self.rect.x += self.speed  

            if Game.instance.CONFIG["wrapping"]:  
                if self.rect.x > 400:  # Off right edge
                    self.rect.x = -self.rect.width  # Wrap to left
                    if key[pygame.K_w]:  
                        self.rect.y = Game.instance.height - (self.rect.height + 15)

            elif self.rect.right > 400:  
                self.rect.x = 400 - self.rect.width  

        # Up/down movement with bounds checking            
        if key[pygame.K_w] and self.rect.y > 0: 
            self.rect.y -= self.speed
        if key[pygame.K_s] and self.rect.y < Game.instance.height - self.rect.height: 
            self.rect.y += self.speed

    def shoot_bullet(self, key):       
        """Handles bullet firing logic."""
        if key[pygame.K_SPACE] and self.ammo > 0:
            current_time = pygame.time.get_ticks()

            # Check fire rate cooldown
            if current_time - self.previous_time > self.fire_rate:
                self.previous_time = current_time
               
                # Create bullets based on ship's pattern
                for pattern in Player.BULLET_PATTERNS[self.selected_ship]:
                    x, y, *direction = pattern  # Unpack position and optional direction
                    bullet = Bullet(self.rect.x + x, self.rect.y + y, 
                                  self.bullet_speed, True, *direction)
                    Game.instance.bullet_player_group.add(bullet)
                
                self.lose_bullet()  # Deduct ammo

    def gain_bullet(self):
        """Adds bullet to ammo count and UI."""
        if self.ammo < 30:
            self.ammo += 1
            # Calculate position for new bullet UI element
            x_initial, y_initial = 465, 470
            bullets_per_column = 6
            x_spacing, y_spacing = 40, 15
            
            bullet_count = len(self.bullet_stack)
            col = bullet_count // bullets_per_column
            row = bullet_count % bullets_per_column

            x_new = x_initial + col * x_spacing
            y_new = y_initial + row * y_spacing

            # Add new bullet
            bullet = Bullet(x_new, y_new, 0)
            self.bullet_stack.append(bullet)

    def lose_bullet(self):
        """Removes bullet from ammo count and UI."""
        if self.bullet_stack:
            self.bullet_stack.pop()  # Remove from stack
            self.ammo -= 1

    def gain_life(self):
        """Adds life and updates UI."""
        if self.lives < self.max_lives:
            self.lives += 1
            
            # Clear and rebuild heart UI for proper positioning
            self.heart_stack = []  
            
            # Grid layout parameters
            x_initial, y_initial = 450, 65  
            hearts_per_row = 3  
            x_spacing, y_spacing = 100, 30  
            
            # Recreate all hearts
            for i in range(self.lives):
                row = i // hearts_per_row
                col = i % hearts_per_row
                
                x_new = x_initial + col * x_spacing
                y_new = y_initial + row * y_spacing
                
                heart = Heart(x_new, y_new)
                self.heart_stack.append(heart)

    def lose_life(self):
        """Removes life and checks for game over."""
        if self.heart_stack:
            self.heart_stack.pop()  # Remove heart from UI
            self.lives -= 1
        
        if self.lives == 0:
            Game.instance.GAME_OVER = True
        
    def render(self):
        """Draws player sprite."""
        Game.instance.screen.blit(self.image, self.rect)  

# UI Elements -------------------------------------------------------------------
class Button():
    """
    Base button class with hover/click functionality.
    Inherited by text and image buttons.
    """
    def __init__(self, pos):
        """
        initialises button with position.
        
        Args:
            pos (tuple): (x,y) screen position
        """
        self.pos = pos  # Button position

    def update(self):
        """Handles button state and rendering."""
        self.handle_button_press()
        self.render_button()

    def handle_button_press(self):
        """Handles button interaction logic."""
        self.on_unhover()  # Default state
        
        # Check for mouse hover
        if self.button_rect.collidepoint(Game.instance.mx, Game.instance.my):
            self.on_hover()  # Hover state
            
            # Check for click
            if Game.instance.click:
                self.on_click() 

    def render_button(self):
        """Draws button on screen."""
        Game.instance.screen.blit(self.button_surface, self.pos)


class ImageButton(Button):
    '''Creates a button using an image.'''
    def __init__(self, img, button_name, pos, on_click_action=None):
        super().__init__(pos)
        self.button_surface = img
        self.button_rect = self.button_surface.get_rect(topleft=pos)
        self.button_name = button_name
        self.on_click_action = on_click_action

    def on_hover(self):
        '''Slightly fades the button and shows ship info if applicable.'''
        self.button_surface.set_alpha(100)
        if self.on_click_action == "ship":
            Game.instance.selected_ship_description = Game.instance.SHIP_DATA.get(self.button_name)
            self.draw_ship_description()

    def on_unhover(self):
        '''Returns the button to full visibility.'''
        self.button_surface.set_alpha(255)

    def draw_ship_description(self):
        '''Displays the selected ship's attributes on screen.'''
        x,y = 10, 300
        for key, value in Game.instance.selected_ship_description.items():
            ship_text = f"{key}  {value}"
            Game.instance.text(ship_text, Game.instance.FONT_SMALL, "WHITE", (x, y))
            y += 30

    def on_click(self):
        '''Handles what happens when the button is clicked (ship selection).'''
        if self.on_click_action == "ship":
            Game.instance.player_group.empty()
            Game.instance.player = Player(self.button_name)
            Game.instance.player_group.add(Game.instance.player)
            Game.instance.initialise_hearts()
            Game.instance.initialise_bullets()

class TextButton(Button):
    '''Creates a button using text.'''
    def __init__(self, message, font, color, pos):
        super().__init__(pos)
        self.message = message
        self.font = font
        self.color = color
        self.button_surface = self.font.render(self.message,False,(Game.instance.COLORS["WHITE"]))
        self.button_rect = self.button_surface.get_rect(topleft=(pos))

    def on_click(self):
        '''Handles what happens when the button is clicked (state changes, options).'''
        if self.message in Game.instance.states:
            Game.instance.current_state = self.message
        elif self.message == "BACK":
            Game.instance.current_state = "MENU"
        elif 'enabled' in self.message:
            for setting in Game.instance.CONFIG:
                if setting in self.message:
                    Game.instance.CONFIG[setting] = False
                    self.color = Game.instance.COLORS["RED"]
                    self.message = f"{setting} disabled"
        elif 'disabled' in self.message:
            for setting in Game.instance.CONFIG:
                if setting in self.message:
                    Game.instance.CONFIG[setting] = True
                    self.color = Game.instance.COLORS["GREEN"]
                    self.message = f"{setting} enabled"
        Game.instance.click = False

    def on_hover(self):
        '''Highlights the button when the mouse is over it.'''
        self.button_surface = self.font.render(self.message,False,(Game.instance.COLORS["YELLOW"]))

    def on_unhover(self):
        '''Returns the button to its normal appearance.'''
        self.button_surface = self.font.render(self.message,False,(self.color))

class Bullet(pygame.sprite.Sprite):
    '''Represents a projectile in the game.'''
    def __init__(self, x, y, speed, is_player=True, direction=None):
        super().__init__()
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = speed
        self.is_player = is_player
        if not is_player:
            self.image = Game.instance.BULLET_LIST["enemy"]
        else:
            self.image = Game.instance.BULLET_LIST["player"]
            if self.direction == "NW":
                self.image = pygame.transform.rotate(self.image, 15)
            elif self.direction == "NE":
                self.image = pygame.transform.rotate(self.image, -15)
        if self.speed != 0:
            self.rect = self.image.get_rect(
                center = ((x + Game.instance.player.rect.width//2), y)
                )
        else:
            self.rect = self.image.get_rect(
                center = (x, y)
                )

    def update(self):
        '''Moves the bullet, checks for collisions, and renders it.'''
        self.handle_trajectory()
        self.handle_collision()
        self.render()

    def handle_trajectory(self):
        '''Determines how the bullet moves.'''
        if self.is_player:
            self.rect.y -= self.speed
        else:
            self.rect.y += self.speed
        if self.rect.y < 0:
            self.kill()
        if self.direction == "NW":
            self.rect.x -= 2
        elif self.direction == "NE":
            self.rect.x += 2

    def handle_collision(self):
        '''Checks if the bullet has hit anything.'''
        if pygame.sprite.groupcollide(Game.instance.bullet_player_group, Game.instance.enemy_group, True, True):
            Game.instance.player.score += 1
            Game.instance.data.write_highscore()
            Game.instance.player.gain_bullet()
            Game.instance.player.gain_bullet()
        elif pygame.sprite.groupcollide(Game.instance.bullet_enemy_group, Game.instance.player_group, True, False):
            Game.instance.player.lose_life()

    def render(self):
        '''Draws the bullet on the screen.'''
        Game.instance.screen.blit(self.image, self.rect)

class Planet(pygame.sprite.Sprite):
    '''Represents a background planet.'''
    PLANET_LIST = [pygame.image.load(f"assets/planets/planet_{i}.png")
                   for i in range(1, 5)]

    def __init__(self):
        super().__init__()
        self.counter = 0
        self.generate_planet()

    def generate_planet(self):
        '''Creates the planet with random attributes.'''
        self.angle = random.randint(0, 360)
        self.speed = 1
        lower_scale, max_scale = 1.15, 1.8
        self.scale = random.uniform(lower_scale, max_scale)
        self.image = pygame.transform.rotozoom(
            Planet.PLANET_LIST[self.counter], self.angle, self.scale
        ).convert_alpha()
        self.pos_x = random.randint(-50, 400 - (self.image.get_width()))
        self.pos_y = -self.image.get_height()
        self.rect = self.image.get_rect(center=(self.pos_x, self.pos_y))

    def update(self):
        '''Moves and draws the planet.'''
        self.handle_movement()
        self.render()

    def render(self):
        '''Draws the planet on the screen.'''
        Game.instance.screen.blit(self.image, (self.pos_x, self.pos_y))

    def handle_movement(self):
        '''Moves the planet downwards and regenerates it off-screen.'''
        self.pos_y += self.speed
        if self.pos_y > Game.instance.height + self.rect.height:
            self.counter += 1
            if self.counter == len(Planet.PLANET_LIST):
                self.counter = 0
            self.generate_planet()

class Enemy(pygame.sprite.Sprite):
    '''Base class for all enemy types.'''
    def __init__(self, image_list, speed, bullet_speed, shoot_interval, pos_x, pos_y):
        super().__init__()
        self.speed_increase = Game.instance.total_waves_completed // 4
        self.speed = speed + self.speed_increase
        self.bullet_speed = bullet_speed + self.speed_increase
        self.shoot_interval = shoot_interval
        self.next_shot_time = pygame.time.get_ticks() + self.shoot_interval
        self.image_list = image_list
        self.image = random.choice(self.image_list)
        self.rect = self.image.get_rect(center=(pos_x, pos_y))

    def update(self):
        '''Updates the enemy's behaviour.'''
        self.handle_behavior()
        '''Logic to be extended by child classes'''

    def handle_behavior(self):
        '''Handles the enemy's actions (render, collision, shooting).'''
        self.render()
        self.collision_with_player()
        self.despawn_if_offscreen()
        self.shoot_bullet()

    def collision_with_player(self):
        '''Checks if the enemy has collided with the player.'''
        if pygame.sprite.groupcollide(Game.instance.player_group, Game.instance.enemy_group, True, True):
            Game.instance.GAME_OVER = True

    def despawn_if_offscreen(self):
        '''Removes the enemy if it goes off the bottom of the screen.'''
        if self.rect.y >= Game.instance.height + 10:
            self.kill()

    def shoot_bullet(self):
        '''Makes the enemy fire a bullet.'''
        current_time = pygame.time.get_ticks()
        if Game.instance.pause_data['total_paused'] > 0:
            self.next_shot_time += Game.instance.pause_data['total_paused']
            Game.instance.pause_data['total_paused'] = 0
        if current_time >= self.next_shot_time and not Game.instance.GAME_OVER:
            enemy_bullet = Bullet(self.rect.x-5, self.rect.bottom, self.bullet_speed, False)
            Game.instance.bullet_enemy_group.add(enemy_bullet)
            self.next_shot_time = current_time + self.shoot_interval

    def kill(self):
        '''Removes the enemy and creates an explosion.'''
        explosion = Explosion(self.rect.center)
        Game.instance.effect_group.add(explosion)
        super().kill()

    def render(self):
        '''Draws the enemy on the screen.'''
        Game.instance.screen.blit(self.image, self.rect)

class StandardEnemy(Enemy):
    '''A basic enemy that moves straight down.'''
    ENEMY_IMG = [pygame.image.load(f"assets/enemy/standard/alien{i}.png") for i in range(1,7)]

    def __init__(self):
        speed = random.randint(2, 4)
        pos_x = random.randint(30, 370)
        pos_y = -500
        bullet_speed = 6
        shoot_interval = random.randint(850, 1100)
        super().__init__(StandardEnemy.ENEMY_IMG, speed, bullet_speed, shoot_interval, pos_x, pos_y)

    def update(self):
        '''Moves the standard enemy downwards.'''
        super().update()
        self.rect.y += self.speed

class DiagonalEnemy(Enemy):
    '''An enemy that moves diagonally.'''
    ENEMY_IMG = [pygame.image.load(f"assets/enemy/diagonal/diagonal_alien{i}.png") for i in range(1, 2)]

    def __init__(self, x, y):
        speed = 2
        bullet_speed = 6
        shoot_interval = 1200
        super().__init__(DiagonalEnemy.ENEMY_IMG, speed, bullet_speed, shoot_interval, x, y)
        self.speed_x = 5

    def update(self):
        '''Moves the diagonal enemy diagonally and bounces off walls.'''
        super().handle_behavior()
        self.rect.y += self.speed
        self.rect.x -= self.speed_x
        if self.rect.x < 390:
            if self.rect.x  < 0:
                self.speed_x *= -1
            if self.rect.x + self.rect.width > 400:
                self.speed_x *= -1

class Heart(pygame.sprite.Sprite):
    '''Represents a life indicator on the screen.'''
    HEART_IMG = [pygame.image.load(f"assets/misc/heart{i}.png") for i in range(1,3)]
    def __init__(self, x, y):
        super().__init__()
        self.pos_x = x
        self.pos_y = y
        self.image = Heart.HEART_IMG[0]
        self.rect = self.image.get_rect(center = ((self.pos_x, self.pos_y)))

    def update(self):
        '''Draws the heart on the screen.'''
        self.render()

    def render(self):
        '''Draws the heart at its position.'''
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

    '''Give the player an extra life when this power-up is collected.'''
    def apply_effect(self):
        Game.instance.player.gain_life()

    '''Update the power-up (which it inherits from the PowerUp class).'''
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

    '''Advance the animation frame by frame.'''
    def update(self):
        self.timer += 1

        if self.timer >= self.frame_duration:
            self.timer = 0
            self.current_frame += 1
            if self.current_frame < len(self.frames):
                self.image = self.frames[self.current_frame]
            else:
                self.kill()  # remove the animation when it's done

        '''Draw the current frame of the animation.'''
        self.render()

    '''Draw the current image of the animation on the screen.'''
    def render(self):
        Game.instance.screen.blit(self.image, self.rect)

class Explosion(Animation):
    EXP_IMG = [pygame.image.load(f"assets/explosion/exp{i}.png") for i in range (1,9)]

    def __init__(self, pos):
        super().__init__(Explosion.EXP_IMG, pos)
      
game = Game()
game.run()
