from .utils import get_pokemon_name
from pogom.utils import get_args
from datetime import datetime

args = get_args()
# temporarily disabling because -o and -i is
# removed from 51f651228c00a96b86f5c38d1a2d53b32e5d9862
# IGNORE = None
# ONLY = None
# if args.ignore:
#    IGNORE =  [i.lower().strip() for i in args.ignore.split(',')]
# elif args.only:
#    ONLY = [i.lower().strip() for i in args.only.split(',')]


def printPokemon(pokemon_id, lat, lng, itime):
    if args.display_in_console:
        print """
        ======================================
         Name: {name}
         Coord: {coords}
         ID: {id}
         Remaining Time: {time}
        ======================================
        """.format(
            name=get_pokemon_name(id).lower().encode('utf-8'),
            coords="(%f, %f)" % (lat, lng),
            id=pokemon_id,
            time=itime - datetime.utcnow())
