import os
import json

directory = "logs"

results = {}
for filename in os.listdir(directory):
    with open(os.path.join(directory, filename)) as f:
        lines = f.readlines()
        if lines:
            last_line = lines[-1]
            parts = last_line.split()
            team1 = parts[1]
            team1_score = int(parts[2][1:-2])
            team2 = parts[3]
            team2_score = int(parts[4][1:-2])
            
            index = sorted([team1, team2])
            index = index[0] + " vs " + index[1]
            if index not in results:
                results[index] = {team1: 0, team2: 0}

            if team1_score > team2_score:
                results[index][team1] += 1
            elif team1_score == team2_score:
                results[index][team1] += 0.5
                results[index][team2] += 0.5
            else:
                results[index][team2] += 1
            
with open("winners.txt", 'w') as f:
    json.dump(results, f)