#!/usr/bin/env python
"""
Generate realistic Portuguese bird observation data for eBird API application.

This script creates a comprehensive dataset including geographic hierarchy,
species, observers, checklists, and observations for Portugal.

Usage:
    python generate_portugal_data.py > portugal_observations.json
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Portuguese States (Districts) with their codes
STATES = [
    ("PT-01", "Aveiro", "PT, Aveiro"),
    ("PT-02", "Beja", "PT, Beja"),
    ("PT-03", "Braga", "PT, Braga"),
    ("PT-04", "Bragança", "PT, Bragança"),
    ("PT-06", "Coimbra", "PT, Coimbra"),
    ("PT-07", "Évora", "PT, Évora"),
    ("PT-08", "Faro", "PT, Faro"),
    ("PT-11", "Lisboa", "PT, Lisboa"),
    ("PT-13", "Porto", "PT, Porto"),
    ("PT-14", "Santarém", "PT, Santarém"),
    ("PT-15", "Setúbal", "PT, Setúbal"),
    ("PT-16", "Viana do Castelo", "PT, Viana do Castelo"),
    ("PT-18", "Viseu", "PT, Viseu"),
]

# Counties for selected states (code, name, state_code, place)
COUNTIES = [
    ("PT-01-AV", "Aveiro", "PT-01", "PT, Aveiro, Aveiro"),
    ("PT-01-OV", "Ovar", "PT-01", "PT, Aveiro, Ovar"),
    ("PT-02-BEJ", "Beja", "PT-02", "PT, Beja, Beja"),
    ("PT-02-OUR", "Ourique", "PT-02", "PT, Beja, Ourique"),
    ("PT-03-BRG", "Braga", "PT-03", "PT, Braga, Braga"),
    ("PT-04-BRN", "Bragança", "PT-04", "PT, Bragança, Bragança"),
    ("PT-06-COI", "Coimbra", "PT-06", "PT, Coimbra, Coimbra"),
    ("PT-07-EVO", "Évora", "PT-07", "PT, Évora, Évora"),
    ("PT-08-FAR", "Faro", "PT-08", "PT, Faro, Faro"),
    ("PT-08-LOL", "Loulé", "PT-08", "PT, Faro, Loulé"),
    ("PT-11-LIS", "Lisboa", "PT-11", "PT, Lisboa, Lisboa"),
    ("PT-11-SIN", "Sintra", "PT-11", "PT, Lisboa, Sintra"),
    ("PT-13-POR", "Porto", "PT-13", "PT, Porto, Porto"),
    ("PT-13-MAI", "Maia", "PT-13", "PT, Porto, Maia"),
    ("PT-14-SAN", "Santarém", "PT-14", "PT, Santarém, Santarém"),
    ("PT-15-SET", "Setúbal", "PT-15", "PT, Setúbal, Setúbal"),
    ("PT-16-VCT", "Viana do Castelo", "PT-16", "PT, Viana do Castelo, Viana do Castelo"),
    ("PT-18-VIS", "Viseu", "PT-18", "PT, Viseu, Viseu"),
]

# Locations with habitat types (id, name, county_code, lat, lon, hotspot, habitat)
LOCATIONS = [
    # Aveiro - Coastal/Wetland
    ("L1001", "Ria de Aveiro", "PT-01-AV", 40.6443, -8.6455, True, "coastal_wetland"),
    ("L1002", "Praia da Barra", "PT-01-AV", 40.6426, -8.7455, True, "coastal"),
    ("L1003", "São Jacinto Dunes", "PT-01-OV", 40.6632, -8.7389, True, "coastal"),

    # Beja - Mediterranean scrubland/farmland
    ("L2001", "Castro Verde Plains", "PT-02-BEJ", 37.7050, -8.0850, True, "grassland"),
    ("L2002", "Baixo Alentejo Farmland", "PT-02-BEJ", 37.9500, -7.8700, False, "farmland"),
    ("L2003", "Ourique Cork Forest", "PT-02-OUR", 37.6550, -8.2900, False, "woodland"),

    # Braga - Mixed/Woodland
    ("L3001", "Peneda-Gerês NP", "PT-03-BRG", 41.7500, -8.1500, True, "mountain"),
    ("L3002", "Braga City Park", "PT-03-BRG", 41.5518, -8.4229, False, "urban"),

    # Bragança - Mountains
    ("L4001", "Montesinho Natural Park", "PT-04-BRN", 41.8500, -6.7500, True, "mountain"),
    ("L4002", "Bragança Reservoir", "PT-04-BRN", 41.8068, -6.7570, False, "wetland"),

    # Coimbra - Mixed
    ("L6001", "Mondego Estuary", "PT-06-COI", 40.1450, -8.8350, True, "coastal_wetland"),
    ("L6002", "Mata Nacional do Choupal", "PT-06-COI", 40.2100, -8.4500, False, "woodland"),

    # Évora - Mediterranean
    ("L7001", "Évora Plains", "PT-07-EVO", 38.5715, -7.9071, False, "grassland"),
    ("L7002", "Évora City Gardens", "PT-07-EVO", 38.5710, -7.9064, False, "urban"),

    # Faro - Coastal/Wetland
    ("L8001", "Ria Formosa", "PT-08-FAR", 37.0194, -7.9322, True, "coastal_wetland"),
    ("L8002", "Quinta do Lago", "PT-08-LOL", 37.0456, -8.0153, True, "coastal_wetland"),
    ("L8003", "Sagres Point", "PT-08-FAR", 37.0083, -8.9483, True, "coastal"),

    # Lisboa - Urban/Coastal
    ("L11001", "Tagus Estuary", "PT-11-LIS", 38.7654, -9.0942, True, "coastal_wetland"),
    ("L11002", "Eduardo VII Park", "PT-11-LIS", 38.7297, -9.1517, False, "urban"),
    ("L11003", "Sintra-Cascais NP", "PT-11-SIN", 38.7869, -9.4500, True, "coastal"),

    # Porto - Urban/Coastal
    ("L13001", "Douro Estuary", "PT-13-POR", 41.1396, -8.6739, True, "coastal"),
    ("L13002", "Parque da Cidade", "PT-13-POR", 41.1626, -8.6764, False, "urban"),
    ("L13003", "Mindelo Beach", "PT-13-MAI", 41.2980, -8.7280, False, "coastal"),

    # Santarém - Mixed
    ("L14001", "Paul do Boquilobo", "PT-14-SAN", 39.3950, -8.5450, True, "wetland"),
    ("L14002", "Tagus Valley", "PT-14-SAN", 39.2367, -8.6850, False, "farmland"),

    # Setúbal - Coastal
    ("L15001", "Sado Estuary", "PT-15-SET", 38.4750, -8.8150, True, "coastal_wetland"),
    ("L15002", "Arrábida Natural Park", "PT-15-SET", 38.4650, -8.9900, True, "coastal"),

    # Viana do Castelo - Coastal
    ("L16001", "Lima Estuary", "PT-16-VCT", 41.6917, -8.8367, True, "coastal_wetland"),

    # Viseu - Mountain/Woodland
    ("L18001", "Serra da Estrela", "PT-18-VIS", 40.3250, -7.6100, True, "mountain"),
    ("L18002", "Viseu City Gardens", "PT-18-VIS", 40.6569, -7.9139, False, "urban"),
]

# Portuguese bird species (code, common_name, scientific_name, family_code, order, category, taxon_order, habitats)
SPECIES = [
    # Seabirds & Coastal
    ("norgat3", '{"en": "Northern Gannet"}', "Morus bassanus", "sulid1", "Suliformes", "species", 470, ["coastal"]),
    ("cooshe1", '{"en": "Cory\'s Shearwater"}', "Calonectris borealis", "proce1", "Procellariiformes", "species", 90, ["coastal"]),
    ("yelgul", '{"en": "Yellow-legged Gull"}', "Larus michahellis", "larid1", "Charadriiformes", "species", 1430, ["coastal", "urban"]),
    ("blkgul2", '{"en": "Lesser Black-backed Gull"}', "Larus fuscus", "larid1", "Charadriiformes", "species", 1420, ["coastal"]),
    ("comter", '{"en": "Common Tern"}', "Sterna hirundo", "larid1", "Charadriiformes", "species", 1520, ["coastal_wetland"]),
    ("lesste", '{"en": "Little Tern"}', "Sternula albifrons", "larid1", "Charadriiformes", "species", 1530, ["coastal"]),
    ("greshe", '{"en": "Great Shearwater"}', "Ardenna gravis", "proce1", "Procellariiformes", "species", 100, ["coastal"]),

    # Waders
    ("pieavo", '{"en": "Pied Avocet"}', "Recurvirostra avosetta", "recur1", "Charadriiformes", "species", 1260, ["coastal_wetland"]),
    ("blkwis", '{"en": "Black-winged Stilt"}', "Himantopus himantopus", "recur1", "Charadriiformes", "species", 1250, ["coastal_wetland", "wetland"]),
    ("litrin", '{"en": "Little Ringed Plover"}', "Charadrius dubius", "charad1", "Charadriiformes", "species", 1310, ["coastal_wetland", "wetland"]),
    ("kensan", '{"en": "Kentish Plover"}', "Charadrius alexandrinus", "charad1", "Charadriiformes", "species", 1320, ["coastal"]),
    ("dunlin", '{"en": "Dunlin"}', "Calidris alpina", "scolo1", "Charadriiformes", "species", 1390, ["coastal_wetland"]),
    ("comshe1", '{"en": "Common Shelduck"}', "Tadorna tadorna", "anatid1", "Anseriformes", "species", 210, ["coastal_wetland"]),

    # Herons & Egrets
    ("greheg", '{"en": "Grey Heron"}', "Ardea cinerea", "arde1", "Pelecaniformes", "species", 490, ["coastal_wetland", "wetland"]),
    ("purher", '{"en": "Purple Heron"}', "Ardea purpurea", "arde1", "Pelecaniformes", "species", 500, ["wetland"]),
    ("litegg", '{"en": "Little Egret"}', "Egretta garzetta", "arde1", "Pelecaniformes", "species", 520, ["coastal_wetland", "wetland"]),
    ("greegg", '{"en": "Great Egret"}', "Ardea alba", "arde1", "Pelecaniformes", "species", 510, ["coastal_wetland", "wetland"]),
    ("squshe", '{"en": "Squacco Heron"}', "Ardeola ralloides", "arde1", "Pelecaniformes", "species", 530, ["wetland"]),

    # Flamingos & Large waders
    ("grefla2", '{"en": "Greater Flamingo"}', "Phoenicopterus roseus", "phoeni1", "Phoenicopteriformes", "species", 590, ["coastal_wetland"]),
    ("eurspo", '{"en": "Eurasian Spoonbill"}', "Platalea leucorodia", "thres1", "Pelecaniformes", "species", 570, ["coastal_wetland", "wetland"]),
    ("whisto", '{"en": "White Stork"}', "Ciconia ciconia", "cico1", "Ciconiiformes", "species", 600, ["farmland", "grassland", "urban"]),
    ("blasto1", '{"en": "Black Stork"}', "Ciconia nigra", "cico1", "Ciconiiformes", "species", 610, ["wetland", "woodland"]),

    # Raptors
    ("boneag1", '{"en": "Bonelli\'s Eagle"}', "Aquila fasciata", "acc1", "Accipitriformes", "species", 850, ["mountain", "grassland"]),
    ("grifvo", '{"en": "Griffon Vulture"}', "Gyps fulvus", "acc1", "Accipitriformes", "species", 710, ["mountain", "grassland"]),
    ("egyvul", '{"en": "Egyptian Vulture"}', "Neophron percnopterus", "acc1", "Accipitriformes", "species", 700, ["mountain", "grassland"]),
    ("spaeag", '{"en": "Spanish Imperial Eagle"}', "Aquila adalberti", "acc1", "Accipitriformes", "species", 840, ["woodland", "grassland"]),
    ("commbu", '{"en": "Common Buzzard"}', "Buteo buteo", "acc1", "Accipitriformes", "species", 900, ["woodland", "farmland", "grassland"]),
    ("comspo1", '{"en": "Common Kestrel"}', "Falco tinnunculus", "falco1", "Falconiformes", "species", 1080, ["urban", "farmland", "grassland"]),
    ("blakil", '{"en": "Black Kite"}', "Milvus migrans", "acc1", "Accipitriformes", "species", 780, ["wetland", "farmland"]),

    # Steppe/Grassland specialists
    ("litbus", '{"en": "Little Bustard"}', "Tetrax tetrax", "otid1", "Otidiformes", "species", 1210, ["grassland"]),
    ("grebta", '{"en": "Great Bustard"}', "Otis tarda", "otid1", "Otidiformes", "species", 1200, ["grassland"]),
    ("calshe", '{"en": "Calandra Lark"}', "Melanocorypha calandra", "alaud1", "Passeriformes", "species", 2890, ["grassland", "farmland"]),
    ("theshe", '{"en": "Thekla Lark"}', "Galerida theklae", "alaud1", "Passeriformes", "species", 2910, ["grassland", "farmland"]),
    ("lasser", '{"en": "Lesser Short-toed Lark"}', "Calandrella rufescens", "alaud1", "Passeriformes", "species", 2900, ["grassland"]),

    # Woodland birds
    ("grespo", '{"en": "Great Spotted Woodpecker"}', "Dendrocopos major", "picid1", "Piciformes", "species", 2050, ["woodland"]),
    ("ibewoo", '{"en": "Iberian Green Woodpecker"}', "Picus sharpei", "picid1", "Piciformes", "species", 2030, ["woodland"]),
    ("eurhoo", '{"en": "Eurasian Hoopoe"}', "Upupa epops", "upu1", "Bucerotiformes", "species", 2100, ["farmland", "woodland"]),
    ("eurjay1", '{"en": "Eurasian Jay"}', "Garrulus glandarius", "corvid1", "Passeriformes", "species", 4350, ["woodland"]),
    ("azuwin", '{"en": "Azure-winged Magpie"}', "Cyanopica cooki", "corvid1", "Passeriformes", "species", 4340, ["woodland", "farmland"]),
    ("eurbla1", '{"en": "European Blackbird"}', "Turdus merula", "turdid1", "Passeriformes", "species", 3450, ["woodland", "urban", "farmland"]),
    ("songthr", '{"en": "Song Thrush"}', "Turdus philomelos", "turdid1", "Passeriformes", "species", 3460, ["woodland", "urban"]),
    ("euirob", '{"en": "European Robin"}', "Erithacus rubecula", "musci1", "Passeriformes", "species", 3090, ["woodland", "urban"]),
    ("comblu1", '{"en": "Common Nightingale"}', "Luscinia megarhynchos", "musci1", "Passeriformes", "species", 3120, ["woodland"]),
    ("blucap1", '{"en": "Blue Tit"}', "Cyanistes caeruleus", "parid1", "Passeriformes", "species", 3800, ["woodland", "urban"]),
    ("gretit1", '{"en": "Great Tit"}', "Parus major", "parid1", "Passeriformes", "species", 3810, ["woodland", "urban"]),

    # Common/Urban birds
    ("houspa", '{"en": "House Sparrow"}', "Passer domesticus", "passe1", "Passeriformes", "species", 4180, ["urban", "farmland"]),
    ("spaspa", '{"en": "Spanish Sparrow"}', "Passer hispaniolensis", "passe1", "Passeriformes", "species", 4190, ["farmland", "urban"]),
    ("comsta", '{"en": "Common Starling"}', "Sturnus vulgaris", "sturn1", "Passeriformes", "species", 4260, ["urban", "farmland"]),
    ("spotsta", '{"en": "Spotless Starling"}', "Sturnus unicolor", "sturn1", "Passeriformes", "species", 4270, ["urban", "farmland"]),
    ("whiwag", '{"en": "White Wagtail"}', "Motacilla alba", "mota1", "Passeriformes", "species", 4140, ["urban", "wetland"]),
    ("eurgol", '{"en": "European Goldfinch"}', "Carduelis carduelis", "fringi1", "Passeriformes", "species", 4630, ["farmland", "urban"]),
    ("eurgre", '{"en": "European Greenfinch"}', "Chloris chloris", "fringi1", "Passeriformes", "species", 4600, ["farmland", "urban"]),
    ("linsco", '{"en": "Common Linnet"}', "Linaria cannabina", "fringi1", "Passeriformes", "species", 4660, ["farmland", "grassland"]),
    ("comcha", '{"en": "Common Chaffinch"}', "Fringilla coelebs", "fringi1", "Passeriformes", "species", 4540, ["woodland", "urban", "farmland"]),
    ("sersco", '{"en": "Serin"}', "Serinus serinus", "fringi1", "Passeriformes", "species", 4590, ["urban", "farmland"]),
    ("barswa", '{"en": "Barn Swallow"}', "Hirundo rustica", "hirun1", "Passeriformes", "species", 3020, ["farmland", "urban"]),
    ("comswi", '{"en": "Common Swift"}', "Apus apus", "apod1", "Apodiformes", "species", 1880, ["urban"]),
    ("eurbee", '{"en": "European Bee-eater"}', "Merops apiaster", "mero1", "Coraciiformes", "species", 2110, ["farmland", "grassland"]),
]

# Observers (id, name, multiple, enabled)
OBSERVERS = [
    ("OBS001", "Maria Silva", False, True),
    ("OBS002", "João Santos", False, True),
    ("OBS003", "Ana Costa", False, True),
    ("OBS004", "Pedro Oliveira", False, True),
    ("OBS005", "Sofia Rodrigues", False, True),
    ("OBS006", "Carlos Ferreira", False, True),
]

# Observer experience levels (affects species counts)
OBSERVER_EXPERIENCE = {
    "OBS001": "expert",      # Sees many species, long duration
    "OBS002": "experienced", # Good species counts
    "OBS003": "intermediate",# Average species counts
    "OBS004": "beginner",    # Fewer species
    "OBS005": "expert",      # Sees many species
    "OBS006": "intermediate",# Average species counts
}


def generate_country():
    """Generate Portugal country data."""
    return {
        "model": "data.Country",
        "pk": "PT",
        "fields": {
            "name": "Portugal",
            "place": "PT",
            "created": "2024-01-01T00:00:00Z",
            "modified": "2024-01-01T00:00:00Z",
        }
    }


def generate_states():
    """Generate Portuguese states data."""
    return [
        {
            "model": "data.State",
            "pk": code,
            "fields": {
                "name": name,
                "place": place,
                "created": "2024-01-01T00:00:00Z",
                "modified": "2024-01-01T00:00:00Z",
            }
        }
        for code, name, place in STATES
    ]


def generate_counties():
    """Generate Portuguese counties data."""
    return [
        {
            "model": "data.County",
            "pk": code,
            "fields": {
                "name": name,
                "place": place,
                "created": "2024-01-01T00:00:00Z",
                "modified": "2024-01-01T00:00:00Z",
            }
        }
        for code, name, state_code, place in COUNTIES
    ]


def generate_locations():
    """Generate location data."""
    locations = []
    for loc_id, name, county_code, lat, lon, hotspot, habitat in LOCATIONS:
        # Find state from county
        county = next(c for c in COUNTIES if c[0] == county_code)
        state_code = county[1]

        locations.append({
            "model": "data.Location",
            "pk": loc_id,
            "fields": {
                "original": name,
                "name": name,
                "country_id": "PT",
                "state_id": state_code,
                "county_id": county_code,
                "latitude": str(lat),
                "longitude": str(lon),
                "url": f"https://ebird.org/hotspot/{loc_id}" if hotspot else "",
                "hotspot": hotspot,
                "data": {"habitat": habitat},
                "created": "2024-01-01T00:00:00Z",
                "modified": "2024-01-01T00:00:00Z",
            }
        })
    return locations


def generate_species():
    """Generate species data."""
    return [
        {
            "model": "data.Species",
            "pk": code,
            "fields": {
                "taxon_order": taxon_order,
                "order": order,
                "category": category,
                "family_code": family_code,
                "common_name": common_name,
                "scientific_name": scientific_name,
                "family_common_name": '{"en": "' + family_code.title() + '"}',
                "family_scientific_name": "",
                "data": {"habitats": habitats},
                "created": "2024-01-01T00:00:00Z",
                "modified": "2024-01-01T00:00:00Z",
            }
        }
        for code, common_name, scientific_name, family_code, order, category, taxon_order, habitats in SPECIES
    ]


def generate_observers():
    """Generate observer data."""
    return [
        {
            "model": "data.Observer",
            "pk": obs_id,
            "fields": {
                "name": name,
                "original": name,
                "enabled": enabled,
                "data": {},
                "created": "2024-01-01T00:00:00Z",
                "modified": "2024-01-01T00:00:00Z",
            }
        }
        for obs_id, name, enabled in OBSERVERS
    ]


def get_habitat_species(habitat: str, max_species: int) -> List[str]:
    """Get species codes appropriate for a habitat."""
    # Filter species by habitat
    suitable_species = [
        code for code, _, _, _, _, _, _, habitats in SPECIES
        if habitat in habitats
    ]

    # Always include some common species
    common_species = ["houspa", "eurbla1", "whiwag", "comcha", "gretit1"]
    suitable_species.extend([s for s in common_species if s not in suitable_species])

    # Randomly select species
    num_species = min(max_species, len(suitable_species))
    return random.sample(suitable_species, num_species)


def generate_checklists_and_observations():
    """Generate realistic checklists and observations."""
    checklists = []
    observations = []
    checklist_counter = 1
    obs_counter = 1

    # Generate checklists for each location
    for loc_id, loc_name, county_code, lat, lon, hotspot, habitat in LOCATIONS:
        # Find geographic hierarchy
        county = next(c for c in COUNTIES if c[0] == county_code)
        state_code = county[1]

        # Generate 10-15 checklists per location
        num_checklists = random.randint(10, 15)

        for _ in range(num_checklists):
            # Random date in the last 6 months
            days_ago = random.randint(0, 180)
            date = datetime.now() - timedelta(days=days_ago)
            hour = random.randint(6, 18)  # Birding time
            minute = random.randint(0, 59)
            time_str = f"{hour:02d}:{minute:02d}:00"
            started = date.replace(hour=hour, minute=minute, second=0)

            # Random observer
            observer_id = random.choice([o[0] for o in OBSERVERS])
            experience = OBSERVER_EXPERIENCE[observer_id]

            # Effort based on experience
            if experience == "expert":
                duration = random.randint(120, 300)  # 2-5 hours
                max_species = random.randint(15, 30)
            elif experience == "experienced":
                duration = random.randint(90, 180)   # 1.5-3 hours
                max_species = random.randint(10, 20)
            elif experience == "intermediate":
                duration = random.randint(60, 120)   # 1-2 hours
                max_species = random.randint(5, 15)
            else:  # beginner
                duration = random.randint(30, 90)    # 0.5-1.5 hours
                max_species = random.randint(3, 10)

            # Protocol and distance
            protocols = ["P20", "P21", "P22"]  # Incidental, Stationary, Traveling
            protocol = random.choice(protocols)
            distance = None if protocol != "P22" else round(random.uniform(0.5, 5.0), 2)

            # Get species for this habitat
            species_codes = get_habitat_species(habitat, max_species)
            species_count = len(species_codes)

            checklist_id = f"S{checklist_counter:06d}"
            checklist_counter += 1

            checklist = {
                "model": "data.Checklist",
                "pk": checklist_id,
                "fields": {
                    "added": started.isoformat() + "Z",
                    "edited": started.isoformat() + "Z",
                    "country_id": "PT",
                    "state_id": state_code,
                    "county_id": county_code,
                    "location_id": loc_id,
                    "observer_id": observer_id,
                    "observer_count": 1,
                    "species_count": species_count,
                    "date": date.strftime("%Y-%m-%d"),
                    "time": time_str,
                    "started": started.isoformat() + "Z",
                    "protocol_code": protocol,
                    "project_code": "EBIRD",
                    "duration": duration,
                    "distance": str(distance) if distance else None,
                    "area": None,
                    "complete": True,
                    "comments": "",
                    "url": f"https://ebird.org/checklist/{checklist_id}",
                    "data": {},
                    "created": started.isoformat() + "Z",
                    "modified": started.isoformat() + "Z",
                }
            }
            checklists.append(checklist)

            # Generate observations for each species
            for species_code in species_codes:
                # Realistic counts based on species
                if species_code in ["houspa", "comsta", "spotsta", "yelgul"]:
                    # Common/flocking species
                    count = random.randint(1, 50)
                elif species_code in ["grefla2", "whisto", "barswa"]:
                    # Sometimes in groups
                    count = random.randint(1, 20)
                elif species_code in ["grifvo", "boneag1", "spaeag"]:
                    # Rare/solitary raptors
                    count = random.randint(1, 3)
                else:
                    # Most other species
                    count = random.randint(1, 10)

                obs_id = f"OBS{obs_counter:08d}"
                obs_counter += 1

                # Random chance of media
                has_photo = random.random() < 0.2  # 20% chance
                has_audio = random.random() < 0.1  # 10% chance
                has_video = random.random() < 0.05  # 5% chance

                observation = {
                    "model": "data.Observation",
                    "pk": obs_id,
                    "fields": {
                        "edited": started.isoformat() + "Z",
                        "checklist_id": checklist_id,
                        "species_id": species_code,
                        "observer_id": observer_id,
                        "country_id": "PT",
                        "state_id": state_code,
                        "county_id": county_code,
                        "location_id": loc_id,
                        "date": date.strftime("%Y-%m-%d"),
                        "time": time_str,
                        "started": started.isoformat() + "Z",
                        "count": count,
                        "audio": has_audio,
                        "photo": has_photo,
                        "video": has_video,
                        "approved": True,
                        "reason": "",
                        "comments": "",
                        "urn": f"urn:observation:{obs_id}",
                        "data": {},
                        "created": started.isoformat() + "Z",
                        "modified": started.isoformat() + "Z",
                    }
                }
                observations.append(observation)

    return checklists, observations


def generate_fixtures():
    """Generate all fixture data."""
    fixtures = []

    # Add all data in order (respecting foreign keys)
    print("Generating fixtures...", file=__import__('sys').stderr)

    fixtures.append(generate_country())
    fixtures.extend(generate_states())
    fixtures.extend(generate_counties())
    fixtures.extend(generate_locations())
    fixtures.extend(generate_species())
    fixtures.extend(generate_observers())

    checklists, observations = generate_checklists_and_observations()
    fixtures.extend(checklists)
    fixtures.extend(observations)

    print(f"Generated {len(fixtures)} total records:", file=__import__('sys').stderr)
    print(f"  - 1 Country", file=__import__('sys').stderr)
    print(f"  - {len(STATES)} States", file=__import__('sys').stderr)
    print(f"  - {len(COUNTIES)} Counties", file=__import__('sys').stderr)
    print(f"  - {len(LOCATIONS)} Locations", file=__import__('sys').stderr)
    print(f"  - {len(SPECIES)} Species", file=__import__('sys').stderr)
    print(f"  - {len(OBSERVERS)} Observers", file=__import__('sys').stderr)
    print(f"  - {len(checklists)} Checklists", file=__import__('sys').stderr)
    print(f"  - {len(observations)} Observations", file=__import__('sys').stderr)

    return fixtures


if __name__ == "__main__":
    random.seed(42)  # For reproducible data
    fixtures = generate_fixtures()
    print(json.dumps(fixtures, indent=2, ensure_ascii=False))
