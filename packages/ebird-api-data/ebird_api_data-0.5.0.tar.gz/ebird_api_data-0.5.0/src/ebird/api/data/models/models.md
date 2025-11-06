# eBird API Data Models

This document describes the Django models used in the eBird API data application, their purposes, and their relationships.

## Overview

The application models eBird bird observation data with a hierarchical structure that 
captures geographic regions, observation locations, checklists, individual observations, 
species information, and observers. The models are designed to efficiently query and 
filter bird sighting data from the eBird API.

## Core Models

### Checklist (`checklist.py`)

Represents a birdwatching checklist submitted to eBird. A checklist is a single birding 
trip or outing where an observer records all birds seen during a specific time and location.

**Key Fields:**
- `identifier` - Unique eBird checklist ID (primary key)
- `date`, `time`, `started` - When the birding started
- `added`, `edited` - Metadata about eBird submission
- `protocol_code` - The birding protocol used (e.g., P20=Incidental, P21=Stationary, P22=Traveling)
- `duration`, `distance`, `area` - Effort metrics
- `complete` - Whether all species seen were reported
- `observer_count`, `species_count` - Summary counts

**Relationships:**
- Belongs to: `Country`, `State`, `County` (optional), `Location`, `Observer`
- Has many: `Observation` (through reverse relationship)

**Protocol Choices:**
The model defines standard eBird protocols as an enum: Incidental, Stationary, Traveling, 
Area, Banding, Nocturnal, Pelagic, and Historical.

### Observation (`observation.py`)

Represents a single species sighting within a checklist. Each observation records one 
species seen during a birding outing.

**Key Fields:**
- `identifier` - Unique global observation ID (primary key)
- `count` - Number of individuals seen
- `audio`, `photo`, `video` - Media availability flags
- `approved` - Whether the observation has been accepted by reviewers
- `reason` - Explanation if not approved (stored as multilingual JSON)
- `comments` - Observer notes
- `date`, `time`, `started` - When the observation was made

**Relationships:**
- Belongs to: `Checklist` (CASCADE delete), `Species`, `Observer`, `Country`, `State`, `County` (optional), `Location`

**Design Note:**
Geographic fields (Country, State, County, Location) are denormalized from the 
Checklist for query performance optimization, reducing the need for joins when 
filtering observations by location.

### Species (`species.py`)

Represents a bird species in the eBird/Clements taxonomy, including species, 
subspecies, hybrids, and other taxonomic categories.

**Key Fields:**
- `species_code` - eBird species code (primary key, e.g., "ostric2")
- `common_name`, `scientific_name` - Species names (common name stored as multilingual JSON)
- `family_code`, `family_common_name`, `family_scientific_name` - Family taxonomy
- `taxon_order` - Position in taxonomic order
- `order` - Taxonomic order (e.g., Struthioniformes)
- `category` - Taxonomic category

**Category Choices:**
- Species - Standard species
- Slash - Species pairs (when identification is uncertain)
- Subspecies (issf) - Subspecies
- Domestic - Domestic varieties
- Hybrid - Hybrid individuals
- Form - Species forms
- Spuh - Unidentified species
- Intergrade - Intergrades between subspecies

**Relationships:**
- Has many: `Observation` (observations of this species)

**Methods:**
- `get_common_name()` - Returns localized common name based on current language
- `get_family_common_name()` - Returns localized family name

### Observer (`observer.py`)

Represents a person who submits checklists to eBird.

**Key Fields:**
- `identifier` - eBird observer ID (primary key)
- `name` - Display name
- `original` - Original name from eBird
- `enabled` - Whether to load checklists from this observer

**Relationships:**
- Has many: `Checklist`, `Observation`

## Geographic Hierarchy Models

The application uses a three-level geographic hierarchy to organize locations:

### Country (`country.py`)

Top-level geographic division.

**Key Fields:**
- `code` - 2-character country code (primary key)
- `name` - Country name
- `place` - Hierarchical place name

**Relationships:**
- Has many: `State`, `County`, `Location`, `Checklist`, `Observation`

### State (`state.py`)

Second-level geographic division (corresponds to eBird's "subnational1" or state/province).

**Key Fields:**
- `code` - State code up to 6 characters (primary key)
- `name` - State name
- `place` - Hierarchical place name

**Relationships:**
- Has many: `County`, `Location`, `Checklist`, `Observation`

### County (`county.py`)

Third-level geographic division (corresponds to eBird's "subnational2" or county).

**Key Fields:**
- `code` - County code up to 10 characters (primary key)
- `name` - County name
- `place` - Hierarchical place name

**Relationships:**
- Has many: `Location`, `Checklist`, `Observation`

### Location (`location.py`)

Represents a specific birding location, which can be a hotspot or a personal location.

**Key Fields:**
- `identifier` - Location ID (primary key)
- `name` - Display name
- `original` - Original eBird name
- `latitude`, `longitude` - Geographic coordinates
- `hotspot` - Whether this is an official eBird hotspot
- `url` - Link to eBird location page

**Relationships:**
- Belongs to: `Country`, `State`, `County` (optional)
- Has many: `Checklist`, `Observation`

**Design Notes:**
The model includes extensive documentation about design decisions:
- Uses Country/State/County naming instead of eBird API's country/subnational1/subnational2 for clarity
- Hierarchical codes (like US-NY-109) were considered but not implemented to avoid administrative burden
- Additional grouping models (Area, Island, Region) were rejected due to maintenance complexity
- Geographic fields are denormalized on Checklist and Observation for performance

## Key Design Patterns

### Denormalization for Performance

Both `Checklist` and `Observation` models duplicate geographic information (Country, 
State, County, Location) even though Location already contains this hierarchy. This 
denormalization reduces database joins and significantly improves query performance 
when filtering by geographic region.

### Cascade vs Protect

- `Observation` → `Checklist`: CASCADE (observations are deleted when checklist is deleted)
- `Observation` → `Species`: PROTECT (cannot delete species with existing observations)
- Most geographic relationships: PROTECT (cannot delete regions with existing data)

### Multilingual Support

The `Species` model stores `common_name` and `family_common_name` as JSON to support
multiple languages, with helper methods to retrieve the appropriate translation based 
on the current language context.

## Common Fields

All models include:
- `data` - JSONField for storing additional flexible data
- `created` - Auto-timestamp when record was created
- `modified` - Auto-timestamp when record was last updated

These fields provide flexibility for storing extra information and tracking data lineage.
