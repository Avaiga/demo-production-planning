from pages.annex_scenario_manager.chart_md import ch_chart_md, ch_choice_chart, ch_show_pie, ch_layout_dict, ch_results
from pages.annex_scenario_manager.parameters_md import pa_parameters_md, pa_param_selector, pa_param_selected, pa_choice_product_param, pa_product_param, solver_name, list_of_solvers

from login.login import detect_inactive_session

from taipy.gui import invoke_long_callback

from taipy.gui.gui_actions import notify
from taipy.gui import Icon
import taipy as tp

import datetime as dt
import pandas as pd



def remove_scenario_from_tree(scenario, sm_tree_dict: dict):
    """This function finds the scenario in the tree and removes it

    Args:
        scenario (Scenario): the scenario to be deleted from the tree
        sm_tree_dict (dict): the tree dict from which the scenario has to be deleted from

    Returns:
        tree: the tree without the scenario
    """
    # This will be the cycle keys that will be dropped if they contain no
    # scenario
    cycle_keys_to_pop = []

    # We explore our 2-level tree
    for cycle, scenarios_ in sm_tree_dict.items():
        for scenario_id, scenario_name in scenarios_:
            if scenario_id == scenario.id:
                # Remove the scenario that has the same id from the tree
                sm_tree_dict[cycle].remove((scenario_id, scenario_name))

                # Add the cycle to the cycles to drop if it is empty
                if len(sm_tree_dict[cycle]) == 0:
                    cycle_keys_to_pop += [cycle]
                print("------------- Scenario found and deleted -------------")
                break

    # Remove the empty cycles
    for cycle in cycle_keys_to_pop:
        sm_tree_dict.pop(cycle)
    return sm_tree_dict

sm_tree_dict = {}

def create_sm_tree_dict(scenarios, sm_tree_dict: dict = None):
    """This function creates a tree dict from a list of scenarios. The levels of the tree are:
    year/month/scenario

    Args:
        scenarios (list): a list of scenarios
        sm_tree_dict (dict, optional): the tree gathering all the scenarios. Defaults to None.

    Returns:
        tree: the tree created to classify the scenarios
    """
    print("Creating tree dict...")
    if sm_tree_dict is None:
        # Initialize the tree dict if it is not already initialized
        sm_tree_dict = {}

    # Add all the scenarios that are in the list
    for scenario in scenarios:
        # Create a name for the cycle
        date = scenario.creation_date
        year = f"{date.strftime('%Y')}"
        period = f"{date.strftime('%b')}"

        # Add the cycle if it was not already added
        if year not in sm_tree_dict:
            sm_tree_dict[year] = {}
        if period not in sm_tree_dict[year]:
            sm_tree_dict[year][period] = []

        # Append a new entry with the scenario id and the scenario name
        scenario_name = (
            Icon(
                'images/icons/flag.svg',
                scenario.name) if scenario.is_primary else scenario.name)
        sm_tree_dict[year][period] += [(scenario.id, scenario_name)]

    return sm_tree_dict



def create_time_selectors():
    """This function creates the time selectors that will be displayed on the GUI and it is also creating 
    the tree dict gathering all the scenarios.

    Returns:
        dict: the tree dict gathering all the scenarios
        list: the list of years
        list: the list of months
    """
    all_scenarios = tp.get_scenarios()
    all_scenarios_ordered = sorted(
        all_scenarios,
        key=lambda x: x.creation_date.timestamp())

    sm_tree_dict = create_sm_tree_dict(all_scenarios_ordered)

    if sm_current_year not in list(sm_tree_dict.keys()):
        sm_tree_dict[sm_current_year] = {}
    if sm_current_month not in sm_tree_dict[sm_current_year]:
        sm_tree_dict[sm_current_year][sm_current_month] = []

    sm_year_selector = list(sm_tree_dict.keys())
    sm_month_selector = list(sm_tree_dict[sm_selected_year].keys())

    return sm_tree_dict, sm_year_selector, sm_month_selector


def change_sm_month_selector(state):
    """This function is called when the user changes the year selector. It updates the selector shown on the GUI
    for the month selector and is calling the same function for the scenario selector.
    

    Args:
        state (State): all the GUI variables
    """
    state.sm_month_selector = list(
        state.sm_tree_dict[state.sm_selected_year].keys())

    if state.sm_selected_month not in state.sm_month_selector:
        state.sm_selected_month = state.sm_month_selector[0]

    change_scenario_selector(state)


def change_scenario_selector(state):
    """This function is called when the user changes the month selector. It updates the selector shown on the GUI
    for the scenario selector.
    

    Args:
        state (State): all the GUI variables
    """
    state.scenario_selector = list(
        state.sm_tree_dict[state.sm_selected_year][state.sm_selected_month])
    state.scenario_selector_two = state.scenario_selector.copy()
    if len(state.scenario_selector) > 0:
        state.selected_scenario = state.scenario_selector[0][0]

    if (state.sm_selected_month != sm_current_month or state.sm_selected_year !=
            sm_current_year) and state.sm_show_config_scenario:
        notify(state, "info", "This scenario is historical, you can't modify it")
        state.sm_show_config_scenario = False


sm_scenario_manager_md = """
<|part|class_name=container|
# **Scenario**{: .color_primary } Manager

<|layout|columns=8 4 auto auto|columns[mobile]=1|class_name=align_columns_bottom|
    <layout_scenario|
        <|layout|columns=1 1 3|columns[mobile]=1|class_name=align_columns_bottom|
            <|
Year

<|{sm_selected_year}|selector|lov={sm_year_selector}|dropdown|width=100%|on_change=change_sm_month_selector|>
            |>

            <|
Month

<|{sm_selected_month}|selector|lov={sm_month_selector}|dropdown|width=100%|on_change=change_scenario_selector|>
            |>

            <|
Scenario

<|{selected_scenario}|selector|lov={scenario_selector}|dropdown|value_by_id|width=18rem|>
            |>
        |>
    |layout_scenario>

    <graph|
Graph

<|{sm_graph_selected}|selector|lov={sm_graph_selector}|dropdown|>
    |graph>

<toggle_chart|
Pie/Line chart
<|{ch_show_pie}|toggle|lov={ch_choice_chart}|value_by_id|active={not 'Product ' in sm_graph_selected}|>
|toggle_chart>

<button_configure_scenario|
<|{sm_show_config_scenario_name}|button|on_action=show_config_scenario_action|active={sm_selected_month == sm_current_month and sm_selected_year == sm_current_year}|>
|button_configure_scenario>
|>

<|part|render={sm_show_config_scenario}|class_name=mt2|
""" + pa_parameters_md + """
|>

<|part|render={not(sm_show_config_scenario)}|class_name=mt2|
""" + ch_chart_md + """
|>
|>
"""

def update_scenario_selector(state, scenarios: list):
    """
    This function will update the scenario selectors. It will be used when
    we create a new scenario. If there is a scenario that is created, we will
    add its (id,name) in this list.

    Args:
        scenarios (list): a list of tuples (scenario,properties)
    """

    state.scenario_selector = [(s.id, s.name) if not s.is_primary else (
        s.id, Icon('images/main.svg', s.name)) for s in scenarios]
    state.scenario_counter = len(state.scenario_selector)
    state.scenario_selector_two = state.scenario_selector.copy()

    sm_tree_dict[state.sm_selected_year][state.sm_selected_month] = state.scenario_selector


def make_primary(state):
    tp.set_primary(tp.get(state.selected_scenario))
    scenarios = [s for s in tp.get_scenarios(
    ) if 'user' in s.properties and state.login == s.properties['user']]
    update_scenario_selector(state, scenarios)
    state.selected_scenario_is_primary = True


def delete_scenario_fct(state):
    if tp.get(state.selected_scenario).is_primary:
        notify(
            state,
            "warning",
            "You can't delete the primary scenario of the month")
    else:
        tp.delete(state.selected_scenario)
        scenarios = [s for s in tp.get_scenarios(
        ) if 'user' in s.properties and state.login == s.properties['user']]
        update_scenario_selector(state, scenarios)

        if state.scenario_counter != 0:
            state.selected_scenario = state.scenario_selector[0][0]


def create_new_scenario(state):
    """
    This function is used whan the 'create' button is pressed in the scenario_manager_md page.
    See the scenario_manager_md page for more information. It will configure another scenario,
    create it and submit it.

    Args:
        state (_type_): the state object of Taipy
    """

    # update the scenario counter
    state.scenario_counter += 1

    print("Creating scenario...")
    name = "Scenario " + dt.datetime.now().strftime('%d-%b-%Y') + " Nb : " + \
        str(state.scenario_counter)
    scenario = tp.create_scenario(scenario_cfg, name=name)
    scenario.properties['user'] = state.login

    # get all the scenarios and their properties
    print("Getting properties...")
    scenarios = [s for s in tp.get_scenarios(
    ) if 'user' in s.properties and state.login == s.properties['user']]

    # change the scenario that is selected. The new scenario is the one that
    # is selected
    state.selected_scenario = scenario.id

    # update the scenario selector
    print("Updating scenario selector...")
    update_scenario_selector(state, scenarios)

    # submit this scenario
    print("Submitting it...")
    submit_scenario(state)


def catch_error_in_submit(state):
    """
    This function is used to catch the error that can occur when we submit a scenario. When an
    error is catched, a notification will appear and variables wil be changed to avoid any error.
    The errors comes from the solution of the Cplex model where infeasible or unbounded problems
    can happen if the fixed variables are wrongly set.

    Args:
        state (_type_): the state object of Taipy
    """

    # if our initial production is higher that our max capacity of production
    if state.fixed_variables["Initial_Production_FPA"] > state.fixed_variables["Max_Capacity_FPA"]:
        state.fixed_variables["Initial_Production_FPA"] = state.fixed_variables["Max_Capacity_FPA"]
        notify(
            state,
            "warning",
            "Value of initial production FPA is greater than max production A")

    # if our initial production is higher that our max capacity of production
    if state.fixed_variables["Initial_Production_FPB"] > state.fixed_variables["Max_Capacity_FPB"]:
        state.fixed_variables["Initial_Production_FPB"] = state.fixed_variables["Max_Capacity_FPB"]
        notify(
            state,
            "warning",
            "Value of initial production FPB is greater than max production B")

    # if our initial stock is higher that our max capacity of production
    if state.fixed_variables["Initial_Stock_RPone"] > state.fixed_variables["Max_Stock_RPone"]:
        state.fixed_variables["Initial_Stock_RPone"] = state.fixed_variables["Max_Stock_RPone"]
        notify(
            state,
            "warning",
            "Value of initial stock RP1 is greater than max stock 1")

    # if our initial stock is higher that our max capacity of production
    if state.fixed_variables["Initial_Stock_RPtwo"] > state.fixed_variables["Max_Stock_RPtwo"]:
        state.fixed_variables["Initial_Stock_RPtwo"] = state.fixed_variables["Max_Stock_RPtwo"]
        notify(
            state,
            "warning",
            "Value of initial stock RP2 is greater than max stock 2")

    # if our initial productions are higher that our max capacity of
    # productions
    if state.fixed_variables["Initial_Production_FPA"] + \
            state.fixed_variables["Initial_Production_FPB"] > state.fixed_variables["Max_Capacity_of_FPA_and_FPB"]:
                
        state.fixed_variables["Initial_Production_FPA"] = int(state.fixed_variables["Max_Capacity_of_FPA_and_FPB"] / 2)
        state.fixed_variables["Initial_Production_FPB"] = int(state.fixed_variables["Max_Capacity_of_FPA_and_FPB"] / 2)
        
        notify(
            state,
            "warning",
            "Value of initial productions is greater than the max capacities")


def submit_heavy(scenario):
    tp.submit(scenario)

def submit_status(state, status):
    # update all the variables that we want to update (ch_results, pie_results
    # and metrics)
    update_variables(state)


def submit_scenario(state):
    """
    This function will submit the scenario that is selected. It will be used when the 'submit' button is pressed
    or when we create a new scenario. It checks if there is any errors then it will change the parameters of the
    problem and submit the scenario. At the end, we update all the variables that we want to update.

    Args:
        state (_type_): the state object of Taipy

    Returns:
        _type_: _description_
    """

    detect_inactive_session(state)

    # see if there are errors in the parameters that will be given to the
    # scenario
    catch_error_in_submit(state)

    # getting the scenario
    scenario = tp.get(state.selected_scenario)

    # setting the scenario with the right parameters
    scenario.fixed_variables.write(state.fixed_variables._dict)

    # running the scenario in a long callback and update variables
    invoke_long_callback(state, submit_heavy, [scenario], submit_status)


def update_variables(state):
    """This function is only used in the submit_scenario or when the selected_scenario changes. It will update all the useful variables that we want to update.

    Args:
        state (_type_): the state object of Taipy
    """
    # getting the selected scenario
    scenario = tp.get(state.selected_scenario)

    # read the result
    state.ch_results = scenario.pipelines['pipeline'].results.read()
    state.pie_results = pd.DataFrame(
        {
            "values": state.ch_results.sum(axis=0),
            "labels": list(state.ch_results.columns)
        })

    state.sum_costs = state.ch_results['Total Cost'].sum()

    bool_costs_of_stock = [c for c in state.ch_results.columns
                           if 'Cost' in c and 'Total' not in c and 'Stock' in c]
    state.sum_costs_of_stock = int(state.ch_results[bool_costs_of_stock].sum(axis=1)\
                                                                        .sum(axis=0))

    bool_costs_of_BO = [c for c in state.ch_results.columns
                        if 'Cost' in c and 'Total' not in c and 'BO' in c]
    state.sum_costs_of_BO = int(state.ch_results[bool_costs_of_BO].sum(axis=1)\
                                                                  .sum(axis=0))




# Button for configuring scenario
sm_show_config_scenario_name = "Hide configuration"
sm_show_config_scenario = True


def show_config_scenario_action(state):
    state.sm_show_config_scenario = not state.sm_show_config_scenario
    state.sm_show_config_scenario_name = "Hide configuration" if state.sm_show_config_scenario else "Configure scenario"


sm_current_month = dt.date.today().strftime('%b')
sm_current_year = dt.date.today().strftime('%Y')

sm_selected_year = sm_current_year
sm_selected_month = sm_current_month

sm_tree_dict, sm_year_selector, sm_month_selector = create_time_selectors()

# Choose the graph to display
sm_graph_selector = [
    'Costs',
    'Purchases',
    'Productions',
    'Stocks',
    'Back Order',
    'Product RP1',
    'Product RP2',
    'Product FPA',
    'Product FPB']
sm_graph_selected = sm_graph_selector[0]
