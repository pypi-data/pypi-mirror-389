import pytest
from dailyDecisionPackage.dailyDecision import pick_color, pick_activity, pick_clothes, pick_food, pick_music


# Unit tests for pick_clothes function
class TestPickClothes:
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

    allClothes = set()
    for clothes in clothes_by_weather.values():
        allClothes.update(clothes)
    for clothes in clothes_by_occasion.values():
        allClothes.update(clothes)

    def test_no_arguments(self, capsys):
        pick_clothes()
        captured = capsys.readouterr()
        assert "Try these clothes! They look good on you: " in captured.out
        assert len(captured.out.strip()) > len(
            "Try these clothes! They look good on you: "
        )

    def test_all_supported_weather(self, capsys):
        supported_weather = ["sunny", "rainy", "snowy", "windy"]
        for weather in supported_weather:
            pick_clothes(weather=weather)
            captured = capsys.readouterr()
            assert (
                f"You chose: '{weather}', so why not wear this bad boy? "
                in captured.out
            )
            assert len(captured.out.strip()) > len(
                f"You chose: '{weather}', so why not wear this bad boy? "
            )
            assert any(
                clothes in captured.out for clothes in self.clothes_by_weather[weather]
            )

    def test_all_supported_occasion(self, capsys):
        supported_occasions = ["casual", "formal", "athletic", "party", "beach"]
        for occasion in supported_occasions:
            pick_clothes(occasion=occasion)
            captured = capsys.readouterr()
            assert (
                f"You chose: '{occasion}', so why not wear this bad boy? " in captured.out
            )
            assert len(captured.out.strip()) > len(
                f"You chose: '{occasion}', so why not wear this bad boy? "
            )
            assert any(
                clothes in captured.out for clothes in self.clothes_by_occasion[occasion]
            )

    def test_both_valid_weather_and_occasion(self, capsys):
        pick_clothes(weather="sunny", occasion="casual")
        captured = capsys.readouterr()
        assert (
            "Good choice! For your weather" in captured.out
            or "Sorry but your weather and occasion didn't fit!" in captured.out
        )

    def test_invalid_weather(self, capsys):
        pick_clothes(weather="invalid")
        captured = capsys.readouterr()
        assert "Oopsie poopsie! :( 'invalid' isn't a weather!" in captured.out
        assert "Choose from: sunny, rainy, snowy, windy" in captured.out
        assert "Otherwise, what do you think of these clothes? " in captured.out

    def test_invalid_occasion(self, capsys):
        pick_clothes(occasion="invalid")
        captured = capsys.readouterr()
        assert "Oopsie poopsie! :( 'invalid' isn't a real occasion!" in captured.out
        assert "Choose from: casual, formal, athletic, party, beach" in captured.out
        assert "Otherwise, what do you think of these clothes? " in captured.out

    def test_invalid_weather_valid_occasion(self, capsys):
        supported_occasions = ["casual", "formal", "athletic", "party", "beach"]
        for occasion in supported_occasions:
            pick_clothes(weather="invalid", occasion=occasion)
            captured = capsys.readouterr()
            assert "Oopsie poopsie! :( 'invalid' isn't a weather!" in captured.out
            assert "Choose from: sunny, rainy, snowy, windy" in captured.out
            assert "Otherwise, what do you think of these clothes? " in captured.out

    def test_valid_weather_invalid_occasion(self, capsys):
        supported_weather = ["sunny", "rainy", "snowy", "windy"]
        for weather in supported_weather:
            pick_clothes(weather=weather, occasion="invalid")
            captured = capsys.readouterr()
            assert "Oopsie poopsie! :( 'invalid' isn't a real occasion!" in captured.out
            assert "Choose from: casual, formal, athletic, party, beach" in captured.out
            assert "Otherwise, what do you think of these clothes? " in captured.out

    def test_both_invalid(self, capsys):
        pick_clothes(weather="invalid", occasion="invalid")
        captured = capsys.readouterr()
        assert "Oopsie poopsie! :( 'invalid' isn't a weather!" in captured.out
        assert "Choose from: sunny, rainy, snowy, windy" in captured.out
        assert "Oopsie poopsie! :( 'invalid' isn't a real occasion!" in captured.out
        assert "Choose from: casual, formal, athletic, party, beach" in captured.out
        assert "Otherwise, what do you think of these clothes? " in captured.out

class TestPickFood:
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
    def test_default_pick(self, capsys):
        pick_food()
        out = capsys.readouterr().out.lower()
        assert "how about:" in out

    def test_valid_restriction(self, capsys):
        pick_food("vegan")
        out = capsys.readouterr().out.lower()
        assert "for a vegan diet" in out
        assert "try" in out

    def test_invalid_restriction(self, capsys):
        pick_food("carnivore")
        out = capsys.readouterr().out.lower()
        assert "sorry" in out or "not a supported restriction" in out
        assert "choose from" in out

    def test_case_insensitive(self, capsys):
        pick_food("VeGeTaRiAn")
        out = capsys.readouterr().out.lower()
        assert "for a vegetarian diet" in out

    def test_alias_anything(self, capsys):
        pick_food("anything")
        out = capsys.readouterr().out.lower()
        assert "how about:" in out

# Unit tests for pick_color function
class TestPickColor:
    happy_colors = [
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
    summer_colors = [
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
    energetic_colors = [
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

    def test_no_arguments(self, capsys):
        pick_color()
        captured = capsys.readouterr()
        assert "Here's a random color for you:" in captured.out
        assert len(captured.out.strip()) > len("Here's a random color for you:")

    def test_all_supported_moods(self, capsys):
        supported_moods = ["happy", "sad", "calm", "energetic", "angry"]
        for mood in supported_moods:
            pick_color(mood=mood)
            captured = capsys.readouterr()
            assert f"For your {mood} mood, try:" in captured.out

    def test_all_supported_seasons(self, capsys):
        supported_seasons = ["winter", "fall", "summer", "spring"]
        for season in supported_seasons:
            pick_color(season=season)
            captured = capsys.readouterr()
            assert f"For {season} season, try:" in captured.out

    def test_mood_happy(self, capsys):
        pick_color(mood="happy")
        captured = capsys.readouterr()
        assert "For your happy mood, try:" in captured.out
        assert any(color in captured.out for color in self.happy_colors)

    def test_invalid_mood(self, capsys):
        pick_color(mood="confused")
        captured = capsys.readouterr()
        assert "Sorry, 'confused' is not a supported mood" in captured.out
        assert "Picking from default list instead:" in captured.out

    def test_season_summer(self, capsys):
        pick_color(season="summer")
        captured = capsys.readouterr()
        assert "For summer season, try:" in captured.out
        assert any(color in captured.out for color in self.summer_colors)

    def test_invalid_season(self, capsys):
        pick_color(season="temp")
        captured = capsys.readouterr()
        assert "Sorry, 'temp' is not a valid season" in captured.out
        assert "Picking from default list instead:" in captured.out

    def test_both_valid_mood_and_season(self, capsys):
        pick_color(mood="calm", season="spring")
        captured = capsys.readouterr()
        assert "Perfect match!" in captured.out or "No perfect match" in captured.out

    def test_both_invalid(self, capsys):
        pick_color(mood="sleepy", season="temp")
        captured = capsys.readouterr()
        assert (
            "Sorry, 'sleepy' is not a valid mood and 'temp' is not a valid season"
            in captured.out
        )
        assert "Picking from default list instead:" in captured.out

    def test_invalid_mood_valid_season(self, capsys):
        pick_color(mood="confused", season="summer")
        captured = capsys.readouterr()
        assert "Sorry, 'confused' is not a valid mood" in captured.out
        assert "Using just your summer season instead, try:" in captured.out
        assert any(color in captured.out for color in self.summer_colors)

    def test_valid_mood_invalid_season(self, capsys):
        pick_color(mood="energetic", season="temp")
        captured = capsys.readouterr()
        assert "Sorry, 'temp' is not a valid season" in captured.out
        assert "Using just your energetic mood instead, try:" in captured.out
        assert any(color in captured.out for color in self.energetic_colors)


# Unit tests for pick_activity function
class TestPickActivity:
    weather_activities = {
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
    energy_activities = {
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

    all_activities = set()
    for activities in energy_activities.values():
        all_activities.update(activities)

    def test_no_arguments(self, capsys):
        pick_activity()
        captured = capsys.readouterr()
        assert "Try this activity: " in captured.out
        assert len(captured.out.strip()) > len("Try this activity: ")

    def test_all_supported_weather(self, capsys):
        supported_weather = ["sunny", "cloudy", "rainy", "snowy"]
        for weather in supported_weather:
            pick_activity(weather=weather)
            captured = capsys.readouterr()
            assert "Try this activity: " in captured.out
            assert len(captured.out.strip()) > len("Try this activity: ")
            assert any(
                activity in captured.out
                for activity in (
                    set(self.weather_activities[weather])
                    | set(self.weather_activities["any"])
                )
            )

    def test_all_supported_energy(self, capsys):
        supported_energy = ["low", "medium", "high"]
        for energy in supported_energy:
            pick_activity(energy_level=energy)
            captured = capsys.readouterr()
            assert "Try this activity: " in captured.out
            assert len(captured.out.strip()) > len("Try this activity: ")
            assert any(
                activity in captured.out for activity in self.energy_activities[energy]
            )

    def test_all_valid_weather_energy_combos(self, capsys):
        supported_weather = ["sunny", "cloudy", "rainy", "snowy"]
        supported_energy = ["low", "medium", "high"]
        for weather in supported_weather:
            for energy in supported_energy:
                pick_activity(weather=weather, energy_level=energy)
                captured = capsys.readouterr()
                assert "Try this activity: " in captured.out
                assert len(captured.out.strip()) > len("Try this activity: ")
                assert any(
                    activity in captured.out
                    for activity in self.energy_activities[energy]
                )
                assert any(
                    activity in captured.out
                    for activity in (
                        set(self.weather_activities[weather])
                        | set(self.weather_activities["any"])
                    )
                )

    def test_invalid_weather(self, capsys):
        pick_activity(weather="invalid")
        captured = capsys.readouterr()
        assert "Sorry, 'invalid' is not a supported weather type." in captured.out
        assert "Please choose from: sunny, cloudy, rainy, snowy" in captured.out
        assert "In the meantime, try this activity: " in captured.out

    def test_invalid_energy(self, capsys):
        pick_activity(energy_level="invalid")
        captured = capsys.readouterr()
        assert "Sorry, 'invalid' is not a supported energy level." in captured.out
        assert "Please choose from: low, medium, high" in captured.out
        assert "In the meantime, try this activity: " in captured.out

    def test_invalid_weather_valid_energy(self, capsys):
        pick_activity(weather="invalid", energy_level="low")
        captured = capsys.readouterr()
        assert "Sorry, 'invalid' is not a supported weather type." in captured.out
        assert "Please choose from: sunny, cloudy, rainy, snowy" in captured.out
        assert "In the meantime, try this activity: " in captured.out

    def test_valid_weather_invalid_energy(self, capsys):
        pick_activity(weather="sunny", energy_level="invalid")
        captured = capsys.readouterr()
        assert "Sorry, 'invalid' is not a supported energy level." in captured.out
        assert "Please choose from: low, medium, high" in captured.out
        assert "In the meantime, try this activity: " in captured.out

    def test_invalid_weather_invalid_energy(self, capsys):
        pick_activity(weather="invalid", energy_level="invalid")
        captured = capsys.readouterr()
        assert "Sorry, 'invalid' is not a supported weather type." in captured.out
        assert "Please choose from: sunny, cloudy, rainy, snowy" in captured.out
        assert "In the meantime, try this activity: " in captured.out

# Unit tests for pick_music function
class TestPickMusic:
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
    
    all_mood_songs = set()
    for songs in songs_by_mood.values():
        all_mood_songs.update(songs)
    all_activity_songs = set()
    for songs in songs_by_activity.values():
        all_activity_songs.update(songs)
    all_rhythm_songs = set()
    for songs in songs_by_rhythm.values():
        all_rhythm_songs.update(songs)

    allSongs = set()
    for lst in [all_mood_songs, all_activity_songs, all_rhythm_songs]:
        allSongs.update(lst)
    
    def test_default_pick_from_catalog(self, capsys):
        pick_music()
        out = capsys.readouterr().out
        assert "How about:" in out
        assert any(song in out for song in self.allSongs)

    def test_alias_anything_from_catalog(self, capsys):
        pick_music("anything")
        out = capsys.readouterr().out
        assert "How about:" in out
        assert any(song in out for song in self.allSongs)

    def test_unrecognized_prompt_guidance_and_fallback(self, capsys):
        pick_music("unicorn vibes xyz")
        out = capsys.readouterr().out.lower()
        assert "sorry, we couldn't recognize any keywords" in out
        assert "please include one of these keywords" in out
        assert "but we've picked something for you to try" in out
        assert any(song.lower() in out for song in self.allSongs)

    def test_single_mood(self, capsys):
        pick_music("calm")
        out = capsys.readouterr().out
        assert "Perfect match" in out
        assert any(song in out for song in self.songs_by_mood["calm"])

    def test_single_activity(self, capsys):
        pick_music("study")
        out = capsys.readouterr().out
        assert "Perfect match" in out
        assert any(song in out for song in self.songs_by_activity["study"])

    def test_single_rhythm(self, capsys):
        pick_music("slow")
        out = capsys.readouterr().out
        assert "Perfect match" in out
        assert any(song in out for song in self.songs_by_rhythm["slow"])

    def test_multiple_moods_union_still_perfect_match(self, capsys):
        union_set = set(self.songs_by_mood["calm"]) | set(self.songs_by_mood["happy"])
        pick_music("calm happy")
        out = capsys.readouterr().out
        assert "Perfect match" in out
        assert any(song in out for song in union_set)

    def test_multiple_activities_union_still_perfect_match(self, capsys):
        union_set = set(self.songs_by_activity["study"]) | set(self.songs_by_activity["focus"])
        pick_music("study focus")
        out = capsys.readouterr().out
        assert "Perfect match" in out
        assert any(song in out for song in union_set)

    def test_activity_and_rhythm_with_intersection(self, capsys):
        act_set = set(self.songs_by_activity["workout"])
        tmp_set = set(self.songs_by_rhythm["fast"])
        inter   = act_set & tmp_set
        assert len(inter) > 0
        pick_music("workout fast")
        out = capsys.readouterr().out
        assert "Perfect match" in out
        assert any(song in out for song in inter)

    def test_mood_and_rhythm_no_intersection_tailored(self, capsys):
        mood_set = set(self.songs_by_mood["angry"])
        tmp_set  = set(self.songs_by_rhythm["chill"])
        inter    = mood_set & tmp_set
        assert len(inter) == 0
        pick_music("angry chill")
        out = capsys.readouterr().out
        assert "No perfect match between your keywords." in out
        assert "Here are the tailored picks:" in out

    def test_valid_rhythm_with_invalid_token_still_works(self, capsys):
        pick_music("abcdefg fast ???")
        out = capsys.readouterr().out
        assert "Perfect match" in out
        assert any(song in out for song in self.songs_by_rhythm["fast"])

    def test_alias_variants_any_anything_works(self, capsys):
        for alias in ["any", "Any", "anything works", "NONE", "no", "idk"]:
            pick_music(alias)
            out = capsys.readouterr().out
            assert "How about:" in out
            assert any(song in out for song in self.allSongs)

    def test_punctuation_and_spacing_robustness(self, capsys):
        pick_music("  calm,   study!!!   slow?? ")
        out = capsys.readouterr().out
        assert ("Perfect match" in out) or ("No perfect match between your keywords." in out)

    def test_invalid_then_valid_category_only_uses_valid(self, capsys):
        pick_music("zzz study")
        out = capsys.readouterr().out
        assert "Perfect match" in out
        assert "Sorry" not in out
        assert any(song in out for song in self.songs_by_activity["study"])

    def test_upper_mixed_case_keywords(self, capsys):
        pick_music("HaPpY")
        out = capsys.readouterr().out
        assert "Perfect match" in out
        assert any(song in out for song in self.songs_by_mood["happy"])

    def test_blank_string_treated_as_unrecognized(self, capsys):
        pick_music("   ")
        out = capsys.readouterr().out.lower()
        assert "sorry, we couldn't recognize any keywords" in out
        assert "please include one of these keywords" in out
        assert "but we've picked something for you to try" in out
        assert any(song.lower() in out for song in self.allSongs)
