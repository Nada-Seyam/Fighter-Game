import sys
import pygame
from pygame import mixer


pygame.init()

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600 

# Colors
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
BLACK =(0, 0, 0,)

# Button class for menu
class Button:
    def __init__(self, x, y, width, height, text, font_size=40, text_color=(255,255,255), button_color=(70,70,70), hover_color=(100,100,100)):
        pygame.font.init()
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, font_size)
        self.text_color = text_color
        self.button_color = button_color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, surface):
        # Change color on hover
        current_color = self.hover_color if self.is_hovered else self.button_color
        pygame.draw.rect(surface, current_color, self.rect)
        pygame.draw.rect(surface, (255,255,255), self.rect, 2)  # White border

        # Render text
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            # Check if mouse is hovering over button
            self.is_hovered = self.rect.collidepoint(event.pos)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                return True
        return False

# Define game variables
global intro_count, last_count_update
intro_count = 4
last_count_update = pygame.time.get_ticks()
score = [0, 0]  # Player scores. [P1, P2]
round_over = False
ROUND_OVER_COOLDOWN = 2000

# Define fighter variables
WARRIOR_SIZE = 162
WARRIOR_SCALE = 4
WARRIOR_OFFSET = [72, 56]
WARRIOR_DATA = [WARRIOR_SIZE, WARRIOR_SCALE, WARRIOR_OFFSET]
WIZARD_SIZE = 250
WIZARD_SCALE = 3
WIZARD_OFFSET = [112, 107]
WIZARD_DATA = [WIZARD_SIZE, WIZARD_SCALE, WIZARD_OFFSET]

#load sounds
sword_fx = pygame.mixer.Sound("assets/audio/sword.wav")
sword_fx.set_volume(0.5)
magic_fx = pygame.mixer.Sound("assets/audio/magic.wav")
magic_fx.set_volume(0.75)


screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Game")

bg_image = pygame.image.load(r'assets/Background/bg.jpg')

# Load spritesheets
warrior_sheet = pygame.image.load("assets/images/warrior/Sprites/warrior.png")
wizard_sheet = pygame.image.load("assets/images/wizard/Sprites/wizard.png")

# Load victory image
victory_img = pygame.image.load("assets/images/icons/victory.png")

# Define number of steps in each animation
WARRIOR_ANIMATION_STEPS = [10, 8, 1, 7, 7, 3, 7]
WIZARD_ANIMATION_STEPS = [8, 8, 1, 8, 8, 3, 7]

#define font
count_font = pygame.font.Font("assets/fonts/turok.ttf", 80)
score_font = pygame.font.Font("assets/fonts/turok.ttf", 30)

#function for deawing text 
def draw_text(text, font, text_col,x , y ):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

def draw_bg():
    scaled_bg = pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.blit(scaled_bg, (0, 0))

def draw_health_bar(health, x, y):
    ratio = health / 100
    pygame.draw.rect(screen, WHITE, (x - 2, y - 2, 404, 34)) 
    pygame.draw.rect(screen, RED, (x, y, 400, 30)) 
    pygame.draw.rect(screen, YELLOW, (x, y, 400 * ratio, 30))  

class Fighter:
    def __init__(self,player, x, y, flip, data, sprite_sheet, animation_steps, sound):
        self.player = player
        self.size = data[0]
        self.image_scale = data[1]
        self.offset = data[2]
        self.flip = flip  
        self.update_time = pygame.time.get_ticks() 
        self.animation_list = self.load_images(sprite_sheet, animation_steps)
        self.action = 0  # 0: idle, 1: run, 2: jump, 3: attack1, 4: attack2, 5: hit, 6: dead
        self.frame_index = 0
        self.image = self.animation_list[self.action][self.frame_index] 
        self.rect = pygame.Rect((x, y, 80, 180)) 
        self.vel_y = 0  # velocity  
        self.running = False
        self.jump = False
        self.attacking = False
        self.attack_type = 0
        self.attack_cooldown = 0
        self.attack_sound = sound
        self.hit = False
        self.health = 100
        self.alive = True
        
    def load_images(self, sprite_sheet, animation_steps):
        # Extract images from spritesheet
        animation_list = []
        for y, animation in enumerate(animation_steps):
            temp_img_list = []
            for x in range(animation):
                temp_img = sprite_sheet.subsurface(x * self.size, y * self.size, self.size, self.size)
                temp_img_list.append(pygame.transform.scale(temp_img, (self.size * self.image_scale, self.size * self.image_scale)))
            animation_list.append(temp_img_list)
        return animation_list  # Return the fully populated list here

    def move(self, screen_width, screen_height, surface, target, round_over):
        SPEED = 10
        dx = 0
        dy = 0
        GRAVITY = 2
        self.running = False
        self.attack_type = 0

        key = pygame.key.get_pressed()

        if self.attacking == False and self.alive == True and round_over == False:
            #check player 1 controls
            if self.player == 1:

                if key[pygame.K_a]:
                    dx = -SPEED
                    self.running = True
                if key[pygame.K_d]:
                    dx = SPEED 
                    self.running = True
                
                # Jump
                if key[pygame.K_w] and self.jump == False:
                    self.vel_y = -30
                    self.jump = True

                # Attack
                if key[pygame.K_r] or key[pygame.K_t]:
                    self.attack(target)
                if key[pygame.K_r]:
                    self.attack_type = 1
                if key[pygame.K_t]:
                    self.attack_type = 2   

            #check player 2 controls
            if self.player == 2:
                
                if key[pygame.K_LEFT]:
                    dx = -SPEED
                    self.running = True
                if key[pygame.K_RIGHT]:
                    dx = SPEED 
                    self.running = True
                
                # Jump
                if key[pygame.K_UP] and self.jump == False:
                    self.vel_y = -30
                    self.jump = True

                # Attack
                if key[pygame.K_KP1] or key[pygame.K_KP2]:
                    self.attack(target)
                if key[pygame.K_KP1]:
                    self.attack_type = 1
                if key[pygame.K_KP2]:
                    self.attack_type = 2         

            # Apply gravity
            self.vel_y += GRAVITY
            dy += self.vel_y     

            # Ensure that the player stays on screen
            if self.rect.left + dx < 0:
                dx = -self.rect.left
            elif self.rect.right + dx > screen_width:
                dx = screen_width - self.rect.right
            if self.rect.bottom + dy > screen_height - 110:
                self.vel_y = 0
                self.jump = False
                dy = screen_height - 110 - self.rect.bottom

            # Ensure players face each other
            if target.rect.centerx > self.rect.centerx:
                self.flip = False
            else:
                self.flip = True
            # apply attack cooldown
            if self.attack_cooldown >0:
                self.attack_cooldown -= 1

            # Update the position of player
            self.rect.x += dx  
            self.rect.y += dy

    def update(self):
        # Handle actions
        if self.health <= 0:
            self.health =0
            self.alive = False
            self.update_action(6) #death animation

        elif self.hit == True:
            self.update_action(5) # hit animation  
        elif self.attacking == True:
            if self.attack_type == 1:
                self.update_action(3)  # attack 1 
            elif self.attack_type == 2:
                self.update_action(4)  # attack 2
        elif self.jump:
            self.update_action(2)
        elif self.running:
            self.update_action(1)
        else:
            self.update_action(0)             
        
        animation_cooldown = 50
        #update image
        self.image = self.animation_list[self.action][self.frame_index]
        if pygame.time.get_ticks() - self.update_time > animation_cooldown:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()
        
        # Check if the animation finished 
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.alive == False:
                self.frame_index = len(self.animation_list[self.action])- 1
            else:
                self.frame_index = 0  
                # check if an attack was excuted 
                if self.action == 3 or self.action == 4:
                    self.attacking = False
                    self.attack_cooldown = 20
                #check if damage was taken
                if self.action == 5:
                    self.hit = False
                    #condition when the player in the middle of attack
                    self.attacking = False
                    self.attack_cooldown = 20


    def attack(self, target):
        if self.attack_cooldown == 0:
        #execute attack
            self.attacking = True
            self.attack_sound.play()
            attacking_rect = pygame.Rect(self.rect.centerx - (2 * self.rect.width * self.flip), self.rect.y, 2 * self.rect.width, self.rect.height)
            if attacking_rect.colliderect(target.rect):
                target.health -= 10
                target.hit = True
                

    def update_action(self, new_action):
        # Check if the new action is different from the previous one
        if new_action != self.action:
            self.action = new_action
            # Update the animation settings
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()     
        
    def draw(self, surface):
        img = pygame.transform.flip(self.image, self.flip, False)  
        surface.blit(img, (self.rect.x - (self.offset[0] * self.image_scale), self.rect.y - (self.offset[1] * self.image_scale)))

def show_start_menu():

    # Create buttons
    start_button = Button(
        SCREEN_WIDTH // 2 - 100, 
        SCREEN_HEIGHT // 2 - 50, 
        200, 
        60, 
        "START GAME" )
    quit_button = Button(
        SCREEN_WIDTH // 2 - 100, 
        SCREEN_HEIGHT // 2 + 50, 
        200, 
        60, 
        "QUIT GAME" )

    menu_active = True
    while menu_active:
        draw_bg()  

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            # Handle button events
            if start_button.handle_event(event):
                return True
            
            if quit_button.handle_event(event):
                return False

        # Draw title
        font = pygame.font.Font(None, 74)
        title = font.render("FIGHTER GAME", True, (255,255,255))
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
        screen.blit(title, title_rect)

        # Draw buttons
        start_button.draw(screen)
        quit_button.draw(screen)

        # Update display
        pygame.display.update()

# Initialize clock
clock = pygame.time.Clock()

class SoundButton:
    def __init__(self, x, y, width, height):
        # Load sound state icons
        self.icon_on = pygame.image.load("assets/images/on.png")
        self.icon_off = pygame.image.load("assets/images/off.png")
        
        # Resize icons to fit button (optional)
        self.icon_on = pygame.transform.scale(self.icon_on, (width, height))
        self.icon_off = pygame.transform.scale(self.icon_off, (width, height))
        
        self.rect = pygame.Rect(x, y, width, height)
        self.is_sound_on = True
        
    def draw(self, surface):
        # Draw the appropriate icon based on sound state
        current_icon = self.icon_on if self.is_sound_on else self.icon_off
        surface.blit(current_icon, self.rect)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                # Toggle sound state
                self.is_sound_on = not self.is_sound_on
                
                # Adjust volume of sound effects
                sword_fx.set_volume(0.5 if self.is_sound_on else 0)
                magic_fx.set_volume(0.75 if self.is_sound_on else 0)
                
                return True
        return False

# Main game loop with menu
def main():

    sound_button = SoundButton(SCREEN_HEIGHT - 150, 10, 60, 60)

    global intro_count, last_count_update
    round_over = False  
    round_over_time = 0

    # Show start menu
    if not show_start_menu():
        pygame.quit()
        return

    # 2 instances of object
    fighter_1 = Fighter(1,200, 310, False, WARRIOR_DATA, warrior_sheet, WARRIOR_ANIMATION_STEPS,sword_fx)
    fighter_2 = Fighter(2,700, 310, True, WIZARD_DATA, wizard_sheet, WIZARD_ANIMATION_STEPS,magic_fx)

    run = True
    while run:
        draw_bg()
        # Draw sound button
        sound_button.draw(screen)

        fighter_1.update()
        fighter_2.update()

        fighter_1.draw(screen)
        fighter_2.draw(screen) 

        if round_over == False:
            if fighter_1.alive == False:
                score[1] += 1
                round_over = True
                round_over_time = pygame.time.get_ticks()
            elif fighter_2.alive == False:
                score[0] += 1
                round_over = True
                round_over_time = pygame.time.get_ticks()
        else:
            screen.blit(victory_img, (360,150 )) 
            if pygame.time.get_ticks() - round_over_time > ROUND_OVER_COOLDOWN:
                round_over = False
                intro_count = 4 
                fighter_1 = Fighter(1,200, 310, False, WARRIOR_DATA, warrior_sheet, WARRIOR_ANIMATION_STEPS,sword_fx)
                fighter_2 = Fighter(2,700, 310, True, WIZARD_DATA, wizard_sheet, WIZARD_ANIMATION_STEPS,magic_fx)      
            

        draw_health_bar(fighter_1.health, 20, 20)
        draw_health_bar(fighter_2.health, 580, 20) 
        draw_text("Player one",score_font, BLACK ,20, 60)
        draw_text("Player two",score_font, BLACK ,580, 60)

        #update countdown
        if intro_count <= 0:
            fighter_1.move(SCREEN_WIDTH, SCREEN_HEIGHT, screen, fighter_2, round_over)
            fighter_2.move(SCREEN_WIDTH, SCREEN_HEIGHT, screen, fighter_1, round_over)
            
        else:
            draw_text(str(intro_count), count_font, RED, SCREEN_WIDTH / 2,SCREEN_HEIGHT/ 3 )
            if (pygame.time.get_ticks() - last_count_update) >= 1000:
                intro_count -= 1
                last_count_update = pygame.time.get_ticks()
                  

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False


            # Handle sound button event
            sound_button.handle_event(event)    

        pygame.display.update()  
        clock.tick(60)  

    pygame.quit()

# Run the game
if __name__ == "__main__":
    main()


   