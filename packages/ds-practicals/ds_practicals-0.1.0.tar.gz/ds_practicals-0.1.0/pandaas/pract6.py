"""
ML Practical 6 - Q-Learning Reinforcement Learning
"""

import numpy as np
import matplotlib.pyplot as plt

# Maze: 0 = path, -1 = wall, 1 = goal
maze = np.array([
    [ 0, -1,  0,  0,  0,  0],
    [ 0, -1,  0, -1,  0, -1],
    [ 0,  0,  0, -1,  0,  0],
    [-1, -1,  0, -1, -1,  0],
    [ 0,  0,  0,  0,  0,  0],
    [ 0, -1,  0, -1,  0,  1]
])

# Rewards and actions
rewards = {"goal": 100, "wall": -10, "step": -1}
actions = {0: (-1,0), 1: (1,0), 2: (0,-1), 3: (0,1)}  # up, down, left, right

rows, cols = maze.shape
q_table = np.zeros((rows, cols, len(actions)))

# Hyperparameters
alpha, gamma = 0.1, 0.99
epsilon, decay, min_epsilon = 1.0, 0.999, 0.01
episodes, max_steps = 3000, 100

for ep in range(episodes):
    r, c = 0, 0
    done = False
    for _ in range(max_steps):
        a = np.random.randint(4) if np.random.rand() < epsilon else np.argmax(q_table[r, c])
        dr, dc = actions[a]
        nr, nc = r + dr, c + dc
        done = False

        if nr < 0 or nr >= rows or nc < 0 or nc >= cols or maze[nr, nc] == -1:
            reward = rewards["wall"]
            nr, nc = r, c
        elif maze[nr, nc] == 1:
            reward = rewards["goal"]
            done = True
        else:
            reward = rewards["step"]

        q_table[r, c, a] += alpha * (reward + gamma * np.max(q_table[nr, nc]) - q_table[r, c, a])
        r, c = nr, nc
        if done:
            break
    epsilon = max(min_epsilon, epsilon * decay)

# Derive the best path from start to goal
r, c = 0, 0
path = [(r, c)]
for _ in range(50):
    a = np.argmax(q_table[r, c])
    dr, dc = actions[a]
    r, c = r + dr, c + dc
    path.append((r, c))
    if maze[r, c] == 1:
        break

# --- Visualization ---
plt.figure(figsize=(6, 6))
for i in range(rows):
    for j in range(cols):
        if maze[i, j] == -1:
            plt.fill_between([j, j+1], [i, i], [i+1, i+1], color='black')
        elif maze[i, j] == 1:
            plt.fill_between([j, j+1], [i, i], [i+1, i+1], color='gold')

# Draw the learned path
path_x = [c + 0.5 for (_, c) in path]
path_y = [r + 0.5 for (r, _) in path]
plt.plot(path_x, path_y, 'r-o', label='Learned Path')


plt.gca().invert_yaxis()
plt.title("Reinforcement Learning Maze Path (Q-Learning)")
plt.legend()
plt.show()


def print_code():
    """Prints the entire code of this practical."""
    code = '''"""
ML Practical 6 - Q-Learning Reinforcement Learning
"""

import numpy as np
import matplotlib.pyplot as plt

# Maze: 0 = path, -1 = wall, 1 = goal
maze = np.array([
    [ 0, -1,  0,  0,  0,  0],
    [ 0, -1,  0, -1,  0, -1],
    [ 0,  0,  0, -1,  0,  0],
    [-1, -1,  0, -1, -1,  0],
    [ 0,  0,  0,  0,  0,  0],
    [ 0, -1,  0, -1,  0,  1]
])

# Rewards and actions
rewards = {"goal": 100, "wall": -10, "step": -1}
actions = {0: (-1,0), 1: (1,0), 2: (0,-1), 3: (0,1)}  # up, down, left, right

rows, cols = maze.shape
q_table = np.zeros((rows, cols, len(actions)))

# Hyperparameters
alpha, gamma = 0.1, 0.99
epsilon, decay, min_epsilon = 1.0, 0.999, 0.01
episodes, max_steps = 3000, 100

for ep in range(episodes):
    r, c = 0, 0
    done = False
    for _ in range(max_steps):
        a = np.random.randint(4) if np.random.rand() < epsilon else np.argmax(q_table[r, c])
        dr, dc = actions[a]
        nr, nc = r + dr, c + dc
        done = False

        if nr < 0 or nr >= rows or nc < 0 or nc >= cols or maze[nr, nc] == -1:
            reward = rewards["wall"]
            nr, nc = r, c
        elif maze[nr, nc] == 1:
            reward = rewards["goal"]
            done = True
        else:
            reward = rewards["step"]

        q_table[r, c, a] += alpha * (reward + gamma * np.max(q_table[nr, nc]) - q_table[r, c, a])
        r, c = nr, nc
        if done:
            break
    epsilon = max(min_epsilon, epsilon * decay)

# Derive the best path from start to goal
r, c = 0, 0
path = [(r, c)]
for _ in range(50):
    a = np.argmax(q_table[r, c])
    dr, dc = actions[a]
    r, c = r + dr, c + dc
    path.append((r, c))
    if maze[r, c] == 1:
        break

# --- Visualization ---
plt.figure(figsize=(6, 6))
for i in range(rows):
    for j in range(cols):
        if maze[i, j] == -1:
            plt.fill_between([j, j+1], [i, i], [i+1, i+1], color='black')
        elif maze[i, j] == 1:
            plt.fill_between([j, j+1], [i, i], [i+1, i+1], color='gold')

# Draw the learned path
path_x = [c + 0.5 for (_, c) in path]
path_y = [r + 0.5 for (r, _) in path]
plt.plot(path_x, path_y, 'r-o', label='Learned Path')


plt.gca().invert_yaxis()
plt.title("Reinforcement Learning Maze Path (Q-Learning)")
plt.legend()
plt.show()'''
    print(code)

