"""
Custom Faker providers for eBird bird observation data.

These providers generate realistic, context-aware data for bird observations,
including species, locations, and observation metadata.

Usage:
    from faker import Faker
    from ebird.api.data.faker_providers import BirdProvider, LocationProvider

    fake = Faker()
    fake.add_provider(BirdProvider)
    fake.add_provider(LocationProvider)

    species_code = fake.bird_species_code()
    habitat = fake.bird_habitat()
"""

from faker.providers import BaseProvider
import random
from typing import Dict, List


class BirdProvider(BaseProvider):
    """Faker provider for bird-related data."""

    # Common Portuguese bird species
    species_codes = [
        "houspa", "eurbla1", "gretit1", "blucap1", "comcha",
        "whiwag", "yelgul", "greheg", "litegg", "whisto",
        "commbu", "comspo1", "grefla2", "pieavo", "blkwis",
        "barswa", "comswi", "eurbee", "eurhoo", "eurgol",
        "grifvo", "boneag1", "litbus", "grebta", "calshe",
    ]

    species_names = {
        "houspa": "House Sparrow",
        "eurbla1": "European Blackbird",
        "gretit1": "Great Tit",
        "blucap1": "Blue Tit",
        "comcha": "Common Chaffinch",
        "whiwag": "White Wagtail",
        "yelgul": "Yellow-legged Gull",
        "greheg": "Grey Heron",
        "litegg": "Little Egret",
        "whisto": "White Stork",
        "commbu": "Common Buzzard",
        "comspo1": "Common Kestrel",
        "grefla2": "Greater Flamingo",
        "pieavo": "Pied Avocet",
        "blkwis": "Black-winged Stilt",
        "barswa": "Barn Swallow",
        "comswi": "Common Swift",
        "eurbee": "European Bee-eater",
        "eurhoo": "Eurasian Hoopoe",
        "eurgol": "European Goldfinch",
        "grifvo": "Griffon Vulture",
        "boneag1": "Bonelli's Eagle",
        "litbus": "Little Bustard",
        "grebta": "Great Bustard",
        "calshe": "Calandra Lark",
    }

    # Species typical counts (min, max)
    species_typical_counts = {
        "houspa": (1, 50),
        "eurbla1": (1, 10),
        "gretit1": (1, 15),
        "blucap1": (1, 12),
        "comcha": (1, 20),
        "whiwag": (1, 8),
        "yelgul": (1, 100),
        "greheg": (1, 5),
        "litegg": (1, 15),
        "whisto": (1, 20),
        "commbu": (1, 3),
        "comspo1": (1, 2),
        "grefla2": (1, 150),
        "pieavo": (1, 30),
        "blkwis": (1, 25),
        "barswa": (1, 40),
        "comswi": (1, 30),
        "eurbee": (1, 15),
        "eurhoo": (1, 3),
        "eurgol": (1, 25),
        "grifvo": (1, 3),
        "boneag1": (1, 2),
        "litbus": (1, 10),
        "grebta": (1, 5),
        "calshe": (1, 30),
    }

    habitats = [
        "coastal",
        "coastal_wetland",
        "wetland",
        "woodland",
        "farmland",
        "grassland",
        "urban",
        "mountain",
    ]

    habitat_species_map = {
        "coastal": ["yelgul", "blkgul2", "comter", "norgat3", "cooshe1"],
        "coastal_wetland": ["pieavo", "blkwis", "litegg", "grefla2", "comshe1", "greheg"],
        "wetland": ["greheg", "purher", "litegg", "blkwis", "whiwag"],
        "woodland": ["grespo", "ibewoo", "eurjay1", "eurbla1", "euirob", "gretit1", "blucap1"],
        "farmland": ["houspa", "whisto", "barswa", "eurbee", "comcha", "calshe"],
        "grassland": ["litbus", "grebta", "calshe", "lasser", "theshe", "grifvo"],
        "urban": ["houspa", "comsta", "spotsta", "comswi", "gretit1", "blucap1"],
        "mountain": ["grifvo", "boneag1", "egyvul", "commbu"],
    }

    protocols = [
        ("P20", "Incidental"),
        ("P21", "Stationary"),
        ("P22", "Traveling"),
        ("P23", "Area"),
    ]

    def bird_species_code(self) -> str:
        """Generate a random bird species code."""
        return self.random_element(self.species_codes)

    def bird_species_name(self, species_code: str = None) -> str:
        """Generate a bird species common name."""
        if species_code and species_code in self.species_names:
            return self.species_names[species_code]
        code = species_code or self.bird_species_code()
        return self.species_names.get(code, f"Species {code}")

    def bird_count(self, species_code: str = None) -> int:
        """Generate a realistic count for a bird species."""
        if species_code and species_code in self.species_typical_counts:
            min_count, max_count = self.species_typical_counts[species_code]
            return self.random_int(min=min_count, max=max_count)
        return self.random_int(min=1, max=10)

    def bird_habitat(self) -> str:
        """Generate a random habitat type."""
        return self.random_element(self.habitats)

    def bird_species_for_habitat(self, habitat: str) -> str:
        """Generate a species code appropriate for a habitat."""
        if habitat in self.habitat_species_map:
            suitable_species = self.habitat_species_map[habitat]
            return self.random_element(suitable_species)
        return self.bird_species_code()

    def bird_species_list_for_habitat(
        self, habitat: str, min_species: int = 3, max_species: int = 15
    ) -> List[str]:
        """Generate a list of species codes for a habitat."""
        num_species = self.random_int(min=min_species, max=max_species)
        suitable_species = self.habitat_species_map.get(habitat, self.species_codes)

        # Add some common species that can appear anywhere
        all_species = list(set(suitable_species + ["houspa", "eurbla1", "comcha"]))

        # Sample species
        return self.random_elements(
            elements=all_species,
            length=min(num_species, len(all_species)),
            unique=True
        )

    def checklist_protocol(self) -> tuple:
        """Generate a birding protocol (code, name)."""
        return self.random_element(self.protocols)

    def checklist_protocol_code(self) -> str:
        """Generate a birding protocol code."""
        return self.random_element([p[0] for p in self.protocols])

    def checklist_duration(self, protocol_code: str = None) -> int:
        """
        Generate a realistic checklist duration in minutes.

        Stationary counts tend to be shorter, traveling counts longer.
        """
        if protocol_code == "P21":  # Stationary
            return self.random_int(min=15, max=120)
        elif protocol_code == "P22":  # Traveling
            return self.random_int(min=30, max=300)
        else:
            return self.random_int(min=15, max=180)

    def checklist_distance(self, protocol_code: str = None) -> float:
        """
        Generate a traveling distance in kilometers.

        Only applicable for traveling protocol (P22).
        """
        if protocol_code == "P22":
            return round(random.uniform(0.5, 10.0), 2)
        return None

    def observation_has_media(self) -> Dict[str, bool]:
        """Generate media availability flags with realistic probabilities."""
        return {
            "photo": random.random() < 0.15,  # 15% chance
            "audio": random.random() < 0.08,  # 8% chance
            "video": random.random() < 0.03,  # 3% chance
        }


class LocationProvider(BaseProvider):
    """Faker provider for Portuguese location data."""

    # Portuguese districts
    states = [
        ("PT-01", "Aveiro"),
        ("PT-02", "Beja"),
        ("PT-03", "Braga"),
        ("PT-04", "Bragança"),
        ("PT-06", "Coimbra"),
        ("PT-07", "Évora"),
        ("PT-08", "Faro"),
        ("PT-11", "Lisboa"),
        ("PT-13", "Porto"),
        ("PT-14", "Santarém"),
        ("PT-15", "Setúbal"),
        ("PT-16", "Viana do Castelo"),
        ("PT-18", "Viseu"),
    ]

    # Sample location names by type
    coastal_locations = [
        "Praia da Rocha", "Praia da Barra", "Praia do Norte",
        "Costa Nova", "Praia de Carcavelos", "Praia da Nazaré"
    ]

    wetland_locations = [
        "Ria de Aveiro", "Ria Formosa", "Tagus Estuary",
        "Sado Estuary", "Paul do Boquilobo", "Lagoa de Óbidos"
    ]

    park_locations = [
        "City Park", "Municipal Garden", "Botanical Garden",
        "Eduardo VII Park", "Parque da Cidade"
    ]

    def portuguese_state(self) -> tuple:
        """Generate a Portuguese state (code, name)."""
        return self.random_element(self.states)

    def portuguese_state_code(self) -> str:
        """Generate a Portuguese state code."""
        return self.random_element([s[0] for s in self.states])

    def portuguese_state_name(self) -> str:
        """Generate a Portuguese state name."""
        return self.random_element([s[1] for s in self.states])

    def location_name(self, habitat: str = None) -> str:
        """Generate a location name, optionally for a specific habitat."""
        if habitat == "coastal" or habitat == "coastal_wetland":
            return self.random_element(self.coastal_locations + self.wetland_locations)
        elif habitat == "wetland":
            return self.random_element(self.wetland_locations)
        elif habitat == "urban":
            return self.random_element(self.park_locations)
        else:
            # Generate a generic location name
            prefixes = ["Parque", "Reserva", "Quinta", "Monte", "Serra", "Vale"]
            suffixes = ["Natural", "das Aves", "Verde", "do Norte", "do Sul"]
            return f"{self.random_element(prefixes)} {self.random_element(suffixes)}"

    def portugal_coordinates(self) -> tuple:
        """
        Generate coordinates within Portugal.

        Returns (latitude, longitude) tuple.
        Portugal bounds: approximately 37°N to 42°N, 9.5°W to 6°W
        """
        latitude = round(random.uniform(37.0, 42.0), 6)
        longitude = round(random.uniform(-9.5, -6.0), 6)
        return (latitude, longitude)

    def location_is_hotspot(self) -> bool:
        """Determine if a location is a hotspot (30% chance)."""
        return random.random() < 0.3


class ObserverProvider(BaseProvider):
    """Faker provider for bird observer data."""

    # Common Portuguese first names
    first_names = [
        "Maria", "João", "Ana", "Pedro", "Sofia", "Carlos",
        "Rita", "Miguel", "Beatriz", "Tiago", "Inês", "Rui",
        "Catarina", "Francisco", "Mariana", "Luís", "Teresa",
        "António", "Isabel", "José"
    ]

    # Common Portuguese surnames
    surnames = [
        "Silva", "Santos", "Costa", "Oliveira", "Rodrigues",
        "Ferreira", "Pereira", "Martins", "Carvalho", "Almeida",
        "Sousa", "Ribeiro", "Fernandes", "Lopes", "Gonçalves"
    ]

    experience_levels = ["beginner", "intermediate", "experienced", "expert"]

    def observer_name(self) -> str:
        """Generate a Portuguese observer name."""
        first = self.random_element(self.first_names)
        last = self.random_element(self.surnames)
        return f"{first} {last}"

    def observer_identifier(self) -> str:
        """Generate an observer identifier."""
        return f"OBS{self.random_int(min=1000, max=9999):04d}"

    def observer_experience_level(self) -> str:
        """Generate an observer experience level."""
        return self.random_element(self.experience_levels)

    def checklist_params_for_experience(self, experience: str) -> Dict:
        """
        Generate realistic checklist parameters based on observer experience.

        Returns dict with duration_range, species_count_range.
        """
        if experience == "expert":
            return {
                "duration_range": (120, 300),
                "species_count_range": (15, 30),
            }
        elif experience == "experienced":
            return {
                "duration_range": (90, 180),
                "species_count_range": (10, 20),
            }
        elif experience == "intermediate":
            return {
                "duration_range": (60, 120),
                "species_count_range": (5, 15),
            }
        else:  # beginner
            return {
                "duration_range": (30, 90),
                "species_count_range": (3, 10),
            }
