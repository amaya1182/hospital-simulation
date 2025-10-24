import simpy
import random
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

# -------------------------------
# Core Simulation Function
# -------------------------------
def run_simulation(run_id, num_doctors, arrival_rate, service_rate, sim_time=28800):
    results = []
    queue_snapshots = []

    class Hospital:
        def __init__(self, env):
            self.doctor = simpy.PriorityResource(env, capacity=num_doctors)

    def patient(env, name, severity, hospital):
        arrival_time = env.now
        with hospital.doctor.request(priority=PRIORITIES[severity]) as req:
            yield req
            wait_time = env.now - arrival_time
            service_time = random.expovariate(service_rate)
            yield env.timeout(service_time)
            results.append({
                "Patient": name,
                "Severity": severity,
                "ArrivalTime": arrival_time,
                "WaitTime": wait_time,
                "ServiceTime": service_time,
                "DepartTime": env.now
            })

    def arrival_generator(env, hospital):
        i = 0
        while True:
            yield env.timeout(random.expovariate(arrival_rate))
            i += 1
            severity = random.choices(["High", "Medium", "Low"], weights=[0.2, 0.3, 0.5])[0]
            env.process(patient(env, f"Patient_{i}", severity, hospital))

    def monitor(env, hospital, interval=5):
        while True:
            queue_snapshots.append({
                "Timestamp": env.now,
                "QueueLength": len(hospital.doctor.queue),
                "Utilization": hospital.doctor.count / num_doctors
            })
            yield env.timeout(interval)

    # Priority levels (lower = higher priority)
    PRIORITIES = {"High": 0, "Medium": 1, "Low": 2}

    # -------------------------------
    # Run the simulation
    # -------------------------------
    random.seed(run_id)
    env = simpy.Environment()
    hospital = Hospital(env)
    env.process(arrival_generator(env, hospital))
    env.process(monitor(env, hospital))
    env.run(until=sim_time)

    df = pd.DataFrame(results)
    ts = pd.DataFrame(queue_snapshots)

    # Compute summary metrics
    summary = {
        "RunID": run_id,
        "NumDoctors": num_doctors,
        "ArrivalRate": arrival_rate,
        "ServiceRate": service_rate,
        "AvgWaitingTime_Low": df[df.Severity=="Low"]["WaitTime"].mean(),
        "AvgWaitingTime_Medium": df[df.Severity=="Medium"]["WaitTime"].mean(),
        "AvgWaitingTime_High": df[df.Severity=="High"]["WaitTime"].mean(),
        "AvgQueueLength": ts["QueueLength"].mean(),
        "AvgSystemTime": (df["WaitTime"] + df["ServiceTime"]).mean(),
        "ResourceUtilization": ts["Utilization"].mean(),
        "Throughput": len(df) / (sim_time / 60)  # patients/hour
    }

    # Save individual CSV
    filename = f"run_{run_id:03d}.csv"
    with open(filename, "w") as f:
        f.write("# --- Metadata ---\n")
        f.write(f"RunID,{run_id}\nDate,{datetime.now()}\nNumDoctors,{num_doctors}\nArrivalRate,{arrival_rate}\nServiceRate,{service_rate}\nSimulationDuration,{sim_time}\n")
        f.write("\n# --- Summary Metrics ---\n")
        pd.DataFrame(summary.items(), columns=["Metric", "Value"]).to_csv(f, index=False)
        f.write("\n# --- Time-Series Data ---\n")
        ts.to_csv(f, index=False)

    return summary

# -------------------------------
# Batch Run Configuration
# -------------------------------
if __name__ == "__main__":
    scenarios = [
        {"num_doctors": 3, "arrival_rate": 0.4, "service_rate": 1/5},
        {"num_doctors": 3, "arrival_rate": 0.6, "service_rate": 1/5},
        {"num_doctors": 3, "arrival_rate": 0.2, "service_rate": 1/5},
        {"num_doctors": 5, "arrival_rate": 0.6, "service_rate": 1/5},
        {"num_doctors": 5, "arrival_rate": 0.2, "service_rate": 1/5},
    ]

    all_summaries = []
    for i, sc in enumerate(scenarios, start=1):
        print(f"Running Scenario {i} with {sc['num_doctors']} doctors...")
        summary = run_simulation(i, sc["num_doctors"], sc["arrival_rate"], sc["service_rate"])
        all_summaries.append(summary)

    # Save master summary
    df_summary = pd.DataFrame(all_summaries)
    df_summary.to_csv("summary_all_runs.csv", index=False)
    print("✅ All runs complete. Summary saved to summary_all_runs.csv")


# -----------------------------
# Load Summary Data
# -----------------------------
df = pd.read_csv("summary_all_runs.csv")

# Convert values if needed
df = df.sort_values("NumDoctors")

# -----------------------------
# Plot 1: Average Waiting Time by Severity
# -----------------------------
plt.figure()
plt.plot(df["NumDoctors"], df["AvgWaitingTime_Low"], marker='o', label="Low Severity")
plt.plot(df["NumDoctors"], df["AvgWaitingTime_Medium"], marker='o', label="Medium Severity")
plt.plot(df["NumDoctors"], df["AvgWaitingTime_High"], marker='o', label="High Severity")
plt.title("Average Waiting Time vs Number of Doctors")
plt.xlabel("Number of Doctors")
plt.ylabel("Average Waiting Time (minutes)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# -----------------------------
# Plot 2: Resource Utilization
# -----------------------------
plt.figure()
plt.plot(df["NumDoctors"], df["ResourceUtilization"], marker='s', linewidth=2)
plt.title("Doctor Utilization vs Number of Doctors")
plt.xlabel("Number of Doctors")
plt.ylabel("Utilization (fraction of time busy)")
plt.grid(True)
plt.tight_layout()
plt.show()

# -----------------------------
# Plot 3: Throughput
# -----------------------------
plt.figure()
plt.plot(df["NumDoctors"], df["Throughput"], marker='^', linewidth=2)
plt.title("Throughput vs Number of Doctors")
plt.xlabel("Number of Doctors")
plt.ylabel("Throughput (patients/hour)")
plt.grid(True)
plt.tight_layout()
plt.show()

# -----------------------------
# Plot 4: Average Queue Length
# -----------------------------
plt.figure()
plt.plot(df["NumDoctors"], df["AvgQueueLength"], marker='d', linewidth=2)
plt.title("Average Queue Length vs Number of Doctors")
plt.xlabel("Number of Doctors")
plt.ylabel("Average Queue Length (patients)")
plt.grid(True)
plt.tight_layout()
plt.show()
