import pandas as pd  # Imports pandas, which is used to create tables/DataFrames and save CSV/Excel files.
import os  # Imports os, which is used to work with file paths and folders on your computer.
import random  # Imports random, which is used to generate random project durations, capacities, and waste rates.
import matplotlib.pyplot as plt  # Imports matplotlib, which is used to create and save dashboard graphs.

# =========================================================
# MONTE CARLO SETTINGS - SINGLE CONTAINER FOR ALL WASTE
# =========================================================

# This is the number of random simulation scenarios that will be generated.
# A Monte Carlo simulation does not test only one fixed project.
# Instead, it runs the same logic many times with different random inputs.
# Here, the model creates 1000 different possible construction projects.
NUMBER_OF_RUNS = 1000

# This is the minimum possible project duration used in the random simulation.
MIN_PROJECT_DAYS = 100

# This is the maximum possible project duration used in the random simulation.
MAX_PROJECT_DAYS = 1000

# This is the minimum possible capacity of the shared waste container, in cubic meters.
MIN_CONTAINER_CAPACITY = 10

# This is the maximum possible capacity of the shared waste container, in cubic meters.
MAX_CONTAINER_CAPACITY = 40

# This controls the maximum random daily waste generation.
# For example, if the shared container capacity is 20 m3, then each waste stream can generate
# up to 20 * 0.30 = 6 m3/day in a phase.
MAX_DAILY_WASTE_AS_CAPACITY_RATIO = 0.30

# This is the assumed working time needed for one truck/container pickup operation.
HOURS_PER_PICKUP = 1.5

# This converts site delay days into delay hours.
# For example, 1 delay day = 8 working hours.
WORKING_HOURS_PER_DELAY_DAY = 8

# This is the assumed one-way distance from the site to the disposal/recycling facility.
AVERAGE_ONE_WAY_DISTANCE_KM = 15

# This calculates the truck round-trip distance.
# The truck goes from the site to the facility and then returns, so the one-way distance is multiplied by 2.
ROUND_TRIP_DISTANCE_KM = AVERAGE_ONE_WAY_DISTANCE_KM * 2

# This is the assumed CO2 emission factor for the truck, in kg CO2 per kilometer.
CO2_EMISSION_FACTOR_KG_PER_KM = 0.9

# This is the name/description of the container type used in this script.
# In this version, all waste streams share one mixed-waste container.
SHARED_CONTAINER_TYPE = "Shared mixed-waste container"

# This is the fixed pickup frequency used by the Fixed Schedule strategy.
# In this case, the shared container is collected once per week.
SHARED_CONTAINER_FREQUENCY = "Weekly"

# This fixes the random generator sequence.
# It means that every time you run the script, you get the same random results.
# This is useful for reports because your numbers do not change every time you run the code.
random.seed(42)

# =========================================================
# OUTPUT FOLDER
# =========================================================

# This finds the folder where the current Python script is located.
# __file__ is the path of this Python file.
# os.path.abspath(__file__) converts it to a full absolute path.
# os.path.dirname(...) takes only the folder part of that path.
script_folder = os.path.dirname(os.path.abspath(__file__))

# This creates the path of the output folder where all results will be saved.
# The folder will be created inside the same folder as this script.
output_folder = os.path.join(script_folder, "monte_carlo_single_container_results")

# This creates the output folder if it does not already exist.
# exist_ok=True means Python will not give an error if the folder already exists.
os.makedirs(output_folder, exist_ok=True)

# =========================================================
# WASTE TYPES
# =========================================================

# This list contains the waste streams considered in the simulation.
# In this single-container version, these waste streams are not assigned separate containers.
# Instead, their daily volumes are added together and placed into one shared container.
waste_types = [
    "Concrete & Masonry",
    "Wood",
    "Metals",
    "Drywall",
    "Packaging",
    "Mixed Residual Waste"
]

# This list contains the construction phases used in the project.
# Each simulated project is randomly split into these four phases.
phase_names = [
    "Site Preparation",
    "Foundation",
    "Interior",
    "Finishing"
]

# =========================================================
# FUNCTIONS
# =========================================================

# This function randomly splits the total project duration into four phase durations.
# Example:
# If the full project is 300 days, the function may split it like this:
# Site Preparation = 40 days
# Foundation = 80 days
# Interior = 120 days
# Finishing = 60 days
# The important point is that the sum of all four phase durations equals total_days.
def split_project_days(total_days):
    # This chooses the first random cut point inside the total project duration.
    # It cannot be too close to the end because we still need space for the other phases.
    cut1 = random.randint(1, total_days - 3)

    # This chooses the second random cut point after cut1.
    # It must be larger than cut1 so that the second phase has a positive duration.
    cut2 = random.randint(cut1 + 1, total_days - 2)

    # This chooses the third random cut point after cut2.
    # It must be larger than cut2 so that the third phase has a positive duration.
    cut3 = random.randint(cut2 + 1, total_days - 1)

    # This returns the length of each phase.
    # Phase 1 is from day 0 to cut1.
    # Phase 2 is from cut1 to cut2.
    # Phase 3 is from cut2 to cut3.
    # Phase 4 is from cut3 to the end of the project.
    return [
        cut1,
        cut2 - cut1,
        cut3 - cut2,
        total_days - cut3
    ]


# This function creates one complete random input scenario for one Monte Carlo run.
# It generates:
# 1. A random total project duration.
# 2. A random shared container capacity.
# 3. Random phase durations.
# 4. Random daily waste generation for every waste stream in every phase.
# 5. An input table that records all generated random values for traceability.
def create_random_input_data(run_id):
    # This randomly selects the total project duration for this run.
    # The duration is between MIN_PROJECT_DAYS and MAX_PROJECT_DAYS.
    total_project_days = random.randint(MIN_PROJECT_DAYS, MAX_PROJECT_DAYS)

    # This randomly selects the capacity of the shared container for this run.
    # Unlike the multi-container version, there is only one container capacity here.
    shared_container_capacity = random.uniform(
        MIN_CONTAINER_CAPACITY,
        MAX_CONTAINER_CAPACITY
    )

    # This splits the total project duration into the four construction phases.
    phase_days = split_project_days(total_project_days)

    # This creates a DataFrame that connects each phase name with its random duration.
    phase_df = pd.DataFrame({
        "Phase": phase_names,
        "Days": phase_days
    })

    # This empty dictionary will store the random daily waste generation values.
    # The structure will be like:
    # {
    #   "Wood": [daily waste in Site Prep, daily waste in Foundation, ...],
    #   "Metals": [...]
    # }
    random_daily_data = {}

    # This loop goes through every waste type and generates its daily waste rate for each phase.
    for waste in waste_types:
        # For the current waste stream, this creates one random daily generation value for each phase.
        # Because this is a single-container model, every waste stream is generated relative to the
        # same shared container capacity.
        random_daily_data[waste] = [
            round(
                random.uniform(
                    0,
                    shared_container_capacity * MAX_DAILY_WASTE_AS_CAPACITY_RATIO
                ),
                3
            )
            for _ in phase_names
        ]

    # This converts the random daily waste dictionary into a DataFrame.
    # Rows are waste streams.
    # Columns are project phases.
    # Each cell shows the daily generation rate in m3/day for that waste stream in that phase.
    daily_df = pd.DataFrame(
        random_daily_data,
        index=phase_names
    ).T

    # This empty list will be used to build a detailed input table row by row.
    input_rows = []

    # This nested loop creates one input record for every phase and every waste stream.
    # This is useful because later you can check exactly which random input was used in every run.
    for phase in phase_names:
        for waste in waste_types:
            input_rows.append({
                "Run ID": run_id,
                "Total Project Days": total_project_days,
                "Shared Container Capacity m3": round(shared_container_capacity, 2),
                "Phase": phase,
                "Phase Days": int(phase_df.loc[phase_df["Phase"] == phase, "Days"].iloc[0]),
                "Waste Stream": waste,
                "Random Daily Waste Generation m3/day": daily_df.loc[waste, phase]
            })

    # This converts the list of input records into a DataFrame.
    input_df = pd.DataFrame(input_rows)

    # This returns all generated input data so the simulation functions can use it.
    return total_project_days, shared_container_capacity, phase_df, daily_df, input_df


# This function converts a pickup frequency name into actual pickup days.
# Example:
# If frequency is Weekly and the phase has 30 days, pickups happen on days 7, 14, 21, and 28.
def get_pickup_days(frequency, phase_days):
    # If pickup is daily, the container is collected every day.
    if frequency == "Daily":
        return list(range(1, phase_days + 1))

    # If pickup is weekly, the container is collected every 7 days.
    if frequency == "Weekly":
        return list(range(7, phase_days + 1, 7))

    # If pickup is twice per week, this simple model collects on days divisible by 3 or 7.
    # This is an approximation, not a real calendar schedule.
    if frequency == "Twice per week":
        return [
            day for day in range(1, phase_days + 1)
            if day % 3 == 0 or day % 7 == 0
        ]

    # If the frequency is not recognized, no scheduled pickup days are returned.
    return []


# This function simulates the Fixed Schedule strategy for one Monte Carlo run.
# Fixed Schedule means the container is picked up according to a fixed rule,
# regardless of how full the container is.
# In this script, the shared container is picked up weekly.
def simulate_fixed(run_id, total_project_days, shared_container_capacity, phase_df, daily_df):
    # This list will store the result rows for all phases in this run.
    results = []

    # This loop goes through each construction phase.
    for _, phase_row in phase_df.iterrows():
        # This gets the name of the current phase.
        phase_name = phase_row["Phase"]

        # This gets the duration of the current phase in days.
        phase_days = int(phase_row["Days"])

        # This is the key difference in the single-container model.
        # The model adds together the daily waste generation of all waste streams for the current phase.
        # Example:
        # Concrete = 2 m3/day
        # Wood = 1 m3/day
        # Metals = 0.5 m3/day
        # Total daily waste entering the shared container = 3.5 m3/day
        daily_rate = daily_df[phase_name].sum()

        # If no waste is generated in this phase, the simulation skips this phase.
        if daily_rate == 0:
            continue

        # This creates the list of days when the fixed scheduled pickups happen.
        pickup_days = get_pickup_days(SHARED_CONTAINER_FREQUENCY, phase_days)

        # This variable tracks how much waste is currently inside the shared container.
        container_level = 0

        # This counts how many pickups are performed.
        pickups = 0

        # This counts how many days the container exceeded its capacity.
        overflow_incidents = 0

        # This stores the total amount of waste above the container capacity.
        overflow_volume = 0

        # This stores the sum of utilization percentages at pickup time.
        # Later it is divided by the number of pickups to calculate the average utilization.
        utilization_sum = 0

        # This counts pickups where the container was less than 30% full.
        # These are considered inefficient or unnecessary pickups.
        unused_pickups = 0

        # This counts site delay days caused by overflow.
        delay_days = 0

        # This loop simulates the phase day by day.
        for day in range(1, phase_days + 1):
            # Every day, new waste is added to the shared container.
            container_level += daily_rate

            # If the container level is above capacity, an overflow has happened.
            # The model records one overflow incident for that day.
            # It also records how much waste is above capacity and adds one delay day.
            if container_level > shared_container_capacity:
                overflow_incidents += 1
                overflow_volume += container_level - shared_container_capacity
                delay_days += 1

            # If the current day is a scheduled pickup day, the container is collected.
            if day in pickup_days:
                # Increase the number of pickups.
                pickups += 1

                # Utilization shows how full the container was when collected.
                # min(container_level, shared_container_capacity) prevents utilization above 100%.
                utilization = min(container_level, shared_container_capacity) / shared_container_capacity * 100

                # Add this pickup utilization to the total utilization sum.
                utilization_sum += utilization

                # If the pickup happened when the container was less than 30% full,
                # the model counts it as an unused/inefficient pickup.
                if utilization < 30:
                    unused_pickups += 1

                # After pickup, the container is emptied.
                container_level = 0

        # This calculates the average pickup utilization.
        # If there were no pickups, it avoids division by zero and returns 0.
        avg_utilization = utilization_sum / pickups if pickups > 0 else 0

        # This stores the final results for this phase and strategy.
        results.append({
            "Run ID": run_id,
            "Total Project Days": total_project_days,
            "Strategy": "Fixed Schedule",
            "Phase": phase_name,
            "Phase Days": phase_days,
            "Container Type": SHARED_CONTAINER_TYPE,
            "Container Capacity m3": round(shared_container_capacity, 2),
            "Current Frequency": SHARED_CONTAINER_FREQUENCY,
            "Total Daily Waste Generation m3/day": round(daily_rate, 3),
            "Total Generated m3": round(daily_rate * phase_days, 2),
            "Best Threshold %": "",
            "Number of Pickups": pickups,
            "Average Utilization at Pickup %": round(avg_utilization, 1),
            "Overflow Incidents": overflow_incidents,
            "Total Overflow Volume m3": round(overflow_volume, 2),
            "Unused Pickups": unused_pickups,
            "Site Delay Days": delay_days,
            "Final Container Level m3": round(container_level, 2)
        })

    # This converts the list of result dictionaries into a DataFrame.
    return pd.DataFrame(results)


# This function simulates the Reactive strategy.
# Reactive means the container is collected only when it becomes full.
# There is no fixed calendar pickup schedule.
def simulate_reactive(run_id, total_project_days, shared_container_capacity, phase_df, daily_df):
    # This list stores the result rows for this strategy.
    results = []

    # This loop goes through each construction phase.
    for _, phase_row in phase_df.iterrows():
        # Get the phase name.
        phase_name = phase_row["Phase"]

        # Get the number of days in this phase.
        phase_days = int(phase_row["Days"])

        # Add all waste streams together because they all go into one shared container.
        daily_rate = daily_df[phase_name].sum()

        # Skip the phase if there is no waste generation.
        if daily_rate == 0:
            continue

        # Start the container empty.
        container_level = 0

        # Initialize the result counters.
        pickups = 0
        overflow_incidents = 0
        overflow_volume = 0
        utilization_sum = 0
        delay_days = 0

        # Simulate each day of the phase.
        for day in range(1, phase_days + 1):
            # Add one day's total waste to the shared container.
            container_level += daily_rate

            # In the reactive strategy, the pickup is triggered when the container reaches or exceeds capacity.
            if container_level >= shared_container_capacity:
                # Count one pickup.
                pickups += 1

                # Calculate how full the container was when the pickup happened.
                utilization = min(container_level, shared_container_capacity) / shared_container_capacity * 100
                utilization_sum += utilization

                # If the level is greater than capacity, overflow occurred before pickup.
                if container_level > shared_container_capacity:
                    overflow_incidents += 1
                    overflow_volume += container_level - shared_container_capacity
                    delay_days += 1

                # Empty the container after pickup.
                container_level = 0

        # Calculate average utilization across all pickups.
        avg_utilization = utilization_sum / pickups if pickups > 0 else 0

        # Store the results for this phase.
        results.append({
            "Run ID": run_id,
            "Total Project Days": total_project_days,
            "Strategy": "Reactive",
            "Phase": phase_name,
            "Phase Days": phase_days,
            "Container Type": SHARED_CONTAINER_TYPE,
            "Container Capacity m3": round(shared_container_capacity, 2),
            "Current Frequency": "",
            "Total Daily Waste Generation m3/day": round(daily_rate, 3),
            "Total Generated m3": round(daily_rate * phase_days, 2),
            "Best Threshold %": "",
            "Number of Pickups": pickups,
            "Average Utilization at Pickup %": round(avg_utilization, 1),
            "Overflow Incidents": overflow_incidents,
            "Total Overflow Volume m3": round(overflow_volume, 2),
            "Unused Pickups": "",
            "Site Delay Days": delay_days,
            "Final Container Level m3": round(container_level, 2)
        })

    # Return the strategy results as a DataFrame.
    return pd.DataFrame(results)


# This function simulates one threshold level for the Dynamic Threshold strategy.
# Dynamic Threshold means pickup happens when the container reaches a selected percentage full.
# Example:
# If the threshold is 80% and the container capacity is 20 m3,
# then pickup is triggered when the container reaches 16 m3.
def simulate_dynamic_threshold(
    run_id,
    total_project_days,
    phase_name,
    phase_days,
    shared_container_capacity,
    daily_rate,
    threshold
):
    # Convert the threshold percentage into an actual volume.
    # Example: 80% of 20 m3 = 16 m3.
    threshold_volume = shared_container_capacity * threshold / 100

    # Start the container empty.
    container_level = 0

    # Initialize counters for this threshold test.
    pickups = 0
    overflow_incidents = 0
    overflow_volume = 0
    utilization_sum = 0
    delay_days = 0

    # Simulate each day of the phase.
    for day in range(1, phase_days + 1):
        # Add one day of waste to the shared container.
        container_level += daily_rate

        # If the container exceeds capacity, record overflow and delay.
        # This can happen if daily waste jumps over the threshold and capacity on the same day.
        if container_level > shared_container_capacity:
            overflow_incidents += 1
            overflow_volume += container_level - shared_container_capacity
            delay_days += 1

        # If the container level has reached the threshold, trigger a pickup.
        if container_level >= threshold_volume:
            # Count one pickup.
            pickups += 1

            # Calculate pickup utilization as a percentage of container capacity.
            utilization = min(container_level, shared_container_capacity) / shared_container_capacity * 100
            utilization_sum += utilization

            # Empty the container after pickup.
            container_level = 0

    # Calculate the average utilization at pickup.
    avg_utilization = utilization_sum / pickups if pickups > 0 else 0

    # Return a dictionary with the result of this threshold test.
    return {
        "Run ID": run_id,
        "Total Project Days": total_project_days,
        "Strategy": "Dynamic Threshold",
        "Phase": phase_name,
        "Phase Days": phase_days,
        "Container Type": SHARED_CONTAINER_TYPE,
        "Container Capacity m3": round(shared_container_capacity, 2),
        "Current Frequency": "",
        "Total Daily Waste Generation m3/day": round(daily_rate, 3),
        "Total Generated m3": round(daily_rate * phase_days, 2),
        "Best Threshold %": threshold,
        "Number of Pickups": pickups,
        "Average Utilization at Pickup %": round(avg_utilization, 1),
        "Overflow Incidents": overflow_incidents,
        "Total Overflow Volume m3": round(overflow_volume, 2),
        "Unused Pickups": "",
        "Site Delay Days": delay_days,
        "Final Container Level m3": round(container_level, 2)
    }


# This function finds the best dynamic threshold for each phase.
# It tests every threshold from 50% to 100%.
# Then it chooses the best threshold based on:
# 1. Prefer no overflow.
# 2. Prefer fewer pickups.
# 3. Prefer higher utilization.
# 4. Prefer a higher threshold if other values are equal.
def simulate_dynamic(run_id, total_project_days, shared_container_capacity, phase_df, daily_df):
    # This list stores only the best threshold result for each phase.
    best_results = []

    # This list stores all threshold tests, not only the best ones.
    # This is useful for later analysis.
    threshold_tests = []

    # Loop through every phase.
    for _, phase_row in phase_df.iterrows():
        # Get the phase name.
        phase_name = phase_row["Phase"]

        # Get the phase duration.
        phase_days = int(phase_row["Days"])

        # Calculate total daily waste entering the shared container.
        daily_rate = daily_df[phase_name].sum()

        # Skip this phase if there is no waste.
        if daily_rate == 0:
            continue

        # This list stores the threshold results only for the current phase.
        threshold_results = []

        # Test all threshold values from 50% to 100%, inclusive.
        for threshold in range(50, 101):
            # Simulate the current threshold.
            result = simulate_dynamic_threshold(
                run_id,
                total_project_days,
                phase_name,
                phase_days,
                shared_container_capacity,
                daily_rate,
                threshold
            )

            # Store the result in the current phase list.
            threshold_results.append(result)

            # Store the result in the global threshold-test list.
            threshold_tests.append(result)

        # Create a list of only the thresholds that created zero overflow incidents.
        no_overflow = [
            r for r in threshold_results
            if r["Overflow Incidents"] == 0
        ]

        # If at least one threshold produced no overflow, choose among those safe options.
        if no_overflow:
            # Sort safe options by:
            # 1. Lowest number of pickups.
            # 2. Highest average utilization.
            # 3. Highest threshold percentage.
            # The [0] takes the best option after sorting.
            best = sorted(
                no_overflow,
                key=lambda r: (
                    r["Number of Pickups"],
                    -r["Average Utilization at Pickup %"],
                    -r["Best Threshold %"]
                )
            )[0]
        else:
            # If all thresholds caused overflow, choose the least bad option.
            # The model prioritizes:
            # 1. Lowest overflow incidents.
            # 2. Lowest number of pickups.
            # 3. Highest utilization.
            best = sorted(
                threshold_results,
                key=lambda r: (
                    r["Overflow Incidents"],
                    r["Number of Pickups"],
                    -r["Average Utilization at Pickup %"]
                )
            )[0]

        # Store the best threshold result for this phase.
        best_results.append(best)

    # Return both the best dynamic results and the full threshold test table.
    return pd.DataFrame(best_results), pd.DataFrame(threshold_tests)


# This function creates a summary table per run and per strategy.
# It combines all phases into one strategy-level result for each Monte Carlo run.
def create_summary(combined_df):
    # This list stores summary rows.
    summary_rows = []

    # This groups the detailed results by Run ID and Strategy.
    # Example group: all Fixed Schedule phase results for Run 1.
    for (run_id, strategy), group in combined_df.groupby(["Run ID", "Strategy"]):
        # The Unused Pickups column sometimes contains blank strings.
        # pd.to_numeric converts valid numbers to numeric values and invalid blanks to NaN.
        # fillna(0) replaces NaN values with zero.
        unused_pickups = pd.to_numeric(
            group["Unused Pickups"],
            errors="coerce"
        ).fillna(0)

        # Sum the total number of pickups across all phases.
        total_pickups = group["Number of Pickups"].sum()

        # Sum the total delay days across all phases.
        delay_days = group["Site Delay Days"].sum()

        # Convert pickup count into working hours.
        operational_hours = total_pickups * HOURS_PER_PICKUP

        # Convert delay days into delay hours.
        delay_hours = delay_days * WORKING_HOURS_PER_DELAY_DAY

        # Total time impact includes pickup operation time plus delay time.
        total_time_impact = operational_hours + delay_hours

        # Calculate total truck kilometers based on number of pickups and round-trip distance.
        total_truck_km = total_pickups * ROUND_TRIP_DISTANCE_KM

        # Estimate total CO2 emissions from truck travel.
        total_co2_kg = total_truck_km * CO2_EMISSION_FACTOR_KG_PER_KM

        # Append one summary row for this run and strategy.
        summary_rows.append({
            "Run ID": run_id,
            "Strategy": strategy,
            "Total Project Days": int(group["Total Project Days"].iloc[0]),
            "Total Generated Waste m3": round(group["Total Generated m3"].sum(), 2),
            "Total Pickups": int(total_pickups),
            "Average Utilization %": round(group["Average Utilization at Pickup %"].mean(), 1),
            "Total Overflow Incidents": int(group["Overflow Incidents"].sum()),
            "Total Overflow Volume m3": round(group["Total Overflow Volume m3"].sum(), 2),
            "Total Site Delay Days": int(delay_days),
            "Total Unused Pickups": int(unused_pickups.sum()),
            "Operational Pickup Hours": round(operational_hours, 2),
            "Delay Hours": round(delay_hours, 2),
            "Total Time Impact Hours": round(total_time_impact, 2),
            "Total Truck Kilometers Traveled": round(total_truck_km, 2),
            "CO2 Emissions kg": round(total_co2_kg, 2)
        })

    # Convert the summary rows into a DataFrame.
    return pd.DataFrame(summary_rows)


# =========================================================
# RUN MONTE CARLO SIMULATION
# =========================================================

# These lists will collect results from all 1000 runs.
all_inputs = []  # Stores all randomly generated input data.
all_fixed = []  # Stores all Fixed Schedule results.
all_reactive = []  # Stores all Reactive strategy results.
all_dynamic = []  # Stores all best Dynamic Threshold results.
all_threshold_tests = []  # Stores all threshold tests from 50% to 100%.

# This loop runs the complete simulation NUMBER_OF_RUNS times.
for run_id in range(1, NUMBER_OF_RUNS + 1):
    # Create a new random input scenario for this run.
    total_project_days, shared_container_capacity, phase_df, daily_df, input_df = create_random_input_data(run_id)

    # Simulate the Fixed Schedule strategy for this run.
    fixed_df = simulate_fixed(
        run_id,
        total_project_days,
        shared_container_capacity,
        phase_df,
        daily_df
    )

    # Simulate the Reactive strategy for this run.
    reactive_df = simulate_reactive(
        run_id,
        total_project_days,
        shared_container_capacity,
        phase_df,
        daily_df
    )

    # Simulate the Dynamic Threshold strategy for this run.
    # dynamic_df contains only the best threshold result per phase.
    # threshold_df contains all threshold tests.
    dynamic_df, threshold_df = simulate_dynamic(
        run_id,
        total_project_days,
        shared_container_capacity,
        phase_df,
        daily_df
    )

    # Store this run's input data.
    all_inputs.append(input_df)

    # Store this run's Fixed Schedule results.
    all_fixed.append(fixed_df)

    # Store this run's Reactive results.
    all_reactive.append(reactive_df)

    # Store this run's Dynamic Threshold results.
    all_dynamic.append(dynamic_df)

    # Store this run's threshold test results.
    all_threshold_tests.append(threshold_df)

# Combine all run input tables into one large DataFrame.
input_all_df = pd.concat(all_inputs, ignore_index=True)

# Combine all Fixed Schedule result tables into one large DataFrame.
fixed_all_df = pd.concat(all_fixed, ignore_index=True)

# Combine all Reactive result tables into one large DataFrame.
reactive_all_df = pd.concat(all_reactive, ignore_index=True)

# Combine all Dynamic Threshold best-result tables into one large DataFrame.
dynamic_all_df = pd.concat(all_dynamic, ignore_index=True)

# Combine all Dynamic Threshold test tables into one large DataFrame.
threshold_all_df = pd.concat(all_threshold_tests, ignore_index=True)

# Combine the three main strategy result tables into one detailed results table.
combined_all_df = pd.concat(
    [fixed_all_df, reactive_all_df, dynamic_all_df],
    ignore_index=True
)

# Create a summary table per run and per strategy.
summary_all_df = create_summary(combined_all_df)

# This creates the overall average summary across all Monte Carlo runs.
# It groups by strategy and calculates the mean value of each KPI.
overall_summary_df = summary_all_df.groupby("Strategy").agg({
    "Total Generated Waste m3": "mean",
    "Total Pickups": "mean",
    "Average Utilization %": "mean",
    "Total Overflow Incidents": "mean",
    "Total Overflow Volume m3": "mean",
    "Total Site Delay Days": "mean",
    "Total Unused Pickups": "mean",
    "Operational Pickup Hours": "mean",
    "Delay Hours": "mean",
    "Total Time Impact Hours": "mean",
    "Total Truck Kilometers Traveled": "mean",
    "CO2 Emissions kg": "mean"
}).reset_index()

# Round all average summary values to 2 decimal places.
overall_summary_df = overall_summary_df.round(2)

# =========================================================
# HOURS SAVED
# =========================================================

# This list will store the time saving result for every run.
hours_saved_rows = []

# This loop calculates how many hours the Dynamic Threshold strategy saves compared with Fixed Schedule.
for run_id in range(1, NUMBER_OF_RUNS + 1):
    # Select only the summary rows for the current run.
    run_summary = summary_all_df[summary_all_df["Run ID"] == run_id]

    # Get total time impact for the Fixed Schedule strategy.
    fixed_hours = run_summary.loc[
        run_summary["Strategy"] == "Fixed Schedule",
        "Total Time Impact Hours"
    ].iloc[0]

    # Get total time impact for the Dynamic Threshold strategy.
    dynamic_hours = run_summary.loc[
        run_summary["Strategy"] == "Dynamic Threshold",
        "Total Time Impact Hours"
    ].iloc[0]

    # Store the hours saved for this run.
    # Positive value means Dynamic Threshold is better than Fixed Schedule.
    # Negative value means Dynamic Threshold performed worse for that run.
    hours_saved_rows.append({
        "Run ID": run_id,
        "Hours Saved by Dynamic vs Fixed": round(fixed_hours - dynamic_hours, 2)
    })

# Convert the hours saved list into a DataFrame.
hours_saved_df = pd.DataFrame(hours_saved_rows)

# This calculates the cumulative average hours saved as the Monte Carlo simulation progresses.
# It is useful for checking convergence.
hours_saved_df["Cumulative Average Hours Saved"] = (
    hours_saved_df["Hours Saved by Dynamic vs Fixed"].expanding().mean()
)

# This calculates the final average hours saved across all runs.
average_hours_saved = hours_saved_df["Hours Saved by Dynamic vs Fixed"].mean()

# =========================================================
# SAVE CSV FILES
# =========================================================

# Save all randomly generated input data to CSV.
input_all_df.to_csv(os.path.join(output_folder, "single_container_random_input_data_all_runs.csv"), index=False)

# Save all Fixed Schedule detailed results to CSV.
fixed_all_df.to_csv(os.path.join(output_folder, "single_container_fixed_results_all_runs.csv"), index=False)

# Save all Reactive detailed results to CSV.
reactive_all_df.to_csv(os.path.join(output_folder, "single_container_reactive_results_all_runs.csv"), index=False)

# Save all Dynamic Threshold best results to CSV.
dynamic_all_df.to_csv(os.path.join(output_folder, "single_container_dynamic_results_all_runs.csv"), index=False)

# Save all Dynamic Threshold test results to CSV.
threshold_all_df.to_csv(os.path.join(output_folder, "single_container_dynamic_threshold_tests_all_runs.csv"), index=False)

# Save all strategies combined into one CSV.
combined_all_df.to_csv(os.path.join(output_folder, "single_container_combined_results_all_runs.csv"), index=False)

# Save the per-run strategy summary to CSV.
summary_all_df.to_csv(os.path.join(output_folder, "single_container_summary_per_run.csv"), index=False)

# Save the overall average summary to CSV.
overall_summary_df.to_csv(os.path.join(output_folder, "single_container_overall_average_summary_1000_runs.csv"), index=False)

# Save the hours saved analysis to CSV.
hours_saved_df.to_csv(os.path.join(output_folder, "single_container_hours_saved_per_run.csv"), index=False)


# =========================================================
# CREATE FORMATTED EXCEL REPORT - SINGLE CONTAINER
# =========================================================

# This creates the full path for the formatted Excel report.
excel_report_path = os.path.join(
    output_folder,
    "single_container_formatted_report.xlsx"
)

# This creates an Excel writer using the xlsxwriter engine.
# The with-statement automatically saves and closes the Excel file when finished.
with pd.ExcelWriter(excel_report_path, engine="xlsxwriter") as writer:

    # Get the workbook object so we can create custom formats.
    workbook = writer.book

    # This format is used for large title rows in the Excel report.
    title_format = workbook.add_format({
        "bold": True,
        "font_size": 16,
        "align": "center",
        "valign": "vcenter",
        "bg_color": "#1F4E78",
        "font_color": "white"
    })

    # This format is used for table headers.
    header_format = workbook.add_format({
        "bold": True,
        "bg_color": "#D9EAF7",
        "border": 1,
        "align": "center",
        "valign": "vcenter"
    })

    # -----------------------------
    # Sheet 1: Executive Summary
    # -----------------------------

    # Write the overall summary table into the Executive Summary sheet.
    overall_summary_df.to_excel(
        writer,
        sheet_name="Executive Summary",
        index=False,
        startrow=3
    )

    # Access the Executive Summary worksheet so we can format it.
    ws = writer.sheets["Executive Summary"]

    # Merge cells A1 to M1 and write a title.
    ws.merge_range(
        "A1:M1",
        "Single-Container Monte Carlo Waste Logistics - Strategy Comparison",
        title_format
    )

    # Write basic simulation information under the title.
    ws.write("A2", f"Number of simulation runs: {NUMBER_OF_RUNS}")
    ws.write("D2", f"Project duration range: {MIN_PROJECT_DAYS} - {MAX_PROJECT_DAYS} days")
    ws.write("H2", f"Shared container capacity range: {MIN_CONTAINER_CAPACITY} - {MAX_CONTAINER_CAPACITY} m³")

    # Rewrite the table headers using the custom header format.
    for col_num, value in enumerate(overall_summary_df.columns.values):
        ws.write(3, col_num, value, header_format)

    # Set the width of column A.
    ws.set_column("A:A", 22)

    # Set the width of columns B to M.
    ws.set_column("B:M", 20)

    # Add filters to the summary table.
    ws.autofilter(3, 0, len(overall_summary_df) + 3, len(overall_summary_df.columns) - 1)

    # Freeze the top rows so headers remain visible when scrolling.
    ws.freeze_panes(4, 0)

    # -----------------------------
    # Sheet 2: Hours Saved
    # -----------------------------

    # Write the hours saved table into the Hours Saved sheet.
    hours_saved_df.to_excel(
        writer,
        sheet_name="Hours Saved",
        index=False,
        startrow=2
    )

    # Access the Hours Saved worksheet.
    ws2 = writer.sheets["Hours Saved"]

    # Create a merged title row.
    ws2.merge_range(
        "A1:C1",
        "Hours Saved Analysis",
        title_format
    )

    # Format the table headers.
    for col_num, value in enumerate(hours_saved_df.columns.values):
        ws2.write(2, col_num, value, header_format)

    # Set column widths.
    ws2.set_column("A:A", 12)
    ws2.set_column("B:C", 32)

    # Add filters to the table.
    ws2.autofilter(2, 0, len(hours_saved_df) + 2, len(hours_saved_df.columns) - 1)

    # Freeze the header row.
    ws2.freeze_panes(3, 0)

    # -----------------------------
    # Sheet 3: Strategy Ranking
    # -----------------------------

    # Copy the overall summary so we can add ranking columns without changing the original table.
    ranking_df = overall_summary_df.copy()

    # Rank strategies by total time impact. Lower time impact is better.
    ranking_df["Operational Rank"] = ranking_df["Total Time Impact Hours"].rank(method="min")

    # Rank strategies by CO2 emissions. Lower emissions are better.
    ranking_df["Environmental Rank"] = ranking_df["CO2 Emissions kg"].rank(method="min")

    # Rank strategies by overflow incidents. Fewer incidents are better.
    ranking_df["Overflow Rank"] = ranking_df["Total Overflow Incidents"].rank(method="min")

    # Add the three ranking scores together.
    # A lower final score means a better overall strategy.
    ranking_df["Final Score"] = (
        ranking_df["Operational Rank"]
        + ranking_df["Environmental Rank"]
        + ranking_df["Overflow Rank"]
    )

    # Sort strategies from best to worst final score.
    ranking_df = ranking_df.sort_values("Final Score")

    # Write the ranking table to Excel.
    ranking_df.to_excel(
        writer,
        sheet_name="Strategy Ranking",
        index=False,
        startrow=2
    )

    # Access the Strategy Ranking worksheet.
    ws3 = writer.sheets["Strategy Ranking"]

    # Create the worksheet title.
    ws3.merge_range(
        "A1:Q1",
        "Single-Container Strategy Ranking",
        title_format
    )

    # Format headers.
    for col_num, value in enumerate(ranking_df.columns.values):
        ws3.write(2, col_num, value, header_format)

    # Set column widths.
    ws3.set_column("A:A", 22)
    ws3.set_column("B:Q", 18)

    # Add filters.
    ws3.autofilter(2, 0, len(ranking_df) + 2, len(ranking_df.columns) - 1)

    # Freeze header rows.
    ws3.freeze_panes(3, 0)

    # -----------------------------
    # Sheet 4: Assumptions
    # -----------------------------

    # Create a table that documents the assumptions used in the simulation.
    assumptions_df = pd.DataFrame({
        "Parameter": [
            "Number of Monte Carlo runs",
            "Minimum project duration",
            "Maximum project duration",
            "Minimum shared container capacity",
            "Maximum shared container capacity",
            "Maximum daily waste ratio",
            "Hours per pickup",
            "Working hours per delay day",
            "One-way truck distance",
            "Round-trip truck distance",
            "CO2 emission factor",
            "Shared container frequency"
        ],
        "Value": [
            NUMBER_OF_RUNS,
            MIN_PROJECT_DAYS,
            MAX_PROJECT_DAYS,
            MIN_CONTAINER_CAPACITY,
            MAX_CONTAINER_CAPACITY,
            MAX_DAILY_WASTE_AS_CAPACITY_RATIO,
            HOURS_PER_PICKUP,
            WORKING_HOURS_PER_DELAY_DAY,
            AVERAGE_ONE_WAY_DISTANCE_KM,
            ROUND_TRIP_DISTANCE_KM,
            CO2_EMISSION_FACTOR_KG_PER_KM,
            SHARED_CONTAINER_FREQUENCY
        ],
        "Unit": [
            "runs",
            "days",
            "days",
            "m3",
            "m3",
            "ratio",
            "hours/pickup",
            "hours/day",
            "km",
            "km",
            "kg CO2/km",
            "frequency"
        ]
    })

    # Write the assumptions table to Excel.
    assumptions_df.to_excel(
        writer,
        sheet_name="Assumptions",
        index=False,
        startrow=2
    )

    # Access the Assumptions worksheet.
    ws4 = writer.sheets["Assumptions"]

    # Create the worksheet title.
    ws4.merge_range(
        "A1:C1",
        "Single-Container Simulation Assumptions",
        title_format
    )

    # Format the headers.
    for col_num, value in enumerate(assumptions_df.columns.values):
        ws4.write(2, col_num, value, header_format)

    # Set column widths.
    ws4.set_column("A:A", 36)
    ws4.set_column("B:C", 20)

    # -----------------------------
    # Sheet 5: Detailed Run Inputs
    # -----------------------------

    # Write the detailed random input data to Excel.
    input_all_df.to_excel(
        writer,
        sheet_name="Detailed Run Inputs",
        index=False,
        startrow=2
    )

    # Access the Detailed Run Inputs worksheet.
    ws5 = writer.sheets["Detailed Run Inputs"]

    # Create the worksheet title.
    ws5.merge_range(
        "A1:G1",
        "Detailed Random Input Data for Every Single-Container Monte Carlo Run",
        title_format
    )

    # Format table headers.
    for col_num, value in enumerate(input_all_df.columns.values):
        ws5.write(2, col_num, value, header_format)

    # Set column widths for readability.
    ws5.set_column("A:A", 10)
    ws5.set_column("B:B", 18)
    ws5.set_column("C:C", 26)
    ws5.set_column("D:D", 20)
    ws5.set_column("E:E", 12)
    ws5.set_column("F:F", 25)
    ws5.set_column("G:G", 32)

    # Add filters to the input table.
    ws5.autofilter(2, 0, len(input_all_df) + 2, len(input_all_df.columns) - 1)

    # Freeze the header row.
    ws5.freeze_panes(3, 0)

    # -----------------------------
    # Sheet 6: Detailed Strategy Results
    # -----------------------------

    # Write all detailed strategy results to Excel.
    combined_all_df.to_excel(
        writer,
        sheet_name="Detailed Results",
        index=False,
        startrow=2
    )

    # Access the Detailed Results worksheet.
    ws6 = writer.sheets["Detailed Results"]

    # Create the worksheet title.
    ws6.merge_range(
        "A1:R1",
        "Detailed Strategy Results for Every Run",
        title_format
    )

    # Format the table headers.
    for col_num, value in enumerate(combined_all_df.columns.values):
        ws6.write(2, col_num, value, header_format)

    # Set column widths.
    ws6.set_column("A:A", 10)
    ws6.set_column("B:B", 18)
    ws6.set_column("C:C", 22)
    ws6.set_column("D:R", 18)

    # Add filters to the detailed results table.
    ws6.autofilter(2, 0, len(combined_all_df) + 2, len(combined_all_df.columns) - 1)

    # Freeze the top rows.
    ws6.freeze_panes(3, 0)

# Print confirmation that the Excel report was created.
print("\nFormatted Excel report created:")
print(excel_report_path)

# =========================================================
# DASHBOARD
# =========================================================

# Create a figure with 2 rows and 3 columns of charts.
fig, axes = plt.subplots(2, 3, figsize=(18, 10))

# Chart 1: average number of pickups by strategy.
axes[0, 0].bar(
    overall_summary_df["Strategy"],
    overall_summary_df["Total Pickups"]
)
axes[0, 0].set_title("Average Total Pickups per Strategy")
axes[0, 0].set_ylabel("Average Pickups")

# Chart 2: average overflow incidents by strategy.
axes[0, 1].bar(
    overall_summary_df["Strategy"],
    overall_summary_df["Total Overflow Incidents"]
)
axes[0, 1].set_title("Average Overflow Incidents per Strategy")
axes[0, 1].set_ylabel("Average Overflow Incidents")

# Chart 3: average container utilization by strategy.
axes[0, 2].bar(
    overall_summary_df["Strategy"],
    overall_summary_df["Average Utilization %"]
)
axes[0, 2].set_title("Average Shared Container Utilization")
axes[0, 2].set_ylabel("Utilization (%)")

# Chart 4: average CO2 emissions by strategy.
axes[1, 0].bar(
    overall_summary_df["Strategy"],
    overall_summary_df["CO2 Emissions kg"]
)
axes[1, 0].set_title("Average CO₂ Emissions per Strategy")
axes[1, 0].set_ylabel("kg CO₂")

# Chart 5: scatter plot showing the tradeoff between pickups and overflow incidents.
axes[1, 1].scatter(
    overall_summary_df["Total Pickups"],
    overall_summary_df["Total Overflow Incidents"]
)

# Add text labels to the scatter plot so each point shows the strategy name.
for _, row in overall_summary_df.iterrows():
    axes[1, 1].annotate(
        row["Strategy"],
        (
            row["Total Pickups"],
            row["Total Overflow Incidents"]
        )
    )

# Set scatter plot title and axis labels.
axes[1, 1].set_title("Pickups vs Overflow Tradeoff")
axes[1, 1].set_xlabel("Average Pickups")
axes[1, 1].set_ylabel("Average Overflow Incidents")

# Chart 6: convergence graph for cumulative average hours saved.
axes[1, 2].plot(
    hours_saved_df["Run ID"],
    hours_saved_df["Cumulative Average Hours Saved"]
)
axes[1, 2].set_title("Monte Carlo Convergence")
axes[1, 2].set_xlabel("Number of Runs")
axes[1, 2].set_ylabel("Cumulative Avg Hours Saved")

# Automatically adjust spacing so chart titles and labels do not overlap.
plt.tight_layout()

# Create the full path for the dashboard image.
dashboard_path = os.path.join(
    output_folder,
    "single_container_monte_carlo_dashboard_1000_runs.png"
)

# Save the dashboard image as a high-resolution PNG file.
plt.savefig(dashboard_path, dpi=300)

# Show the dashboard graph on the screen.
plt.show()

# Close the figure to free memory.
plt.close()

# =========================================================
# PRINT RESULTS
# =========================================================

# Print a separator line.
print("\n====================================================")

# Print completion title.
print("SINGLE-CONTAINER MONTE CARLO SIMULATION COMPLETED")

# Print another separator line.
print("====================================================")

# Print the number of Monte Carlo runs.
print(f"\nNumber of runs: {NUMBER_OF_RUNS}")

# Print a short description of the system type.
print("System type: One shared container for all waste streams")

# Print the simulated container capacity range.
print(f"Container capacity range: {MIN_CONTAINER_CAPACITY} - {MAX_CONTAINER_CAPACITY} m3")

# Print the maximum daily waste generation assumption.
print(f"Daily waste generation per waste stream: 0 to {MAX_DAILY_WASTE_AS_CAPACITY_RATIO * 100:.0f}% of shared container capacity per day")

# Print where all files were saved.
print("\nFiles saved in folder:")
print(output_folder)

# Print the title for the overall summary table.
print("\n====================================================")
print("OVERALL AVERAGE SUMMARY FOR 1000 RUNS")
print("====================================================")

# Print the overall summary table without the DataFrame index.
print(overall_summary_df.to_string(index=False))

# Print the title for the hours saved table.
print("\n====================================================")
print("HOURS SAVED")
print("====================================================")

# Print the last 20 rows of the hours saved table.
print(hours_saved_df.tail(20).to_string(index=False))

# Print the final average hours saved.
print(f"\nAverage hours saved by Dynamic Strategy compared to Fixed Schedule: {average_hours_saved:.2f} hours")

# Print where the dashboard graph was saved.
print("\nDashboard graph created:")
print(dashboard_path)
