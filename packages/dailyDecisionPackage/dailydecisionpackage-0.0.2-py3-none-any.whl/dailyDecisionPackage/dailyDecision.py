# This is where we will write our actual functions for the package
import random
import re

def pick_clothes(weather: str = None, occasion: str = None) -> None:
    clothes_by_weather = {
        "sunny": [
            "sports bra",
            "jersey",
            "T-shirt",
            "shorts",
            "sneakers",
            "khakis",
            "jeans",
            "sandals",
            "sombrero",
            "high heels",
        ],
        "rainy": ["poncho", "raincoat", "boots"],
        "snowy": ["fleece jacket", "scarf", "neckerchief", "beanie", "mittens"],
        "windy": ["light jacket", "hoodie", "athletic pants", "earmuffs"],
    }
    clothes_by_occasion = {
        "casual": ["T-shirt", "shorts", "sneakers", "hoodie", "jeans", "sandals"],
        "formal": [
            "necktie",
            "neckerchief",
            "bowtie",
            "tuxedo",
            "dress shoes",
            "button-up shirt/blouse",
            "khakis",
            "skirt",
        ],
        "athletic": ["sports bra", "jersey", "cleats", "athletic pants", "headband"],
        "party": [
            "sequin dress",
            "high heels",
            "blazer",
            "fedora",
            "rings",
            "slacks",
            "halter top",
        ],
        "beach": [
            "sandals",
            "bikini",
            "swimtrunks",
            "speedo",
            "sombrero",
            "cap",
            "one-piece suit",
            "crocs",
        ],
    }

    # build full set of clothes
    allClothes = set()
    for clothes in clothes_by_weather.values():
        allClothes.update(clothes)
    for clothes in clothes_by_occasion.values():
        allClothes.update(clothes)

    # No arguments (pick random clothes)
    if weather is None and occasion is None:
        print(
            f"Try these clothes! They look good on you: {random.choice(list(allClothes))}"
        )
    # Only weather, no occasion
    elif occasion is None:
        # Invalid weather
        if weather.lower() not in clothes_by_weather:
            print(f"Oopsie poopsie! :( '{weather}' isn't a weather!")
            print(f"Choose from: sunny, rainy, snowy, windy")
            print(
                f"Otherwise, what do you think of these clothes? {random.choice(list(allClothes))}"
            )
            return
        # Valid weather
        validClothes = set(clothes_by_weather[weather.lower()])
        print(
            f"You chose: '{weather}', so why not wear this bad boy? {random.choice(list(validClothes))}"
        )
    # Only occasion, no weather
    elif weather is None:
        # Invalid occasion
        if occasion.lower() not in clothes_by_occasion:
            print(f"Oopsie poopsie! :( '{occasion}' isn't a real occasion!")
            print(f"Choose from: casual, formal, athletic, party, beach")
            print(
                f"Otherwise, what do you think of these clothes? {random.choice(list(allClothes))}"
            )
            return
        # Valid occasion
        validClothes = set(clothes_by_occasion[occasion.lower()])
        print(
            f"You chose: '{occasion}', so why not wear this bad boy? {random.choice(list(validClothes))}"
        )
    # Arguments for both weather and occasion
    else:
        # Invalid weather
        if weather.lower() not in clothes_by_weather:
            print(f"Oopsie poopsie! :( '{weather}' isn't a weather!")
            print(f"Choose from: sunny, rainy, snowy, windy")
            print(
                f"Otherwise, what do you think of these clothes? {random.choice(list(allClothes))}"
            )
        # Invalid occasion
        if occasion.lower() not in clothes_by_occasion:
            print(f"Oopsie poopsie! :( '{occasion}' isn't a real occasion!")
            print(f"Choose from: casual, formal, athletic, party, beach")
            print(
                f"Otherwise, what do you think of these clothes? {random.choice(list(allClothes))}"
            )
        # If either is invalid, return early
        if (
            weather.lower() not in clothes_by_weather
            or occasion.lower() not in clothes_by_occasion
        ):
            return
        # Both valid weather and occasion
        validClothes = list(
            set(clothes_by_occasion[occasion.lower()])
            & set(clothes_by_weather[weather.lower()])
        )
        if validClothes:
            clothes = random.choice(validClothes)
            print(
                f"Good choice! For your weather {weather} and occasion {occasion}, try these clothes out! {clothes}"
            )
        # but they may not have clothes in common
        else:
            rand_weather = random.choice(clothes_by_weather[weather.lower()])
            rand_occasion = random.choice(clothes_by_occasion[occasion.lower()])
            print(
                f"Sorry but your weather and occasion didn't fit! But for {weather.lower()} weather, try on {rand_weather}"
            )
            print(
                f"For {occasion.lower()} occasion, why not give {rand_occasion} a shot?"
            )
    return


def pick_food(dietary_restriction: str = None) -> None:
    # Foods by restriction
    foods_by_restriction = {
        "halal": [
            "chicken biryani",
            "beef kebab plate",
            "shawarma bowl",
            "lentil dal with rice",
            "falafel wrap",
            "grilled salmon",
        ],
        "high_protein": [
            "grilled chicken breast with quinoa",
            "salmon with asparagus",
            "beef stir-fry",
            "lentil salad",
            "tofu and broccoli bowl",
            "turkey chili",
        ],
        "high_protein": [
            "grilled chicken breast with quinoa",
            "salmon with asparagus",
            "beef stir-fry",
            "lentil salad",
            "tofu and broccoli bowl",
            "turkey chili",
        ],
        "jain": [
            "vegetable khichdi",
            "paneer tikka (no onion/garlic)",
            "sabudana khichdi",
            "dal dhokli",
            "vegetable pulao",
            "coconut curry",
        ],
        "keto": [
            "zucchini noodles with pesto",
            "grilled salmon with avocado",
            "cauliflower rice stir-fry",
            "bunless burger with cheese and salad",
            "omelet with spinach and mushrooms",
            "chicken caesar salad (no croutons)",
        ],
        "kosher": [
            "bagel with lox",
            "matzo ball soup",
            "tuna salad",
            "grilled salmon with potatoes",
            "egg salad sandwich",
            "falafel plate",
        ],
        "low_carb": [
            "grilled chicken and veggies",
            "beef lettuce wraps",
            "zoodle bolognese",
            "egg omelet with avocado",
            "shrimp and broccoli stir-fry",
            "cauliflower crust pizza",
        ],
        "no_dairy": [
            "tom yum soup",
            "poke bowl",
            "chicken shawarma wrap (no yogurt sauce)",
            "vegan ramen",
            "tofu curry",
            "bibimbap (no egg)",
        ],
        "no_eggs": [
            "pasta primavera",
            "mushroom risotto",
            "vegetable stir-fry",
            "falafel wrap",
            "vegan curry",
            "tofu scramble",
        ],
        "no_gluten": [
            "rice bowl with chicken",
            "corn tacos",
            "pho",
            "sashimi platter",
            "thai green curry",
            "baked sweet potato",
        ],
        "no_nuts": [
            "margherita pizza",
            "spaghetti pomodoro",
            "fried rice",
            "beef tacos",
            "rotisserie chicken plate",
            "tomato soup & grilled cheese",
        ],
        "no_nuts": [
            "margherita pizza",
            "spaghetti pomodoro",
            "fried rice",
            "beef tacos",
            "rotisserie chicken plate",
            "tomato soup & grilled cheese",
        ],
        "no_soy": [
            "grilled chicken salad",
            "roasted veggie pasta",
            "eggplant parm",
            "mushroom risotto",
            "omelet with veggies",
            "lentil soup",
        ],
        "paleo": [
            "grilled steak with roasted veggies",
            "salmon with sweet potato mash",
            "zucchini noodles with tomato sauce",
            "chicken lettuce wraps",
            "baked cod with olive oil",
            "fruit and nut bowl",
        ],
        "pescatarian": [
            "salmon poke bowl",
            "shrimp tacos",
            "grilled cod with veggies",
            "tuna niçoise salad",
            "sushi combo",
            "miso-glazed salmon",
            "fish and chips (light batter)",
        ],
        "vegan": [
            "tofu stir-fry",
            "chickpea curry",
            "veggie sushi",
            "buddha bowl",
            "lentil bolognese",
            "quinoa salad",
        ],
        "vegetarian": [
            "margherita pizza",
            "mushroom risotto",
            "spinach ravioli",
            "caprese sandwich",
            "falafel bowl",
            "paneer tikka",
        ],
    }

    # Build full set of all foods
    allFoods = set()
    for foods in foods_by_restriction.values():
        allFoods.update(foods)

    # No restriction given — pick from all
    if dietary_restriction is None:
        print(f"How about: {random.choice(list(allFoods))}")
        return

    restriction = dietary_restriction.strip().lower()

    aliases_any = {
        "any", "anything", "whatever", "no", "none",
        "no restriction", "normal", "idk", "anything works"
    }
    if restriction in aliases_any:
        print(f"How about: {random.choice(list(allFoods))}")
        return


    if restriction not in foods_by_restriction:
        accepted = ", ".join(sorted(foods_by_restriction.keys()))
        print(f"Sorry, '{restriction}' is not a supported restriction.")
        print(f"Please choose from: {accepted}")
        print(f"In the meantime, try: {random.choice(list(allFoods))}")
        return
    

    choice = random.choice(foods_by_restriction[restriction])
    print(f"For a {restriction} diet, you could try: {choice}")


def pick_color(mood: str = None, season: str = None) -> None:
    winter = [
        "blue",
        "navy",
        "white",
        "silver",
        "black",
        "burgundy",
        "emerald green",
        "royal purple",
        "ice blue",
        "charcoal",
    ]
    fall = [
        "orange",
        "rust",
        "brown",
        "burgundy",
        "mustard yellow",
        "olive green",
        "burnt sienna",
        "copper",
        "maroon",
        "tan",
    ]
    summer = [
        "yellow",
        "coral",
        "turquoise",
        "hot pink",
        "lime green",
        "sky blue",
        "peach",
        "tangerine",
        "mint",
        "aqua",
    ]
    spring = [
        "pastel pink",
        "lavender",
        "mint",
        "baby blue",
        "lemon yellow",
        "peach",
        "soft coral",
        "light purple",
        "sage green",
        "cream",
    ]
    happy = [
        "yellow",
        "bright orange",
        "sunny gold",
        "lime green",
        "sky blue",
        "pink",
        "coral",
        "peach",
        "turquoise",
    ]
    sad = ["blue", "grey", "dark purple", "navy", "slate blue", "charcoal", "ice blue"]
    calm = [
        "light blue",
        "lavender",
        "sage green",
        "soft grey",
        "beige",
        "mint",
        "powder blue",
        "pale pink",
        "baby blue",
    ]
    energetic = [
        "red",
        "bright orange",
        "electric blue",
        "neon green",
        "hot pink",
        "vibrant yellow",
        "magenta",
        "lime green",
        "tangerine",
    ]
    angry = [
        "red",
        "crimson",
        "black",
        "dark orange",
        "blood red",
        "maroon",
        "dark grey",
        "burgundy",
    ]

    # Season and mood dictionaries for easy lookup
    seasonColors = {"winter": winter, "fall": fall, "summer": summer, "spring": spring}
    moodColors = {
        "happy": happy,
        "sad": sad,
        "calm": calm,
        "energetic": energetic,
        "angry": angry,
    }
    # Default color set
    allColors = set()
    for colors in seasonColors.values():
        allColors.update(colors)
    for colors in moodColors.values():
        allColors.update(colors)

    # No arguments - pick from default
    if mood is None and season is None:
        print(f"Here's a random color for you: {random.choice(list(allColors))}")
    # Only mood provided
    elif mood is not None and season is None:
        mood = mood.lower()
        if mood not in moodColors:
            print(
                f"Sorry, '{mood}' is not a supported mood. Here's the list of accepted moods: {', '.join(moodColors.keys())}"
            )
            print(
                f"Picking from default list instead: {random.choice(list(allColors))}"
            )
        else:
            color = random.choice(moodColors[mood])
            print(f"For your {mood} mood, try: {color}")
    # Only season provided
    elif season is not None and mood is None:
        season = season.lower()
        if season not in seasonColors:
            print(
                f"Sorry, '{season}' is not a valid season. Here's the list of accepted seasons: {', '.join(seasonColors.keys())}"
            )
            print(
                f"Picking from default list instead: {random.choice(list(allColors))}"
            )
        else:
            color = random.choice(seasonColors[season])
            print(f"For {season} season, try: {color}")
    # Both mood and season provided
    else:
        mood = mood.lower()
        season = season.lower()
        validMood = mood in moodColors
        validSeason = season in seasonColors
        # If both invalid, pick from default
        if not validMood and not validSeason:
            print(
                f"Sorry, '{mood}' is not a valid mood and '{season}' is not a valid season."
            )
            print(f"Here's the list of accepted moods: {', '.join(moodColors.keys())}")
            print(
                f"Here's the list of accepted seasons: {', '.join(seasonColors.keys())}"
            )
            print(
                f"Picking from default list instead: {random.choice(list(allColors))}"
            )
        # If only mood invalid, use season
        elif not validMood:
            print(
                f"Sorry, '{mood}' is not a valid mood. Try: {', '.join(moodColors.keys())}"
            )
            color = random.choice(seasonColors[season])
            print(f"Using just your {season} season instead, try: {color}")
        # If only season invalid, use mood
        elif not validSeason:
            print(
                f"Sorry, '{season}' is not a valid season. Try: {', '.join(seasonColors.keys())}"
            )
            color = random.choice(moodColors[mood])
            print(f"Using just your {mood} mood instead, try: {color}")
        # Both valid
        else:
            commonColors = list(set(moodColors[mood]) & set(seasonColors[season]))
            if commonColors:
                color = random.choice(commonColors)
                print(f"Perfect match! For {mood} mood in {season}: {color}")
            else:
                mood_color = random.choice(moodColors[mood])
                season_color = random.choice(seasonColors[season])
                print(
                    f"No perfect match, but try {mood} color: {mood_color} or {season} color: {season_color}"
                )


def pick_activity(weather: str = None, energy_level: str = None) -> None:
    # Activities by weather
    activities_by_weather = {
        "sunny": [
            "go for a walk",
            "read a book at the park",
            "explore a new part of the city",
            "go for a run",
            "go hiking",
            "bike around your neighborhood",
            "go to the beach",
        ],
        "cloudy": ["watch the clouds"],
        "rainy": ["dance in the rain"],
        "snowy": ["make snow angels", "build a snowman", "snowball fight"],
        "any": [
            "watch a movie or TV",
            "play a video game",
            "read a book indoors",
            "listen to a podcast",
            "listen to music",
            "write a journal entry",
            "call a friend",
            "play a board game",
            "solve a crossword",
            "clean your bedroom",
            "light exercise",
            "dance",
            "make a home-cooked meal",
            "arts & crafts",
            "yoga",
            "go to the gym",
            "go to the club",
            "go to a party",
            "clean the house",
            "painting",
            "go for a drive",
        ],
    }
    # Activities by energy level
    activities_by_energy_level = {
        "low": [
            "watch a movie or TV",
            "play a video game",
            "read a book indoors",
            "read a book at the park",
            "listen to a podcast",
            "listen to music",
            "write a journal entry",
            "call a friend",
            "play a board game",
            "solve a crossword",
            "watch the clouds",
            "painting",
        ],
        "medium": [
            "go for a walk",
            "clean your bedroom",
            "light exercise",
            "dance",
            "dance in the rain",
            "make a home-cooked meal",
            "arts & crafts",
            "yoga",
            "make snow angels",
            "build a snowman",
            "go to the beach",
            "go for a drive",
        ],
        "high": [
            "go to the gym",
            "go for a run",
            "go hiking",
            "bike around your neighborhood",
            "go to the club",
            "go to a party",
            "clean the house",
            "snowball fight",
            "explore a new part of the city",
        ],
    }
    # create set of all activities
    allActivities = set()
    for activities in activities_by_weather.values():
        allActivities.update(activities)
    for activities in activities_by_energy_level.values():
        allActivities.update(activities)

    # No arguments (pick random activity)
    if weather is None and energy_level is None:
        print(f"Try this activity: {random.choice(list(allActivities))}")
        return
    # No energy level argument (weather only)
    elif energy_level is None:
        # Invalid weather
        if weather.lower() not in activities_by_weather:
            accepted = ", ".join(sorted(activities_by_weather.keys()))
            print(f"Sorry, '{weather}' is not a supported weather type.")
            print(f"Please choose from: sunny, cloudy, rainy, snowy")
            print(
                f"In the meantime, try this activity: {random.choice(list(allActivities))}"
            )
            return
        # Valid weather
        validActivities = set(activities_by_weather[weather.lower()]) | set(
            activities_by_weather["any"]
        )
        print(f"Try this activity: {random.choice(list(validActivities))}")
        return
    # No weather argument (energy level only)
    elif weather is None:
        # Invalid energy level
        if energy_level.lower() not in activities_by_energy_level:
            print(f"Sorry, '{energy_level}' is not a supported energy level.")
            print(f"Please choose from: low, medium, high")
            print(
                f"In the meantime, try this activity: {random.choice(list(allActivities))}"
            )
            return
        # Valid energy level
        validActivities = set(activities_by_energy_level[energy_level.lower()])
        print(f"Try this activity: {random.choice(list(validActivities))}")
        return
    # Arguments for both weather and energy level
    else:
        # Invalid weather
        if weather.lower() not in activities_by_weather:
            accepted = ", ".join(sorted(activities_by_weather.keys()))
            print(f"Sorry, '{weather}' is not a supported weather type.")
            print(f"Please choose from: sunny, cloudy, rainy, snowy")
            print(
                f"In the meantime, try this activity: {random.choice(list(allActivities))}"
            )
            return
        # Invalid energy level
        if energy_level.lower() not in activities_by_energy_level:
            print(f"Sorry, '{energy_level}' is not a supported energy level.")
            print(f"Please choose from: low, medium, high")
            print(
                f"In the meantime, try this activity: {random.choice(list(allActivities))}"
            )
            return
        # Valid arguments
        # Valid arguments
        validActivities = (
            set(activities_by_weather[weather.lower()])
            | set(activities_by_weather["any"])
        ) & set(activities_by_energy_level[energy_level.lower()])

        if validActivities:
            print(f"Try this activity: {random.choice(list(validActivities))}")
        else:
            # No perfect match - suggest activities from default list
            print(
                f"Sorry, no perfect match! But for now try: {random.choice(list(allActivities))}"
            )
        return

def pick_music(prompt: str = None) -> None:
    # Songs by prompt
    songs_by_mood = {
        "happy": [
            "Happy - Pharrell Williams",
            "Walking on Sunshine - Katrina & The Waves",
            "Shut Up and Dance - WALK THE MOON",
            "Good as Hell - Lizzo",
            "Uptown Funk - Mark Ronson ft. Bruno Mars",
            "I Gotta Feeling - The Black Eyed Peas",
            "Best Day of My Life - American Authors",
            "Can’t Stop The Feeling! - Justin Timberlake",
        ],
        "sad": [
            "Someone Like You - Adele",
            "Fix You - Coldplay",
            "Skinny Love - Bon Iver",
            "The Night We Met - Lord Huron",
            "All I Want - Kodaline",
            "Happier - Ed Sheeran",
            "When The Party's Over - Billie Eilish",
            "Let Her Go - Passenger",
        ],
        "calm": [
            "Holocene - Bon Iver",
            "Bloom - The Paper Kites",
            "Budapest - George Ezra",
            "Photograph - Ed Sheeran",
            "Lost in Japan - Shawn Mendes",
            "Rivers and Roads - The Head and the Heart",
            "Banana Pancakes - Jack Johnson",
            "Ocean Eyes - Billie Eilish",
        ],
        "focused": [
            "Weightless - Marconi Union",
            "Experience - Ludovico Einaudi",
            "Sunset Lover - Petit Biscuit",
            "Intro - The xx",
            "Comptine d’un autre été - Yann Tiersen",
            "We Move Lightly - Dustin O’Halloran",
            "Midnight - Lane 8",
            "Night Owl - Galimatias",
        ],
        "angry": [
            "Smells Like Teen Spirit - Nirvana",
            "In the End - Linkin Park",
            "Killing In The Name - Rage Against The Machine",
            "Enter Sandman - Metallica",
            "Duality - Slipknot",
            "Hail to the King - Avenged Sevenfold",
            "Papercut - Linkin Park",
            "Break Stuff - Limp Bizkit",
        ],
        "romantic": [
            "All of Me - John Legend",
            "Perfect - Ed Sheeran",
            "Just The Way You Are - Bruno Mars",
            "Make You Feel My Love - Adele",
            "Stay With Me - Sam Smith",
            "Yellow - Coldplay",
            "Say You Won’t Let Go - James Arthur",
            "Die For You - The Weeknd",
        ],
        "nostalgic": [
            "Wonderwall - Oasis",
            "Mr. Brightside - The Killers",
            "Iris - Goo Goo Dolls",
            "Chasing Cars - Snow Patrol",
            "Hey There Delilah - Plain White T’s",
            "Viva La Vida - Coldplay",
            "Stacy’s Mom - Fountains of Wayne",
            "Seven Nation Army - The White Stripes",
        ],
    }

    songs_by_activity = {
        "study": [
            "Experience - Ludovico Einaudi",
            "River Flows in You - Yiruma",
            "Sunset Lover - Petit Biscuit",
            "Night Owl - Galimatias",
            "Weightless - Marconi Union",
            "Intro - The xx",
            "We Move Lightly - Dustin O’Halloran",
            "Gymnopédie No.1 - Erik Satie",
        ],
        "workout": [
            "Stronger - Kanye West",
            "Lose Yourself - Eminem",
            "Can’t Hold Us - Macklemore & Ryan Lewis",
            "Don’t Start Now - Dua Lipa",
            "Eye of the Tiger - Survivor",
            "Till I Collapse - Eminem",
            "Believer - Imagine Dragons",
            "Remember the Name - Fort Minor",
        ],
        "commute": [
            "Budapest - George Ezra",
            "Riptide - Vance Joy",
            "Viva La Vida - Coldplay",
            "Paris - The Chainsmokers",
            "Feel It Still - Portugal. The Man",
            "Blinding Lights - The Weeknd",
            "Pocket Full of Sunshine - Natasha Bedingfield",
            "Electric Feel - MGMT",
        ],
        "party": [
            "Uptown Funk - Mark Ronson ft. Bruno Mars",
            "Levitating - Dua Lipa",
            "One Kiss - Calvin Harris & Dua Lipa",
            "Hey Ya! - OutKast",
            "Turn Down for What - DJ Snake & Lil Jon",
            "Starboy - The Weeknd",
            "I Like It - Cardi B",
            "Low - Flo Rida",
        ],
        "relax": [
            "Better Together - Jack Johnson",
            "Holocene - Bon Iver",
            "Banana Pancakes - Jack Johnson",
            "Bloom - The Paper Kites",
            "I’m Yours - Jason Mraz",
            "Budapest - George Ezra",
            "Ocean Eyes - Billie Eilish",
            "Sunflower - Rex Orange County",
        ],
        "focus": [
            "Experience - Ludovico Einaudi",
            "Midnight - Lane 8",
            "Open Eye Signal - Jon Hopkins",
            "Saturn - Sleeping at Last",
            "Prelude in E Minor - Chopin",
            "Outro - M83",
            "We Move Lightly - Dustin O’Halloran",
            "Sunset Lover - Petit Biscuit",
        ],
        "drive": [
            "Midnight City - M83",
            "Blinding Lights - The Weeknd",
            "Shut Up and Drive - Rihanna",
            "Ride - Twenty One Pilots",
            "On the Road Again - Willie Nelson",
            "Take Me Out - Franz Ferdinand",
            "Go Your Own Way - Fleetwood Mac",
            "Feel Good Inc. - Gorillaz",
        ],
        "cook": [
            "Put Your Records On - Corinne Bailey Rae",
            "Sunday Morning - Maroon 5",
            "Mariposa - Peach Tree Rascals",
            "Budapest - George Ezra",
            "Brown Eyed Girl - Van Morrison",
            "Best Part - Daniel Caesar ft. H.E.R.",
            "I’m Yours - Jason Mraz",
            "Dreams - Fleetwood Mac",
        ],
    }

    songs_by_rhythm = {
        "fast": [
            "Don’t Start Now - Dua Lipa",
            "Levitating - Dua Lipa",
            "On Top of the World - Imagine Dragons",
            "Blinding Lights - The Weeknd",
            "Can’t Hold Us - Macklemore & Ryan Lewis",
            "Don’t Stop Me Now - Queen",
            "We Found Love - Rihanna",
            "Titanium - David Guetta ft. Sia",
        ],
        "mid": [
            "Viva La Vida - Coldplay",
            "Counting Stars - OneRepublic",
            "Shut Up and Dance - WALK THE MOON",
            "Riptide - Vance Joy",
            "Feel It Still - Portugal. The Man",
            "Send Me On My Way - Rusted Root",
            "Electric Feel - MGMT",
            "Stolen Dance - Milky Chance",
        ],
        "slow": [
            "All of Me - John Legend",
            "Let Her Go - Passenger",
            "Skinny Love - Bon Iver",
            "Stay With Me - Sam Smith",
            "River Flows in You - Yiruma",
            "Holocene - Bon Iver",
            "Make You Feel My Love - Adele",
            "Fix You - Coldplay",
        ],
        "chill": [
            "Sunset Lover - Petit Biscuit",
            "Night Owl - Galimatias",
            "Lovely - Billie Eilish & Khalid",
            "Lost in Japan - Shawn Mendes",
            "Beyond - Leon Bridges",
            "Talk - Khalid",
            "Put It All on Me - Ed Sheeran",
            "Warm - Majid Jordan",
        ],
    }

    # Build full set of all songs
    allSongs = set()
    for lst in (
        list(songs_by_mood.values())
        + list(songs_by_activity.values())
        + list(songs_by_rhythm.values())
    ):
        allSongs.update(lst)

    # No prompts given then pick from all
    if prompt is None:
        print(f"How about: {random.choice(list(allSongs))}")
        return

    text = prompt.strip().lower()
    aliases_any = {"any", "anything", "whatever", "no", "none", "idk", "anything works"}
    if text in aliases_any:
        print(f"How about: {random.choice(list(allSongs))}")
        return

    # Disassemble the prompts into set of single prompt
    tokens = re.findall(r"[a-zA-Z]+", text)

    mood_keys     = set(songs_by_mood.keys())
    activity_keys = set(songs_by_activity.keys())
    rhythm_keys    = set(songs_by_rhythm.keys())

    # Check the keywords
    found_moods      = [t for t in tokens if t in mood_keys]
    found_activities = [t for t in tokens if t in activity_keys]
    found_rhythms     = [t for t in tokens if t in rhythm_keys]

    # When keywords don't match
    if not (found_moods or found_activities or found_rhythms):
        accepted = (
            "moods: "
            + ", ".join(sorted(mood_keys))
            + "; "
            + "activities: "
            + ", ".join(sorted(activity_keys))
            + "; "
            + "rhythms: "
            + ", ".join(sorted(rhythm_keys))
        )
        print(f"Sorry, we couldn't recognize any keywords from: '{text}'.")
        print(f"Please include one of these keywords: {accepted}")
        print(f"But we've picked something for you to try: {random.choice(list(allSongs))}")
        return

    # Collect possible songs based on all recognized keyword sets
    candidate_sets = []

    if found_moods:
        mood_union = set()
        for m in found_moods:
            mood_union.update(songs_by_mood[m])
        candidate_sets.append(mood_union)

    if found_activities:
        act_union = set()
        for a in found_activities:
            act_union.update(songs_by_activity[a])
        candidate_sets.append(act_union)

    if found_rhythms:
        rhythm_union = set()
        for s in found_rhythms:
            rhythm_union.update(songs_by_rhythm[s])
        candidate_sets.append(rhythm_union)

    # Try to find songs that satisfy ALL categories
    if candidate_sets:
        inter = set.intersection(*candidate_sets) if len(candidate_sets) > 1 else candidate_sets[0]

        # If found perfect match across all categories
        if inter:
            picked = random.choice(list(inter))
            summary_parts = []
            if found_moods:
                summary_parts.append("/".join(found_moods))
            if found_activities:
                summary_parts.append("/".join(found_activities))
            if found_rhythms:
                summary_parts.append("/".join(found_rhythms))
            summary = " & ".join(summary_parts)
            print(f"Perfect match for {summary}. Try: {picked}")
            return

        # If no intersection then give one suggestion per category
        suggestions = []
        if found_moods:
            mood_keywords = "/".join(found_moods)
            suggestions.append(
                (
                    mood_keywords,
                    random.choice(
                        list(set().union(*[set(songs_by_mood[m]) for m in found_moods]))
                    ),
                )
            )
        if found_activities:
            activity_keywords = "/".join(found_activities)
            suggestions.append(
                (
                    activity_keywords,
                    random.choice(
                        list(
                            set().union(
                                *[set(songs_by_activity[a]) for a in found_activities]
                            )
                        )
                    ),
                )
            )
        if found_rhythms:
            rhythm_keywords = "/".join(found_rhythms)
            suggestions.append(
                (
                    rhythm_keywords,
                    random.choice(
                        list(
                            set().union(
                                *[set(songs_by_rhythm[s]) for s in found_rhythms]
                            )
                        )
                    ),
                )
            )

        print("No perfect match between your keywords. Here are the tailored picks:")
        for k, v in suggestions:
            print(f"- For {k}, try: {v}")
        return
