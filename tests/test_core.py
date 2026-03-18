"""Tests for Fixmystreet."""
from src.core import Fixmystreet
def test_init(): assert Fixmystreet().get_stats()["ops"] == 0
def test_op(): c = Fixmystreet(); c.process(x=1); assert c.get_stats()["ops"] == 1
def test_multi(): c = Fixmystreet(); [c.process() for _ in range(5)]; assert c.get_stats()["ops"] == 5
def test_reset(): c = Fixmystreet(); c.process(); c.reset(); assert c.get_stats()["ops"] == 0
def test_service_name(): c = Fixmystreet(); r = c.process(); assert r["service"] == "fixmystreet"
