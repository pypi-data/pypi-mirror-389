[![CI / CD](https://github.com/swe-students-fall2025/3-python-package-team_aurora/actions/workflows/test.yml/badge.svg)](https://github.com/swe-students-fall2025/3-python-package-team_aurora/actions/workflows/test.yml)

# Python Package Exercise - Daily Decision Helper

**PyPI Package:** [dailyDecisionPackage on PyPI](https://pypi.org/project/dailyDecisionPackage/0.0.2/)

## Overview

Do you ever struggle to make everyday decisions? Whether it's choosing what to eat for lunch, picking an outfit color, or deciding what music to listen to, sometimes the smallest choices can feel overwhelming. DailyDecisions is here to help! This Python package takes the stress out of life's minor decisions by providing randomized suggestions when you need them most.

## Installation

1. Install the package using `pipenv`: `pipenv install dailyDecisionPackage==0.0.2`
2. Activate the virtual environment: `pipenv shell`
3. Create a Python program file that imports the package and uses it, e.g.:

    ```
    from dailyDecisionPackage import dailyDecision

    # This would print out the randomly suggested color
    dailyDecision.pick_color()
    ```

4. Run the program: `python filename.py`
5. Exit the virutal environment: `exit`

## Features

This package provides a few functions to help with your daily decision making:

-   `dailyDecision.pick_clothes(weather, occasion)` - a function to help you pick clothes based on the weather and/or occasion.
-   `dailyDecision.pick_food(dietary_restriction)` - a function to help you pick a food based on your dietary restriction.
-   `dailyDecision.pick_color(mood, season)` - a function to help you pick a color (of clothing) based on your mood and/or the season.
-   `dailyDecision.pick_activity(weather, energy_level)` - a function to help you pick an activity to do based on your energy level and/or the weather.
-   `dailyDecision.pick_music(prompts)` - a function to help you pick a song or songs to listen to based on your prompt(s) (could be mood/activity/rhythm).

## Usage

### Import the Package

`from dailyDecisionPackage import dailyDecision`

### Function Documentation

#### 1. `dailyDecision.pick_clothes(weather: str, occasion: str)`

Suggests clothing items based on weather conditions and/or the occasion.

**Parameters**:

-   `weather` (optional): The weather condition - "sunny", "rainy", "snowy", or "windy"
-   `occasion` (optional): The occasion or dress code - "casual", "formal", "athletic", "party", or "beach"

**Behavior**:

-   No arguments: Returns a random clothing item from all available options
-   Only weather: Returns clothing appropriate for that weather
-   Only occasion: Returns clothing appropriate for that occasion
-   Both valid arguments: Returns clothing that fits both criteria (or suggests separate items if no match exists)
-   Invalid input: Displays valid options and suggests a random item from all available options

#### 2. `dailyDecision.pick_food(dietary_restriction: str)`

Suggests food options based on dietary restrictions.

**Parameters**:

-   `dietary_restriction` (optional): Your dietary need - "halal", "high_protein", "jain", "keto", "kosher", "low_carb", "no_dairy", "no_eggs", "no_gluten", "no_nuts", "no_soy", "paleo", "pescatarian", "vegan", or "vegetarian"

**Behavior**:

-   No argument: Returns a random food from all available options
-   Valid restriction: Returns food that meets the specified dietary restriction
-   Invalid restriction: Displays valid options and suggests a random food from all available options

#### 3. `dailyDecision.pick_color(mood: str, season: str)`

Suggests colors based on your mood and/or the current season.

**Parameters**:
-   `mood` (optional): Your emotional state - "happy", "sad", "calm", "energetic", or "angry"
-   `season` (optional): The current season - "winter", "fall", "summer", or "spring"

**Behavior**:

-   No arguments: Returns a random color from all available options
-   Only mood: Returns a color matching that mood
-   Only season: Returns a color matching that season
-   Both valid arguments: Returns a color that fits both (or suggests separate colors if no perfect match)
-   Both arguments, but only mood is valid: Displays valid options for seasons and suggests a random color matching the mood
-   Both arguments, but only season is valid: Displays valid options for moods and suggests a random color matching the season
-   Invalid input: Displays valid options and suggests a random color from all available options

#### 4. `dailyDecision.pick_activity(weather: str, energy_level: str)`

Suggests activities based on weather conditions and/or your energy level.

**Parameters**:

-   `weather` (optional): The weather condition - "sunny", "cloudy", "rainy", or "snowy"
-   `energy_level` (optional): Your current energy - "low", "medium", or "high"

**Behavior**:

-   No arguments: Returns a random activity from all available options
-   Only weather: Returns activities suitable for that weather
-   Only energy level: Returns activities matching your energy level
-   Both arguments: Returns activities that fit both criteria
-   Invalid input: Displays valid options and suggests a random activity from all available options

#### 5. `dailyDecision.pick_music(prompts: str)`

Suggests songs based on the prompt(s) given. You can provide multiple keywords separated by spaces or other non-letter characters to combine different criteria. For example, "happy workout" will find songs that match both happy mood and workout activity, and "happy workout fast" will find songs matching all three categories.

**Parameters**:

-   `prompt` (optional) — a keyword describing what kind of music you're looking for
    -   **Mood** examples: "happy", "sad", "calm", "focused", "angry", "romantic", "nostalgic"
    -   **Activity** examples: "study", "workout", "commute", "party", "relex", "focus", "drive", "cook"
    -   **Rhythm** examples: "fast", "mid", "slow", "chill"

**Behavior**:

-   No argument: suggests a random song from the full catalog
-   Prompt matches mood/activity/rhythm: returns a random song from the matching category
-   Prompt appears in multiple categories:
    -   If categories overlap: return one song representing all categories
    -   If not: return separate songs for each category
-   Invalid input: displays valid options and suggests a random song

### Example

For a complete example program that demonstrates all four functions with various parameter combinations, see [exampleUsage.py](https://github.com/swe-students-fall2025/3-python-package-team_aurora/blob/pipfile-experiment/examples/exampleUsage.py).  
To run the example from root: `python examples/exampleUsage.py`

## Contributing

Want to contribute to this project? Here's how to get started:

1. **Clone the repository:** `https://github.com/swe-students-fall2025/3-python-package-team_aurora.git`
2. **Install pipenv** (if not already installed): `pip install pipenv`
3. **Install dependencies:** `pipenv install --dev`
4. **Activate the virtual environment:** `pipenv shell`

### Unit tests

Run the unit tests using pytest: `pipenv run pytest tests/tests.py`

### Building the Package

To build the package locally: `pipenv run python -m build`

## Team members:

[Maria Lee](https://github.com/MariaLuo826)  
[Reece Huey](https://github.com/Coffee859)  
[Jubilee Tang](https://github.com/MajesticSeagull26)  
[Anshu Aramandla](https://github.com/aa10150)  
[Natalie Han](https://github.com/nateisnataliehan)
