import subprocess
import threading
import os
import time
runs=[]
# ( runs, porta)


'''
runs.append((1, 8080))
runs.append((10, 8081))
runs.append((10, 8082))
runs.append((10, 8083))
runs.append((11, 8084))
runs.append((9, 8085))

runs.append((10, 8086))
runs.append((12, 8087))

runs.append((12, 8088))

runs.append((10, 8089))
'''
runs.append((10, 8090))


runs.append((10, 8091))
runs.append((12, 8092))
runs.append((12, 8093))
runs.append((10, 8094))

'''
python3 server.py --ghosts 0 --level 1 --port 8080   &
python3 server.py --ghosts 1 --level 1 --port 8081   &
python3 server.py --ghosts 2 --level 2 --port 8082   &
python3 server.py --ghosts 4 --level 0 --port 8083   &
python3 server.py --ghosts 4 --level 1 --port 8084   &
python3 server.py --ghosts 4 --level 2 --port 8085   &
python3 server.py --ghosts 1 --level 1 --port 8086  --map data/map2.bmp &
python3 server.py --ghosts 2 --level 1 --port 8087 --map data/map2.bmp &
python3 server.py --ghosts 4 --level 0 --port 8088 --map data/map2.bmp &
python3 server.py --ghosts 4 --level 1 --port 8089 --map data/map2.bmp &
python3 server.py --ghosts 4 --level 2 --port 8090 --map data/map2.bmp &
'''

# python3 server.py --ghosts 0 --level 1 --port 8080   &
# python3 server.py --ghosts 1 --level 1 --port 8081   &
# python3 server.py --ghosts 2 --level 2 --port 8082   &
# python3 server.py --ghosts 4 --level 0 --port 8083   &
# python3 server.py --ghosts 4 --level 1 --port 8084   &
# python3 server.py --ghosts 4 --level 2 --port 8085   &

# python3 server.py --ghosts 1 --level 1 --port 8086  --map data/map2.bmp &
# python3 server.py --ghosts 2 --level 1 --port 8087 --map data/map2.bmp &
# python3 server.py --ghosts 4 --level 0 --port 8088 --map data/map2.bmp &
# python3 server.py --ghosts 4 --level 1 --port 8089 --map data/map2.bmp &
# python3 server.py --ghosts 4 --level 2 --port 8090 --map data/map2.bmp &


# python3 server.py --ghosts 2 --level 3 --port 8091   &
# python3 server.py --ghosts 4 --level 3 --port 8092   &
# python3 server.py --ghosts 2 --level 3 --port 8093 --map data/map2.bmp &
# python3 server.py --ghosts 4 --level 3 --port 8094 --map data/map2.bmp &

'''
os.system('source venv/bin/activate')
os.system(' python3 server.py --ghosts 4 --level 2')
time.sleep(1)
os.system('python3 viewer.py')
time.sleep(1)
os.system('python3 student.py')
'''
for r in runs:
    for run_number in range(0, r[0]):
        os.system('python3 student_args.py ' + str(r[1]))
        print(" One game is done!")
