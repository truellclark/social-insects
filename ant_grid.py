import pygame
import numpy as np
import matplotlib.pyplot as plt
import netsci.visualization as nsv
import netsci.metrics.motifs as nsm
from pygame.constants import MOUSEBUTTONDOWN
from classes import Ant, Wall, SFZ, Colony

K1, K2 = 30, 30 # dimensions of initial colony (int)
N = 30 # number of ants in the initial colony (int)
density = 0.3 # density of ants in the initial colont (0-1)
P = 2 # number of sfzs in the initial colony (int)
config = 'RID' # ('RM', 'RID', 'AID')
mode = 'tunnel' # determines whether additions to grid are additive ('wall') or subtractive ('tunnel')
time_steps = 300 # number of update steps to run (int)
scale = 20 # size of individual grid cell (int)
dt = 1

# Define SFZs
'''sfzs = []
colors = [(200, 0, 0), (200, 200, 0), (0, 200, 0), (0, 0, 200)] # list of colors to assign sfz
for n in range(3):
    i, j = np.random.randint(K1), np.random.randint(K2)
    sfzs.append(SFZ([(x,y) for x in range(i, i+3) for y in range(j, j+3)], colors[n]))'''

# Create Colonies to run in parallel
f = [0.98, 0.8, 0.6, 0.4, 0.2] # list of spatial fidelities to run with
f = [0.8 for i in range(1)]
view = 0 # which colony to visualize
colonies = [Colony(K1, K2, N, f[i], P, config = config, mode = mode) for i in range(len(f))]

print('SHD max:', N*(K1*K2-N)/(K1*K2)**2)

def undo(command, colonies):
    for colony in colonies:
        if command in ['wall', 'tunnel'] and colony.shapes:
            colony.grid = colony.shapes.pop()[1]
        elif command == 'sfz' and colony.sfzs: 
            colony.sfzs.pop()

if __name__ == '__main__':
    # Start a new pygame window
    run = True
    start = None
    current_shape = 'wall' if mode == 'wall' else 'tunnel'
    commands = []
    update = False
    win = pygame.display.set_mode((K1 * scale, K2 * scale))
    pygame.display.set_caption('Ant Nest Simulator')
    
    t = 0
    clock = pygame.time.Clock()
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            elif event.type == pygame.MOUSEBUTTONDOWN and not update:
                cursor = list(pygame.mouse.get_pos())
                start = (cursor[0] // scale, cursor[1] // scale)

            elif event.type == pygame.MOUSEBUTTONUP and not update:
                cursor = list(pygame.mouse.get_pos())
                stop = (cursor[0] // scale + (cursor[0] // scale >= start[0]), cursor[1] // scale + (cursor[1] // scale >= start[1]))
                colors = [(200, 0, 0), (0, 200, 0), (200, 200, 0), (88, 107, 164), (178, 112, 146)]
                for colony in colonies:
                    if current_shape == 'wall': colony.set_wall(start, stop)
                    elif current_shape == 'tunnel': colony.set_tunnel(start, stop)
                    elif current_shape == 'sfz': colony.set_sfz(start, stop, colors[len(colony.sfzs)])
                commands.append(current_shape)
                start = None

            elif event.type == pygame.KEYDOWN:
                if event.key in [115, 116, 119]:
                    current_shape = ['sfz', 'tunnel', 'wall'][[115, 116, 119].index(event.key)]
                elif event.key == 122 and commands:
                    undo(commands.pop(), colonies)
                elif event.key == pygame.K_SPACE:
                    update = True
                    for colony in colonies:
                        if colony.ants == []:
                            colony.area -= abs(np.sum(colony.grid))
                            #colony.N = int(density * colony.area)
                            colony.create_ants()
                            #colony.create_sfzs()

        colonies[view].draw_grid(win, scale)
        if start != None:
            cursor = list(pygame.mouse.get_pos())
            i, j = min(start[0], cursor[0] // scale), min(start[1], cursor[1] // scale)
            w, h = abs(cursor[0] // scale - start[0]) + (cursor[0] // scale >= start[0]), abs(cursor[1] // scale - start[1]) + (cursor[1] // scale >= start[1])
            pygame.draw.rect(win, (100, 100, 100), (i*scale, j*scale, w*scale, h*scale), 2)
            pygame.display.update()
            
        if update:
            for colony in colonies:
                colony.update()
            t += 1
            if t == time_steps:
                run = False

    SHDs = [colony.shd for colony in colonies]
    C = [colony.contacts for colony in colonies]
    R = [np.array([(contacts[i+1]-contacts[i])/dt for i in range(len(contacts)-1)]) for contacts in C]
    I = [contacts / N for contacts in [colony.new_contacts for colony in colonies]]

    # Spatial Fidelity of each task group
    '''for p in range(colony.P):
        print('SF('+str(p)+'):', colony.get_sf(p))'''

    #print(colonies[view].network)
    motif_frequencies = nsm.motifs(colonies[view].network, algorithm = 'brute-force')
    print(motif_frequencies)

    if N <= 50:
        colonies[view].draw_network()

    #print(colonies[view].grid)

    plot1 = plt.figure(1)
    plt.title('Motif Counts')
    plt.bar(np.arange(3,16), motif_frequencies[3:])

    plot2 = plt.figure(2)
    legend = []
    for i in range(len(SHDs)):
        plt.plot(SHDs[i])
        legend.append('SF:' + str(colonies[i].f))
    plt.title(config)
    plt.legend(legend)
    plt.xlabel('t')
    plt.ylabel('SHD')

    plot3 = plt.figure(3)
    for i in range(len(I)):
        plt.plot(I[i])
    plt.title('Proportion of Informed Ants')
    plt.legend(legend)
    plt.xlabel('t')
    plt.ylabel('I(t)')

    plot4 = plt.figure(4)
    for i in range(len(R)):
        plt.scatter(np.arange(len(R[i])), R[i], s = 2)
    plt.title('Contact Rate')
    plt.legend(legend)
    plt.xlabel('t')
    plt.ylabel('C(t) - C(t-dt)')

    plt.show()