import random
from concurrent.futures import ProcessPoolExecutor
import time
import importlib


# --- IMPORT YOUR FILES HERE ---
import main 
import bot_dupla_0 # Your bot (Player 0 & 2)

# ==========================================
# GA HYPERPARAMETERS (Tweak these!)
# ==========================================
NUM_WEIGHTS = 8        # You have 8 heuristic functions
POPULATION_SIZE = 40   # Number of bots per generation
GENERATIONS = 50       # How many times to evolve
MUTATION_RATE = 0.1    # 10% chance a weight randomly changes
MUTATION_AMOUNT = 0.05  # How much a weight changes when mutated
LEAGUE_OF_OPPONENTS = ["bot_baseline", "bot_orion"] 


def create_random_bot():
    """Creates a bot with 8 random weights between 0.0 and 1.0"""
    return [random.uniform(0.0, 1.0) for _ in range(NUM_WEIGHTS)]

def calculate_match_score(pontuacoes, target=50):
    """
    pontuacoes is a list: [Team_0_Score, Team_1_Score]
    Team 0 is ALWAYS our bot.
    'target' lets us easily switch between 20-point and 50-point matches.
    """
    my_score = pontuacoes[0]
    opp_score = pontuacoes[1]
    
    if my_score >= target:
        # We won! Reward 100 points, PLUS bonus points for keeping their score low.
        return 100 + (target - opp_score) 
    else:
        # We lost. Penalize 50 points, AND deduct more if we got crushed.
        return -50 - opp_score




def evaluate_fitness(weights):
    bot_dupla_0.GLOBAL_GA_WEIGHTS = weights
    total_score = 0
    
    # Iterate through every bot in your league
    for opponent_name in LEAGUE_OF_OPPONENTS:
        # Dynamically import the module
        opponent_module = importlib.import_module(opponent_name)
        
        # Play matches against this specific opponent
        for _ in range(3):
            engine = main.criar_engine(
                bot_dupla_0.joga, 
                opponent_module.joga, 
                "Bot Evo", 
                opponent_name, 
                target_score=50
            )
            main.jogar_partida(engine)
            total_score += calculate_match_score(engine["pontuacoes"], target=50)
            
    return total_score

def crossover(parent1, parent2):
    """Mixes the weights of two good bots to create a child"""
    child = []
    for i in range(NUM_WEIGHTS):
        # 50/50 chance to inherit weight from Parent 1 or Parent 2
        if random.random() > 0.5:
            child.append(parent1[i])
        else:
            child.append(parent2[i])
    return child

def mutate(weights):
    """Randomly tweaks weights to discover new strategies"""
    mutated = []
    for w in weights:
        if random.random() < MUTATION_RATE:
            # Add or subtract a small amount
            new_w = w + random.uniform(-MUTATION_AMOUNT, MUTATION_AMOUNT)
            # Keep weights between 0 and 1
            new_w = max(0.0, min(1.0, new_w)) 
            mutated.append(new_w)
        else:
            mutated.append(w)
    return mutated

# ==========================================
# THE MAIN TRAINING LOOP
# ==========================================
if __name__ == '__main__':
    print("Starting Genetic Algorithm Training...")
    start_time = time.time()
    
    PHASE_1_CHAMPION = [0.4963672738699805, 0.8255614294145706, 0.40841805357868727, 0.22510209926977592, 0.5944135949014532, 0.9682123229548345, 0.3331048927926647, 0.13374204812263957]

    population = [PHASE_1_CHAMPION] # Start with the champion
    for _ in range(POPULATION_SIZE - 1):
        # Fill the rest with slightly mutated versions of the champion
        population.append(mutate(PHASE_1_CHAMPION))
    
    for gen in range(GENERATIONS):
        print(f"\n--- Generation {gen+1}/{GENERATIONS} ---")
        
        # 2. Evaluate Fitness (Using all CPU cores!)
        with ProcessPoolExecutor(max_workers=16) as executor:
            fitness_scores = list(executor.map(evaluate_fitness, population))
        
        # Pair bots with their scores and sort them (highest score first)
        scored_population = list(zip(population, fitness_scores))
        scored_population.sort(key=lambda x: x[1], reverse=True)
        
        best_bot, best_score = scored_population[0]
        print(f"Best Score: {best_score} | Weights: {[round(w, 2) for w in best_bot]}")
        
        # 3. Selection (Keep the top 20%)
        num_elite = int(POPULATION_SIZE * 0.2)
        next_generation = [bot for bot, score in scored_population[:num_elite]]
        
        # 4. Breed to fill the rest of the population
        while len(next_generation) < POPULATION_SIZE:
            # Pick two random parents from the top 50%
            top_half = [bot for bot, score in scored_population[:int(POPULATION_SIZE/2)]]
            p1 = random.choice(top_half)
            p2 = random.choice(top_half)
            
            # Crossover & Mutate
            child = crossover(p1, p2)
            child = mutate(child)
            next_generation.append(child)
            
        population = next_generation
        
    print(f"\nTraining Complete in {(time.time() - start_time)/60:.1f} minutes!")
    print(f"THE ULTIMATE WEIGHTS: {best_bot}")