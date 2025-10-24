# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import simpy
import random
import statistics
import matplotlib.pyplot as plt

# PARAMETERS
NUM_BEDS = 10
SIM_TIME = 500         # total simulation time
ARRIVAL_RATE = 4        # 4 patients per hour
TREATMENT_TIME = (10,30)     # treatment duration range (min, max)
SEVERITY_LEVELS = [0, 1, 2]   # 0 = critical, 2 = mild
SEVERITY_NAMES = {0: "Critical", 1: "Serious", 2: "Mild"}

# DATA COLLECTION
wait_times = {0: [], 1: [], 2: []}
queue_lengths = []
utilization = []
time_points = []

# PATIENT PROCESS
def patient(env, name, hospital, severity):
    arrival_time = env.now

    # print(f"{name} with severity {severity} arrives at {arrival_time:.2f}")

    # Request bed with priority
    with hospital.request(priority=severity) as req:
        yield req
        wait_time = env.now - arrival_time
        wait_times[severity].append(wait_time)

        # print(f"{name} admitted at {env.now:.2f} after waiting {wait_time:.2f}")

        # treatment time
        treatment_duration = random.uniform(*TREATMENT_TIME)
        yield env.timeout(treatment_duration)

        # print(f"{name} discharged at {env.now:.2f} (treatment {treatment_duration:.2f})")

# ARRIVAL PROCESS
def arrival_process(env, hospital):
    i = 0
    while True:
        # exponential interarrival time
        yield env.timeout(random.expovariate(1 / ARRIVAL_RATE))
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
# 1. Average Wait Time per Severity
avg_waits = [
    sum(wait_times[s]) / len(wait_times[s]) if wait_times[s] else 0
    for s in SEVERITY_LEVELS
]
plt.figure(figsize=(8, 5))
plt.bar(SEVERITY_NAMES.values(), avg_waits, color=['red', 'orange', 'green'])
plt.title("Average Wait Time per Severity Level")
plt.ylabel("Average Wait Time")
plt.show()

# 2. Hospital Utilization Over Time
plt.figure(figsize=(8, 5))
plt.plot(time_points, utilization, label="Utilization")
plt.title("Hospital Bed Utilization Over Time")
plt.xlabel("Time")
plt.ylabel("Utilization (fraction)")
plt.ylim(0, 1.1)
plt.legend()
plt.show()

# 3. Queue Length Over Time
plt.figure(figsize=(8, 5))
plt.plot(time_points, queue_lengths, label="Queue Length", color='purple')
plt.title("Queue Length Over Time")
plt.xlabel("Time")
plt.ylabel("Number of Patients Waiting")
plt.legend()
plt.show()

# 4. Histogram of Wait Times per Severity
plt.figure(figsize=(10, 6))
colors = {0: "red", 1: "orange", 2: "green"}

for s in SEVERITY_LEVELS:
    if wait_times[s]:  # only plot if we had patients of that severity
        plt.hist(wait_times[s], bins=20, alpha=0.6, label=SEVERITY_NAMES[s], color=colors[s])

plt.title("Wait Time Distribution by Severity")
plt.xlabel("Wait Time")
plt.ylabel("Number of Patients")
plt.legend()
plt.show()



# See PyCharm help at https://www.jetbrains.com/help/pycharm/
