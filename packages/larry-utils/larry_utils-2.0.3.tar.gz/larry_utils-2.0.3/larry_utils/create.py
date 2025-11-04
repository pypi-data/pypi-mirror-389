d1 = open('deviant').read().split('\n')
d2 = open('danbooru').read().split('\n')


map = {}
for i in range(max(len(d1), len(d2))):
    if len(d1) > i:
        l = d1[i].split('\t')
        if len(l) != 2:
            continue
        if l[0] not in map:
            map[l[0]] = l[1]
    if len(d2) > i:
        l = d2[i].split('\t')
        if len(l) != 2:
            continue
        if l[0] not in map:
            map[l[0]] = l[1]
print(len(map))
import pickle 
with open('map.pkl', 'wb') as f:
    f.write(pickle.dumps(map))
