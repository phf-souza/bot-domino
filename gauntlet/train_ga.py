import random
from concurrent.futures import ProcessPoolExecutor
import time

# --- IMPORT YOUR FILES HERE ---
import main 
import bot_dupla_0 # Your bot (Player 0 & 2)
import bot_dupla_1 # The opponent "slot" (Player 1 & 3)

# Import the Gauntlet Opponents
import bot_baseline

# ==========================================
# GA HYPERPARAMETERS (Tweak these!)
# ==========================================
NUM_WEIGHTS = 8        # You have 8 heuristic functions
POPULATION_SIZE = 40   # Number of bots per generation
GENERATIONS = 50       # How many times to evolve
MUTATION_RATE = 0.1    # 10% chance a weight randomly changes
MUTATION_AMOUNT = 0.05  # How much a weight changes when mutated


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
    
    # NO MORE RANDOM OR SIMPLES. Just 5 hard matches vs the Phase 1 Champion!
    for _ in range(5):
        engine_baseline = main.criar_engine(bot_dupla_0.joga, bot_baseline.joga, "Bot Evo", "Baseline", target_score=50)
        main.jogar_partida(engine_baseline)
        
        # Make sure to update your calculate_match_score to expect 50 points again!
        total_score += calculate_match_score(engine_baseline["pontuacoes"], target=50) 
            
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
    
    # 1. Initialize Generation 0
    population = [create_random_bot() for _ in range(POPULATION_SIZE)]
    
    for gen in range(GENERATIONS):
        print(f"\n--- Generation {gen+1}/{GENERATIONS} ---")
        
        # 2. Evaluate Fitness (Using all CPU cores!)
        with ProcessPoolExecutor() as executor:
            # This runs 'evaluate_fitness' for every bot in the population simultaneously
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