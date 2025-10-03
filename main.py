# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import simpy
import random
import statistics
import matplotlib.pyplot as plt

# PARAMETERS
NUM_BEDS = 10
SIM_TIME = 1000         # total simulation time
ARRIVAL_RATE = 5        # avg time btw patient arrivals
TREATMENT_TIME = (10,30)     # treatment duration range (min, max)
SEVERITY_LEVELS = [1, 2, 3]   # 1 = critical, 3 = mild

# DATA COLLECTION
wait_times = {1: [], 2: [], 3: []}
queue_lengths = []
utilization = []
time_points = []

# PATIENT PROCESS
def patient(env, name, hospital, severity):
    arrival_time = env.now

    # Request bed with priority
    with hospital.request(priority=severity) as req:
        yield req
        wait_time = env.now - arrival_time
        wait_times[severity].append(wait_time)

        treatment_duration = random.uniform(*TREATMENT_TIME)
        yield env.timeout(treatment_duration)

# ARRIVAL PROCESS
def arrival_process(env, hospital):
    i = 0
    while True:
        yield env.timeout(random.expovariate(1.0 / ARRIVAL_RATE))
        i += 1
        severity = random.choices(SEVERITY_LEVELS, weights=[0.2, 0.3, 0.5])[0]
        env.process(patient(env, f"Patient {i}", hospital, severity))

# MONITORING PROCESS
def monitor(env, hospital):
    while True:
        queue_lengths.append(len(hospital.queue))
        utilization.append(hospital.count / NUM_BEDS)
        time_points.append(env.now)
        yield env.timeout(1)

# MAIN SIMULATION
env = simpy.Environment()
hospital = simpy.PriorityResource(env, capacity=3)

env.process(arrival_process(env, hospital))
env.process(monitor(env, hospital))
env.run(until=SIM_TIME)

# RESULTS
print("\n--- Simulation Results ---")
for s in SEVERITY_LEVELS:
    if wait_times[s]:
        print(f"Priority {s} avg wait time: {statistics.mean(wait_times[s]):.2f}")
        print(f"Priority {s} max wait time: {max(wait_times[s]):.2f}")
print("Total patients served:", sum(len(w) for w in wait_times.values()))

# PLOTS
plt.figure()
plt.plot(time_points, queue_lengths)
plt.xlabel("Time")
plt.ylabel("Queue Length")
plt.title("Queue Length Over Time")
plt.show()

plt.figure()
plt.plot(time_points, utilization)
plt.xlabel("Time")
plt.ylabel("Bed Utilization (fraction)")
plt.title("Bed Utilization Over Time")
plt.show()





# See PyCharm help at https://www.jetbrains.com/help/pycharm/
