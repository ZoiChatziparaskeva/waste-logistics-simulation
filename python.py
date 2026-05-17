import pandas as pd # Brings in a tool called 'pandas' (nicknamed 'pd') used for creating and reading data tables (like Excel in Python).
import os # Brings in a tool called 'os' to help the computer read and create files and folders on your specific operating system.
import matplotlib.pyplot as plt # Brings in a tool called 'matplotlib' (nicknamed 'plt') used for drawing graphs and charts.

# =========================================================
# ASSUMPTIONS FOR TIME SAVINGS
# =========================================================

HOURS_PER_PICKUP = 1.5 # We assume it takes 1.5 hours of work every time a waste truck comes.
WORKING_HOURS_PER_DELAY_DAY = 8 # We assume a full day of work is 8 hours.

AVERAGE_ONE_WAY_DISTANCE_KM = 15 # The garbage dump is assumed to be 15 kilometers away.
ROUND_TRIP_DISTANCE_KM = AVERAGE_ONE_WAY_DISTANCE_KM * 2 # A full trip there and back is 15 times 2 (30 km).
CO2_EMISSION_FACTOR_KG_PER_KM = 0.9 # For every kilometer driven, the truck releases 0.9 kg of CO2 into the air.

# =========================================================
# OUTPUT FOLDER
# =========================================================

script_folder = os.path.dirname(os.path.abspath(__file__)) # Finds the exact folder on your computer where this Python file is currently saved.

output_folder = os.path.join( # Combines your current folder path with a new folder name to create a full destination path.
    script_folder, # The folder where we currently are.
    "construction_waste_results" # The name of the new folder we want to create inside the current one.
) # Ends the joining command.

os.makedirs(output_folder, exist_ok=True) # Tells the computer: "Create this folder. If it already exists, just ignore this step and don't crash."

# =========================================================
# DATA
# =========================================================

waste_streams = [ # Creates a list containing the details of different types of trash on the site.
    ["Concrete & Masonry", 480, 2.5, 192.0, "20-yard roll-off bin", 15.3, "Weekly"], # Data for Concrete.
    ["Wood", 90, 0.7, 128.6, "Covered skip", 8.0, "Twice per week"], # Data for Wood.
    ["Metals", 60, 7.85, 7.6, "10-yd metal bin", 7.65, "On demand"], # Data for Metals.
    ["Drywall", 75, 0.67, 111.9, "10-yd bin", 7.65, "Weekly"], # Data for Drywall.
    ["Packaging", 25, 0.9, 27.8, "Bag cages / bins", 1.0, "Daily"], # Data for Packaging.
    ["Mixed Residual Waste", 70, 1.2, 58.3, "Sealed dumpster", 20.0, "Weekly"] # Data for Mixed Waste.
] # Ends the list of waste streams.

waste_df = pd.DataFrame( # Converts our list into a nicely formatted, searchable data table (a DataFrame).
    waste_streams, # The data we are putting into the table.
    columns=[ # Giving names to the columns at the top of our table.
        "Waste Stream", # Column 1: The name of the trash.
        "Total Quantity tons", # Column 2: How heavy it is.
        "Density tons/m3", # Column 3: How dense it is.
        "Total Volume m3", # Column 4: How much space it takes up.
        "Container Type", # Column 5: The type of bin used.
        "Container Capacity m3", # Column 6: How much the bin can hold.
        "Current Frequency" # Column 7: How often it gets picked up right now.
    ] # Ends the column naming.
) # Ends the table creation.

phases = [ # Creates a list of the different stages of building the project.
    ["Site Preparation", 28], # Stage 1 takes 28 days.
    ["Foundation", 150], # Stage 2 takes 150 days.
    ["Interior", 120], # Stage 3 takes 120 days.
    ["Finishing", 120] # Stage 4 takes 120 days.
] # Ends the list of construction phases.

phase_df = pd.DataFrame(phases, columns=["Phase", "Days"]) # Turns the phases list into a small data table with column names.

daily_waste_generation = { # A dictionary (like a lookup book) showing how much of each waste is created per day during each phase.
    "Concrete & Masonry": [1.371, 1.024, 0.000, 0.000], # Daily concrete waste for the 4 phases.
    "Wood": [0.000, 0.600, 0.000, 0.321], # Daily wood waste for the 4 phases.
    "Metals": [0.000, 0.031, 0.025, 0.000], # Daily metal waste for the 4 phases.
    "Drywall": [0.000, 0.000, 0.933, 0.000], # Daily drywall waste for the 4 phases.
    "Packaging": [0.000, 0.037, 0.116, 0.069], # Daily packaging waste for the 4 phases.
    "Mixed Residual Waste": [0.000, 0.078, 0.194, 0.194] # Daily mixed waste for the 4 phases.
} # Ends the dictionary.

daily_df = pd.DataFrame( # Turns the daily dictionary into a data table.
    daily_waste_generation, # The raw daily data.
    index=["Site Preparation", "Foundation", "Interior", "Finishing"] # Labels the rows with the phase names.
).T # The ".T" flips the table sideways (transposes it) so columns become rows and rows become columns.

# =========================================================
# FUNCTIONS
# =========================================================

# -------------------------------------------------------------------------
# EXPLANATION: get_pickup_days
# Imagine you have a calendar for a specific construction phase.
# If someone says "Pick up daily", you circle every day on the calendar.
# If they say "Weekly", you count by 7s and circle days 7, 14, 21, etc.
# This function creates and returns that list of "circled" days.
# -------------------------------------------------------------------------
def get_pickup_days(frequency, phase_days): # Defines a function that takes two inputs: "how often" and "how many days total".
    if frequency == "Daily": # Checks if the frequency word is exactly "Daily".
        return list(range(1, phase_days + 1)) # Gives back a list of every single number from day 1 to the final day.

    if frequency == "Weekly": # Checks if the frequency word is exactly "Weekly".
        return list(range(7, phase_days + 1, 7)) # Gives back a list starting at 7, counting by 7s, until the final day.

    if frequency == "Twice per week": # Checks if the frequency word is "Twice per week".
        return [day for day in range(1, phase_days + 1) if day % 3 == 0 or day % 7 == 0] # Mathematical trick: picks days that are multiples of 3 or 7.

    return [] # If the word is "On demand" or anything else, return an empty list (meaning no planned calendar days).


# -------------------------------------------------------------------------
# EXPLANATION: simulate_fixed
# This simulates the "Old School" way of picking up trash.
# You schedule a truck to come on specific days (like every Friday), 
# regardless of whether the bin is completely empty or overflowing.
# The code goes day-by-day. It adds daily trash to a virtual "bin". 
# If it spills over, it records a penalty. If it's pickup day, it empties the bin.
# -------------------------------------------------------------------------
def simulate_fixed(): # Defines the function for the fixed schedule simulation.
    results = [] # Creates an empty bucket to hold all our final answers.

    for _, phase_row in phase_df.iterrows(): # Loops through every single phase (Site Prep, Foundation, etc.) one by one.
        phase_name = phase_row["Phase"] # Grabs the name of the current phase we are looking at.
        phase_days = int(phase_row["Days"]) # Grabs the number of days this phase lasts.

        for _, waste_row in waste_df.iterrows(): # Inside the phase loop, it loops through every single type of trash.
            waste_name = waste_row["Waste Stream"] # Grabs the name of the trash (e.g., "Wood").
            container_capacity = waste_row["Container Capacity m3"] # Grabs how big the bin is for this trash.
            daily_rate = daily_df.loc[waste_name, phase_name] # Looks up exactly how much of this trash is made per day in this phase.

            if daily_rate == 0: # Checks if NO trash of this type is made in this phase.
                continue # If true, skip the rest of the steps and move to the next type of trash.

            pickup_days = get_pickup_days(waste_row["Current Frequency"], phase_days) # Uses our calendar function above to get the scheduled pickup days.

            container_level = 0 # Sets the starting trash level in the bin to zero.
            pickups = 0 # Sets the starting count of truck visits to zero.
            overflow_incidents = 0 # Sets the starting count of times the bin overflowed to zero.
            overflow_volume = 0 # Sets the total amount of spilled trash to zero.
            utilization_sum = 0 # A running total used later to find out the average fullness of the bin.
            unused_pickups = 0 # A counter for how many times the truck showed up but the bin was mostly empty.
            delay_days = 0 # A counter for how many days the site was paused because of overflowing trash.

            for day in range(1, phase_days + 1): # A time-machine loop! We step through every single day of the phase, 1 by 1.
                container_level += daily_rate # Every day, we add the daily trash amount into our virtual bin.

                if container_level > container_capacity: # We check: is there more trash in the bin than the bin can actually hold?
                    overflow_incidents += 1 # If yes, add 1 to our record of overflow disasters.
                    overflow_volume += container_level - container_capacity # Calculate exactly how much extra trash spilled onto the ground.
                    delay_days += 1 # Add 1 to our delay penalty because the site is a mess.

                if day in pickup_days: # We check: is today one of the circled days on our calendar?
                    pickups += 1 # The truck arrived! Add 1 to our pickup count.
                    utilization = min(container_level, container_capacity) / container_capacity * 100 # Calculates how full the bin is as a percentage (capped at 100%).
                    utilization_sum += utilization # Adds this percentage to our running total for later math.

                    if utilization < 30: # We check: was the bin less than 30% full?
                        unused_pickups += 1 # If yes, count this as a "wasted trip" for the truck.

                    container_level = 0 # The truck emptied the bin. Reset the trash level back to 0.

            avg_utilization = utilization_sum / pickups if pickups > 0 else 0 # After all days pass, calculate the average fullness of the bin.

            results.append({ # We pack up all the stats we just calculated into a neat little dictionary...
                "Strategy": "Fixed Schedule", # Saves the name of the strategy.
                "Phase": phase_name, # Saves the phase name.
                "Waste Stream": waste_name, # Saves the waste name.
                "Container Type": waste_row["Container Type"], # Saves the bin type.
                "Container Capacity m3": container_capacity, # Saves the bin capacity.
                "Current Frequency": waste_row["Current Frequency"], # Saves the schedule type.
                "Daily Generation Rate m3/day": round(daily_rate, 3), # Saves daily rate, rounded to 3 decimal places.
                "Total Generated m3": round(daily_rate * phase_days, 2), # Saves total trash created in this phase.
                "Best Threshold %": "", # Left blank because fixed schedules don't use thresholds.
                "Number of Pickups": pickups, # Saves total truck visits.
                "Average Utilization at Pickup %": round(avg_utilization, 1), # Saves average fullness.
                "Overflow Incidents": overflow_incidents, # Saves total spills.
                "Total Overflow Volume m3": round(overflow_volume, 2), # Saves volume of spilled trash.
                "Unused Pickups": unused_pickups, # Saves wasted truck visits.
                "Site Delay Days": delay_days, # Saves total delay days.
                "Final Container Level m3": round(container_level, 2) # Saves how much trash was left in the bin on the very last day.
            }) # ...and toss that dictionary into our 'results' bucket.

    return pd.DataFrame(results) # Turns our 'results' bucket into a beautiful, readable data table.


# -------------------------------------------------------------------------
# EXPLANATION: simulate_reactive
# This simulates calling the truck ONLY when the bin is 100% full (or overflowing).
# There is no calendar. The site manager literally looks at the bin,
# sees it hit the limit, and calls the truck. 
# -------------------------------------------------------------------------
def simulate_reactive(): # Defines the function for the reactive strategy.
    results = [] # Creates an empty bucket for results.

    for _, phase_row in phase_df.iterrows(): # Loops through phases.
        phase_name = phase_row["Phase"] # Gets phase name.
        phase_days = int(phase_row["Days"]) # Gets phase duration.

        for _, waste_row in waste_df.iterrows(): # Loops through waste types.
            waste_name = waste_row["Waste Stream"] # Gets waste name.
            container_capacity = waste_row["Container Capacity m3"] # Gets bin capacity.
            daily_rate = daily_df.loc[waste_name, phase_name] # Gets daily trash rate.

            if daily_rate == 0: # Checks if no trash is made.
                continue # Skips to next if true.

            container_level = 0 # Starting trash level.
            pickups = 0 # Starting truck visits.
            overflow_incidents = 0 # Starting spills.
            overflow_volume = 0 # Starting spill volume.
            utilization_sum = 0 # Running total for fullness math.
            delay_days = 0 # Starting delay penalty.

            for day in range(1, phase_days + 1): # Time-machine loop, day by day.
                container_level += daily_rate # Add today's trash to the bin.

                if container_level >= container_capacity: # Check: Is the bin 100% full or overflowing?
                    pickups += 1 # We call the truck immediately! Add 1 to pickups.

                    utilization = min(container_level, container_capacity) / container_capacity * 100 # Calculate fullness (will usually be 100%).
                    utilization_sum += utilization # Add to our running total.

                    if container_level > container_capacity: # Check: Did we put in so much today that it literally spilled over before the truck arrived?
                        overflow_incidents += 1 # Count a spill.
                        overflow_volume += container_level - container_capacity # Calculate spilled amount.
                        delay_days += 1 # Count a delay penalty.

                    container_level = 0 # The truck emptied the bin. Reset to zero.

            avg_utilization = utilization_sum / pickups if pickups > 0 else 0 # Calculate average fullness.

            results.append({ # Pack up the stats.
                "Strategy": "Reactive", # Strategy name.
                "Phase": phase_name, # Phase name.
                "Waste Stream": waste_name, # Waste name.
                "Container Type": waste_row["Container Type"], # Bin type.
                "Container Capacity m3": container_capacity, # Bin capacity.
                "Current Frequency": "", # Blank, no calendar used.
                "Daily Generation Rate m3/day": round(daily_rate, 3), # Daily rate.
                "Total Generated m3": round(daily_rate * phase_days, 2), # Total trash.
                "Best Threshold %": "", # Blank.
                "Number of Pickups": pickups, # Total truck visits.
                "Average Utilization at Pickup %": round(avg_utilization, 1), # Average fullness.
                "Overflow Incidents": overflow_incidents, # Total spills.
                "Total Overflow Volume m3": round(overflow_volume, 2), # Total spilled volume.
                "Unused Pickups": "", # Blank, we never do unused pickups in this strategy.
                "Site Delay Days": delay_days, # Total delays.
                "Final Container Level m3": round(container_level, 2) # Trash left at the end.
            }) # Add to bucket.

    return pd.DataFrame(results) # Return a formatted data table.


# -------------------------------------------------------------------------
# EXPLANATION: simulate_dynamic_threshold
# This is a "helper" function. It runs a single test for a specific percentage.
# For example, we tell it: "Run a simulation where we call the truck when the bin 
# reaches exactly 75% full." It runs the simulation and returns the stats.
# -------------------------------------------------------------------------
def simulate_dynamic_threshold(phase_name, phase_days, waste_row, daily_rate, threshold): # Defines a function that takes specific variables, including a 'threshold' percentage.
    container_capacity = waste_row["Container Capacity m3"] # Gets bin capacity.
    threshold_volume = container_capacity * threshold / 100 # Calculates the physical volume of the threshold (e.g., 75% of a 10m3 bin is 7.5m3).

    container_level = 0 # Starting trash level.
    pickups = 0 # Starting truck visits.
    overflow_incidents = 0 # Starting spills.
    overflow_volume = 0 # Starting spill volume.
    utilization_sum = 0 # Running total for fullness math.
    delay_days = 0 # Starting delay penalty.

    for day in range(1, phase_days + 1): # Time-machine loop.
        container_level += daily_rate # Add today's trash.

        if container_level > container_capacity: # If the trash physically exceeds the absolute limit of the bin...
            overflow_incidents += 1 # Count a spill.
            overflow_volume += container_level - container_capacity # Calculate amount spilled.
            delay_days += 1 # Count delay penalty.

        if container_level >= threshold_volume: # Did we hit our magic target percentage (e.g., 75%)?
            pickups += 1 # If yes, call the truck!
            utilization = min(container_level, container_capacity) / container_capacity * 100 # Calculate fullness.
            utilization_sum += utilization # Add to running total.
            container_level = 0 # Empty the bin.

    avg_utilization = utilization_sum / pickups if pickups > 0 else 0 # Calculate average fullness.

    return { # Instead of appending to a list, this function immediately hands back one single dictionary of results.
        "Strategy": "Dynamic Threshold", # Strategy name.
        "Phase": phase_name, # Phase name.
        "Waste Stream": waste_row["Waste Stream"], # Waste name.
        "Container Type": waste_row["Container Type"], # Bin type.
        "Container Capacity m3": container_capacity, # Bin capacity.
        "Current Frequency": "", # Blank.
        "Daily Generation Rate m3/day": round(daily_rate, 3), # Daily rate.
        "Total Generated m3": round(daily_rate * phase_days, 2), # Total trash.
        "Best Threshold %": threshold, # Records WHICH percentage we tested here.
        "Number of Pickups": pickups, # Total truck visits.
        "Average Utilization at Pickup %": round(avg_utilization, 1), # Average fullness.
        "Overflow Incidents": overflow_incidents, # Total spills.
        "Total Overflow Volume m3": round(overflow_volume, 2), # Spill volume.
        "Unused Pickups": "", # Blank.
        "Site Delay Days": delay_days, # Delay days.
        "Final Container Level m3": round(container_level, 2) # Trash left over.
    } # Ends the returned dictionary.


# -------------------------------------------------------------------------
# EXPLANATION: simulate_dynamic
# This is the "Smart AI" manager. It wants to find the perfect time to call a truck.
# It uses the helper function above to test EVERY single percentage from 50% to 100%.
# Then it looks at all the tests and picks the undisputed winner based on three rules:
# 1st Rule: NO OVERFLOWS ALLOWED. 
# 2nd Rule: Least amount of truck pickups possible.
# 3rd Rule: Bin should be as full as possible without breaking rules 1 and 2.
# -------------------------------------------------------------------------
def simulate_dynamic(): # Defines the master dynamic simulation function.
    best_results = [] # A bucket to hold ONLY the winning strategies.
    all_threshold_tests = [] # A bucket to keep a record of EVERY single percentage test we ran.

    for _, phase_row in phase_df.iterrows(): # Loops through phases.
        phase_name = phase_row["Phase"] # Gets phase name.
        phase_days = int(phase_row["Days"]) # Gets phase duration.

        for _, waste_row in waste_df.iterrows(): # Loops through waste types.
            waste_name = waste_row["Waste Stream"] # Gets waste name.
            daily_rate = daily_df.loc[waste_name, phase_name] # Gets daily rate.

            if daily_rate == 0: # Checks if no trash is made.
                continue # Skips to next.

            threshold_results = [] # A temporary bucket to hold the 50 tests for this specific waste in this specific phase.

            for threshold in range(50, 101): # A loop that tests the numbers 50, 51, 52... all the way to 100.
                result = simulate_dynamic_threshold( # Calls our helper function and gives it the current percentage to test.
                    phase_name, # Passes phase name.
                    phase_days, # Passes phase duration.
                    waste_row, # Passes bin details.
                    daily_rate, # Passes daily rate.
                    threshold # Passes the specific percentage (e.g., 75).
                ) # Ends the function call.

                threshold_results.append(result) # Puts the test result into our temporary bucket.
                all_threshold_tests.append(result) # Puts the test result into our master record bucket.

            # Now we evaluate all 50 tests to find the winner.
            no_overflow = [r for r in threshold_results if r["Overflow Incidents"] == 0] # Filters the list to ONLY include tests where zero spills happened.

            if no_overflow: # If there is at least one strategy that had zero spills...
                best = sorted( # We sort those successful strategies.
                    no_overflow, # The list we are sorting.
                    key=lambda r: ( # The rules we use to sort them (in order of importance):
                        r["Number of Pickups"], # Rule 1: Sort by lowest number of pickups first.
                        -r["Average Utilization at Pickup %"], # Rule 2: If tied, sort by highest bin fullness (the minus sign makes it sort highest to lowest).
                        -r["Best Threshold %"] # Rule 3: If still tied, sort by the highest threshold percentage used.
                    ) # Ends sorting rules.
                )[0] # Grabs the very first item in the sorted list (the ultimate winner).
            else: # If EVERY SINGLE strategy resulted in a spill (meaning the bin is too small for the daily trash)...
                best = sorted( # We sort all the failing strategies to find the "least bad" one.
                    threshold_results, # The list of all tests.
                    key=lambda r: ( # Sorting rules:
                        r["Overflow Incidents"], # Rule 1: Lowest number of spills.
                        r["Number of Pickups"], # Rule 2: Lowest number of pickups.
                        -r["Average Utilization at Pickup %"] # Rule 3: Highest fullness.
                    ) # Ends sorting rules.
                )[0] # Grabs the least bad result.

            best_results.append(best) # Puts the winner into our final winners bucket.

    return pd.DataFrame(best_results), pd.DataFrame(all_threshold_tests) # Hands back TWO tables: one of winners, and one of all tests ever run.


# =========================================================
# RUN SIMULATIONS
# =========================================================

fixed_df = simulate_fixed() # Runs the fixed schedule function and saves the table to a variable.
reactive_df = simulate_reactive() # Runs the reactive function and saves the table to a variable.
dynamic_df, threshold_tests_df = simulate_dynamic() # Runs the dynamic function and catches BOTH tables it returns.

combined_df = pd.concat( # Stacks tables on top of each other into one giant master table.
    [fixed_df, reactive_df, dynamic_df], # The three tables we want to stack.
    ignore_index=True # Cleans up the row numbers so they count nicely from 0 to the end.
)

# =========================================================
# SUMMARY KPIs
# =========================================================

summary_rows = [] # Empty list to hold summary statistics.

for strategy, group in combined_df.groupby("Strategy"): # Splits the master table into three groups (Fixed, Reactive, Dynamic) and loops through them.
    unused_pickups = pd.to_numeric(group["Unused Pickups"], errors="coerce").fillna(0) # Makes sure unused pickups are treated as numbers, replacing blanks with 0.

    total_pickups = group["Number of Pickups"].sum() # Adds up all the pickups for this strategy group.
    delay_days = group["Site Delay Days"].sum() # Adds up all the delay days for this strategy group.

    operational_hours = total_pickups * HOURS_PER_PICKUP # Calculates total time spent managing trucks.
    delay_hours = delay_days * WORKING_HOURS_PER_DELAY_DAY # Calculates total work hours lost due to site delays.
    total_time_impact = operational_hours + delay_hours # Adds operational and delay hours together for a final penalty score.

    total_truck_km = total_pickups * ROUND_TRIP_DISTANCE_KM # Calculates total kilometers driven by trucks.
    total_co2_kg = total_truck_km * CO2_EMISSION_FACTOR_KG_PER_KM # Calculates total CO2 emissions based on kilometers.

    summary_rows.append({ # Creates a dictionary summarizing all the grand totals for this strategy.
        "Strategy": strategy, # Strategy name.
        "Total Generated Waste m3": round(group["Total Generated m3"].sum(), 2), # Total trash.
        "Total Pickups": int(total_pickups), # Total pickups.
        "Average Utilization %": round(group["Average Utilization at Pickup %"].mean(), 1), # Overall average bin fullness.
        "Total Overflow Incidents": int(group["Overflow Incidents"].sum()), # Total spills.
        "Total Overflow Volume m3": round(group["Total Overflow Volume m3"].sum(), 2), # Total spilled volume.
        "Total Site Delay Days": int(delay_days), # Total delay days.
        "Total Unused Pickups": int(unused_pickups.sum()), # Total wasted truck trips.
        "Operational Pickup Hours": round(operational_hours, 2), # Total hours managing trucks.
        "Delay Hours": round(delay_hours, 2), # Total hours lost to delays.
        "Total Time Impact Hours": round(total_time_impact, 2), # Total overall time penalty.
        "Total Truck Kilometers Traveled": round(total_truck_km, 2), # Total distance driven.
        "CO2 Emissions kg": round(total_co2_kg, 2) # Total CO2 emitted.
    }) # Add to summary list.

summary_df = pd.DataFrame(summary_rows) # Turns summary list into a data table.

fixed_hours = summary_df.loc[ # Searches the summary table to find the Total Time Impact Hours specifically for the "Fixed Schedule" row.
    summary_df["Strategy"] == "Fixed Schedule", # The search condition.
    "Total Time Impact Hours" # The specific column value we want to pull out.
].iloc[0] # Grabs the actual number from the search result.

dynamic_hours = summary_df.loc[ # Searches the summary table to find the Total Time Impact Hours specifically for the "Dynamic Threshold" row.
    summary_df["Strategy"] == "Dynamic Threshold", # The search condition.
    "Total Time Impact Hours" # The column value.
].iloc[0] # Grabs the number.

hours_saved_vs_fixed = fixed_hours - dynamic_hours # Simple math: Subtracts dynamic penalty hours from fixed penalty hours to see how much time the AI saved us.

# =========================================================
# SAVE CSV FILES
# =========================================================

script_folder = os.path.dirname(os.path.abspath(__file__)) # (Redundant) Finds the folder again.

fixed_df.to_csv(os.path.join(output_folder, "fixed_schedule_results.csv"), index=False) # Saves the fixed table as a basic text spreadsheet (.csv). 'index=False' prevents it from writing useless row numbers.

reactive_df.to_csv( # Starts saving reactive table.
    os.path.join(output_folder, "reactive_strategy_results.csv"), # Sets file path and name.
    index=False # Removes row numbers.
)

dynamic_df.to_csv( # Saves dynamic winners table as a CSV.
    os.path.join(output_folder, "dynamic_strategy_results.csv"),
    index=False
)

threshold_tests_df.to_csv( # Saves massive table of all 50 tests as a CSV.
    os.path.join(output_folder, "dynamic_threshold_tests.csv"),
    index=False
)

combined_df.to_csv( # Saves the giant stacked table as a CSV.
    os.path.join(output_folder, "combined_strategy_results.csv"),
    index=False
)

summary_df.to_csv( # Saves the summary math table as a CSV.
    os.path.join(output_folder, "strategy_comparison_summary.csv"),
    index=False
)

# =========================================================
# CREATE FORMATTED EXCEL REPORT - SINGLE SCENARIO
# =========================================================

excel_report_path = os.path.join( # Prepares the file path for a Microsoft Excel file.
    output_folder,
    "construction_waste_report.xlsx"
)

with pd.ExcelWriter(excel_report_path, engine="xlsxwriter") as writer: # Opens a special tool that lets Python write multiple tabs inside one Excel file.

    workbook = writer.book # Grants access to the background Excel workbook formatting features.

    title_format = workbook.add_format({ # Creates a custom visual style for titles (bold, big, centered, blue background, white text).
        "bold": True,
        "font_size": 16,
        "align": "center",
        "valign": "vcenter",
        "bg_color": "#1F4E78",
        "font_color": "white"
    })

    header_format = workbook.add_format({ # Creates a custom visual style for column headers (bold, light blue background, bordered).
        "bold": True,
        "bg_color": "#D9EAF7",
        "border": 1,
        "align": "center",
        "valign": "vcenter"
    })

    # -----------------------------
    # Sheet 1: Executive Summary
    # -----------------------------

    summary_df.to_excel( # Pastes the summary table into an Excel tab.
        writer, # Uses the Excel tool.
        sheet_name="Executive Summary", # Names the tab at the bottom of Excel.
        index=False, # No row numbers.
        startrow=3 # Pushes the table down to row 4 (leaves space at top for title).
    )

    ws = writer.sheets["Executive Summary"] # Grabs control of this specific Excel tab so we can format it.

    ws.merge_range( # Merges cells A1 through M1 together and writes a big title in it using our blue title style.
        "A1:M1",
        "Single Scenario Construction Waste Logistics - Strategy Comparison",
        title_format
    )

    ws.write("A2", "Scenario type: Deterministic single project") # Writes basic text into cell A2.
    ws.write("D2", "Strategies: Fixed, Reactive, Dynamic") # Writes basic text into cell D2.

    for col_num, value in enumerate(summary_df.columns.values): # Loops over the column names and applies the light-blue header style to them.
        ws.write(3, col_num, value, header_format)

    ws.set_column("A:A", 22) # Adjusts the width of Column A.
    ws.set_column("B:M", 20) # Adjusts the width of Columns B through M.
    ws.autofilter(3, 0, len(summary_df) + 3, len(summary_df.columns) - 1) # Adds those little drop-down filter arrows to the top of the table.
    ws.freeze_panes(4, 0) # Freezes the top 4 rows so they stay visible when you scroll down.

    # -----------------------------
    # Sheet 2: Detailed Results
    # -----------------------------

    combined_df.to_excel( # Pastes the master stacked table into a new tab.
        writer,
        sheet_name="Detailed Results",
        index=False,
        startrow=2
    )

    ws2 = writer.sheets["Detailed Results"] # Grabs control of tab 2.

    ws2.merge_range( # Merges cells and adds a title.
        "A1:R1",
        "Detailed Strategy Results by Phase and Waste Stream",
        title_format
    )

    for col_num, value in enumerate(combined_df.columns.values): # Styles headers.
        ws2.write(2, col_num, value, header_format)

    ws2.set_column("A:A", 20) # Sets column width.
    ws2.set_column("B:R", 18) # Sets column widths.
    ws2.autofilter(2, 0, len(combined_df) + 2, len(combined_df.columns) - 1) # Adds filter arrows.
    ws2.freeze_panes(3, 0) # Freezes headers.

    # -----------------------------
    # Sheet 3: Dynamic Threshold Tests
    # -----------------------------

    threshold_tests_df.to_excel( # Pastes the massive 50-test table into a new tab.
        writer,
        sheet_name="Threshold Tests",
        index=False,
        startrow=2
    )

    ws3 = writer.sheets["Threshold Tests"] # Grabs control of tab 3.

    ws3.merge_range( # Merges cells and adds a title.
        "A1:R1",
        "Dynamic Threshold Test Results",
        title_format
    )

    for col_num, value in enumerate(threshold_tests_df.columns.values): # Styles headers.
        ws3.write(2, col_num, value, header_format)

    ws3.set_column("A:A", 22) # Sets width.
    ws3.set_column("B:R", 18) # Sets widths.
    ws3.autofilter(2, 0, len(threshold_tests_df) + 2, len(threshold_tests_df.columns) - 1) # Adds filters.
    ws3.freeze_panes(3, 0) # Freezes pane.

    # -----------------------------
    # Sheet 4: Input Data
    # -----------------------------

    waste_df.to_excel( # Pastes original waste assumptions into a tab.
        writer,
        sheet_name="Input Waste Data",
        index=False,
        startrow=2
    )

    ws4 = writer.sheets["Input Waste Data"] # Grabs control of tab 4.

    ws4.merge_range( # Title.
        "A1:G1",
        "Input Waste Stream Data",
        title_format
    )

    for col_num, value in enumerate(waste_df.columns.values): # Header styling.
        ws4.write(2, col_num, value, header_format)

    ws4.set_column("A:A", 25) # Sets width.
    ws4.set_column("B:G", 20) # Sets width.

    # -----------------------------
    # Sheet 5: Daily Generation
    # -----------------------------

    daily_df.to_excel( # Pastes daily rate data into a tab.
        writer,
        sheet_name="Daily Generation"
    )

    ws5 = writer.sheets["Daily Generation"] # Grabs control of tab 5.

    ws5.merge_range( # Title.
        "A1:E1",
        "Daily Waste Generation Rate per Phase",
        title_format
    )

    ws5.set_column("A:A", 25) # Width.
    ws5.set_column("B:E", 18) # Width.

    # -----------------------------
    # Sheet 6: Assumptions
    # -----------------------------

    assumptions_df = pd.DataFrame({ # Creates a fresh little table out of thin air just to show the hardcoded numbers from the very top of the script.
        "Parameter": [
            "Hours per pickup",
            "Working hours per delay day",
            "One-way truck distance",
            "Round-trip truck distance",
            "CO2 emission factor"
        ],
        "Value": [
            HOURS_PER_PICKUP,
            WORKING_HOURS_PER_DELAY_DAY,
            AVERAGE_ONE_WAY_DISTANCE_KM,
            ROUND_TRIP_DISTANCE_KM,
            CO2_EMISSION_FACTOR_KG_PER_KM
        ],
        "Unit": [
            "hours/pickup",
            "hours/day",
            "km",
            "km",
            "kg CO2/km"
        ]
    })

    assumptions_df.to_excel( # Pastes this assumptions table into a final tab.
        writer,
        sheet_name="Assumptions",
        index=False,
        startrow=2
    )

    ws6 = writer.sheets["Assumptions"] # Grabs control of tab 6.

    ws6.merge_range( # Title.
        "A1:C1",
        "Simulation Assumptions",
        title_format
    )

    for col_num, value in enumerate(assumptions_df.columns.values): # Header styles.
        ws6.write(2, col_num, value, header_format)

    ws6.set_column("A:A", 32) # Width.
    ws6.set_column("B:C", 18) # Width.

print("\nFormatted Excel report created:") # Prints a message to your screen letting you know it worked.
print(excel_report_path) # Prints the location of the file.

# =========================================================
# GRAPHS
# =========================================================

# =========================================================
# DASHBOARD GRAPH
# =========================================================

fig, axes = plt.subplots(2, 3, figsize=(18, 10)) # Creates a blank canvas for a picture. Divides it into 2 rows and 3 columns (6 slots total), and sets the picture size to 18x10.

# ---------------------------------------------------------
# 1. Total Pickups per Strategy
# ---------------------------------------------------------

axes[0, 0].bar( # In the top-left slot (Row 0, Col 0), draw a Bar Chart.
    summary_df["Strategy"], # The bottom labels (X-axis) will be the Strategy names.
    summary_df["Total Pickups"] # The heights of the bars (Y-axis) will be the Number of Pickups.
)

axes[0, 0].set_title("Total Pickups per Strategy") # Gives this chart a title.
axes[0, 0].set_ylabel("Pickups") # Labels the Y-axis.


# ---------------------------------------------------------
# 2. Overflow Incidents per Strategy
# ---------------------------------------------------------

axes[0, 1].bar( # In the top-middle slot (Row 0, Col 1), draw a Bar Chart.
    summary_df["Strategy"], # X-axis: Strategy names.
    summary_df["Total Overflow Incidents"] # Y-axis: Number of spills.
)

axes[0, 1].set_title("Overflow Incidents per Strategy") # Title.
axes[0, 1].set_ylabel("Overflow Incidents") # Y-axis label.


# ---------------------------------------------------------
# 3. Average Utilization per Strategy
# ---------------------------------------------------------

axes[0, 2].bar( # In the top-right slot (Row 0, Col 2), draw a Bar Chart.
    summary_df["Strategy"], # X-axis: Strategy names.
    summary_df["Average Utilization %"] # Y-axis: Bin fullness percentage.
)

axes[0, 2].set_title("Average Container Utilization") # Title.
axes[0, 2].set_ylabel("Utilization (%)") # Y-axis label.


# ---------------------------------------------------------
# 4. Total Time Impact
# ---------------------------------------------------------

axes[1, 0].bar( # In the bottom-left slot (Row 1, Col 0), draw a Bar Chart.
    summary_df["Strategy"], # X-axis: Strategy names.
    summary_df["Total Time Impact Hours"] # Y-axis: Total penalty hours.
)

axes[1, 0].set_title("Total Time Impact") # Title.
axes[1, 0].set_ylabel("Hours") # Y-axis label.


# ---------------------------------------------------------
# 5. Pickups vs Overflow Scatter
# ---------------------------------------------------------

axes[1, 1].scatter( # In the bottom-middle slot (Row 1, Col 1), draw a Scatter Plot (dots on a grid).
    summary_df["Total Pickups"], # X-axis position of dot: Number of pickups.
    summary_df["Total Overflow Incidents"] # Y-axis position of dot: Number of spills.
)

for _, row in summary_df.iterrows(): # Loops through the summary table to write words next to the dots.

    axes[1, 1].annotate( # Adds text to the chart.
        row["Strategy"], # The text to write (the name of the strategy).
        ( # The exact coordinate to put the text:
            row["Total Pickups"], # X-coordinate.
            row["Total Overflow Incidents"] # Y-coordinate.
        )
    )

axes[1, 1].set_title("Pickups vs Overflow") # Title.
axes[1, 1].set_xlabel("Total Pickups") # X-axis label.
axes[1, 1].set_ylabel("Overflow Incidents") # Y-axis label.


# ---------------------------------------------------------
# 6. Waste Generation per Phase
# ---------------------------------------------------------
# (Notice: The original author commented this out but left the header. Nothing happens here.)

# ---------------------------------------------------------
# 6. CO2 Emissions per Strategy
# ---------------------------------------------------------

axes[1, 2].bar( # In the bottom-right slot (Row 1, Col 2), draw a Bar Chart.
    summary_df["Strategy"], # X-axis: Strategy names.
    summary_df["CO2 Emissions kg"] # Y-axis: Amount of CO2.
)

axes[1, 2].set_title("CO₂ Emissions per Strategy") # Title.
axes[1, 2].set_ylabel("kg CO₂") # Y-axis label.


# ---------------------------------------------------------
# FINAL LAYOUT
# ---------------------------------------------------------

axes[0, 0].tick_params(axis="x", rotation=15) # Tilts the words on the X-axis 15 degrees so they don't overlap.
axes[0, 1].tick_params(axis="x", rotation=15) # Tilts text.
axes[0, 2].tick_params(axis="x", rotation=15) # Tilts text.
axes[1, 0].tick_params(axis="x", rotation=15) # Tilts text.
axes[1, 2].tick_params(axis="x", rotation=15) # Tilts text.

plt.tight_layout() # A magic command that perfectly spaces out all 6 charts so titles and axes don't bump into each other.

dashboard_path = os.path.join( # Sets up a file path to save the picture.
    output_folder,
    "construction_waste_dashboard.png"
)

plt.savefig( # Actually saves the picture file to your hard drive.
    dashboard_path,
    dpi=300 # Sets the quality to High-Definition (300 Dots Per Inch).
)

plt.show() # Pops open a window on your screen to show you the charts right now.

plt.close() # Closes the picture inside the computer's memory to keep things fast.

# =========================================================
# PRINT FINAL RESULTS
# =========================================================
# This final section just prints text to the little black screen (terminal/console) where you ran the code.
# The "\n" symbol just means "Hit Enter" to create a blank line.

print("\n====================================================") # Prints a divider line.
print("SIMULATION COMPLETED") # Prints text.
print("====================================================") # Prints divider.

print("\nCSV files created:") # Prints text.
print("- fixed_schedule_results.csv") # Prints text.
print("- reactive_strategy_results.csv") # Prints text.
print("- dynamic_strategy_results.csv") # Prints text.
print("- dynamic_threshold_tests.csv") # Prints text.
print("- combined_strategy_results.csv") # Prints text.
print("- strategy_comparison_summary.csv") # Prints text.

print("\nGraphs created as PNG files in the same folder.") # Prints text.

print("\n====================================================") # Prints divider.
print("STRATEGY COMPARISON SUMMARY") # Prints text.
print("====================================================") # Prints divider.
print(summary_df.to_string(index=False)) # Grabs the summary table, converts it all to raw text, and prints it cleanly without row numbers.

print("\n====================================================") # Prints divider.
print("HOURS SAVED RESULT") # Prints text.
print("====================================================") # Prints divider.
print(f"Assumption: each pickup requires {HOURS_PER_PICKUP} operational hours.") # Uses an f-string (formatted string) to inject our variable (1.5) into the sentence dynamically.
print(f"Assumption: each site delay day equals {WORKING_HOURS_PER_DELAY_DAY} working hours.") # Injects the variable (8) into the sentence.
print(f"Hours saved by Dynamic Strategy compared to Fixed Schedule: {hours_saved_vs_fixed:.2f} hours") # Injects the final math answer into the sentence, formatting it to exactly 2 decimal places (:.2f).

print("\n====================================================") # Prints divider.
print("BEST DYNAMIC THRESHOLDS") # Prints text.
print("====================================================") # Prints divider.

for _, row in dynamic_df.iterrows(): # Loops over the table containing the dynamic winners.
    print( # Prints out a custom sentence for every single winning strategy.
        f"{row['Phase']} | {row['Waste Stream']} | " # Injects phase and waste type.
        f"Best Threshold: {row['Best Threshold %']}% | " # Injects the winning target percentage.
        f"Pickups: {row['Number of Pickups']} | " # Injects pickup count.
        f"Utilization: {row['Average Utilization at Pickup %']}% | " # Injects fullness score.
        f"Overflow: {row['Overflow Incidents']}" # Injects spill count.
    )