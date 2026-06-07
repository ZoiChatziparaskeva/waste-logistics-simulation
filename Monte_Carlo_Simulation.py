import pandas as pd
import os
import random
import matplotlib.pyplot as plt         

# =========================================================
# MONTE CARLO SIMULATION SETTINGS
# =========================================================

NUMBER_OF_RUNS = 1000
MIN_PROJECT_DAYS = 100
MAX_PROJECT_DAYS = 1000

MIN_CONTAINER_CAPACITY = 10
MAX_CONTAINER_CAPACITY = 40
MAX_DAILY_WASTE_AS_CAPACITY_RATIO = 0.30

# Pickup hours are kept only as a logistics indicator.
# They are NOT used for the on-site hours saved calculation.
HOURS_PER_PICKUP = 1.5

# This is the only time assumption used for ON-SITE hours saved.
# Example: if one overflow episode causes disruption, it is counted as 3 on-site hours.
WORKING_HOURS_PER_DELAY_DAY = 1

AVERAGE_ONE_WAY_DISTANCE_KM = 15
ROUND_TRIP_DISTANCE_KM = AVERAGE_ONE_WAY_DISTANCE_KM * 2
CO2_EMISSION_FACTOR_KG_PER_KM = 0.9



random.seed(42)

# =========================================================
# OUTPUT FOLDER
# =========================================================

script_folder = os.path.dirname(os.path.abspath(__file__))
output_folder = os.path.join(script_folder, "monte_carlo_results_on_site_hours")
os.makedirs(output_folder, exist_ok=True)

# =========================================================
# FIXED DATA
# =========================================================

waste_streams = [
    ["Concrete & Masonry", "20-yard roll-off bin", random.uniform(MIN_CONTAINER_CAPACITY, MAX_CONTAINER_CAPACITY), "Weekly"],
    ["Wood", "Covered skip", random.uniform(MIN_CONTAINER_CAPACITY, MAX_CONTAINER_CAPACITY), "Twice per week"],
    ["Metals", "10-yd metal bin", random.uniform(MIN_CONTAINER_CAPACITY, MAX_CONTAINER_CAPACITY), "On demand"],
    ["Drywall", "10-yd bin", random.uniform(MIN_CONTAINER_CAPACITY, MAX_CONTAINER_CAPACITY), "Weekly"],
    ["Packaging", "Bag cages / bins", random.uniform(MIN_CONTAINER_CAPACITY, MAX_CONTAINER_CAPACITY), "Daily"],
    ["Mixed Residual Waste", "Sealed dumpster", random.uniform(MIN_CONTAINER_CAPACITY, MAX_CONTAINER_CAPACITY), "Weekly"]
]

waste_df = pd.DataFrame(
    waste_streams,
    columns=[
        "Waste Stream",
        "Container Type",
        "Container Capacity m3",
        "Current Frequency"
    ]
)

phase_names = [
    "Site Preparation",
    "Foundation",
    "Interior",
    "Finishing"
]

# =========================================================
# FUNCTIONS
# =========================================================

def split_project_days(total_days):
    cut1 = random.randint(1, total_days - 3)
    cut2 = random.randint(cut1 + 1, total_days - 2)
    cut3 = random.randint(cut2 + 1, total_days - 1)

    return [
        cut1,
        cut2 - cut1,
        cut3 - cut2,
        total_days - cut3
    ]


def create_random_input_data(run_id):
    total_project_days = random.randint(MIN_PROJECT_DAYS, MAX_PROJECT_DAYS)
    phase_days = split_project_days(total_project_days)

    phase_df = pd.DataFrame({
        "Phase": phase_names,
        "Days": phase_days
    })

    random_daily_data = {}

    for _, waste_row in waste_df.iterrows():
        waste_name = waste_row["Waste Stream"]
        container_capacity = waste_row["Container Capacity m3"]

        random_daily_data[waste_name] = [
            round(
                random.uniform(
                    0,
                    container_capacity * MAX_DAILY_WASTE_AS_CAPACITY_RATIO
                ),
                3
            )
            for _ in phase_names
        ]

    daily_df = pd.DataFrame(
        random_daily_data,
        index=phase_names
    ).T

    input_rows = []

    for phase in phase_names:
        for waste in waste_df["Waste Stream"]:
            input_rows.append({
                "Run ID": run_id,
                "Total Project Days": total_project_days,
                "Phase": phase,
                "Phase Days": int(phase_df.loc[phase_df["Phase"] == phase, "Days"].iloc[0]),
                "Waste Stream": waste,
                "Random Daily Waste Generation m3/day": daily_df.loc[waste, phase]
            })

    input_df = pd.DataFrame(input_rows)

    return total_project_days, phase_df, daily_df, input_df


def get_pickup_days(frequency, phase_days):
    if frequency == "Daily":
        return list(range(1, phase_days + 1))

    if frequency == "Weekly":
        return list(range(7, phase_days + 1, 7))

    if frequency == "Twice per week":
        return [
            day for day in range(1, phase_days + 1)
            if day % 3 == 0 or day % 7 == 0
        ]

    # "On demand" means pickup when the container becomes full.
    # Returning None lets the fixed strategy handle this separately.
    if frequency == "On demand":
        return None

    return []


def simulate_fixed(run_id, total_project_days, phase_df, daily_df):
    results = []

    for _, phase_row in phase_df.iterrows():
        phase_name = phase_row["Phase"]
        phase_days = int(phase_row["Days"])

        for _, waste_row in waste_df.iterrows():
            waste_name = waste_row["Waste Stream"]
            container_capacity = waste_row["Container Capacity m3"]
            daily_rate = daily_df.loc[waste_name, phase_name]

            if daily_rate == 0:
                continue

            pickup_days = get_pickup_days(
                waste_row["Current Frequency"],
                phase_days
            )

            container_level = 0
            pickups = 0
            overflow_incidents = 0
            overflow_volume = 0
            utilization_sum = 0
            unused_pickups = 0
            delay_days = 0
            previous_overflow = False

            for day in range(1, phase_days + 1):
                container_level += daily_rate

                # Count only the first day of a continuous overflow episode.
                if container_level > container_capacity:
                    if previous_overflow is False:
                        overflow_incidents += 1
                        delay_days += 1

                    overflow_volume += container_level - container_capacity
                    previous_overflow = True

                else:
                    previous_overflow = False

                # If frequency is "On demand", pickup occurs when full.
                if pickup_days is None:
                    pickup_today = container_level >= container_capacity
                else:
                    pickup_today = day in pickup_days

                if pickup_today:
                    pickups += 1

                    utilization = (
                        min(container_level, container_capacity)
                        / container_capacity
                        * 100
                    )

                    utilization_sum += utilization

                    if utilization < 30:
                        unused_pickups += 1

                    container_level = 0
                    previous_overflow = False

            avg_utilization = utilization_sum / pickups if pickups > 0 else 0

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

    return pd.DataFrame(results)


def simulate_reactive(run_id, total_project_days, phase_df, daily_df):
    results = []

    for _, phase_row in phase_df.iterrows():
        phase_name = phase_row["Phase"]
        phase_days = int(phase_row["Days"])

        for _, waste_row in waste_df.iterrows():
            waste_name = waste_row["Waste Stream"]
            container_capacity = waste_row["Container Capacity m3"]
            daily_rate = daily_df.loc[waste_name, phase_name]

            if daily_rate == 0:
                continue

            container_level = 0
            pickups = 0
            overflow_incidents = 0
            overflow_volume = 0
            utilization_sum = 0
            delay_days = 0
            previous_overflow = False

            for day in range(1, phase_days + 1):
                container_level += daily_rate

                # Count only the first day of a continuous overflow episode.
                if container_level > container_capacity:
                    if previous_overflow is False:
                        overflow_incidents += 1
                        delay_days += 1

                    overflow_volume += container_level - container_capacity
                    previous_overflow = True

                else:
                    previous_overflow = False

                # Reactive pickup occurs when the container reaches capacity.
                if container_level >= container_capacity:
                    pickups += 1

                    utilization = (
                        min(container_level, container_capacity)
                        / container_capacity
                        * 100
                    )

                    utilization_sum += utilization

                    container_level = 0
                    previous_overflow = False

            avg_utilization = utilization_sum / pickups if pickups > 0 else 0

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

    return pd.DataFrame(results)


def simulate_dynamic_threshold(run_id, total_project_days, phase_name, phase_days, waste_row, daily_rate, threshold):
    container_capacity = waste_row["Container Capacity m3"]
    threshold_volume = container_capacity * threshold / 100

    container_level = 0
    pickups = 0
    overflow_incidents = 0
    overflow_volume = 0
    utilization_sum = 0
    delay_days = 0
    previous_overflow = False

    for day in range(1, phase_days + 1):
        container_level += daily_rate

        # Count only the first day of a continuous overflow episode.
        if container_level > container_capacity:
            if previous_overflow is False:
                overflow_incidents += 1
                delay_days += 1

            overflow_volume += container_level - container_capacity
            previous_overflow = True

        else:
            previous_overflow = False

        # Dynamic pickup occurs when selected threshold is reached.
        if container_level >= threshold_volume:
            pickups += 1

            utilization = (
                min(container_level, container_capacity)
                / container_capacity
                * 100
            )

            utilization_sum += utilization
            container_level = 0
            previous_overflow = False

    avg_utilization = utilization_sum / pickups if pickups > 0 else 0

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


def simulate_dynamic(run_id, total_project_days, phase_df, daily_df):
    best_results = []
    threshold_tests = []

    for _, phase_row in phase_df.iterrows():
        phase_name = phase_row["Phase"]
        phase_days = int(phase_row["Days"])

        for _, waste_row in waste_df.iterrows():
            waste_name = waste_row["Waste Stream"]
            daily_rate = daily_df.loc[waste_name, phase_name]

            if daily_rate == 0:
                continue

            threshold_results = []

            for threshold in range(50, 101):
                result = simulate_dynamic_threshold(
                    run_id,
                    total_project_days,
                    phase_name,
                    phase_days,
                    waste_row,
                    daily_rate,
                    threshold
                )

                threshold_results.append(result)
                threshold_tests.append(result)

            no_overflow = [
                r for r in threshold_results
                if r["Overflow Incidents"] == 0
            ]

            if no_overflow:
                best = sorted(
                    no_overflow,
                    key=lambda r: (
                        r["Number of Pickups"],
                        -r["Average Utilization at Pickup %"],
                        -r["Best Threshold %"]
                    )
                )[0]
            else:
                best = sorted(
                    threshold_results,
                    key=lambda r: (
                        r["Overflow Incidents"],
                        r["Number of Pickups"],
                        -r["Average Utilization at Pickup %"]
                    )
                )[0]

            best_results.append(best)

    return pd.DataFrame(best_results), pd.DataFrame(threshold_tests)




def create_summary(combined_df):
    summary_rows = []

    for (run_id, strategy), group in combined_df.groupby(["Run ID", "Strategy"]):
        unused_pickups = pd.to_numeric(
            group["Unused Pickups"],
            errors="coerce"
        ).fillna(0)

        total_project_days = int(group["Total Project Days"].iloc[0])
        total_pickups = group["Number of Pickups"].sum()

        raw_delay_days = group["Site Delay Days"].sum()
        delay_days = min(raw_delay_days, total_project_days)

        operational_hours = total_pickups * HOURS_PER_PICKUP

        # ON-SITE TIME LOGIC:
        # Hours saved are based only on avoided site delay/disruption hours.
        delay_hours = delay_days * WORKING_HOURS_PER_DELAY_DAY
        on_site_time_impact_hours = delay_hours

        # This is kept only as an additional logistics indicator.
        total_logistics_time_hours = operational_hours + delay_hours

        total_truck_km = total_pickups * ROUND_TRIP_DISTANCE_KM
        total_co2_kg = total_truck_km * CO2_EMISSION_FACTOR_KG_PER_KM

        summary_rows.append({
            "Run ID": run_id,
            "Strategy": strategy,
            "Total Project Days": total_project_days,
            "Total Generated Waste m3": round(group["Total Generated m3"].sum(), 2),
            "Total Pickups": int(total_pickups),
            "Average Utilization %": round(group["Average Utilization at Pickup %"].mean(), 1),
            "Total Overflow Incidents": int(group["Overflow Incidents"].sum()),
            "Total Overflow Volume m3": round(group["Total Overflow Volume m3"].sum(), 2),
            "Total Site Delay Days": int(delay_days),
            "Raw Delay Events Before Cap": int(raw_delay_days),
            "Total Unused Pickups": int(unused_pickups.sum()),
            "Operational Pickup Hours": round(operational_hours, 2),
            "Delay Hours": round(delay_hours, 2),
            "On-Site Time Impact Hours": round(on_site_time_impact_hours, 2),
            "Total Logistics Time Hours": round(total_logistics_time_hours, 2),
            "Total Truck Kilometers Traveled": round(total_truck_km, 2),
            "CO2 Emissions kg": round(total_co2_kg, 2)
        })

    return pd.DataFrame(summary_rows)

# =========================================================
# RUN MONTE CARLO SIMULATIONS
# =========================================================

all_inputs = []
all_fixed = []
all_reactive = []
all_dynamic = []
all_threshold_tests = []

for run_id in range(1, NUMBER_OF_RUNS + 1):
    total_project_days, phase_df, daily_df, input_df = create_random_input_data(run_id)

    fixed_df = simulate_fixed(run_id, total_project_days, phase_df, daily_df)
    reactive_df = simulate_reactive(run_id, total_project_days, phase_df, daily_df)
    dynamic_df, threshold_df = simulate_dynamic(run_id, total_project_days, phase_df, daily_df)


    all_inputs.append(input_df)
    all_fixed.append(fixed_df)
    all_reactive.append(reactive_df)
    all_dynamic.append(dynamic_df)
    all_threshold_tests.append(threshold_df)

input_all_df = pd.concat(all_inputs, ignore_index=True)
fixed_all_df = pd.concat(all_fixed, ignore_index=True)
reactive_all_df = pd.concat(all_reactive, ignore_index=True)
dynamic_all_df = pd.concat(all_dynamic, ignore_index=True)
threshold_all_df = pd.concat(all_threshold_tests, ignore_index=True)

combined_all_df = pd.concat(
    [fixed_all_df, reactive_all_df, dynamic_all_df],
    ignore_index=True
)

summary_all_df = create_summary(combined_all_df)

# =========================================================
# OVERALL AVERAGE SUMMARY
# =========================================================

overall_summary_df = summary_all_df.groupby("Strategy").agg({
    "Total Generated Waste m3": "mean",
    "Total Pickups": "mean",
    "Average Utilization %": "mean",
    "Total Overflow Incidents": "mean",
    "Total Overflow Volume m3": "mean",
    "Total Site Delay Days": "mean",
    "Raw Delay Events Before Cap": "mean",
    "Total Unused Pickups": "mean",
    "Operational Pickup Hours": "mean",
    "Delay Hours": "mean",
    "On-Site Time Impact Hours": "mean",
    "Total Logistics Time Hours": "mean",
    "Total Truck Kilometers Traveled": "mean",
    "CO2 Emissions kg": "mean"
}).reset_index()

overall_summary_df = overall_summary_df.round(2)

# =========================================================
# HOURS SAVED
# =========================================================

hours_saved_rows = []

for run_id in range(1, NUMBER_OF_RUNS + 1):
    run_summary = summary_all_df[
        summary_all_df["Run ID"] == run_id
    ]

    fixed_hours = run_summary.loc[
        run_summary["Strategy"] == "Fixed Schedule",
        "On-Site Time Impact Hours"
    ].iloc[0]

    dynamic_hours = run_summary.loc[
        run_summary["Strategy"] == "Dynamic Threshold",
        "On-Site Time Impact Hours"
    ].iloc[0]


    hours_saved_rows.append({
        "Run ID": run_id,
        "On-Site Hours Saved by Dynamic vs Fixed": round(fixed_hours - dynamic_hours, 2),
        "On-Site Days Saved by Dynamic vs Fixed": round((fixed_hours - dynamic_hours) / WORKING_HOURS_PER_DELAY_DAY, 2)
    })

hours_saved_df = pd.DataFrame(hours_saved_rows)

hours_saved_df["Cumulative Average Hours Saved"] = (
    hours_saved_df["On-Site Hours Saved by Dynamic vs Fixed"].expanding().mean()
)

average_hours_saved = hours_saved_df["On-Site Hours Saved by Dynamic vs Fixed"].mean()

# =========================================================
# SAVE CSV FILES
# =========================================================

input_all_df.to_csv(os.path.join(output_folder, "random_input_data_all_runs.csv"), index=False)
fixed_all_df.to_csv(os.path.join(output_folder, "fixed_results_all_runs.csv"), index=False)
reactive_all_df.to_csv(os.path.join(output_folder, "reactive_results_all_runs.csv"), index=False)
dynamic_all_df.to_csv(os.path.join(output_folder, "dynamic_results_all_runs.csv"), index=False)
threshold_all_df.to_csv(os.path.join(output_folder, "dynamic_threshold_tests_all_runs.csv"), index=False)
combined_all_df.to_csv(os.path.join(output_folder, "combined_results_all_runs.csv"), index=False)
summary_all_df.to_csv(os.path.join(output_folder, "summary_per_run.csv"), index=False)
overall_summary_df.to_csv(os.path.join(output_folder, "overall_average_summary_1000_runs.csv"), index=False)
hours_saved_df.to_csv(os.path.join(output_folder, "on_site_hours_saved_per_run.csv"), index=False)

# =========================================================
# CREATE FORMATTED EXCEL REPORT
# =========================================================

excel_report_path = os.path.join(
    output_folder,
    "monte_carlo_formatted_report_on_site_hours.xlsx"
)

with pd.ExcelWriter(excel_report_path, engine="xlsxwriter") as writer:
    workbook = writer.book

    title_format = workbook.add_format({
        "bold": True,
        "font_size": 16,
        "align": "center",
        "valign": "vcenter",
        "bg_color": "#1F4E78",
        "font_color": "white"
    })

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

    overall_summary_df.to_excel(
        writer,
        sheet_name="Executive Summary",
        index=False,
        startrow=3
    )

    ws = writer.sheets["Executive Summary"]

    ws.merge_range(
        "A1:N1",
        "Monte Carlo Construction Waste Logistics - Strategy Comparison",
        title_format
    )

    ws.write("A2", f"Number of simulation runs: {NUMBER_OF_RUNS}")
    ws.write("D2", f"Project duration range: {MIN_PROJECT_DAYS} - {MAX_PROJECT_DAYS} days")
    ws.write("H2", f"Container capacity range: {MIN_CONTAINER_CAPACITY} - {MAX_CONTAINER_CAPACITY} m³")

    for col_num, value in enumerate(overall_summary_df.columns.values):
        ws.write(3, col_num, value, header_format)

    ws.set_column("A:A", 22)
    ws.set_column("B:N", 20)
    ws.autofilter(3, 0, len(overall_summary_df) + 3, len(overall_summary_df.columns) - 1)
    ws.freeze_panes(4, 0)

    # -----------------------------
    # Sheet 2: Hours Saved
    # -----------------------------

    hours_saved_df.to_excel(
        writer,
        sheet_name="Hours Saved",
        index=False,
        startrow=2
    )

    ws2 = writer.sheets["Hours Saved"]

    ws2.merge_range(
        "A1:F1",
        "Hours Saved Analysis",
        title_format
    )

    for col_num, value in enumerate(hours_saved_df.columns.values):
        ws2.write(2, col_num, value, header_format)

    ws2.set_column("A:A", 12)
    ws2.set_column("B:F", 32)
    ws2.autofilter(2, 0, len(hours_saved_df) + 2, len(hours_saved_df.columns) - 1)
    ws2.freeze_panes(3, 0)

    # -----------------------------
    # Sheet 3: Strategy Ranking
    # -----------------------------

    ranking_df = overall_summary_df.copy()

    ranking_df["Operational Rank"] = ranking_df["On-Site Time Impact Hours"].rank(method="min")
    ranking_df["Environmental Rank"] = ranking_df["CO2 Emissions kg"].rank(method="min")
    ranking_df["Overflow Rank"] = ranking_df["Total Overflow Incidents"].rank(method="min")

    ranking_df["Final Score"] = (
        ranking_df["Operational Rank"]
        + ranking_df["Environmental Rank"]
        + ranking_df["Overflow Rank"]
    )

    ranking_df = ranking_df.sort_values("Final Score")

    ranking_df.to_excel(
        writer,
        sheet_name="Strategy Ranking",
        index=False,
        startrow=2
    )

    ws3 = writer.sheets["Strategy Ranking"]

    ws3.merge_range(
        "A1:R1",
        "Strategy Ranking Based on Operational and Environmental KPIs",
        title_format
    )

    for col_num, value in enumerate(ranking_df.columns.values):
        ws3.write(2, col_num, value, header_format)

    ws3.set_column("A:A", 22)
    ws3.set_column("B:R", 18)
    ws3.autofilter(2, 0, len(ranking_df) + 2, len(ranking_df.columns) - 1)
    ws3.freeze_panes(3, 0)

    # -----------------------------
    # Sheet 4: Assumptions
    # -----------------------------

    assumptions_df = pd.DataFrame({
        "Parameter": [
            "Number of Monte Carlo runs",
            "Minimum project duration",
            "Maximum project duration",
            "Minimum container capacity",
            "Maximum container capacity",
            "Maximum daily waste ratio",
            "Hours per pickup",
            "Working hours per delay event",
            "One-way truck distance",
            "Round-trip truck distance",
            "CO2 emission factor",
            "Delay cap rule",
            "Overflow delay counting rule",
            "Hours saved definition"
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
            "Delay days capped at total project duration",
            "One continuous overflow episode counts as one delay event",
            "Only avoided site delay hours; pickup hours excluded"
        ],
        "Unit": [
            "runs",
            "days",
            "days",
            "m3",
            "m3",
            "ratio",
            "hours/pickup",
            "hours/event",
            "km",
            "km",
            "kg CO2/km",
            "logic rule",
            "logic rule",
            "calculation rule"
        ]
    })

    assumptions_df.to_excel(
        writer,
        sheet_name="Assumptions",
        index=False,
        startrow=2
    )

    ws4 = writer.sheets["Assumptions"]

    ws4.merge_range(
        "A1:C1",
        "Simulation Assumptions",
        title_format
    )

    for col_num, value in enumerate(assumptions_df.columns.values):
        ws4.write(2, col_num, value, header_format)

    ws4.set_column("A:A", 38)
    ws4.set_column("B:C", 34)

    # -----------------------------
    # Sheet 5: Detailed Run Inputs
    # -----------------------------

    input_all_df.to_excel(
        writer,
        sheet_name="Detailed Run Inputs",
        index=False,
        startrow=2
    )

    ws5 = writer.sheets["Detailed Run Inputs"]

    ws5.merge_range(
        "A1:F1",
        "Detailed Random Input Data for Every Monte Carlo Run",
        title_format
    )

    for col_num, value in enumerate(input_all_df.columns.values):
        ws5.write(2, col_num, value, header_format)

    ws5.set_column("A:A", 10)
    ws5.set_column("B:B", 18)
    ws5.set_column("C:C", 20)
    ws5.set_column("D:D", 12)
    ws5.set_column("E:E", 25)
    ws5.set_column("F:F", 32)

    ws5.autofilter(2, 0, len(input_all_df) + 2, len(input_all_df.columns) - 1)
    ws5.freeze_panes(3, 0)

    # -----------------------------
    # Sheet 6: Detailed Strategy Results
    # -----------------------------

    combined_all_df.to_excel(
        writer,
        sheet_name="Detailed Results",
        index=False,
        startrow=2
    )

    ws6 = writer.sheets["Detailed Results"]

    ws6.merge_range(
        "A1:R1",
        "Detailed Strategy Results for Every Run",
        title_format
    )

    for col_num, value in enumerate(combined_all_df.columns.values):
        ws6.write(2, col_num, value, header_format)

    ws6.set_column("A:A", 10)
    ws6.set_column("B:B", 18)
    ws6.set_column("C:C", 22)
    ws6.set_column("D:R", 18)

    ws6.autofilter(2, 0, len(combined_all_df) + 2, len(combined_all_df.columns) - 1)
    ws6.freeze_panes(3, 0)

print("\nFormatted Excel report created:")
print(excel_report_path)

# =========================================================
# DASHBOARD GRAPHS
# =========================================================

fig, axes = plt.subplots(2, 3, figsize=(18, 10))

axes[0, 0].bar(
    overall_summary_df["Strategy"],
    overall_summary_df["Total Pickups"]
)
axes[0, 0].set_title("Average Total Pickups per Strategy")
axes[0, 0].set_ylabel("Average Pickups")

axes[0, 1].bar(
    overall_summary_df["Strategy"],
    overall_summary_df["Total Overflow Incidents"]
)
axes[0, 1].set_title("Average Overflow Incidents per Strategy")
axes[0, 1].set_ylabel("Average Overflow Incidents")

axes[0, 2].bar(
    overall_summary_df["Strategy"],
    overall_summary_df["Average Utilization %"]
)
axes[0, 2].set_title("Average Container Utilization")
axes[0, 2].set_ylabel("Utilization (%)")

axes[1, 0].bar(
    overall_summary_df["Strategy"],
    overall_summary_df["CO2 Emissions kg"]
)
axes[1, 0].set_title("Average CO₂ Emissions per Strategy")
axes[1, 0].set_ylabel("kg CO₂")

axes[1, 1].scatter(
    overall_summary_df["Total Pickups"],
    overall_summary_df["Total Overflow Incidents"]
)

for _, row in overall_summary_df.iterrows():
    axes[1, 1].annotate(
        row["Strategy"],
        (
            row["Total Pickups"],
            row["Total Overflow Incidents"]
        )
    )

axes[1, 1].set_title("Pickups vs Overflow Tradeoff")
axes[1, 1].set_xlabel("Average Pickups")
axes[1, 1].set_ylabel("Average Overflow Incidents")

axes[1, 2].plot(
    hours_saved_df["Run ID"],
    hours_saved_df["Cumulative Average Hours Saved"]
)
axes[1, 2].set_title("Monte Carlo Convergence")
axes[1, 2].set_xlabel("Number of Runs")
axes[1, 2].set_ylabel("Cumulative Avg On-Site Hours Saved")

axes[0, 0].tick_params(axis="x", rotation=15)
axes[0, 1].tick_params(axis="x", rotation=15)
axes[0, 2].tick_params(axis="x", rotation=15)
axes[1, 0].tick_params(axis="x", rotation=15)

plt.tight_layout()

dashboard_path = os.path.join(
    output_folder,
    "monte_carlo_dashboard_1000_runs_on_site_hours.png"
)

plt.savefig(dashboard_path, dpi=300)
plt.show()
plt.close()

# =========================================================
# CDF GRAPH - DAYS SAVED
# =========================================================

cdf_x = (
    hours_saved_df["On-Site Days Saved by Dynamic vs Fixed"]
    .sort_values()
    .reset_index(drop=True)
)

cdf_y = [
    (i + 1) / len(cdf_x)
    for i in range(len(cdf_x))
]

plt.figure(figsize=(10, 6))

plt.plot(
    cdf_x,
    cdf_y,
    linewidth=2
)

plt.title("Cumulative Distribution of On-Site Days Saved\nDynamic Strategy vs Fixed Schedule")
plt.xlabel("Days Saved")
plt.ylabel("Cumulative Distribution")
plt.grid(True)
plt.tight_layout()

cdf_graph_path = os.path.join(
    output_folder,
    "cdf_on_site_days_saved_dynamic_vs_fixed.png"
)

plt.savefig(cdf_graph_path, dpi=300)
plt.show()
plt.close()

# =========================================================
# PRINT FINAL RESULTS
# =========================================================

print("\n====================================================")
print("MONTE CARLO SIMULATION COMPLETED")
print("====================================================")

print(f"\nNumber of runs: {NUMBER_OF_RUNS}")
print(f"Project duration range: {MIN_PROJECT_DAYS} - {MAX_PROJECT_DAYS} days")
print(f"Container capacity range: {MIN_CONTAINER_CAPACITY} - {MAX_CONTAINER_CAPACITY} m3")
print(f"Daily waste generation: 0 to {MAX_DAILY_WASTE_AS_CAPACITY_RATIO * 100:.0f}% of container capacity per day")

print("\nFiles saved in folder:")
print(output_folder)

print("\n====================================================")
print("OVERALL AVERAGE SUMMARY FOR 1000 RUNS")
print("====================================================")
print(overall_summary_df.to_string(index=False))

print("\n====================================================")
print("ON-SITE HOURS SAVED")
print("====================================================")
print(hours_saved_df.tail(20).to_string(index=False))

print(f"\nAverage ON-SITE hours saved by Dynamic Strategy compared to Fixed Schedule: {average_hours_saved:.2f} hours")

print("\nDashboard graph created:")
print(dashboard_path)

print("\nCDF graph created:")
print(cdf_graph_path)
