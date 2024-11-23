#initialize the screen
import pickle
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
            self.radars = []
            self.row = 0
            
            # Set up rect during initialization
            self.image = pygame.transform.rotate(self.src_image, self.direction)
            self.rect = self.image.get_rect()
            self.rect.center = self.position
        def coords_on(self,x,y,pads):
            for pad in pads:
                if x > pad.rect.x and x < pad.rect.x + pad.rect.w and y > pad.rect.y and y < pad.rect.y + pad.rect.h:
                    return True
        def check_radar(self, deg, pads):
            len = 0
            x = int(self.rect.center[0] + math.cos(math.radians(270 - (self.direction + deg))) * len)
            y = int(self.rect.center[1] + math.sin(math.radians(270 - (self.direction + deg))) * len)

            while not self.coords_on(x, y, pads) and len < 300:
                len = len + 1
                x = int(self.rect.center[0] + math.cos(math.radians(270 - (self.direction + deg))) * len)
                y = int(self.rect.center[1] + math.sin(math.radians(270 - (self.direction + deg))) * len)

            dist = int(math.sqrt(math.pow(x - self.rect.center[0], 2) + math.pow(y - self.rect.center[1], 2)))
            self.radars.append([(x, y), dist])
        def update(self, deltat, pads):
            # SIMULATION
            self.speed += (self.k_up + self.k_down)
            if self.speed > self.MAX_FORWARD_SPEED:
                self.speed = self.MAX_FORWARD_SPEED
            if self.speed < -self.MAX_REVERSE_SPEED:
                self.speed = -self.MAX_REVERSE_SPEED
            self.direction += (self.k_right + self.k_left)
            x, y = (self.position)
            rad = self.direction * math.pi / 180
            x += -self.speed * math.sin(rad)
            y += -self.speed * math.cos(rad)
            self.position = (x, y)
            self.image = pygame.transform.rotate(self.src_image, self.direction)
            self.rect = self.image.get_rect()
            self.rect.center = self.position
            self.distance += self.speed
            self.radars.clear()
            for d in range(-120, 150, 30):  # Wider range, smaller increments
                self.check_radar(d, pads)

            
        def get_reward(self):
            return self.distance / 25
        def draw_radar(self, screen):
            for r in self.radars:
                pos, dist = r
                pygame.draw.line(screen, (0, 255, 0), self.rect.center, pos, 1)
                pygame.draw.circle(screen, (0, 255, 0), pos, 5)
        def get_data(self):
            radars = self.radars
            ret = [0 for i in range(len(radars))]
            for i, r in enumerate(radars):
                ret[i] = int(r[1] / 30)
            return ret

    class PadSprite(pygame.sprite.Sprite):
        normal = pygame.image.load('Race_Game/images/race_pads.png')
        hit = pygame.image.load('Race_Game/images/collision.png')
        vert = pygame.image.load('Race_Game/images/vertical_pads.png')
        def __init__(self, position, orientation = True):
            super(PadSprite, self).__init__()
            if orientation:
                self.rect = pygame.Rect(self.normal.get_rect())
            else:
                self.rect = pygame.Rect(self.vert.get_rect())
            self.orientation = orientation
            self.rect.center = position
        def update(self, hit_list):
            if self in hit_list: self.image = self.hit
            elif self.orientation: self.image = self.normal
            elif not self.orientation: self.image = self.vert
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
        PadSprite((0, 0), False),
        PadSprite((0, 400), False),
        PadSprite((0, 800), False),
        PadSprite((0, 750)),
        PadSprite((1024, 0), False),
        PadSprite((1024, 400), False),
        PadSprite((1024, 800), False),
        PadSprite((600, 600), False)


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
        car = CarSprite('Race_Game/images/car.png', (45, 700))
        car.direction = -90
        cars[car] = pygame.sprite.RenderPlain(car)

    #THE GAME LOOP
    while True:
        #USER INPUT
        t1 = time.time()
        dt = t1-t0

        deltat = clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
    
        #COUNTDOWN TIMER
        seconds = round((20 - dt),2)
        if win_condition == None:
            timer_text = font.render(str(seconds), True, (255,255,0))
            if seconds <= 0:
                timer_text = font.render("Time!", True, (255,0,0))            
    
        #RENDERING
        for i, (car, car_group) in enumerate(cars.items()):
            if car.is_alive:
                car_group.update(deltat, pads)
        for index, (car, car_group) in enumerate(cars.items()):
            output = nets[index].activate(car.get_data())
            car.k_right = -abs(output[0]) * 10
            car.k_left = abs(output[1]) * 10
            if output[2] <= 0:
                car.k_up = 1 * 2
            elif output[2] > 0:
                car.k_down = 1 * -2 

        remaining_time = 20 - (t1 - t0)
        remaining_cars = 0
        screen.fill((0,0,0))
        for i, (car, car_group) in enumerate(cars.items()):
            if car.is_alive:
                collisions = pygame.sprite.groupcollide(car_group, pad_group, False, False, collided = None)
                if collisions != {}:
                    if remaining_time > 15:
                        genomes[i][1].fitness -= 1000
                    elif remaining_time > 10:
                        genomes[i][1].fitness -= 800
                    elif remaining_time > 5:
                        genomes[i][1].fitness -= 500
                    car.is_alive = False
                    seconds = 0
                    car.MAX_FORWARD_SPEED = 0
                    car.MAX_REVERSE_SPEED = 0
                    car.k_right = 0
                    car.k_left = 0
            if car.is_alive:
                remaining_cars += 1
                trophy_collision = pygame.sprite.groupcollide(car_group, trophy_group, False, True)
                car_group.update(deltat, pads)
                if trophy_collision != {}:
                    genomes[i][1].fitness += 1000
                    print("winner")
                    car.is_alive = False
                else:
                    genomes[i][1].fitness += car.get_reward()
                if car.position[1] < 600:
                    if car.row == 0:
                        car.row += 1
                        genomes[i][1].fitness += 500
                    else:
                        genomes[i][1].fitness -= 1200
                        car.row = 0
                if car.position[1] < 450:
                    if car.row == 1:
                        car.row += 1
                        genomes[i][1].fitness += 500
                    else:
                        genomes[i][1].fitness -= 1200
                        car.row = 1
                if car.position[1] < 300:
                    if car.row == 2:
                        car.row += 1
                        genomes[i][1].fitness += 500
                    else:
                        genomes[i][1].fitness -= 1200
                        car.row = 2
                if car.position[1] < 150:
                    if car.row == 3:
                        car.row += 1
                        genomes[i][1].fitness += 500
                    else:
                        genomes[i][1].fitness -= 1200
                        car.row = 3
                rad_distance = 0
                for rad in car.radars:
                    rad_distance += rad[1]
                genomes[i][1].fitness += rad_distance * 0.08

                genomes[i][1].fitness += remaining_time * 5

                if car.position[0] > 700 and car.position[1] > 800:
                    genomes[i][1].fitness -= 100
                dist_from_goal = int(math.sqrt(math.pow(car.position[0] - trophies[0].rect.x, 2) + math.pow(car.position[1] - trophies[0].rect.y, 2)))
                genomes[i][1].fitness += abs(dist_from_goal - 600)/25

                


            
        remaining_time = 20 - (t1 - t0)
        if remaining_time <= 0:
            timer_text = font.render("Time!", True, (255,0,0))
            break
        else:
            timer_text = font.render(str(round(remaining_time, 2)), True, (255,255,0))

        if remaining_cars == 0:
            break
        pad_group.update(collisions)
        pad_group.draw(screen)
        for car, car_group in cars.items():
            if car.is_alive:
                car_group.draw(screen)
                # Skip radar drawing since its too intensive
                # car.draw_radar(screen)
        # print(remaining_cars)
        trophy_group.draw(screen)
        #Counter Render
        screen.blit(timer_text, (20,60))
        pygame.display.flip()

if __name__ == "__main__":
    config_path = "config.txt"
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

    # Load from checkpoint if available
    checkpoint_file = "Checkpoints/neat-checkpoint-"
    try:
        p = neat.Checkpointer.restore_checkpoint(checkpoint_file)
        print(f"Resuming from checkpoint: {checkpoint_file}")
    except FileNotFoundError:
        # Create a new population if no checkpoint is found
        print("No checkpoint found, starting new training.")
        p = neat.Population(config)

    # Add reporters for statistics and checkpointing
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # Add Checkpointer to save progress every 10 generations
    p.add_reporter(neat.Checkpointer(10, filename_prefix=checkpoint_file))

    # Run NEAT
    winner = p.run(level1, 2500)

    # Save the best genome
    with open("best_genome.pkl", "wb") as f:
        pickle.dump(winner, f)

    print("Best genome saved as 'best_genome.pkl'")

