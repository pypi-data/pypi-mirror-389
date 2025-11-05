import unittest

from dict_toolset._compare import Comparer, DifferenceGenerator, Difference, default_type_comparers

def custom_bool_int_comparer(
    comparer: Comparer,
    data_a: bool | int,
    data_b: bool | int,
    current_key: list[str] = None,
) -> DifferenceGenerator:
    if data_a == data_b:
        return
    
    if isinstance(data_a, bool) and isinstance(data_b, int):
        if data_a == bool(data_b):
            return
        
    if isinstance(data_a, int) and isinstance(data_b, bool):
        if bool(data_a) == data_b:
            return
        
    yield Difference(
        current_key,
        "NOT_EQUAL",
        value_a = data_a,
        value_b = data_b
    )

custom_type_comparers = default_type_comparers | {
    (int, bool): custom_bool_int_comparer
}

compare = Comparer(type_comparers=custom_type_comparers).compare

class CompareTest(unittest.TestCase):

    def test_c1(self):
        result = list(compare({
            "name": "Supi",
            "sub": {
                "name": "SupiSub"
            }
        }, {
            "name": "Supi",
            "sub": {
                "name": "SupiSub",
                "content": "Sdjjahsdh"
            }
        }))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "MISSING sub.content IN A: Sdjjahsdh")

    def test_c2(self):
        result = list(compare({
            "name": "Supi",
            "subs": [
                "str"
            ]
        }, {
            "name": "Supi",
            "subs": [
                "duf",
                "str",
            ]
        }))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].type, "MISSING")

    def test_c3(self):
        result = list(compare([
            {
                "id": "djajshd",
                "name": "supi",
                "kacki": "dsadasdasd"
            }
        ], [
            {
                "id": "sdajsjdhas",
                "name": "supi2",
                "kacki": "dsad2asdasdd"
            },
            {
                "id": "djajshd",
                "name": "supi",
                "kacki": "dsadasdasd"
            },
        ]))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].type, "MISSING")

    def test_int_index(self):
        result = list(compare([
            {"name": "supi"}
        ], [
            {"name": "supi2"}
        ]))

        self.assertEqual(len(result), 1)
        self.assertEqual(str(result[0]), "NOT_EQUAL [0].name supi!=supi2")

    def test_uuid_index(self):
        result = list(compare([
            {"uuid": "123", "name": "supi"}
        ], [
            {"uuid": "123", "name": "supi2"}
        ]))

        self.assertEqual(len(result), 1)
        self.assertEqual(str(result[0]), "NOT_EQUAL [uuid=123].name supi!=supi2")

    def test_custom_bool_int(self):
        result = list(compare({
            "flag": True,
            "count": 1,
        }, {
            "flag": 1,
            "count": True,
        }))

        self.assertEqual(len(result), 0)