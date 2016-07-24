#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import peewee

from base64 import b64encode
from datetime import datetime
from datetime import timedelta

from . import config
from .customLog import printPokemon
from .transform import transform_from_wgs_to_gcj
from .utils import get_pokemon_name, get_args

logging_format = '%(asctime)s [%(module)11s] [%(levelname)7s] %(message)s'
logging.basicConfig(level=logging.INFO, format=logging_format)

log = logging.getLogger(__name__)

args = get_args()
db = None


def init_database():
    global db
    if db is not None:
        return db

    print args.db_type
    if args.db_type == 'mysql':
        db = peewee.MySQLDatabase(
            args.db_name,
            user=args.db_user,
            password=args.db_pass,
            host=args.db_host)
        log.info('Connecting to MySQL database on {}.'.format(args.db_host))
    else:
        db = peewee.SqliteDatabase(args.db)
        log.info('Connecting to local SQLLite database.')

    return db


class BaseModel(peewee.Model):
    class Meta:
        database = init_database()

    @classmethod
    def get_all(cls):
        results = [m for m in cls.select().dicts()]
        if args.china:
            for r in results:
                r['latitude'], r['longitude'] = transform_from_wgs_to_gcj(
                    r['latitude'], r['longitude'])
        return results


class Pokemon(BaseModel):
    # We are base64 encoding the ids delivered by the api
    # because they are too big for sqlite to handle
    encounter_id = peewee.CharField(primary_key=True)
    spawnpoint_id = peewee.CharField()
    pokemon_id = peewee.IntegerField()
    latitude = peewee.FloatField()
    longitude = peewee.FloatField()
    disappear_time = peewee.DateTimeField()

    @classmethod
    def get_active(cls, swLat, swLng, neLat, neLng):
        if any(coord is None for coord in [swLat, swLng, neLat, neLng]):
            query = (
                Pokemon
                .select()
                .where(Pokemon.disappear_time > datetime.utcnow())
                .dicts())
        else:
            query = (
                Pokemon
                .select()
                .where(
                    (Pokemon.disappear_time > datetime.utcnow()) &
                    (Pokemon.latitude >= swLat) &
                    (Pokemon.longitude >= swLng) &
                    (Pokemon.latitude <= neLat) &
                    (Pokemon.longitude <= neLng))
                .dicts())

        pokemons = []
        for p in query:
            p['pokemon_name'] = get_pokemon_name(p['pokemon_id'])
            if args.china:
                p['latitude'], p['longitude'] = transform_from_wgs_to_gcj(
                    p['latitude'], p['longitude'])
            pokemons.append(p)

        return pokemons

    @classmethod
    def get_active_by_id(cls, ids, swLat, swLng, neLat, neLng):
        if any(coord is None for coord in [swLat, swLng, neLat, neLng]):
            query = (
                Pokemon
                .select()
                .where(
                    (Pokemon.pokemon_id << ids) &
                    (Pokemon.disappear_time > datetime.utcnow()))
                .dicts())
        else:
            query = (
                Pokemon
                .select()
                .where(
                    (Pokemon.pokemon_id << ids) &
                    (Pokemon.disappear_time > datetime.utcnow()) &
                    (Pokemon.latitude >= swLat) &
                    (Pokemon.longitude >= swLng) &
                    (Pokemon.latitude <= neLat) &
                    (Pokemon.longitude <= neLng))
                .dicts())

        pokemons = []
        for p in query:
            p['pokemon_name'] = get_pokemon_name(p['pokemon_id'])
            if args.china:
                p['latitude'], p['longitude'] = \
                    transform_from_wgs_to_gcj(p['latitude'], p['longitude'])
            pokemons.append(p)

        return pokemons


class Pokestop(BaseModel):
    pokestop_id = peewee.CharField(primary_key=True)
    enabled = peewee.BooleanField()
    latitude = peewee.FloatField()
    longitude = peewee.FloatField()
    last_modified = peewee.DateTimeField()
    lure_expiration = peewee.DateTimeField(null=True)
    active_pokemon_id = peewee.IntegerField(null=True)

    @classmethod
    def get_stops(cls, swLat, swLng, neLat, neLng):
        if any(coord is None for coord in [swLat, swLng, neLat, neLng]):
            query = (
                Pokestop
                .select()
                .dicts())
        else:
            query = (
                Pokestop
                .select()
                .where(
                    (Pokestop.latitude >= swLat) &
                    (Pokestop.longitude >= swLng) &
                    (Pokestop.latitude <= neLat) &
                    (Pokestop.longitude <= neLng))
                .dicts())
        return list(query)


class Gym(BaseModel):

    UNCONTESTED = 0
    TEAM_MYSTIC = 1
    TEAM_VALOR = 2
    TEAM_INSTINCT = 3

    gym_id = peewee.CharField(primary_key=True)
    team_id = peewee.IntegerField()
    guard_pokemon_id = peewee.IntegerField()
    gym_points = peewee.IntegerField()
    enabled = peewee.BooleanField()
    latitude = peewee.FloatField()
    longitude = peewee.FloatField()
    last_modified = peewee.DateTimeField()

    @classmethod
    def get_gyms(cls, swLat, swLng, neLat, neLng):
        if any(coord is None for coord in [swLat, swLng, neLat, neLng]):
            query = (
                Gym
                .select()
                .dicts())
        else:
            query = (
                Gym
                .select()
                .where(
                    (Gym.latitude >= swLat) &
                    (Gym.longitude >= swLng) &
                    (Gym.latitude <= neLat) &
                    (Gym.longitude <= neLng))
                .dicts())
        return list(query)


class ScannedLocation(BaseModel):
    scanned_id = peewee.CharField(primary_key=True)
    latitude = peewee.FloatField()
    longitude = peewee.FloatField()
    last_modified = peewee.DateTimeField()

    @classmethod
    def get_recent(cls, swLat, swLng, neLat, neLng):
        visible_time = datetime.utcnow() - timedelta(minutes=15)
        return list(
            ScannedLocation
            .select()
            .where(
                (ScannedLocation.last_modified >= visible_time) &
                (ScannedLocation.latitude >= swLat) &
                (ScannedLocation.longitude >= swLng) &
                (ScannedLocation.latitude <= neLat) &
                (ScannedLocation.longitude <= neLng))
            .dicts())


def parse_map(map_dict, iteration_num, step, step_location):
    pokemons = {}
    pokestops = {}
    gyms = {}
    scanned = {}

    cells = map_dict['responses']['GET_MAP_OBJECTS']['map_cells']
    for cell in cells:
        if config['parse_pokemon']:
            for p in cell.get('wild_pokemons', []):
                d_t = datetime.utcfromtimestamp((
                    p['last_modified_timestamp_ms'] +
                    p['time_till_hidden_ms']) / 1000.0)
                printPokemon(
                    p['pokemon_data']['pokemon_id'],
                    p['latitude'], p['longitude'], d_t)
                pokemons[p['encounter_id']] = {
                    'encounter_id': b64encode(str(p['encounter_id'])),
                    'spawnpoint_id': p['spawnpoint_id'],
                    'pokemon_id': p['pokemon_data']['pokemon_id'],
                    'latitude': p['latitude'],
                    'longitude': p['longitude'],
                    'disappear_time': d_t
                }

        if iteration_num > 0 or step > 50:
            for f in cell.get('forts', []):
                # Pokestops
                if config['parse_pokestops'] and f.get('type') == 1:
                    lure_expiration, active_pokemon_id = None, None
                    if 'lure_info' in f:
                        lure_info = f['lure_info']
                        lure_expiration = datetime.utcfromtimestamp(
                            lure_info['lure_expires_timestamp_ms'] / 1000.0)
                        active_pokemon_id = lure_info['active_pokemon_id']

                    pokestops[f['id']] = {
                        'pokestop_id': f['id'],
                        'enabled': f['enabled'],
                        'latitude': f['latitude'],
                        'longitude': f['longitude'],
                        'last_modified': datetime.utcfromtimestamp(
                            f['last_modified_timestamp_ms'] / 1000.0),
                        'lure_expiration': lure_expiration,
                        'active_pokemon_id': active_pokemon_id
                    }

                elif config['parse_gyms'] and f.get('type') is None:
                    # Currently, there are only stops and gyms
                    gyms[f['id']] = {
                        'gym_id': f['id'],
                        'team_id': f.get('owned_by_team', 0),
                        'guard_pokemon_id': f.get('guard_pokemon_id', 0),
                        'gym_points': f.get('gym_points', 0),
                        'enabled': f['enabled'],
                        'latitude': f['latitude'],
                        'longitude': f['longitude'],
                        'last_modified': datetime.utcfromtimestamp(
                            f['last_modified_timestamp_ms'] / 1000.0),
                    }

    if pokemons and config['parse_pokemon']:
        log.info("Upserting {} pokemon".format(len(pokemons)))
        bulk_upsert(Pokemon, pokemons)

    if pokestops and config['parse_pokestops']:
        log.info("Upserting {} pokestops".format(len(pokestops)))
        bulk_upsert(Pokestop, pokestops)

    if gyms and config['parse_gyms']:
        log.info("Upserting {} gyms".format(len(gyms)))
        bulk_upsert(Gym, gyms)

    scanned[0] = {
        'scanned_id': str(step_location[0])+','+str(step_location[1]),
        'latitude': step_location[0],
        'longitude': step_location[1],
        'last_modified': datetime.utcnow(),
    }

    bulk_upsert(ScannedLocation, scanned)


def bulk_upsert(cls, data):
    num_rows = len(data.values())
    i = 0
    step = 120

    while i < num_rows:
        log.debug("Inserting items {} to {}".format(i, min(i+step, num_rows)))
        try:
            values_to_insert = data.values()[i:min(i + step, num_rows)]
            peewee.InsertQuery(cls, rows=values_to_insert).upsert().execute()
        except peewee.OperationalError as e:
            log.warning("%s... Retrying", e)
            continue

        i += step


def create_tables(db):
    db.connect()
    db.create_tables([Pokemon, Pokestop, Gym, ScannedLocation], safe=True)
    db.close()
