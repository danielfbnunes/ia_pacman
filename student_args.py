import random
from math import sqrt 
import sys
import json
import asyncio
import websockets
import os
from mapa import Map
import time


start_time = 0
# custo associado aos caminhos que se cruzam com possiveis posicoes
# dos fantasmas
trouble_cost = 0
# profundidade associada à procura dos caminhos que se cruzam com possiveis posicoes
# dos fantasmas
trouble_depth = 0
# distancia maxima do pacman ao fantasma a ser comido
# se a distancia for superior ao ghost_persuit o pacaman nao tenta comer o fantasma
ghost_persuit = 20



class SearchNode:
    def __init__(self,pos,parent,cost=0, heuristic=0):
        self.pos = pos
        self.parent = parent
        #custo de um determinado nó
        self.cost=cost  
    def __str__(self):
        #retorna "no(" + str(self.pos) + ", " + str(self.parent) + ", "  + str(self.cost) + ")"
        return str(self.pos)
    def __repr__(self):
        return str(self)

class Pacman:  
    def __init__(self,pos):
        self.pos = pos
        self.buffer = []
        self.followed = False
        self.target_not_found = 0
    
    def __str__(self):
        return str(self.pos)

    def __repr__(self):
        return str(self)
    
    def being_followed(self, ghos_pos, mapa):
        #coloca no buffer as distancias do pacman aos fantasmas que não podem ser comidos
        ghost_pos = [(g[0][0], g[0][1]) for g in ghos_pos if g[1] == False]
        self.buffer = list(map(lambda x: m_distance(self.pos,x) , ghost_pos))
        #coloca o followed a true se existirem pelo menos 1 ou 2 (dependendo da situação) fantasmas a uma distância de 10 do pacman e a tentar comer o mesmo
        following = [b for b in self.buffer if b <=10]
        #indica quando pacman esta a ser seguido por um fantasma
        if len(ghos_pos) < 3:
            self.followed = (len(following) >= 1)
        else:
            if len(mapa._energy) > mapa._initial_energies_count/2:
                self.followed = (len(following) >= 2)
            else:
                self.followed = (len(following) >= 1)
            
    
    def find_next_target(self, ghost_pos, mapa):
        #ghosts que o pacman pode comer 
        eatable_ghost = eatable_ghosts(self.pos, ghost_pos, mapa, 10)
        #distancias aos fantasmas que podem ser comidos
        dists = list(map(lambda x: m_distance(self.pos,x), eatable_ghost))
        #obter os boosts restantes 
        rest_boost = []
        boost_dists = []
        for b in mapa._boost:
            if m_distance(b, self.pos) < 8:
                boost_dists.append(m_distance(self.pos, b))
                rest_boost.append(b)

        #caso não existam energias, comer boosts
        if len(mapa._energy) == 0:
            #print("COMER BOOST - v2")
            boost_dists = list(map(lambda x: m_distance(self.pos,x), [b for b in mapa._boost]))
            next_pos = mapa._boost[boost_dists.index(min(boost_dists))]
        #ir ao boost
        elif self.followed and len(boost_dists)>0 :
            #print("COMER BOOST")
            next_pos = rest_boost[boost_dists.index(min(boost_dists))]
        #se ha fantasmas para comer
        elif len(eatable_ghost) != 0 and len(dists) != 0 and min(dists) <= ghost_persuit:
            #print("COMER GHOST")
            next_pos = eatable_ghost[dists.index(min(dists))][0]
            next_pos = (next_pos[0], next_pos[1])
        # comer energias
        else:
            #print("COMER ENERGIA")
            if len(ghost_pos) == 0:
                next_pos = get_close_energy(self.pos, mapa._energy,mapa, ghost_pos)
            else:
                next_pos = get_close_energy_ghosts(self.pos, mapa._energy, mapa, ghost_pos)
        
        return next_pos


#retorna o path de um node
def get_path(node):
    if node.parent == None:
        return [node.pos]
    path = get_path(node.parent)
    path += [node.pos]
    return(path)


#calculo da distancia de manhattan
def m_distance(p1, p2):
    if type(p2) == list:
        p2 = (p2[0][0],p2[0][1])
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

#calcula as proximas posicoes possiveis
def possible_next_positions(node, mapa, ghost_pos=[]):
    possible_next_positions=[]
    possible_next_positions.append((node[0]+1, node[1])) if node[0]+1<mapa.hor_tiles else possible_next_positions.append((0, node[1]))
    possible_next_positions.append((node[0]-1, node[1])) if node[0]-1>=0 else possible_next_positions.append((mapa.hor_tiles-1, node[1]))
    possible_next_positions.append((node[0], node[1]+1)) if node[1]+1<mapa.ver_tiles else possible_next_positions.append((node[0], 0))
    possible_next_positions.append((node[0], node[1]-1)) if node[1]-1>=0 else possible_next_positions.append((node[0],mapa.ver_tiles-1))
    pos=[]
    for p in possible_next_positions:
        if not mapa.is_wall(p): pos.append(p)
    return pos

#retorna a energia mais próxima do pacman
def get_close_energy(pacman_pos, energies, mapa, ghosts):
    ghost_pos = [(e[0][0], e[0][1]) for e in ghosts]
    # rever a condicao
    dists = list(map(lambda x: m_distance(pacman_pos,x) if x not in ghost_pos else m_distance(pacman_pos,x)*1000, energies))
    next_pos = energies[ dists.index(min(dists))]
    return next_pos


# retorna a energia mais próxima do pacman tendo em conta os fantasmas
def get_close_energy_ghosts( pacman_pos, energies, mapa, ghosts):
    #lista de distâncias do pacman às energias
    dists = list(map(lambda x: (m_distance(pacman_pos,x),0,1,x), energies)) 
    #ordenar por custos
    dists = sorted(dists, key = lambda x: x[0])
    #utilizar um subconjunto com as 15 energias mais proximas
    if len(dists) >=15:
        dists = dists[:15]

    # considerar apenas os fantasmas a menos de 6 casas da energia em questao
    for e_index in range(len(dists)):
        for g in ghosts: 
            dist_2_en = m_distance(dists[e_index][3],(g[0][0], g[0][1])) 
            if g[1] == False and dist_2_en <=6:
                dists[e_index]  = (dists[e_index][0], dists[e_index][1] + dist_2_en, dists[e_index][2] + 1,  dists[e_index][3])
                    
    # energias ponderadas
    energies_cost = [ (e[0] + e[1]/e[2], e[3]) for e in dists]
    # sort - escolha da energia mais vantajosa (fantasmas + distancia à energia)
    energies_cost = sorted(energies_cost, key = lambda x: x[0])

    return energies_cost[0][1]

# retorna as distancias aos ghosts
def get_bad_ghost_dists(ghosts, open_nodes, mapa, max_depth, d_threshold):
    #open nodes tem a posicao inicial
    initial_node = SearchNode(open_nodes[0].pos, None)
    #distâncias do primeiro nó dos open_nodes (posição inicial) aos fantasmas que tentam perseguir o pacman
    tmp_dists = list(map(lambda x: m_distance(initial_node.pos,x), [g for g in ghosts if g[1]==False]))
    #print(initial_node.pos, tmp_dists, d_threshold)
    final_dists = []
    for i in range (0,len(tmp_dists)):
        if tmp_dists[i] > d_threshold:
            final_dists.append(tmp_dists[i])
        #para pequenas distâncias, ir pesquisar as distâncias corretas aos ghosts contando com as paredes pelo meio
        else:
            # verificar se a distancia nao tem paredes no meio - pesquisa uniforme simples
            out = simple_search((ghosts[i][0][0], ghosts[i][0][1]), [initial_node], mapa, max_depth)
            if out != None and out[1] > tmp_dists[i]:
                final_dists.append(out[1])
            else:
                final_dists.append(tmp_dists[i])
    return final_dists


# método que retorna a distância real de um nó a um fantasma
# tem em atencao a profundidade maxima que pode atingir
def simple_search(f_pos, open_nodes, mapa, max_depth):
    #contador para não exceder a profundidade máxima
    count = 0
    while open_nodes != [] and count < max_depth:
        node = open_nodes.pop(0)
        #se encontrou o seu objetivo
        if node.pos == f_pos:
            return (get_path(node), len(get_path(node)))

        lnewnodes = []
        for new_pos in possible_next_positions(node.pos, mapa):
            if new_pos not in get_path(node):
                new_node=SearchNode(new_pos,node, m_distance(new_pos, f_pos))
                lnewnodes += [new_node]
        #adicionar novos nós aos open nodes
        open_nodes = add_to_open('uniform', open_nodes, lnewnodes)
        count += 1
    return None

# usado para calcular os caminhos dos fantasmas ao pacman
# evita que o pacaman fique preso entre 2 fantasmas 
def g2p_shortest_path(p_pos, ghost_list, mapa, max_deph):
    dic = dict()
    ghosts=[g for g in ghost_list if g[1] == False]
    if ghosts == []: return [],[]

    for g in ghosts:
        #criar no inicial do fantasma
        initial_node = SearchNode( (g[0][0], g[0][1]) , None)
        path = simple_search(p_pos, [initial_node], mapa, max_deph)
        if path != None:
            for p in path[0]:
                if p not in dic:
                    dic[p] = m_distance(p,(g[0][0], g[0][1]))
                else:
                   dic[p] += m_distance(p,(g[0][0], g[0][1])) 

    # lista de posicoes e respetivos pesos
    positions = []
    weights = []
    for key in dic:
        positions.append(key)
        weights.append(dic[key]/max_deph)

    return positions, weights


# retorna todos os fantasmas que podem ser comido
def eatable_ghosts(p_pos, ghost_list, mapa, max_deph):
    goodies = []
    ghosts=[g for g in ghost_list if g[1] == True and m_distance(p_pos, (g[0][0], g[0][1])) < ghost_persuit ]

    if ghosts == []: return []

    for g in ghosts:
        #criar no inicial do fantasma
        initial_node = SearchNode( (g[0][0], g[0][1]) , None)
        path = simple_search(p_pos, [initial_node], mapa, max_deph)
        if path != None:
            goodies += [g]
    return goodies
        

# pesquisa qual o caminho mais rápido até um target
def search(pacman, target_pos, open_nodes, mapa, ghost_pos, start_time):
    p_pos = pacman.pos
    while open_nodes != []:
        node = open_nodes.pop(0)
        # se encontrou o seu objetivo
        if node.pos == target_pos:
            pacman.target_not_found = 0
            return get_path(node), node
        
        lnewnodes = []
        # considerar os caminhos a partir dos fantasmas
        #trouble = g2p_shortest_path(pacman.pos, ghost_pos, mapa, 18)
        trouble = g2p_shortest_path(pacman.pos, ghost_pos, mapa, trouble_depth)
        #para todas as posições possíveis a partir de um nó...
        for new_pos in possible_next_positions(node.pos,mapa,ghost_pos):
            elapsed_time = int(round(time.time() * 1000)) - start_time
            if elapsed_time > 95:
                #print(elapsed_time, start_time,"\n-----UPS-----\n")
                return next_position_panic(pacman, ghost_pos, mapa, target_pos), node
                
            #evita ciclos
            if new_pos not in get_path(node): 

                #calculo de distancias
                cost = m_distance(new_pos,target_pos) 
                # adiciona ao custo a heuristica dos caminhos onde o pacmana pode ser intercetado pelo fantasma
                for key in trouble:
                   if key == new_pos:
                        # cost += 80 * trouble[key]
                        cost += trouble_cost * trouble[key]

                bad_ghost_pos = [g for g in ghost_pos if g[1]==False]
                appendNode=True
                #caso existam fantasmas que possam comer o pacman
                if len(bad_ghost_pos) != 0:
                    #distância do fantasma mais perto da possível próxima posição
                    bad_ghost_dists = list(get_bad_ghost_dists(bad_ghost_pos, [SearchNode(new_pos, None)], mapa, 8, 2))
                    min_bad_ghost_dist = min(bad_ghost_dists)
                    #impede que o pacman vá para uma posicao onde normalmente poderá ser comido
                    for g in ghost_pos:
                        g_dist = list(get_bad_ghost_dists([g], [SearchNode(new_pos, None)], mapa, 8, 2))[0] if len(list(get_bad_ghost_dists([g], [SearchNode(new_pos, None)], mapa, 8, 2))) != 0 else 100
                        if g[1]==False and m_distance(new_pos,p_pos) <= 2 and g_dist <= 2 and (new_pos[0]-g[0][0],new_pos[1]-g[0][1]) not in [(1,1), (1,-1), (-1,1), (-1,-1)]  and new_pos != pacman.last_pos:                           
                            #print("removed node: ", node.pos)
                            appendNode=False
                            
                        if not appendNode:
                            continue

                        # se o fantasma estiver a 6 ou menos posicoes da proxima posição
                        if min_bad_ghost_dist <= 6:                            
                            # se a pesquisa ja estiver muito grande, tentar encontrar rapidamente posições possíveis num raio
                            # mais curto, isto é, sem expandir mais a árvore em termos de número de nós
                            energies_counter = len(mapa._energy)
                            if energies_counter == 0:
                                energies_counter = 1

                            # se o fantasma pode ir para a nova posicao em 3 jogadas    
                            if min_bad_ghost_dist <= 3:
                                cost += 5
                            # no restante raio
                            else:
                                cost += 10* (1/min_bad_ghost_dist)
                            
                        # dar mais custo aos boosts caso não existam fantasmas perto deste e ainda existam mais de metade das energias iniciais no mapa
                        if new_pos in mapa._boost and min(list(get_bad_ghost_dists(bad_ghost_pos, [SearchNode(new_pos, None)], mapa, 8, 3))) >= 6 and len(mapa._energy) > mapa._initial_energies_count/2:
                            if len(ghost_pos) >= 4:
                                cost +=10
                            elif len(ghost_pos) >= 3:
                                cost += 8
                            elif len(ghost_pos) >= 2:
                                cost += 6
                            else:
                                cost += 2

                #adicionar nó aos lnewnodes
                if appendNode:
                    new_node=SearchNode(new_pos,node, cost)
                    lnewnodes += [new_node]   
               
        #adicionar novos nós aos open nodes
        open_nodes = add_to_open('uniform', open_nodes, lnewnodes)
    
    #se nao encontrar nenhuma solucao, tentar apenas fugir do fantasma
    return next_position_panic(pacman, ghost_pos, mapa, target_pos), node


#escolher nova posicao quando em panico
def next_position_panic(pacman, ghost_list, mapa, target_pos):
    bad_ghost_pos =  [g for g in ghost_list if g[1]==False]
    pacman_poss_positions = possible_next_positions(pacman.pos, mapa, [])
    next_pos = list(pacman_poss_positions)
    
    # retira  as posicoes onde  pode morrer
    for p in pacman_poss_positions:
        for g in bad_ghost_pos:
            if m_distance(p,g)<=2 and p != pacman.last_pos and p in next_pos:
                next_pos.remove(p)
    
    # calcular valores para um esperanca de vida mais reduzida :)
    if next_pos == []:
        next_pos = list(pacman_poss_positions)
        for p in pacman_poss_positions:
            for g in bad_ghost_pos:
                if m_distance(p,g)<2 and p != pacman.last_pos and p in next_pos:
                    next_pos.remove(p)
        
        if next_pos == []:
            return [pacman.pos, (0,0)]   

    #ordenar por distancia ao target
    next_pos = sorted(next_pos, key = lambda x: m_distance(x, target_pos))
    next_pos = [pacman.pos] + next_pos
    return  next_pos

#adicionar novos nós aos open_nodes com diferentes estratégias
def add_to_open(strategy, open_nodes, lnewnodes):
    if strategy == 'breadth':
        open_nodes.extend(lnewnodes)

    elif strategy == 'uniform':
        open_nodes += lnewnodes
        open_nodes = sorted(open_nodes, key = lambda x: x.cost)

    elif strategy == 'A*':
        open_nodes += lnewnodes
        open_nodes = sorted(open_nodes, key = lambda x: x.cost + (100/x.heuristic))
    
    return open_nodes

#retorna uma key perante uma posição inicial e uma posição seguinte
def get_key_to_position(curr_pos, next_pos):
    if (next_pos[0] - curr_pos[0], next_pos[1] - curr_pos[1])  in [ (0,1), (0,2)]:
        return 's'
    elif  (next_pos[0] - curr_pos[0], next_pos[1] - curr_pos[1]) in [(0,-1), (0,-2)]:
        return 'w'
    elif (next_pos[0] - curr_pos[0], next_pos[1] - curr_pos[1]) in [ (1,0), (2,0)]:
        return 'd'
    elif (next_pos[0] - curr_pos[0], next_pos[1] - curr_pos[1]) in [(-1,0), (-2,0)]:
        return 'a'
    # codigo para ir de um lado para o outro ( buffer circular ) 
    else:
        #está na horizontal
        if (curr_pos[1] - next_pos[1]) == 0: 
            #quer ir para o lado esquerdo do mapa
            if next_pos[0] == 0:
                return 'd'
            else:
                return 'a'
        #esta na vertical
        else:
            #quer ir para o topo do mapa
            if next_pos[1] == 0:
                return's'
            else:
                return 'w'



async def agent_loop(server_address = "localhost:8000", agent_name="student"):

    print("---------------------------------------------------------------------------")
    async with websockets.connect("ws://{}/player".format(server_address)) as websocket:

        # Receive information about static game properties 
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
        msg = await websocket.recv()
        game_properties = json.loads(msg) 
         
        mapa = Map(game_properties['map'])

        # ver valores consoantes os mapas
        map_name = game_properties['map']
        if map_name == "data/map1.bmp":
            trouble_cost = 80
            trouble_depth = 20
        elif map_name == "data/map2.bmp":
            trouble_cost = 100
            trouble_depth = 27
        else:
            trouble_cost = 90
            trouble_depth =  22

        
        # determinar valores para a perseguicao dos fantasmas tendo em conta o seu nivel
        if game_properties["ghosts_level"] == 0 and game_properties["ghosts"] <= 2:
            ghost_persuit = 24
        elif game_properties["ghosts_level"] == 0 and game_properties["ghosts"] >2:
            ghost_persuit = 22
        elif game_properties["ghosts_level"] == 1:
            ghost_persuit = 22
        elif game_properties["ghosts_level"] == 2:
            ghost_persuit = 18
        elif game_properties["ghosts_level"] == 3:
            ghost_persuit = 14
        else:
            ghost_persuit = 13

        mapa._initial_energies_count = len(mapa._energy)
       
        #init agent properties 
        key = 'a'
        pacman = Pacman((0,0))
        pacman.last_pos = pacman.pos


        while True: 
            r = await websocket.recv()
            start_time = int(round(time.time() * 1000))
            state = json.loads(r) #receive game state


            print("\nLives: ",state["lives"])
            if  'lives' not in state or not state['lives']:
                f = open("results.txt", "a")
                f.write("LOST | " + str(state["score"]) + " | " + str(state["lives"]) +  " | " +  str(game_properties["ghosts"]) +  " | " + str(game_properties["ghosts_level"]) + "\n")
                f.close()
                print("GAME OVER")
                return

            ghost_list = state["ghosts"]
            x,y = state['pacman']
            pacman.pos= (x,y)

            #caso o pacman esteja em cima de uma energia, remove-la:
            if (pacman.pos[0], pacman.pos[1]) in mapa._energy:
                mapa._energy.remove((pacman.pos[0], pacman.pos[1]))
            
            #remover o boost
            if (pacman.pos[0], pacman.pos[1]) in mapa._boost:
                mapa._boost.remove((pacman.pos[0], pacman.pos[1]))
        
            #ganhou o jogo
            if len(mapa._energy) == len(mapa._boost) == 0:
                f = open("results.txt", "a")
                f.write("WON | " + str(state["score"]) + " | " + str(state["lives"]) +  " | " +  str(game_properties["ghosts"]) +  " | " + str(game_properties["ghosts_level"]) + "\n")
                f.close()
                print("WON :D")
                sys.exit()

            #passar à parte da pesquisa segundo determinado target
            root = SearchNode(pacman.pos, None, 0)
            open_nodes = [root]     
            pacman.being_followed(ghost_list, mapa )
            next_target = pacman.find_next_target(ghost_list, mapa)           
            '''
            para teste
            ghost_list =[[[14,10], False, 0],[[14,5], False, 0],[[12,1], False, 0],[[15,29], False, 0]]
            pacman.pos = (16,4)
            next_target = (16,5) 
            root = SearchNode(pacman.pos, None, 0)
            open_nodes = [root]  
            '''
            path, node = search(pacman, next_target, open_nodes, mapa, ghost_list, start_time)   
            
            print("Pacman: ", pacman.pos)
            print("Target: ", next_target)
            print("Boosts: ", mapa._boost)
            print("Ghosts: ", ghost_list)
            print("Path: ", path[0] , " --> ", path[1])
            print("Solution Cost: ", node.cost)
            
            #escolher tecla perante uma posição inicial e uma posição final
            key = get_key_to_position(path[0], path[1])
            #print("key: ", key)

            pacman.last_pos = (path[0], path[1])
            
            elapsed_time = int(round(time.time() * 1000)) - start_time
            print("Time elapsed: ", elapsed_time)

            #para nao perder ciclos
            mesages_to_be_received = (elapsed_time -100)//100
            
            if mesages_to_be_received != 0:
                for i in range(0, mesages_to_be_received):
                    msg = await websocket.recv()
            #send new key
            await websocket.send(json.dumps({"cmd": "key", "key": key}))


loop = asyncio.get_event_loop()
SERVER = os.environ.get('SERVER', 'localhost')
PORT = os.environ.get('PORT', sys.argv[1])
#SERVER = os.environ.get('SERVER', 'pacman-aulas.ws.atnog.av.it.pt')
#PORT = os.environ.get('PORT', '80')
# $ python3 viewer.py --server pacman-aulas.ws.atnog.av.it.pt --port 80
NAME = os.environ.get('NAME', 'pacwoman')
loop.run_until_complete(agent_loop("{}:{}".format(SERVER,PORT), NAME))
