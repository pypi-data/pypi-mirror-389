"""Expose the classes in the API."""
# pylint: disable=unused-import
from bfgdealer.board import Board, Trick, Contract, Auction
from bfgdealer.dealer import Dealer
from bfgdealer.dealer_solo import Dealer as DealerSolo
from bfgdealer.dealer_duo import Dealer as DealerDuo

from bfgdealer._version import __version__
VERSION = __version__
SOLO_SET_HANDS = {index: item[0]
                  for index, item in enumerate(DealerSolo().set_hands)}
DUO_SET_HANDS = {index: item[0]
                 for index, item in enumerate(DealerDuo().set_hands)}
