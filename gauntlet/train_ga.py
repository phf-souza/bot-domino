import random
from concurrent.futures import ProcessPoolExecutor
import time
import importlib
import main 
import bot_dupla_0

# ==========================================
# TRAINING PARAMETERS
# ==========================================
NUM_WEIGHTS = 8        
POPULATION_SIZE = 40   
GENERATIONS = 50       
MUTATION_RATE = 0.1    
MUTATION_AMOUNT = 0.05 
LEAGUE_OF_OPPONENTS = ["bot_baseline", "bot_random"] 

# ==========================================
# MATCH RUNNING
# ==========================================
def evaluate_fitness(weights):
    """Runs the match cycle"""
    bot_dupla_0.GLOBAL_GA_WEIGHTS = weights
    total_score = 0
    
    for opponent_name in LEAGUE_OF_OPPONENTS:
        opponent_module = importlib.import_module(opponent_name)
        
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

# ==========================================
# GENETIC FUNCTIONS
# ==========================================
def crossover(parent1, parent2):
    """Mixes the weights of two bots"""
    child = []
    for i in range(NUM_WEIGHTS):
        if random.random() > 0.5:
            child.append(parent1[i])
        else:
            child.append(parent2[i])
    return child

def mutate(weights):
    """Randomly tweaks weights"""
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
# HELPER FUNCTIONS
# ==========================================
def create_random_bot():
    """Creates a bot with random weights"""
    return [random.uniform(0.0, 1.0) for _ in range(NUM_WEIGHTS)]

def calculate_match_score(pontuacoes, target=50):
    """Calculates match quality"""
    my_score = pontuacoes[0]
    opp_score = pontuacoes[1]
    
    if my_score >= target:
        return 100 + (target - opp_score) 
    else:
        return -50 + my_score

# ==========================================
# THE GAUNTLET!!!!
# ==========================================
if __name__ == '__main__':
    print("Starting Genetic Algorithm Training...")
    start_time = time.time()
    
    PHASE_1_CHAMPION = [0.4963672738699805, 0.8255614294145706, 0.40841805357868727, 0.22510209926977592, 0.5944135949014532, 0.9682123229548345, 0.3331048927926647, 0.13374204812263957]

    population = [PHASE_1_CHAMPION]
    for _ in range(POPULATION_SIZE - 1):
        population.append(mutate(PHASE_1_CHAMPION))
    
    for gen in range(GENERATIONS):
        print(f"\n--- Generation {gen+1}/{GENERATIONS} ---")
        
        with ProcessPoolExecutor(max_workers=16) as executor:
            fitness_scores = list(executor.map(evaluate_fitness, population))
        
        scored_population = list(zip(population, fitness_scores))
        scored_population.sort(key=lambda x: x[1], reverse=True)
        
        best_bot, best_score = scored_population[0]
        print(f"Best Score: {best_score} | Weights: {[round(w, 2) for w in best_bot]}")
        
        num_elite = int(POPULATION_SIZE * 0.2)
        next_generation = [bot for bot, score in scored_population[:num_elite]]
        
        while len(next_generation) < POPULATION_SIZE:
            top_half = [bot for bot, score in scored_population[:num_elite]]
            p1 = random.choice(top_half)
            p2 = random.choice(top_half)
            
            child = crossover(p1, p2)
            child = mutate(child)
            next_generation.append(child)
            
        population = next_generation
        
    print(f"\nTraining Complete in {(time.time() - start_time)/60:.1f} minutes.")
    print(f"BEHOLD THE CHAMPION: {best_bot}")