"""
FactoryBoy factories for eBird API data models.

These factories provide an easy way to create test data with realistic,
contextually appropriate values using Faker providers.

Usage:
    from ebird.api.data.factories import ChecklistFactory, ObservationFactory

    # Create a single checklist with observations
    checklist = ChecklistFactory()

    # Create multiple checklists
    checklists = ChecklistFactory.create_batch(10)

    # Create checklist with specific location
    checklist = ChecklistFactory(location__name="Ria de Aveiro")

    # Create observation with specific species
    observation = ObservationFactory(species__species_code="houspa")
"""

import factory
from factory import fuzzy
from factory.django import DjangoModelFactory
from faker import Faker

from ebird.api.data.models import (
    Country,
    State,
    County,
    Location,
    Species,
    Observer,
    Checklist,
    Observation,
)
from ebird.api.data.faker_providers import (
    BirdProvider,
    LocationProvider,
    ObserverProvider,
)

# Initialize Faker with custom providers
fake = Faker()
fake.add_provider(BirdProvider)
fake.add_provider(LocationProvider)
fake.add_provider(ObserverProvider)


class CountryFactory(DjangoModelFactory):
    """Factory for Country model."""

    class Meta:
        model = Country
        django_get_or_create = ("code",)

    code = "PT"
    name = "Portugal"
    place = "PT"


class StateFactory(DjangoModelFactory):
    """Factory for State model."""

    class Meta:
        model = State
        django_get_or_create = ("code",)

    code = factory.LazyFunction(lambda: fake.portuguese_state_code())
    name = factory.LazyAttribute(lambda obj: fake.portuguese_state_name())
    place = factory.LazyAttribute(lambda obj: f"PT, {obj.name}")


class CountyFactory(DjangoModelFactory):
    """Factory for County model."""

    class Meta:
        model = County

    code = factory.Sequence(lambda n: f"PT-{n:02d}-CTY")
    name = factory.Faker("city", locale="pt_PT")
    place = factory.LazyAttribute(lambda obj: f"PT, {obj.name}")


class LocationFactory(DjangoModelFactory):
    """Factory for Location model."""

    class Meta:
        model = Location

    identifier = factory.Sequence(lambda n: f"L{n:06d}")
    original = factory.LazyFunction(lambda: fake.location_name())
    name = factory.LazyAttribute(lambda obj: obj.original)

    country = factory.SubFactory(CountryFactory)
    state = factory.SubFactory(StateFactory)
    county = factory.SubFactory(CountyFactory)

    latitude = factory.LazyFunction(lambda: fake.portugal_coordinates()[0])
    longitude = factory.LazyFunction(lambda: fake.portugal_coordinates()[1])

    url = factory.LazyAttribute(
        lambda obj: f"https://ebird.org/hotspot/{obj.identifier}" if obj.hotspot else ""
    )
    hotspot = factory.LazyFunction(lambda: fake.location_is_hotspot())

    data = factory.LazyFunction(lambda: {"habitat": fake.bird_habitat()})


class SpeciesFactory(DjangoModelFactory):
    """Factory for Species model."""

    class Meta:
        model = Species
        django_get_or_create = ("species_code",)

    species_code = factory.LazyFunction(lambda: fake.bird_species_code())
    taxon_order = factory.Faker("random_int", min=1, max=5000)
    order = "Passeriformes"
    category = "species"
    family_code = factory.Faker("word")

    common_name = factory.LazyAttribute(
        lambda obj: f'{{"en": "{fake.bird_species_name(obj.species_code)}"}}'
    )
    scientific_name = factory.Faker("sentence", nb_words=2)

    family_common_name = factory.LazyAttribute(
        lambda obj: f'{{"en": "{obj.family_code.title()}"}}'
    )
    family_scientific_name = ""

    data = factory.Dict({"habitats": factory.List([factory.LazyFunction(lambda: fake.bird_habitat())])})


class ObserverFactory(DjangoModelFactory):
    """Factory for Observer model."""

    class Meta:
        model = Observer

    identifier = factory.LazyFunction(lambda: fake.observer_identifier())
    name = factory.LazyFunction(lambda: fake.observer_name())
    original = factory.LazyAttribute(lambda obj: obj.name)
    enabled = True

    data = factory.LazyFunction(
        lambda: {"experience": fake.observer_experience_level()}
    )


class ChecklistFactory(DjangoModelFactory):
    """
    Factory for Checklist model.

    Creates realistic checklists with appropriate effort metrics based on protocol.
    """

    class Meta:
        model = Checklist

    identifier = factory.Sequence(lambda n: f"S{n:08d}")

    # Timestamps
    added = factory.Faker("date_time_this_year", tzinfo=None)
    edited = factory.LazyAttribute(lambda obj: obj.added)

    # Relationships
    country = factory.SubFactory(CountryFactory)
    state = factory.SubFactory(StateFactory)
    county = factory.SubFactory(CountyFactory)
    location = factory.SubFactory(LocationFactory)
    observer = factory.SubFactory(ObserverFactory)

    # Counts (will be set by post_generation for observations)
    observer_count = 1
    species_count = factory.Faker("random_int", min=3, max=20)

    # Date/Time
    date = factory.LazyAttribute(lambda obj: obj.started.date() if obj.started else fake.date_this_year())
    time = factory.LazyAttribute(lambda obj: obj.started.time() if obj.started else fake.time())
    started = factory.Faker("date_time_this_year", tzinfo=None)

    # Protocol and effort
    protocol_code = factory.LazyFunction(lambda: fake.checklist_protocol_code())
    project_code = "EBIRD"

    duration = factory.LazyAttribute(
        lambda obj: fake.checklist_duration(obj.protocol_code)
    )
    distance = factory.LazyAttribute(
        lambda obj: fake.checklist_distance(obj.protocol_code)
    )
    area = None

    complete = True
    comments = ""

    url = factory.LazyAttribute(
        lambda obj: f"https://ebird.org/checklist/{obj.identifier}"
    )

    data = factory.Dict({})

    @factory.post_generation
    def with_observations(self, create, extracted, **kwargs):
        """
        Post-generation hook to create observations for the checklist.

        Usage:
            ChecklistFactory(with_observations=5)  # Creates 5 observations
            ChecklistFactory(with_observations=True)  # Creates 3-10 observations
        """
        if not create:
            return

        if extracted:
            # If boolean True, create random number of observations
            if extracted is True:
                num_observations = fake.random_int(min=3, max=10)
            else:
                num_observations = extracted

            # Get habitat from location
            habitat = self.location.data.get("habitat", "urban")

            # Get appropriate species for habitat
            species_codes = fake.bird_species_list_for_habitat(
                habitat, min_species=num_observations, max_species=num_observations
            )

            for species_code in species_codes:
                species, _ = Species.objects.get_or_create(
                    species_code=species_code,
                    defaults={
                        "common_name": f'{{"en": "{fake.bird_species_name(species_code)}"}}',
                        "scientific_name": f"Species {species_code}",
                        "taxon_order": fake.random_int(min=1, max=5000),
                        "order": "Passeriformes",
                        "category": "species",
                        "family_code": "family1",
                    }
                )

                ObservationFactory(
                    checklist=self,
                    species=species,
                    observer=self.observer,
                    country=self.country,
                    state=self.state,
                    county=self.county,
                    location=self.location,
                    date=self.date,
                    time=self.time,
                    started=self.started,
                )

            # Update species count
            self.species_count = num_observations
            self.save()


class ObservationFactory(DjangoModelFactory):
    """
    Factory for Observation model.

    Creates realistic observations with appropriate counts and media flags.
    """

    class Meta:
        model = Observation

    identifier = factory.Sequence(lambda n: f"OBS{n:09d}")

    # Timestamps
    edited = factory.Faker("date_time_this_year", tzinfo=None)

    # Relationships
    checklist = factory.SubFactory(ChecklistFactory)
    species = factory.SubFactory(SpeciesFactory)
    observer = factory.SubFactory(ObserverFactory)

    country = factory.LazyAttribute(lambda obj: obj.checklist.country)
    state = factory.LazyAttribute(lambda obj: obj.checklist.state)
    county = factory.LazyAttribute(lambda obj: obj.checklist.county)
    location = factory.LazyAttribute(lambda obj: obj.checklist.location)

    # Date/Time (inherit from checklist)
    date = factory.LazyAttribute(lambda obj: obj.checklist.date)
    time = factory.LazyAttribute(lambda obj: obj.checklist.time)
    started = factory.LazyAttribute(lambda obj: obj.checklist.started)

    # Count based on species
    count = factory.LazyAttribute(
        lambda obj: fake.bird_count(obj.species.species_code)
    )

    # Media flags (realistic probabilities)
    audio = factory.LazyFunction(lambda: fake.observation_has_media()["audio"])
    photo = factory.LazyFunction(lambda: fake.observation_has_media()["photo"])
    video = factory.LazyFunction(lambda: fake.observation_has_media()["video"])

    approved = True
    reason = ""
    comments = ""

    urn = factory.LazyAttribute(lambda obj: f"urn:observation:{obj.identifier}")

    data = factory.Dict({})


# Convenience functions for common scenarios

def create_coastal_checklist(**kwargs):
    """Create a checklist at a coastal location with appropriate species."""
    location = LocationFactory(data={"habitat": "coastal"})
    checklist = ChecklistFactory(
        location=location,
        with_observations=True,
        **kwargs
    )
    return checklist


def create_wetland_checklist(**kwargs):
    """Create a checklist at a wetland location with appropriate species."""
    location = LocationFactory(data={"habitat": "coastal_wetland"})
    checklist = ChecklistFactory(
        location=location,
        with_observations=True,
        **kwargs
    )
    return checklist


def create_urban_checklist(**kwargs):
    """Create a checklist at an urban location with appropriate species."""
    location = LocationFactory(data={"habitat": "urban"})
    checklist = ChecklistFactory(
        location=location,
        with_observations=True,
        **kwargs
    )
    return checklist


def create_grassland_checklist(**kwargs):
    """Create a checklist at a grassland location with steppe specialists."""
    location = LocationFactory(data={"habitat": "grassland"})
    checklist = ChecklistFactory(
        location=location,
        with_observations=True,
        **kwargs
    )
    return checklist


def create_expert_observer_checklist(**kwargs):
    """Create a checklist by an expert observer with many species."""
    observer = ObserverFactory(data={"experience": "expert"})
    checklist = ChecklistFactory(
        observer=observer,
        duration=fuzzy.FuzzyInteger(120, 300).fuzz(),
        species_count=fuzzy.FuzzyInteger(15, 30).fuzz(),
        with_observations=fuzzy.FuzzyInteger(15, 30).fuzz(),
        **kwargs
    )
    return checklist


def create_beginner_observer_checklist(**kwargs):
    """Create a checklist by a beginner observer with fewer species."""
    observer = ObserverFactory(data={"experience": "beginner"})
    checklist = ChecklistFactory(
        observer=observer,
        duration=fuzzy.FuzzyInteger(30, 90).fuzz(),
        species_count=fuzzy.FuzzyInteger(3, 8).fuzz(),
        with_observations=fuzzy.FuzzyInteger(3, 8).fuzz(),
        **kwargs
    )
    return checklist
