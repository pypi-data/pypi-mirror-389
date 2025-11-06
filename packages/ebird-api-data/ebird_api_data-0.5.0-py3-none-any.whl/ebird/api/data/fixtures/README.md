# eBird API Data Fixtures and Factories

This directory contains comprehensive test data for Portuguese bird observations and factories for generating additional test data.

## Contents

### Fixture Data

**`portugal_observations.json`** - Complete dataset of Portuguese bird observations including:
- 1 Country (Portugal)
- 13 States (Portuguese districts)
- 18 Counties
- 30 Locations (covering diverse habitats: coastal, wetland, woodland, grassland, urban, mountain)
- 58 Bird Species (representative of Portuguese avifauna)
- 6 Observers (varying experience levels)
- 395 Checklists
- 4,507 Observations

### Generator Script

**`generate_portugal_data.py`** - Python script that generates the fixture data. You can modify and re-run it to create customized datasets:

```bash
python src/ebird/api/data/fixtures/generate_portugal_data.py > custom_data.json
```

### Factories

**`../factories.py`** - FactoryBoy factories for creating test data programmatically

**`../faker_providers.py`** - Custom Faker providers for realistic bird observation data

## Loading Fixture Data

Load the complete Portuguese dataset into your database:

```bash
python manage.py loaddata src/ebird/api/data/fixtures/portugal_observations.json
```

Or if you're in the Django app directory:

```bash
python manage.py loaddata portugal_observations.json
```

This will populate your database with a complete, realistic dataset of Portuguese bird observations.

## Using FactoryBoy Factories

The factories provide an easy way to create test data programmatically in your tests.

### Basic Usage

```python
from ebird.api.data.factories import (
    ChecklistFactory,
    ObservationFactory,
    LocationFactory,
    SpeciesFactory,
    ObserverFactory,
)

# Create a single checklist
checklist = ChecklistFactory()

# Create multiple checklists
checklists = ChecklistFactory.create_batch(10)

# Create a checklist with observations
checklist = ChecklistFactory(with_observations=5)

# Create observation with specific species
observation = ObservationFactory(species__species_code="houspa")
```

### Habitat-Specific Checklists

```python
from ebird.api.data.factories import (
    create_coastal_checklist,
    create_wetland_checklist,
    create_urban_checklist,
    create_grassland_checklist,
)

# Create checklist at coastal location with appropriate seabirds
coastal = create_coastal_checklist()

# Create checklist at wetland with herons, egrets, etc.
wetland = create_wetland_checklist()

# Create checklist in urban park with common species
urban = create_urban_checklist()

# Create checklist in grassland with steppe specialists
grassland = create_grassland_checklist()
```

### Observer Experience Levels

```python
from ebird.api.data.factories import (
    create_expert_observer_checklist,
    create_beginner_observer_checklist,
)

# Expert observer - sees many species, long duration
expert_checklist = create_expert_observer_checklist()
# Will have 15-30 species, 2-5 hours duration

# Beginner observer - fewer species, shorter duration
beginner_checklist = create_beginner_observer_checklist()
# Will have 3-8 species, 0.5-1.5 hours duration
```

### Advanced Factory Usage

```python
# Create checklist with specific attributes
checklist = ChecklistFactory(
    location__name="Ria de Aveiro",
    location__hotspot=True,
    observer__name="Maria Silva",
    duration=120,
    protocol_code="P22",  # Traveling count
    distance=3.5,
    complete=True,
    with_observations=15
)

# Create observation with media
observation = ObservationFactory(
    species__species_code="grefla2",  # Greater Flamingo
    count=50,
    photo=True,
    audio=False,
    video=False,
)

# Use SubFactory relationships
from ebird.api.data.factories import CountryFactory, StateFactory

country = CountryFactory()
state = StateFactory()
location = LocationFactory(country=country, state=state)
```

## Using Custom Faker Providers

The custom Faker providers can be used independently for generating realistic data:

```python
from faker import Faker
from ebird.api.data.faker_providers import (
    BirdProvider,
    LocationProvider,
    ObserverProvider,
)

fake = Faker()
fake.add_provider(BirdProvider)
fake.add_provider(LocationProvider)
fake.add_provider(ObserverProvider)

# Generate bird data
species_code = fake.bird_species_code()  # e.g., "houspa"
species_name = fake.bird_species_name()  # e.g., "House Sparrow"
count = fake.bird_count("grefla2")  # Realistic count for species
habitat = fake.bird_habitat()  # e.g., "coastal_wetland"

# Generate species list for habitat
species_list = fake.bird_species_list_for_habitat("coastal", min_species=5, max_species=10)

# Generate location data
state_code = fake.portuguese_state_code()  # e.g., "PT-08"
state_name = fake.portuguese_state_name()  # e.g., "Faro"
location_name = fake.location_name("wetland")  # e.g., "Ria Formosa"
lat, lon = fake.portugal_coordinates()  # Within Portugal bounds
is_hotspot = fake.location_is_hotspot()  # Boolean

# Generate observer data
observer_name = fake.observer_name()  # e.g., "João Santos"
observer_id = fake.observer_identifier()  # e.g., "OBS1234"
experience = fake.observer_experience_level()  # e.g., "expert"

# Get parameters for experience level
params = fake.checklist_params_for_experience("expert")
# Returns: {"duration_range": (120, 300), "species_count_range": (15, 30)}

# Generate checklist data
protocol_code = fake.checklist_protocol_code()  # e.g., "P22"
duration = fake.checklist_duration("P22")  # Appropriate for traveling
distance = fake.checklist_distance("P22")  # Only for traveling protocol

# Generate media flags
media = fake.observation_has_media()
# Returns: {"photo": True/False, "audio": True/False, "video": True/False}
```

## Testing Example

Here's a complete example of using factories in a Django test:

```python
from django.test import TestCase
from ebird.api.data.factories import ChecklistFactory, ObservationFactory
from ebird.api.data.models import Checklist, Observation

class ChecklistTestCase(TestCase):
    def test_create_checklist_with_observations(self):
        """Test creating a checklist with multiple observations."""
        # Create a checklist with 10 observations
        checklist = ChecklistFactory(with_observations=10)

        # Verify the checklist was created
        self.assertIsNotNone(checklist.identifier)

        # Verify observations were created
        observations = Observation.objects.filter(checklist=checklist)
        self.assertEqual(observations.count(), 10)
        self.assertEqual(checklist.species_count, 10)

        # All observations should have the same location as checklist
        for obs in observations:
            self.assertEqual(obs.location, checklist.location)
            self.assertEqual(obs.date, checklist.date)

    def test_coastal_habitat_species(self):
        """Test that coastal checklists have appropriate species."""
        from ebird.api.data.factories import create_coastal_checklist

        checklist = create_coastal_checklist()

        # Verify location habitat
        self.assertEqual(checklist.location.data["habitat"], "coastal")

        # Verify we have observations
        observations = checklist.observations.all()
        self.assertGreater(observations.count(), 0)

        # Species should be appropriate for coastal habitat
        # (This assumes your habitat filtering is working)
        for obs in observations:
            self.assertIsNotNone(obs.species)

    def test_observer_experience_affects_species_count(self):
        """Test that expert observers see more species than beginners."""
        from ebird.api.data.factories import (
            create_expert_observer_checklist,
            create_beginner_observer_checklist,
        )

        expert = create_expert_observer_checklist()
        beginner = create_beginner_observer_checklist()

        # Expert should see more species
        self.assertGreater(expert.species_count, beginner.species_count)

        # Expert should spend more time
        self.assertGreater(expert.duration, beginner.duration)
```

## Dataset Characteristics

### Geographic Coverage

The dataset covers 13 Portuguese districts with diverse habitats:
- **Coastal regions**: Aveiro, Faro, Lisboa, Porto, Setúbal, Viana do Castelo
- **Interior/Mediterranean**: Beja, Évora, Santarém
- **Mountain regions**: Bragança, Viseu
- **Mixed**: Braga, Coimbra

### Species Coverage

58 species representing Portuguese avifauna:
- **Seabirds**: Gannets, Shearwaters, Gulls, Terns
- **Waders**: Avocets, Stilts, Plovers, Dunlins
- **Herons & Large Waders**: Herons, Egrets, Flamingos, Spoonbills, Storks
- **Raptors**: Eagles, Vultures, Buzzards, Kestrels
- **Steppe Specialists**: Bustards, Larks
- **Woodland Birds**: Woodpeckers, Jays, Tits, Thrushes
- **Common Species**: Sparrows, Starlings, Finches, Swallows

### Observation Patterns

- **Seasonal distribution**: Observations span the last 6 months
- **Time of day**: Realistic birding hours (6 AM - 6 PM)
- **Protocols**: Mix of Incidental (P20), Stationary (P21), and Traveling (P22)
- **Effort metrics**: Duration 30-300 minutes, distance 0.5-10 km for traveling counts
- **Species counts**: 3-30 species per checklist based on observer experience
- **Individual counts**: Realistic for each species (1-3 for raptors, up to 150 for flamingos)
- **Media**: 15% photos, 8% audio, 3% video (realistic ratios)

## Customization

### Modifying the Generator Script

Edit `generate_portugal_data.py` to customize:
- Add more states, counties, or locations
- Adjust species list
- Change observation patterns (dates, times, protocols)
- Modify observer behavior

After editing, regenerate the fixture:

```bash
python src/ebird/api/data/fixtures/generate_portugal_data.py > custom_fixtures.json
```

### Extending Faker Providers

Add new methods to the Faker providers in `faker_providers.py`:

```python
class BirdProvider(BaseProvider):
    def rare_species_code(self):
        """Generate a code for a rare species."""
        rare_species = ["boneag1", "spaeag", "grebta"]
        return self.random_element(rare_species)
```

### Creating New Factories

Create specialized factories for your needs:

```python
class RareSpeciesObservationFactory(ObservationFactory):
    """Factory for rare species observations."""

    species = factory.LazyFunction(
        lambda: SpeciesFactory(species_code=fake.rare_species_code())
    )
    approved = True  # Rare species need review
    comments = "Rare sighting, well documented"
    photo = True  # Documentation required
```

## Requirements

To use the factories and Faker providers, install:

```bash
pip install factory-boy faker
```

These should be added to your test requirements or development dependencies.

## See Also

- [Model Documentation](../models/models.md) - Detailed description of all models
- [Django Fixtures Documentation](https://docs.djangoproject.com/en/stable/howto/initial-data/)
- [FactoryBoy Documentation](https://factoryboy.readthedocs.io/)
- [Faker Documentation](https://faker.readthedocs.io/)
