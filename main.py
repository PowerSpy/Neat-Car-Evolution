#initialize the screen
import pygame, math, sys, time
from pygame.locals import *
import neat

def level1(genomes, config):
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    #GAME CLOCK
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 75)
    win_font = pygame.font.Font(None, 50)
    win_condition = None
    t0 = time.time()
    



    class CarSprite(pygame.sprite.Sprite):
        MAX_FORWARD_SPEED = 10
        MAX_REVERSE_SPEED = 10
        ACCELERATION = 2
        TURN_SPEED = 10

        def __init__(self, image, position):
            pygame.sprite.Sprite.__init__(self)
            self.src_image = pygame.image.load(image)
            self.position = position
            self.speed = self.direction = 0
            self.k_left = self.k_right = self.k_down = self.k_up = 0
            self.is_alive = True
            self.distance = 0
        
        def update(self, deltat):
            #SIMULATION
            self.speed += (self.k_up + self.k_down)
            if self.speed > self.MAX_FORWARD_SPEED:
                self.speed = self.MAX_FORWARD_SPEED
            if self.speed < -self.MAX_REVERSE_SPEED:
                self.speed = -self.MAX_REVERSE_SPEED
            self.direction += (self.k_right + self.k_left)
            x, y = (self.position)
            rad = self.direction * math.pi / 180
            x += -self.speed*math.sin(rad)
            y += -self.speed*math.cos(rad)
            self.position = (x, y)
            self.image = pygame.transform.rotate(self.src_image, self.direction)
            self.rect = self.image.get_rect()
            self.rect.center = self.position
            self.distance += self.speed
        def get_reward(self):
            return self.distance/50

    class PadSprite(pygame.sprite.Sprite):
        normal = pygame.image.load('Race_Game/images/race_pads.png')
        hit = pygame.image.load('Race_Game/images/collision.png')
        def __init__(self, position):
            super(PadSprite, self).__init__()
            self.rect = pygame.Rect(self.normal.get_rect())
            self.rect.center = position
        def update(self, hit_list):
            if self in hit_list: self.image = self.hit
            else: self.image = self.normal
    pads = [
        PadSprite((0, 10)),
        PadSprite((600, 10)),
        PadSprite((1100, 10)),
        PadSprite((100, 150)),
        PadSprite((600, 150)),
        PadSprite((100, 300)),
        PadSprite((800, 300)),
        PadSprite((400, 450)),
        PadSprite((700, 450)),
        PadSprite((200, 600)),
        PadSprite((900, 600)),
        PadSprite((400, 750)),
        PadSprite((800, 750)),
    ]
    pad_group = pygame.sprite.RenderPlain(*pads)

    class Trophy(pygame.sprite.Sprite):
        def __init__(self, position):
            pygame.sprite.Sprite.__init__(self)
            self.image = pygame.image.load('Race_Game/images/trophy.png')
            self.rect = self.image.get_rect()
            self.rect.x, self.rect.y = position
        def draw(self, screen):
            screen.blit(self.image, self.rect)

    trophies = [Trophy((285,0))]
    trophy_group = pygame.sprite.RenderPlain(*trophies)

    # CREATE A CAR AND RUN
    rect = screen.get_rect()
    nets = []
    cars = {}
    for id, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0
        car = CarSprite('Race_Game/images/car.png', (10, 730))
        cars[car] = pygame.sprite.RenderPlain(car)

    #THE GAME LOOP
    while 1:
        #USER INPUT
        t1 = time.time()
        dt = t1-t0

        deltat = clock.tick(30)
        for event in pygame.event.get():
            if not hasattr(event, 'key'): continue
            down = event.type == KEYDOWN 
            if win_condition == None: 
                if event.key == K_RIGHT: car.k_right = down * -5 
                elif event.key == K_LEFT: car.k_left = down * 5
                elif event.key == K_UP: car.k_up = down * 2
                elif event.key == K_DOWN: car.k_down = down * -2 
                elif event.key == K_ESCAPE: sys.exit(0) # quit the game 
    
        #COUNTDOWN TIMER
        seconds = round((20 - dt),2)
        if win_condition == None:
            timer_text = font.render(str(seconds), True, (255,255,0))
            if seconds <= 0:
                timer_text = font.render("Time!", True, (255,0,0))
                loss_text = win_font.render('Press Space to Retry', True, (255,0,0))
            
    
        #RENDERING
        remaining_cars = 0
        screen.fill((0,0,0))
        for i, (car, car_group) in enumerate(cars.items()):
            if car.is_alive:
                collisions = pygame.sprite.groupcollide(car_group, pad_group, False, False, collided = None)
                if collisions != {}:
                    car.is_alive = False
                    seconds = 0
                    car.MAX_FORWARD_SPEED = 0
                    car.MAX_REVERSE_SPEED = 0
                    car.k_right = 0
                    car.k_left = 0
            if car.is_alive:
                remaining += 1
                trophy_collision = pygame.sprite.groupcollide(car_group, trophy_group, False, True)
                car_group.update(deltat)
                if trophy_collision != {}:
                    genomes[i][1].fitness += 1000
                    car.is_alive = False
                else:
                    genomes[i][1].fitness += car.get_reward()

            
                
        if remaining_cars == 0:
            break
        pad_group.update(collisions)
        pad_group.draw(screen)
        for car, car_group in cars.items():
            if car.is_alive:
                car_group.draw(screen)
        print(remaining_cars)
        trophy_group.draw(screen)
        #Counter Render
        screen.blit(timer_text, (20,60))
        pygame.display.flip()

if __name__ == "__main__":
    config_path = "config.txt"
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

    # Create core evolution algorithm class
    p = neat.Population(config)

    # Add reporter for fancy statistical result
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # Run NEAT
    p.run(level1, 1000)
