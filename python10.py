# Import pandas, which is used to create and manage tables called DataFrames.
import pandas as pd

# Import os, which is used to work with folders, file paths, and operating-system locations.
import os

# Import random, which is used to generate random numbers for the Monte Carlo simulation.
import random

# Import matplotlib.pyplot, which is used to create graphs and charts.
import matplotlib.pyplot as plt

# =========================================================
# MONTE CARLO SIMULATION SETTINGS
# =========================================================

# This is the number of random simulation scenarios that will be created and tested.
NUMBER_OF_RUNS = 1000

# This is the minimum possible project duration, in days, for each random simulation run.
MIN_PROJECT_DAYS = 100

# This is the maximum possible project duration, in days, for each random simulation run.
MAX_PROJECT_DAYS = 1000

# This is the minimum possible container capacity, in cubic meters.
MIN_CONTAINER_CAPACITY = 10

# This is the maximum possible container capacity, in cubic meters.
MAX_CONTAINER_CAPACITY = 40

# This means that the daily waste generation can be up to 30% of the container capacity.
MAX_DAILY_WASTE_AS_CAPACITY_RATIO = 0.30

# This is the assumed time needed for one truck pickup operation.
HOURS_PER_PICKUP = 1.5

# This is the number of working hours that are considered equal to one site delay day.
WORKING_HOURS_PER_DELAY_DAY = 8

# This is the assumed average one-way truck travel distance in kilometers.
AVERAGE_ONE_WAY_DISTANCE_KM = 15

# This calculates the round-trip distance, meaning the truck goes to the site and then returns.
ROUND_TRIP_DISTANCE_KM = AVERAGE_ONE_WAY_DISTANCE_KM * 2

# This is the assumed CO2 emission factor for the truck, in kg CO2 per kilometer.
CO2_EMISSION_FACTOR_KG_PER_KM = 0.9

# This ratio is used in the ideal strategy to size the container as 25% of the total waste of that phase.
IDEAL_CONTAINER_RATIO = 0.25

# This fixes the random generator so the results are repeatable every time the code runs.
random.seed(42)

# =========================================================
# OUTPUT FOLDER
# =========================================================

# This finds the folder where this Python script is located.
script_folder = os.path.dirname(os.path.abspath(__file__))

# This creates the path for a new output folder called "monte_carlo_results" inside the script folder.
output_folder = os.path.join(script_folder, "monte_carlo_results")

# This creates the output folder if it does not already exist.
os.makedirs(output_folder, exist_ok=True)

# =========================================================
# FIXED DATA
# =========================================================

# This list contains the waste streams that exist in the construction project.
# Each row contains:
# 1. the waste stream name,
# 2. the container type,
# 3. a random container capacity between the minimum and maximum capacity,
# 4. the current pickup frequency used in the fixed schedule strategy.
waste_streams = [
    # Concrete and masonry waste uses a 20-yard roll-off bin and is collected weekly.
    ["Concrete & Masonry", "20-yard roll-off bin", random.uniform(MIN_CONTAINER_CAPACITY, MAX_CONTAINER_CAPACITY), "Weekly"],

    # Wood waste uses a covered skip and is collected twice per week.
    ["Wood", "Covered skip", random.uniform(MIN_CONTAINER_CAPACITY, MAX_CONTAINER_CAPACITY), "Twice per week"],

    # Metal waste uses a 10-yard metal bin and is collected only when needed.
    ["Metals", "10-yd metal bin", random.uniform(MIN_CONTAINER_CAPACITY, MAX_CONTAINER_CAPACITY), "On demand"],

    # Drywall waste uses a 10-yard bin and is collected weekly.
    ["Drywall", "10-yd bin", random.uniform(MIN_CONTAINER_CAPACITY, MAX_CONTAINER_CAPACITY), "Weekly"],

    # Packaging waste uses bag cages or bins and is collected daily.
    ["Packaging", "Bag cages / bins", random.uniform(MIN_CONTAINER_CAPACITY, MAX_CONTAINER_CAPACITY), "Daily"],

    # Mixed residual waste uses a sealed dumpster and is collected weekly.
    ["Mixed Residual Waste", "Sealed dumpster", random.uniform(MIN_CONTAINER_CAPACITY, MAX_CONTAINER_CAPACITY), "Weekly"]
]

# This converts the waste_streams list into a pandas DataFrame, which is easier to process.
waste_df = pd.DataFrame(
    # This is the source list that will become the table.
    waste_streams,

    # These are the column names of the new DataFrame.
    columns=[
        # Name of the waste category.
        "Waste Stream",

        # Type of container used for that waste category.
        "Container Type",

        # Capacity of the container in cubic meters.
        "Container Capacity m3",

        # Existing collection frequency for the fixed schedule strategy.
        "Current Frequency"
    ]
)

# This list defines the four construction phases used in every simulation run.
phase_names = [
    # The first phase of the construction project.
    "Site Preparation",

    # The foundation construction phase.
    "Foundation",

    # The interior construction phase.
    "Interior",

    # The final finishing phase.
    "Finishing"
]

# =========================================================
# FUNCTIONS
# =========================================================

# This function randomly splits the total project duration into four phase durations.
def split_project_days(total_days):
    # We need four project phases, so we create three random cut points inside the total project duration.
    # For example, if the project has 200 days, the random cuts might be day 40, day 110, and day 170.
    # Then the phase lengths become:
    # Phase 1 = 40 days,
    # Phase 2 = 110 - 40 = 70 days,
    # Phase 3 = 170 - 110 = 60 days,
    # Phase 4 = 200 - 170 = 30 days.

    # This creates the first cut point. It must leave enough days for the other three phases.
    cut1 = random.randint(1, total_days - 3)

    # This creates the second cut point after cut1, leaving enough days for the last two phases.
    cut2 = random.randint(cut1 + 1, total_days - 2)

    # This creates the third cut point after cut2, leaving at least one day for the final phase.
    cut3 = random.randint(cut2 + 1, total_days - 1)

    # This returns the duration of the four phases.
    return [
        # Duration of phase 1, from day 0 to cut1.
        cut1,

        # Duration of phase 2, from cut1 to cut2.
        cut2 - cut1,

        # Duration of phase 3, from cut2 to cut3.
        cut3 - cut2,

        # Duration of phase 4, from cut3 to the final project day.
        total_days - cut3
    ]


# This function creates one full random input scenario for one Monte Carlo run.
def create_random_input_data(run_id):
    # A Monte Carlo simulation works by repeating the same calculation many times with random inputs.
    # In this function, we create those random inputs for one run.
    # The inputs include:
    # 1. total project duration,
    # 2. duration of each construction phase,
    # 3. daily waste generation rate for each waste stream in each phase.

    # This randomly chooses the total number of project days for this run.
    total_project_days = random.randint(MIN_PROJECT_DAYS, MAX_PROJECT_DAYS)

    # This splits the total project days into four random phase durations.
    phase_days = split_project_days(total_project_days)

    # This creates a table where each construction phase has its own duration.
    phase_df = pd.DataFrame({
        # This column stores the phase names.
        "Phase": phase_names,

        # This column stores the number of days for each phase.
        "Days": phase_days
    })

    # This empty dictionary will store random daily waste generation values.
    # The final structure will look like this:
    # {
    #   "Concrete & Masonry": [value for Site Preparation, value for Foundation, value for Interior, value for Finishing],
    #   "Wood": [...],
    #   etc.
    # }
    random_daily_data = {}

    # This loop goes through every waste stream in the waste_df table.
    for _, waste_row in waste_df.iterrows():
        # This gets the name of the current waste stream.
        waste_name = waste_row["Waste Stream"]

        # This gets the container capacity of the current waste stream.
        container_capacity = waste_row["Container Capacity m3"]

        # This creates random daily waste generation values for this waste stream.
        # One random value is created for each project phase.
        # The maximum possible daily waste is limited to 30% of the container capacity.
        random_daily_data[waste_name] = [
            # Round the random value to 3 decimal places for cleaner output.
            round(
                # Generate a random number between 0 and the maximum allowed daily waste.
                random.uniform(
                    # Minimum possible daily generation is zero.
                    0,

                    # Maximum daily generation is a percentage of the container capacity.
                    container_capacity * MAX_DAILY_WASTE_AS_CAPACITY_RATIO
                ),

                # Keep only 3 decimal places.
                3
            )

            # Repeat this once for every phase name.
            for _ in phase_names
        ]

    # This converts the random daily waste dictionary into a table.
    daily_df = pd.DataFrame(
        # This is the dictionary with random waste generation values.
        random_daily_data,

        # The rows are initially the phase names.
        index=phase_names
    ).T

    # The .T transposes the table.
    # After transposing:
    # rows = waste streams,
    # columns = construction phases.

    # This empty list will store the input data in a long table format.
    input_rows = []

    # This loop goes through each construction phase.
    for phase in phase_names:
        # This inner loop goes through each waste stream.
        for waste in waste_df["Waste Stream"]:
            # This adds one row describing the input for one waste stream in one phase.
            input_rows.append({
                # Store the Monte Carlo run number.
                "Run ID": run_id,

                # Store the total project duration for this run.
                "Total Project Days": total_project_days,

                # Store the current construction phase.
                "Phase": phase,

                # Find and store the number of days for this phase.
                "Phase Days": int(phase_df.loc[phase_df["Phase"] == phase, "Days"].iloc[0]),

                # Store the current waste stream.
                "Waste Stream": waste,

                # Store the random daily waste generation value for this waste stream and phase.
                "Random Daily Waste Generation m3/day": daily_df.loc[waste, phase]
            })

    # This converts the list of input rows into a DataFrame.
    input_df = pd.DataFrame(input_rows)

    # This returns all the input data needed by the simulation functions.
    return total_project_days, phase_df, daily_df, input_df


# This function converts a text frequency into actual pickup days inside a phase.
def get_pickup_days(frequency, phase_days):
    # The fixed schedule strategy needs to know on which days the truck arrives.
    # For example:
    # Daily means day 1, day 2, day 3, etc.
    # Weekly means day 7, day 14, day 21, etc.
    # Twice per week is approximated using days divisible by 3 or 7.

    # If the frequency is daily, the truck comes every day.
    if frequency == "Daily":
        # Return all days from 1 to the last phase day.
        return list(range(1, phase_days + 1))

    # If the frequency is weekly, the truck comes every 7 days.
    if frequency == "Weekly":
        # Return days 7, 14, 21, etc.
        return list(range(7, phase_days + 1, 7))

    # If the frequency is twice per week, this creates an approximate twice-weekly pattern.
    if frequency == "Twice per week":
        # Return days where the day number is divisible by 3 or divisible by 7.
        return [
            # Keep this day in the pickup list.
            day for day in range(1, phase_days + 1)

            # The truck comes when this condition is true.
            if day % 3 == 0 or day % 7 == 0
        ]

    # If the frequency is "On demand" or anything else, the fixed schedule has no planned pickup days.
    return []


# This function simulates the fixed schedule strategy.
def simulate_fixed(run_id, total_project_days, phase_df, daily_df):
    # In the fixed schedule strategy, the truck comes according to the existing pickup frequency.
    # It does not care how full the container is.
    # This can create two problems:
    # 1. The truck may come too early, when the container is almost empty. This creates unused pickups.
    # 2. The truck may come too late, after the container has overflowed. This creates overflow incidents and delay days.

    # This empty list will store all result rows for this strategy.
    results = []

    # This loop goes through every project phase.
    for _, phase_row in phase_df.iterrows():
        # Get the current phase name.
        phase_name = phase_row["Phase"]

        # Get the number of days in the current phase.
        phase_days = int(phase_row["Days"])

        # This loop goes through every waste stream.
        for _, waste_row in waste_df.iterrows():
            # Get the waste stream name.
            waste_name = waste_row["Waste Stream"]

            # Get the container capacity for this waste stream.
            container_capacity = waste_row["Container Capacity m3"]

            # Get the daily waste generation rate for this waste stream in this phase.
            daily_rate = daily_df.loc[waste_name, phase_name]

            # If there is no daily waste, there is nothing to simulate.
            if daily_rate == 0:
                # Skip this waste stream and move to the next one.
                continue

            # Convert the fixed frequency into actual pickup days.
            pickup_days = get_pickup_days(
                # Use the current frequency written in the waste table.
                waste_row["Current Frequency"],

                # Use the number of days in the current phase.
                phase_days
            )

            # This variable represents how much waste is currently inside the container.
            container_level = 0

            # This counts the total number of pickups.
            pickups = 0

            # This counts how many days the container overflowed.
            overflow_incidents = 0

            # This stores the total amount of waste that exceeded the container capacity.
            overflow_volume = 0

            # This adds up the utilization percentage at each pickup.
            utilization_sum = 0

            # This counts pickups where the container was less than 30% full.
            unused_pickups = 0

            # This counts site delay days caused by overflow.
            delay_days = 0

            # This loop simulates the phase day by day.
            for day in range(1, phase_days + 1):
                # Every day, new waste is added into the container.
                container_level += daily_rate

                # If the container level is higher than the container capacity, overflow happens.
                if container_level > container_capacity:
                    # Count one overflow incident for this day.
                    overflow_incidents += 1

                    # Add the amount above the container capacity to the overflow volume.
                    overflow_volume += container_level - container_capacity

                    # Add one delay day because overflow is assumed to disturb site operations.
                    delay_days += 1

                # If today is one of the planned pickup days, the truck arrives.
                if day in pickup_days:
                    # Count one pickup.
                    pickups += 1

                    # Calculate how full the container is at pickup time.
                    # min(container_level, container_capacity) is used so utilization cannot exceed 100%.
                    utilization = min(container_level, container_capacity) / container_capacity * 100

                    # Add this pickup utilization to the total utilization sum.
                    utilization_sum += utilization

                    # If the container is less than 30% full, this pickup is considered inefficient.
                    if utilization < 30:
                        # Count one unused or poorly used pickup.
                        unused_pickups += 1

                    # After pickup, the container is emptied.
                    container_level = 0

            # Calculate the average utilization across all pickups.
            avg_utilization = utilization_sum / pickups if pickups > 0 else 0

            # Add the result row for this phase and waste stream.
            results.append({
                "Run ID": run_id,
                "Total Project Days": total_project_days,
                "Strategy": "Fixed Schedule",
                "Phase": phase_name,
                "Phase Days": phase_days,
                "Waste Stream": waste_name,
                "Container Type": waste_row["Container Type"],
                "Container Capacity m3": round(container_capacity, 2),
                "Daily Generation Rate m3/day": daily_rate,
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

    # Convert all result rows into a DataFrame and return it.
    return pd.DataFrame(results)


# This function simulates the reactive strategy.
def simulate_reactive(run_id, total_project_days, phase_df, daily_df):
    # In the reactive strategy, there is no fixed schedule.
    # The pickup happens only when the container becomes full.
    # This usually reduces unused pickups, because the truck does not come when the container is almost empty.
    # However, because the check happens after daily waste is added, the container can still overflow slightly.

    # This empty list will store all result rows for the reactive strategy.
    results = []

    # Go through every construction phase.
    for _, phase_row in phase_df.iterrows():
        # Get the phase name.
        phase_name = phase_row["Phase"]

        # Get the number of days in this phase.
        phase_days = int(phase_row["Days"])

        # Go through every waste stream.
        for _, waste_row in waste_df.iterrows():
            # Get the waste stream name.
            waste_name = waste_row["Waste Stream"]

            # Get the container capacity.
            container_capacity = waste_row["Container Capacity m3"]

            # Get the daily waste generation rate for this waste stream and phase.
            daily_rate = daily_df.loc[waste_name, phase_name]

            # If no waste is generated, skip this case.
            if daily_rate == 0:
                # Move to the next waste stream.
                continue

            # Current amount of waste in the container.
            container_level = 0

            # Number of pickups performed.
            pickups = 0

            # Number of overflow events.
            overflow_incidents = 0

            # Total overflow volume.
            overflow_volume = 0

            # Sum of pickup utilizations.
            utilization_sum = 0

            # Number of delay days caused by overflow.
            delay_days = 0

            # Simulate the phase day by day.
            for day in range(1, phase_days + 1):
                # Add the daily waste generation to the container.
                container_level += daily_rate

                # If the container is full or above full, a pickup is triggered immediately.
                if container_level >= container_capacity:
                    # Count one pickup.
                    pickups += 1

                    # Calculate utilization at pickup, capped at 100%.
                    utilization = min(container_level, container_capacity) / container_capacity * 100

                    # Add the utilization to the total utilization sum.
                    utilization_sum += utilization

                    # If the container went above capacity, overflow occurred.
                    if container_level > container_capacity:
                        # Count one overflow incident.
                        overflow_incidents += 1

                        # Add the volume above capacity.
                        overflow_volume += container_level - container_capacity

                        # Count one site delay day.
                        delay_days += 1

                    # Empty the container after pickup.
                    container_level = 0

            # Calculate average utilization at pickup.
            avg_utilization = utilization_sum / pickups if pickups > 0 else 0

            # Store the result for this waste stream and phase.
            results.append({
                "Run ID": run_id,
                "Total Project Days": total_project_days,
                "Strategy": "Reactive",
                "Phase": phase_name,
                "Phase Days": phase_days,
                "Waste Stream": waste_name,
                "Container Type": waste_row["Container Type"],
                "Container Capacity m3": round(container_capacity, 2),
                "Daily Generation Rate m3/day": daily_rate,
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

    # Convert results to a DataFrame and return it.
    return pd.DataFrame(results)


# This function simulates one dynamic threshold test for one waste stream in one phase.
def simulate_dynamic_threshold(run_id, total_project_days, phase_name, phase_days, waste_row, daily_rate, threshold):
    # In the dynamic threshold strategy, the truck comes when the container reaches a chosen fullness level.
    # Example:
    # If the threshold is 80%, the pickup is triggered when the container is at least 80% full.
    # The code tests many thresholds from 50% to 100% and later selects the best one.

    # Get the container capacity for this waste stream.
    container_capacity = waste_row["Container Capacity m3"]

    # Convert the threshold percentage into an actual volume.
    # Example: if capacity = 20 m3 and threshold = 80%, threshold_volume = 16 m3.
    threshold_volume = container_capacity * threshold / 100

    # Current amount of waste in the container.
    container_level = 0

    # Number of pickups.
    pickups = 0

    # Number of overflow incidents.
    overflow_incidents = 0

    # Total overflow volume.
    overflow_volume = 0

    # Sum of utilization values at pickup.
    utilization_sum = 0

    # Number of site delay days caused by overflow.
    delay_days = 0

    # Simulate the current phase day by day.
    for day in range(1, phase_days + 1):
        # Add daily waste to the container.
        container_level += daily_rate

        # Check if the container has exceeded its maximum capacity.
        if container_level > container_capacity:
            # Count an overflow incident.
            overflow_incidents += 1

            # Add the excess volume to the overflow total.
            overflow_volume += container_level - container_capacity

            # Count one delay day due to overflow.
            delay_days += 1

        # If the container level reaches the selected threshold, trigger a pickup.
        if container_level >= threshold_volume:
            # Count one pickup.
            pickups += 1

            # Calculate pickup utilization, capped at 100%.
            utilization = min(container_level, container_capacity) / container_capacity * 100

            # Add this utilization to the total sum.
            utilization_sum += utilization

            # Empty the container after pickup.
            container_level = 0

    # Calculate average pickup utilization.
    avg_utilization = utilization_sum / pickups if pickups > 0 else 0

    # Return one dictionary with all results for this threshold test.
    return {
        "Run ID": run_id,
        "Total Project Days": total_project_days,
        "Strategy": "Dynamic Threshold",
        "Phase": phase_name,
        "Phase Days": phase_days,
        "Waste Stream": waste_row["Waste Stream"],
        "Container Type": waste_row["Container Type"],
        "Container Capacity m3": round(container_capacity, 2),
        "Daily Generation Rate m3/day": daily_rate,
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


# This function simulates the ideal optimized strategy.
def simulate_ideal(run_id, total_project_days, phase_df, daily_df):
    # The ideal optimized strategy is a theoretical benchmark.
    # Instead of using the existing container size, it creates a custom ideal container size.
    # The ideal capacity is calculated as a percentage of the total waste generated in the phase.
    # This is useful because it shows how good the system could be if container sizing was perfectly optimized.

    # This empty list will store the ideal strategy results.
    results = []

    # Loop through each construction phase.
    for _, phase_row in phase_df.iterrows():
        # Get the phase name.
        phase_name = phase_row["Phase"]

        # Get the number of days in this phase.
        phase_days = int(phase_row["Days"])

        # Loop through each waste stream.
        for _, waste_row in waste_df.iterrows():
            # Get the waste stream name.
            waste_name = waste_row["Waste Stream"]

            # Get the daily waste generation rate.
            daily_rate = daily_df.loc[waste_name, phase_name]

            # If no waste is generated, skip this case.
            if daily_rate == 0:
                # Move to the next waste stream.
                continue

            # Calculate total waste generated during this phase.
            total_generated = daily_rate * phase_days

            # Calculate the ideal container capacity as 25% of total generated waste.
            ideal_capacity = total_generated * IDEAL_CONTAINER_RATIO

            # Make sure the ideal container is not smaller than one day of waste generation.
            # This is a safety rule. Without it, a very small ideal container could be unrealistic.
            ideal_capacity = max(ideal_capacity, daily_rate)

            # Current waste level inside the ideal container.
            container_level = 0

            # Number of pickups.
            pickups = 0

            # Sum of utilization percentages at pickup.
            utilization_sum = 0

            # Simulate the phase day by day.
            for day in range(1, phase_days + 1):
                # Add daily waste to the container.
                container_level += daily_rate

                # If the ideal container reaches its capacity, trigger a pickup.
                if container_level >= ideal_capacity:
                    # Count one pickup.
                    pickups += 1

                    # Calculate utilization, capped at 100%.
                    utilization = min(container_level, ideal_capacity) / ideal_capacity * 100

                    # Add this utilization to the total.
                    utilization_sum += utilization

                    # Empty the container after pickup.
                    container_level = 0

            # At the end of the phase, there may still be some waste left in the container.
            if container_level > 0:
                # Count one final pickup to remove the remaining waste.
                pickups += 1

                # Calculate utilization for the final pickup.
                utilization = container_level / ideal_capacity * 100

                # Add the final pickup utilization to the total.
                utilization_sum += utilization

                # Empty the container.
                container_level = 0

            # Calculate average utilization across all ideal pickups.
            avg_utilization = utilization_sum / pickups if pickups > 0 else 0

            # Store the ideal strategy result.
            results.append({
                "Run ID": run_id,
                "Total Project Days": total_project_days,
                "Strategy": "Ideal Optimized",
                "Phase": phase_name,
                "Phase Days": phase_days,
                "Waste Stream": waste_name,
                "Container Type": "Ideal sized container",
                "Container Capacity m3": round(ideal_capacity, 2),
                "Daily Generation Rate m3/day": daily_rate,
                "Total Generated m3": round(total_generated, 2),
                "Best Threshold %": "100",
                "Number of Pickups": pickups,
                "Average Utilization at Pickup %": round(avg_utilization, 1),
                "Overflow Incidents": 0,
                "Total Overflow Volume m3": 0,
                "Unused Pickups": 0,
                "Site Delay Days": 0,
                "Final Container Level m3": 0
            })

    # Convert all ideal results into a DataFrame and return it.
    return pd.DataFrame(results)


# This function tests all dynamic thresholds and chooses the best one.
def simulate_dynamic(run_id, total_project_days, phase_df, daily_df):
    # This is the main dynamic strategy function.
    # For each phase and waste stream, it tests many threshold values from 50% to 100%.
    # Then it chooses the best threshold using this logic:
    # 1. Prefer thresholds with zero overflow.
    # 2. Among zero-overflow thresholds, choose the one with the fewest pickups.
    # 3. If pickups are equal, choose the one with higher utilization.
    # 4. If utilization is also similar, choose the higher threshold.
    # If every threshold causes overflow, it chooses the threshold with the least overflow first.

    # This list stores only the best threshold result for each phase and waste stream.
    best_results = []

    # This list stores every threshold test, not only the best one.
    threshold_tests = []

    # Loop through every construction phase.
    for _, phase_row in phase_df.iterrows():
        # Get the phase name.
        phase_name = phase_row["Phase"]

        # Get the phase duration.
        phase_days = int(phase_row["Days"])

        # Loop through every waste stream.
        for _, waste_row in waste_df.iterrows():
            # Get the waste stream name.
            waste_name = waste_row["Waste Stream"]

            # Get the daily waste rate for this phase and waste stream.
            daily_rate = daily_df.loc[waste_name, phase_name]

            # If no waste is generated, skip this case.
            if daily_rate == 0:
                # Move to the next case.
                continue

            # This list stores the threshold results for this specific phase and waste stream.
            threshold_results = []

            # Test every threshold from 50% to 100%.
            for threshold in range(50, 101):
                # Simulate the current threshold.
                result = simulate_dynamic_threshold(
                    run_id,
                    total_project_days,
                    phase_name,
                    phase_days,
                    waste_row,
                    daily_rate,
                    threshold
                )

                # Store this threshold result for choosing the best threshold later.
                threshold_results.append(result)

                # Store this threshold result in the complete threshold test list.
                threshold_tests.append(result)

            # Keep only the threshold results that produced zero overflow incidents.
            no_overflow = [
                # Keep this result.
                r for r in threshold_results

                # Only if the number of overflow incidents is zero.
                if r["Overflow Incidents"] == 0
            ]

            # If there are thresholds with no overflow, choose the best among them.
            if no_overflow:
                # Sort the zero-overflow results using the optimization rules.
                best = sorted(
                    # Sort only the no-overflow results.
                    no_overflow,

                    # Sorting key defines what "best" means.
                    key=lambda r: (
                        # First priority: fewer pickups is better.
                        r["Number of Pickups"],

                        # Second priority: higher utilization is better, so we use negative value.
                        -r["Average Utilization at Pickup %"],

                        # Third priority: higher threshold is better, so we use negative value.
                        -r["Best Threshold %"]
                    )

                # Take the first result after sorting, which is the best one.
                )[0]

            # If all threshold options caused overflow, choose the least bad option.
            else:
                # Sort all threshold results using fallback rules.
                best = sorted(
                    # Sort all tested thresholds.
                    threshold_results,

                    # Sorting key for the fallback case.
                    key=lambda r: (
                        # First priority: fewer overflow incidents.
                        r["Overflow Incidents"],

                        # Second priority: fewer pickups.
                        r["Number of Pickups"],

                        # Third priority: higher utilization.
                        -r["Average Utilization at Pickup %"]
                    )

                # Take the best fallback result.
                )[0]

            # Add the selected best threshold result to the final dynamic results.
            best_results.append(best)

    # Return two DataFrames: best dynamic results and all threshold test results.
    return pd.DataFrame(best_results), pd.DataFrame(threshold_tests)


# This function creates a summary per run and per strategy.
def create_summary(combined_df):
    # The detailed simulation results have one row per phase, waste stream, and strategy.
    # This function groups those detailed rows into one summary row per run and strategy.
    # For example, for Run 1 and Fixed Schedule, it calculates:
    # total pickups,
    # total overflow,
    # total delays,
    # total truck kilometers,
    # total CO2 emissions,
    # and total time impact.

    # This empty list will store the summary rows.
    summary_rows = []

    # Group the combined results by Run ID and Strategy.
    for (run_id, strategy), group in combined_df.groupby(["Run ID", "Strategy"]):
        # Convert the Unused Pickups column into numeric values.
        # Some strategies use blank values, so errors="coerce" converts blanks to NaN.
        unused_pickups = pd.to_numeric(
            group["Unused Pickups"],
            errors="coerce"
        ).fillna(0)

        # Calculate the total number of pickups for this run and strategy.
        total_pickups = group["Number of Pickups"].sum()

        # Calculate the total site delay days for this run and strategy.
        delay_days = group["Site Delay Days"].sum()

        # Convert pickups into operational hours.
        operational_hours = total_pickups * HOURS_PER_PICKUP

        # Convert delay days into delay hours.
        delay_hours = delay_days * WORKING_HOURS_PER_DELAY_DAY

        # Total time impact is pickup operation time plus delay time.
        total_time_impact = operational_hours + delay_hours

        # Calculate total truck distance for all pickups.
        total_truck_km = total_pickups * ROUND_TRIP_DISTANCE_KM

        # Calculate CO2 emissions from truck kilometers.
        total_co2_kg = total_truck_km * CO2_EMISSION_FACTOR_KG_PER_KM

        # Add one summary row for this run and strategy.
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

    # Convert summary rows into a DataFrame and return it.
    return pd.DataFrame(summary_rows)


# =========================================================
# RUN MONTE CARLO SIMULATIONS
# =========================================================

# This list will store all random input data for every run.
all_inputs = []

# This list will store fixed schedule results for every run.
all_fixed = []

# This list will store reactive strategy results for every run.
all_reactive = []

# This list will store best dynamic threshold results for every run.
all_dynamic = []

# This list will store all dynamic threshold tests for every run.
all_threshold_tests = []

# This list will store ideal optimized strategy results for every run.
all_ideal = []

# This loop runs the complete Monte Carlo simulation from run 1 to run 1000.
for run_id in range(1, NUMBER_OF_RUNS + 1):
    # Create the random project duration, phase durations, and waste rates for this run.
    total_project_days, phase_df, daily_df, input_df = create_random_input_data(run_id)

    # Simulate the fixed schedule strategy for this run.
    fixed_df = simulate_fixed(run_id, total_project_days, phase_df, daily_df)

    # Simulate the reactive strategy for this run.
    reactive_df = simulate_reactive(run_id, total_project_days, phase_df, daily_df)

    # Simulate the dynamic strategy and get both best thresholds and all tested thresholds.
    dynamic_df, threshold_df = simulate_dynamic(run_id, total_project_days, phase_df, daily_df)

    # Simulate the theoretical ideal optimized strategy.
    ideal_df = simulate_ideal(run_id, total_project_days, phase_df, daily_df)

    # Store the input data for this run.
    all_inputs.append(input_df)

    # Store the fixed schedule results for this run.
    all_fixed.append(fixed_df)

    # Store the reactive results for this run.
    all_reactive.append(reactive_df)

    # Store the dynamic results for this run.
    all_dynamic.append(dynamic_df)

    # Store the ideal results for this run.
    all_ideal.append(ideal_df)

    # Store all threshold test results for this run.
    all_threshold_tests.append(threshold_df)

# Combine all input DataFrames into one big input table.
input_all_df = pd.concat(all_inputs, ignore_index=True)

# Combine all fixed schedule results into one big table.
fixed_all_df = pd.concat(all_fixed, ignore_index=True)

# Combine all reactive results into one big table.
reactive_all_df = pd.concat(all_reactive, ignore_index=True)

# Combine all dynamic results into one big table.
dynamic_all_df = pd.concat(all_dynamic, ignore_index=True)

# Combine all ideal optimized results into one big table.
ideal_all_df = pd.concat(all_ideal, ignore_index=True)

# Combine all dynamic threshold test results into one big table.
threshold_all_df = pd.concat(all_threshold_tests, ignore_index=True)

# Combine the main strategy results into one table.
combined_all_df = pd.concat(
    # These are the strategy result tables to combine.
    [fixed_all_df, reactive_all_df, dynamic_all_df, ideal_all_df],

    # This resets the row index after combining.
    ignore_index=True
)

# Create one summary table per run and per strategy.
summary_all_df = create_summary(combined_all_df)

# =========================================================
# OVERALL AVERAGE SUMMARY
# =========================================================

# This groups the summary table by strategy and calculates the average result across all runs.
overall_summary_df = summary_all_df.groupby("Strategy").agg({
    # Average total generated waste.
    "Total Generated Waste m3": "mean",

    # Average number of pickups.
    "Total Pickups": "mean",

    # Average utilization percentage.
    "Average Utilization %": "mean",

    # Average overflow incidents.
    "Total Overflow Incidents": "mean",

    # Average overflow volume.
    "Total Overflow Volume m3": "mean",

    # Average site delay days.
    "Total Site Delay Days": "mean",

    # Average unused pickups.
    "Total Unused Pickups": "mean",

    # Average pickup operation hours.
    "Operational Pickup Hours": "mean",

    # Average delay hours.
    "Delay Hours": "mean",

    # Average total time impact hours.
    "Total Time Impact Hours": "mean",

    # Average truck kilometers.
    "Total Truck Kilometers Traveled": "mean",

    # Average CO2 emissions.
    "CO2 Emissions kg": "mean"
}).reset_index()

# Round all numerical columns in the overall summary to 2 decimal places.
overall_summary_df = overall_summary_df.round(2)

# =========================================================
# HOURS SAVED
# =========================================================

# This list will store the hours saved calculation for every run.
hours_saved_rows = []

# Go through every Monte Carlo run.
for run_id in range(1, NUMBER_OF_RUNS + 1):

    # Select only the summary rows belonging to the current run.
    run_summary = summary_all_df[
        summary_all_df["Run ID"] == run_id
    ]

    # Get the total time impact hours for the fixed schedule strategy.
    fixed_hours = run_summary.loc[
        run_summary["Strategy"] == "Fixed Schedule",
        "Total Time Impact Hours"
    ].iloc[0]

    # Get the total time impact hours for the dynamic threshold strategy.
    dynamic_hours = run_summary.loc[
        run_summary["Strategy"] == "Dynamic Threshold",
        "Total Time Impact Hours"
    ].iloc[0]

    # Get the total time impact hours for the ideal optimized strategy.
    ideal_hours = run_summary.loc[
        run_summary["Strategy"] == "Ideal Optimized",
        "Total Time Impact Hours"
    ].iloc[0]

    # Add one row with the calculated time savings for this run.
    hours_saved_rows.append({
        # Store the run number.
        "Run ID": run_id,

        # Calculate how many hours the dynamic strategy saves compared to the fixed schedule.
        "Hours Saved by Dynamic vs Fixed":
            round(fixed_hours - dynamic_hours, 2),

        # Calculate how many hours the ideal strategy saves compared to the fixed schedule.
        "Hours Saved by Ideal vs Fixed":
            round(fixed_hours - ideal_hours, 2),

        # Calculate how far the dynamic strategy is from the ideal strategy.
        "Dynamic Gap from Ideal Hours":
            round(dynamic_hours - ideal_hours, 2)
    })

# Convert the hours saved rows into a DataFrame.
hours_saved_df = pd.DataFrame(hours_saved_rows)

# Calculate the cumulative average hours saved as the runs increase.
hours_saved_df["Cumulative Average Hours Saved"] = (
    hours_saved_df["Hours Saved by Dynamic vs Fixed"].expanding().mean()
)

# Calculate the average hours saved by the dynamic strategy compared with the fixed schedule.
average_hours_saved = hours_saved_df["Hours Saved by Dynamic vs Fixed"].mean()

# =========================================================
# SAVE CSV FILES
# =========================================================

# Save all random input data to a CSV file.
input_all_df.to_csv(os.path.join(output_folder, "random_input_data_all_runs.csv"), index=False)

# Save all fixed schedule results to a CSV file.
fixed_all_df.to_csv(os.path.join(output_folder, "fixed_results_all_runs.csv"), index=False)

# Save all reactive strategy results to a CSV file.
reactive_all_df.to_csv(os.path.join(output_folder, "reactive_results_all_runs.csv"), index=False)

# Save all dynamic strategy results to a CSV file.
dynamic_all_df.to_csv(os.path.join(output_folder, "dynamic_results_all_runs.csv"), index=False)

# Save all ideal optimized results to a CSV file.
ideal_all_df.to_csv(os.path.join(output_folder, "ideal_optimized_results_all_runs.csv"), index=False)

# Save all dynamic threshold test results to a CSV file.
threshold_all_df.to_csv(os.path.join(output_folder, "dynamic_threshold_tests_all_runs.csv"), index=False)

# Save all combined strategy results to a CSV file.
combined_all_df.to_csv(os.path.join(output_folder, "combined_results_all_runs.csv"), index=False)

# Save the summary per run to a CSV file.
summary_all_df.to_csv(os.path.join(output_folder, "summary_per_run.csv"), index=False)

# Save the overall average summary to a CSV file.
overall_summary_df.to_csv(os.path.join(output_folder, "overall_average_summary_1000_runs.csv"), index=False)

# Save the hours saved analysis to a CSV file.
hours_saved_df.to_csv(os.path.join(output_folder, "hours_saved_per_run.csv"), index=False)

# =========================================================
# CREATE FORMATTED EXCEL REPORT
# =========================================================

# Create the full path for the formatted Excel report.
excel_report_path = os.path.join(
    # Save it inside the output folder.
    output_folder,

    # This is the Excel file name.
    "monte_carlo_formatted_report.xlsx"
)

# Open an Excel writer using the xlsxwriter engine.
with pd.ExcelWriter(excel_report_path, engine="xlsxwriter") as writer:

    # Access the workbook object so formatting can be created.
    workbook = writer.book

    # Create a format for large title cells.
    title_format = workbook.add_format({
        "bold": True,
        "font_size": 16,
        "align": "center",
        "valign": "vcenter",
        "bg_color": "#1F4E78",
        "font_color": "white"
    })

    # Create a format for table headers.
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

    # Write the overall summary table into the Excel report.
    overall_summary_df.to_excel(
        writer,
        sheet_name="Executive Summary",
        index=False,
        startrow=3
    )

    # Access the Executive Summary worksheet.
    ws = writer.sheets["Executive Summary"]

    # Merge cells A1 to M1 and write the main sheet title.
    ws.merge_range(
        "A1:M1",
        "Monte Carlo Construction Waste Logistics - Strategy Comparison",
        title_format
    )

    # Write the number of simulation runs.
    ws.write("A2", f"Number of simulation runs: {NUMBER_OF_RUNS}")

    # Write the project duration range.
    ws.write("D2", f"Project duration range: {MIN_PROJECT_DAYS} - {MAX_PROJECT_DAYS} days")

    # Write the container capacity range.
    ws.write("H2", f"Container capacity range: {MIN_CONTAINER_CAPACITY} - {MAX_CONTAINER_CAPACITY} m³")

    # Apply the custom header format to every column header.
    for col_num, value in enumerate(overall_summary_df.columns.values):
        ws.write(3, col_num, value, header_format)

    # Set the width of column A.
    ws.set_column("A:A", 22)

    # Set the width of columns B to M.
    ws.set_column("B:M", 20)

    # Add filters to the summary table.
    ws.autofilter(3, 0, len(overall_summary_df) + 3, len(overall_summary_df.columns) - 1)

    # Freeze the top rows so the headers stay visible while scrolling.
    ws.freeze_panes(4, 0)

    # -----------------------------
    # Sheet 2: Hours Saved
    # -----------------------------

    # Write the hours saved table into the Excel report.
    hours_saved_df.to_excel(
        writer,
        sheet_name="Hours Saved",
        index=False,
        startrow=2
    )

    # Access the Hours Saved worksheet.
    ws2 = writer.sheets["Hours Saved"]

    # Merge cells A1 to D1 and write the sheet title.
    ws2.merge_range(
        "A1:D1",
        "Hours Saved Analysis",
        title_format
    )

    # Apply the custom header format to the table headers.
    for col_num, value in enumerate(hours_saved_df.columns.values):
        ws2.write(2, col_num, value, header_format)

    # Set the width of column A.
    ws2.set_column("A:A", 12)

    # Set the width of columns B to E.
    ws2.set_column("B:E", 32)

    # Add filters to the hours saved table.
    ws2.autofilter(2, 0, len(hours_saved_df) + 2, len(hours_saved_df.columns) - 1)

    # Freeze the top rows.
    ws2.freeze_panes(3, 0)

    # -----------------------------
    # Sheet 3: Strategy Ranking
    # -----------------------------

    # Make a copy of the overall summary table for ranking.
    ranking_df = overall_summary_df.copy()

    # Rank strategies by total time impact. Lower time impact is better.
    ranking_df["Operational Rank"] = ranking_df["Total Time Impact Hours"].rank(method="min")

    # Rank strategies by CO2 emissions. Lower emissions are better.
    ranking_df["Environmental Rank"] = ranking_df["CO2 Emissions kg"].rank(method="min")

    # Rank strategies by overflow incidents. Lower overflow is better.
    ranking_df["Overflow Rank"] = ranking_df["Total Overflow Incidents"].rank(method="min")

    # Calculate the final score by adding the three ranks.
    ranking_df["Final Score"] = (
        ranking_df["Operational Rank"]
        + ranking_df["Environmental Rank"]
        + ranking_df["Overflow Rank"]
    )

    # Sort the strategies by the final score. Lower score is better.
    ranking_df = ranking_df.sort_values("Final Score")

    # Write the ranking table into the Excel report.
    ranking_df.to_excel(
        writer,
        sheet_name="Strategy Ranking",
        index=False,
        startrow=2
    )

    # Access the Strategy Ranking worksheet.
    ws3 = writer.sheets["Strategy Ranking"]

    # Merge cells A1 to Q1 and write the sheet title.
    ws3.merge_range(
        "A1:Q1",
        "Strategy Ranking Based on Operational and Environmental KPIs",
        title_format
    )

    # Apply the custom header format to the ranking table headers.
    for col_num, value in enumerate(ranking_df.columns.values):
        ws3.write(2, col_num, value, header_format)

    # Set the width of column A.
    ws3.set_column("A:A", 22)

    # Set the width of columns B to Q.
    ws3.set_column("B:Q", 18)

    # Add filters to the ranking table.
    ws3.autofilter(2, 0, len(ranking_df) + 2, len(ranking_df.columns) - 1)

    # Freeze the top rows.
    ws3.freeze_panes(3, 0)

    # -----------------------------
    # Sheet 4: Assumptions
    # -----------------------------

    # Create a table containing the main assumptions used in the simulation.
    assumptions_df = pd.DataFrame({
        "Parameter": [
            "Number of Monte Carlo runs",
            "Minimum project duration",
            "Maximum project duration",
            "Minimum container capacity",
            "Maximum container capacity",
            "Maximum daily waste ratio",
            "Hours per pickup",
            "Working hours per delay day",
            "One-way truck distance",
            "Round-trip truck distance",
            "CO2 emission factor",
            "Ideal container ratio"
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
            IDEAL_CONTAINER_RATIO
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
            "ratio"
        ]
    })

    # Write the assumptions table into the Excel report.
    assumptions_df.to_excel(
        writer,
        sheet_name="Assumptions",
        index=False,
        startrow=2
    )

    # Access the Assumptions worksheet.
    ws4 = writer.sheets["Assumptions"]

    # Merge cells A1 to C1 and write the sheet title.
    ws4.merge_range(
        "A1:C1",
        "Simulation Assumptions",
        title_format
    )

    # Apply the custom header format to the assumptions table headers.
    for col_num, value in enumerate(assumptions_df.columns.values):
        ws4.write(2, col_num, value, header_format)

    # Set the width of column A.
    ws4.set_column("A:A", 34)

    # Set the width of columns B and C.
    ws4.set_column("B:C", 20)

    # -----------------------------
    # Sheet 5: Detailed Run Inputs
    # -----------------------------

    # Write all random input data into the Excel report.
    input_all_df.to_excel(
        writer,
        sheet_name="Detailed Run Inputs",
        index=False,
        startrow=2
    )

    # Access the Detailed Run Inputs worksheet.
    ws5 = writer.sheets["Detailed Run Inputs"]

    # Merge cells A1 to F1 and write the sheet title.
    ws5.merge_range(
        "A1:F1",
        "Detailed Random Input Data for Every Monte Carlo Run",
        title_format
    )

    # Apply the custom header format to the input table headers.
    for col_num, value in enumerate(input_all_df.columns.values):
        ws5.write(2, col_num, value, header_format)

    # Set the width of column A.
    ws5.set_column("A:A", 10)

    # Set the width of column B.
    ws5.set_column("B:B", 18)

    # Set the width of column C.
    ws5.set_column("C:C", 20)

    # Set the width of column D.
    ws5.set_column("D:D", 12)

    # Set the width of column E.
    ws5.set_column("E:E", 25)

    # Set the width of column F.
    ws5.set_column("F:F", 32)

    # Add filters to the input table.
    ws5.autofilter(2, 0, len(input_all_df) + 2, len(input_all_df.columns) - 1)

    # Freeze the top rows.
    ws5.freeze_panes(3, 0)

    # -----------------------------
    # Sheet 6: Detailed Strategy Results
    # -----------------------------

    # Write all combined strategy results into the Excel report.
    combined_all_df.to_excel(
        writer,
        sheet_name="Detailed Results",
        index=False,
        startrow=2
    )

    # Access the Detailed Results worksheet.
    ws6 = writer.sheets["Detailed Results"]

    # Merge cells A1 to R1 and write the sheet title.
    ws6.merge_range(
        "A1:R1",
        "Detailed Strategy Results for Every Run",
        title_format
    )

    # Apply the custom header format to the detailed results table headers.
    for col_num, value in enumerate(combined_all_df.columns.values):
        ws6.write(2, col_num, value, header_format)

    # Set the width of column A.
    ws6.set_column("A:A", 10)

    # Set the width of column B.
    ws6.set_column("B:B", 18)

    # Set the width of column C.
    ws6.set_column("C:C", 22)

    # Set the width of columns D to R.
    ws6.set_column("D:R", 18)

    # Add filters to the detailed results table.
    ws6.autofilter(2, 0, len(combined_all_df) + 2, len(combined_all_df.columns) - 1)

    # Freeze the top rows.
    ws6.freeze_panes(3, 0)

# Print a blank line and a message saying the formatted Excel report was created.
print("\nFormatted Excel report created:")

# Print the full path of the formatted Excel report.
print(excel_report_path)


# =========================================================
# DASHBOARD GRAPHS
# =========================================================

# Create a dashboard figure with 2 rows and 3 columns of charts.
fig, axes = plt.subplots(2, 3, figsize=(18, 10))

# Create a bar chart for average total pickups per strategy.
axes[0, 0].bar(
    overall_summary_df["Strategy"],
    overall_summary_df["Total Pickups"]
)

# Set the chart title.
axes[0, 0].set_title("Average Total Pickups per Strategy")

# Set the y-axis label.
axes[0, 0].set_ylabel("Average Pickups")

# Create a bar chart for average overflow incidents per strategy.
axes[0, 1].bar(
    overall_summary_df["Strategy"],
    overall_summary_df["Total Overflow Incidents"]
)

# Set the chart title.
axes[0, 1].set_title("Average Overflow Incidents per Strategy")

# Set the y-axis label.
axes[0, 1].set_ylabel("Average Overflow Incidents")

# Create a bar chart for average container utilization.
axes[0, 2].bar(
    overall_summary_df["Strategy"],
    overall_summary_df["Average Utilization %"]
)

# Set the chart title.
axes[0, 2].set_title("Average Container Utilization")

# Set the y-axis label.
axes[0, 2].set_ylabel("Utilization (%)")

# Create a bar chart for average CO2 emissions.
axes[1, 0].bar(
    overall_summary_df["Strategy"],
    overall_summary_df["CO2 Emissions kg"]
)

# Set the chart title.
axes[1, 0].set_title("Average CO₂ Emissions per Strategy")

# Set the y-axis label.
axes[1, 0].set_ylabel("kg CO₂")

# Create a scatter plot showing the relationship between pickups and overflow incidents.
axes[1, 1].scatter(
    overall_summary_df["Total Pickups"],
    overall_summary_df["Total Overflow Incidents"]
)

# Add the strategy name next to each scatter point.
for _, row in overall_summary_df.iterrows():
    axes[1, 1].annotate(
        row["Strategy"],
        (
            row["Total Pickups"],
            row["Total Overflow Incidents"]
        )
    )

# Set the scatter plot title.
axes[1, 1].set_title("Pickups vs Overflow Tradeoff")

# Set the x-axis label.
axes[1, 1].set_xlabel("Average Pickups")

# Set the y-axis label.
axes[1, 1].set_ylabel("Average Overflow Incidents")

# Create a line chart showing how the cumulative average hours saved changes as more runs are added.
axes[1, 2].plot(
    hours_saved_df["Run ID"],
    hours_saved_df["Cumulative Average Hours Saved"]
)

# Set the chart title.
axes[1, 2].set_title("Monte Carlo Convergence")

# Set the x-axis label.
axes[1, 2].set_xlabel("Number of Runs")

# Set the y-axis label.
axes[1, 2].set_ylabel("Cumulative Avg Hours Saved")

# Rotate the x-axis labels on the first chart to make the strategy names easier to read.
axes[0, 0].tick_params(axis="x", rotation=15)

# Rotate the x-axis labels on the second chart.
axes[0, 1].tick_params(axis="x", rotation=15)

# Rotate the x-axis labels on the third chart.
axes[0, 2].tick_params(axis="x", rotation=15)

# Rotate the x-axis labels on the fourth chart.
axes[1, 0].tick_params(axis="x", rotation=15)

# Adjust the layout so chart titles and labels do not overlap.
plt.tight_layout()

# Create the full file path for the dashboard image.
dashboard_path = os.path.join(
    output_folder,
    "monte_carlo_dashboard_1000_runs.png"
)

# Save the dashboard image as a high-resolution PNG file.
plt.savefig(dashboard_path, dpi=300)

# Display the dashboard graph on the screen.
plt.show()

# Close the figure to free memory.
plt.close()

# =========================================================
# PRINT FINAL RESULTS
# =========================================================

# Print a separator line.
print("\n====================================================")

# Print the final completion title.
print("MONTE CARLO SIMULATION COMPLETED")

# Print another separator line.
print("====================================================")

# Print the number of Monte Carlo runs.
print(f"\nNumber of runs: {NUMBER_OF_RUNS}")

# Print the project duration range.
print(f"Project duration range: {MIN_PROJECT_DAYS} - {MAX_PROJECT_DAYS} days")

# Print the container capacity range.
print(f"Container capacity range: {MIN_CONTAINER_CAPACITY} - {MAX_CONTAINER_CAPACITY} m3")

# Print the daily waste generation assumption.
print(f"Daily waste generation: 0 to {MAX_DAILY_WASTE_AS_CAPACITY_RATIO * 100:.0f}% of container capacity per day")

# Print a heading for the output folder.
print("\nFiles saved in folder:")

# Print the output folder path.
print(output_folder)

# Print a separator line.
print("\n====================================================")

# Print a heading for the overall average summary.
print("OVERALL AVERAGE SUMMARY FOR 1000 RUNS")

# Print a separator line.
print("====================================================")

# Print the overall summary table without the DataFrame index.
print(overall_summary_df.to_string(index=False))

# Print a separator line.
print("\n====================================================")

# Print a heading for the hours saved section.
print("HOURS SAVED")

# Print a separator line.
print("====================================================")

# Print the last 20 rows of the hours saved table.
print(hours_saved_df.tail(20).to_string(index=False))

# Print the average hours saved by the dynamic strategy compared to the fixed schedule.
print(f"\nAverage hours saved by Dynamic Strategy compared to Fixed Schedule: {average_hours_saved:.2f} hours")

# Print a heading for the dashboard path.
print("\nDashboard graph created:")

# Print the dashboard image path.
print(dashboard_path)
