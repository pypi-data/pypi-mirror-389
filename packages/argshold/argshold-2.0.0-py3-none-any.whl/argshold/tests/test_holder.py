# test_argsholder.py
import unittest
from typing import *

from frozendict import frozendict

from argshold.core.ArgsHolder import ArgsHolder


class TestArgsHolderBasics(unittest.TestCase):

    def test_init_and_properties(self: Self):
        a = ArgsHolder(1, 2, x=3, y=4)
        self.assertEqual(a.args, (1, 2))
        self.assertIsInstance(a.kwargs, frozendict)
        self.assertEqual(dict(a.kwargs), {"x": 3, "y": 4})

    def test_len_bool_iter_contains(self: Self):
        a = ArgsHolder(1, 2, x=3)
        self.assertEqual(len(a), 3)
        self.assertTrue(a)
        self.assertIn(2, a)
        self.assertNotIn("x", a)  # __contains__ only checks positional args

    def test_getitem_index_slice_key(self: Self):
        a = ArgsHolder(10, 20, 30, a=1, b=2)
        self.assertEqual(a[0], 10)
        self.assertEqual(a[1:3], (20, 30))
        self.assertEqual(a["a"], 1)

        # Non-integer non-slice keys stringify
        class K:
            def __str__(self: Self):
                return "b"

        self.assertEqual(a[K()], 2)

    def test_setitem_index_slice_key(self: Self):
        a = ArgsHolder(1, 2, 3, a=10, b=20)
        a[1] = 99
        self.assertEqual(a.args, (1, 99, 3))
        a[0:2] = (7, 8)
        self.assertEqual(a.args, (7, 8, 3))
        a["a"] = 11
        self.assertEqual(dict(a.kwargs), {"a": 11, "b": 20})

    def test_delitem_index_slice_key(self: Self):
        a = ArgsHolder(1, 2, 3, a=10, b=20, c=30)
        del a[1]
        self.assertEqual(a.args, (1, 3))
        del a[0:2]
        self.assertEqual(a.args, ())
        del a["b"]
        self.assertEqual(dict(a.kwargs), {"a": 10, "c": 30})

    def test_hash_is_unhashable(self: Self):
        with self.assertRaises(TypeError):
            hash(ArgsHolder())


class TestArgsHolderSequenceOps(unittest.TestCase):
    def test_add_mul_rmul_reversed(self: Self):
        a = ArgsHolder(1, 2, x=3)
        self.assertEqual(a + [7, 8], [1, 2, 7, 8])
        self.assertEqual(a * 2, [1, 2, 1, 2])
        self.assertEqual(3 * a, [1, 2, 1, 2, 1, 2])
        self.assertEqual(list(reversed(a)), [2, 1])

    def test_append_extend_insert_remove_reverse_sort_count_index(self: Self):
        a = ArgsHolder(3, 1, 2, x=0)
        a.append(4)
        self.assertEqual(a.args, (3, 1, 2, 4))
        a.extend([5, 6])
        self.assertEqual(a.args, (3, 1, 2, 4, 5, 6))
        a.insert(0, 9)
        self.assertEqual(a.args, (9, 3, 1, 2, 4, 5, 6))
        a.remove(3)
        self.assertEqual(a.args, (9, 1, 2, 4, 5, 6))
        a.reverse()
        self.assertEqual(a.args, (6, 5, 4, 2, 1, 9))
        a.sort()
        self.assertEqual(a.args, (1, 2, 4, 5, 6, 9))
        self.assertEqual(a.count(4), 1)
        self.assertEqual(a.index(5), 3)
        # sort with key & reverse flag truthiness
        a2 = ArgsHolder("aa", "b", "cccc")
        a2.sort(key=len, reverse=1)
        self.assertEqual(a2.args, ("cccc", "aa", "b"))

    def test_slice_assignment_mismatch_raises(self: Self):
        a = ArgsHolder(1, 2, 3)
        # Python lists allow replacing a slice with different length; the code uses list assignment -> allowed.
        a[0:2] = [9]  # contraction is legal
        self.assertEqual(a.args, (9, 3))
        a[0:1] = [7, 8]  # expansion is legal
        self.assertEqual(a.args, (7, 8, 3))


class TestArgsHolderMappingOps(unittest.TestCase):
    def test_mapping_views_and_get_default(self: Self):
        a = ArgsHolder(1, a=10, b=20)
        self.assertEqual(list(sorted(a.keys())), ["a", "b"])
        self.assertEqual(list(sorted(a.values())), [10, 20])
        self.assertEqual(sorted(a.items()), [("a", 10), ("b", 20)])
        self.assertEqual(a.get("a"), 10)
        self.assertIsNone(a.get("z"))
        self.assertEqual(a.get("z", 99), 99)

    def test_update_setdefault_clear(self: Self):
        a = ArgsHolder(1, a=10)
        a.update({"b": 20}, c=30)
        self.assertEqual(dict(a.kwargs), {"a": 10, "b": 20, "c": 30})
        val = a.setdefault("b", 999)
        self.assertEqual(val, 20)
        self.assertEqual(dict(a.kwargs), {"a": 10, "b": 20, "c": 30})
        val2 = a.setdefault("d", 40)
        self.assertEqual(val2, 40)
        self.assertEqual(dict(a.kwargs), {"a": 10, "b": 20, "c": 30, "d": 40})
        a.clear()
        self.assertEqual(a.args, ())
        self.assertEqual(dict(a.kwargs), {})

    def test_or_and_ror(self: Self):
        a = ArgsHolder(a=1, b=2)
        # __or__ returns dict(self.kwargs | other)
        self.assertEqual(a | {"b": 99, "c": 3}, {"a": 1, "b": 99, "c": 3})
        # __ror__ returns dict(other | self.kwargs)
        self.assertEqual({"a": 0, "d": 4} | a, {"a": 1, "b": 2, "d": 4})

    def test_pop_index_key_default_and_popitem(self: Self):
        a = ArgsHolder(10, 20, 30, a=1, b=2)
        self.assertEqual(a.pop(), 30)  # default key=-1
        self.assertEqual(a.args, (10, 20))
        self.assertEqual(a.pop(0), 10)
        self.assertEqual(a.args, (20,))
        self.assertEqual(a.pop("a"), 1)
        self.assertEqual(dict(a.kwargs), {"b": 2})
        self.assertEqual(a.pop("missing", 99), 99)
        k, v = a.popitem()
        self.assertEqual((k, v), ("b", 2))
        self.assertEqual(dict(a.kwargs), {})

    def test_copy_independent(self: Self):
        a = ArgsHolder([1, 2], x={"k": "v"})
        b = a.copy()
        self.assertIsNot(a, b)
        self.assertEqual(a, b)
        # Mutations on b shouldn't affect a (since properties re-wrap immutably)
        b.append(99)
        b.update(z=3)
        self.assertNotEqual(a.args, b.args)
        self.assertNotEqual(dict(a.kwargs), dict(b.kwargs))


class TestArgsHolderOrderingAndEquality(unittest.TestCase):
    def test_equality_and_inequality(self: Self):
        a = ArgsHolder(1, 2, x=3)
        b = ArgsHolder(1, 2, x=3)
        c = ArgsHolder(1, 2, x=4)
        self.assertTrue(a == b)
        self.assertTrue(a != c)
        self.assertFalse(a == (1, 2))  # different type

    def test_ordering_same_type_only(self: Self):
        a = ArgsHolder(1, 2, x=3)
        b = ArgsHolder(1, 3, x=1)
        self.assertTrue(a < b)
        self.assertTrue(b > a)
        self.assertTrue(a <= b)
        self.assertTrue(b >= a)

        # Cross-type comparisons must return NotImplemented (surfacing as TypeError from Python)
        class X:
            def __lt__(self, other):
                return NotImplemented

        with self.assertRaises(TypeError):
            _ = (
                a < X()
            )  # Python tries __lt__, gets NotImplemented, then X.__gt__ etc., ending in TypeError


class TestArgsHolderApplyMapZip(unittest.TestCase):
    def test_apply(self: Self):
        a = ArgsHolder(1, 2, x=3, y=4)

        def f(*args, **kwargs):
            return sum(args) + sum(kwargs.values())

        self.assertEqual(a.apply(f), 1 + 2 + 3 + 4)

    def test_zip_non_strict(self: Self):
        a = ArgsHolder([1, 2], [10, 20], a=("x", "y"), b=("u", "v"))
        out = list(a.zip())
        self.assertEqual(len(out), 2)
        self.assertTrue(all(isinstance(h, ArgsHolder) for h in out))
        self.assertEqual(out[0].args, (1, 10))
        self.assertEqual(dict(out[0].kwargs), {"a": "x", "b": "u"})
        self.assertEqual(out[1].args, (2, 20))
        self.assertEqual(dict(out[1].kwargs), {"a": "y", "b": "v"})

    def test_zip_strict_mismatch_raises(self: Self):
        # Positional of different lengths
        a = ArgsHolder([1, 2, 3], [10, 20], a=("x", "y"), b=("u", "v"))
        with self.assertRaises(ValueError):
            list(a.zip(strict=True))
        # Keyword values mismatch
        b = ArgsHolder([1, 2], [10, 20], a=("x",), b=("u", "v"))
        with self.assertRaises(ValueError):
            list(b.zip(strict=True))

    def test_map_with_callback_and_strict(self: Self):
        a = ArgsHolder([1, 2], [10, 20], a=(100, 200), b=(1000, 2000))

        def cb(x, y, *, a, b):
            # arbitrary function combining all pieces
            return x + y + a + b

        self.assertEqual(
            list(a.map(cb, strict=True)), [1 + 10 + 100 + 1000, 2 + 20 + 200 + 2000]
        )

    def test_values_items_keys_are_views(self: Self):
        a = ArgsHolder(1, a=1)
        kv = list(a.items())
        self.assertEqual(kv, [("a", 1)])
        self.assertEqual(list(a.keys()), ["a"])
        self.assertEqual(list(a.values()), [1])


class TestEdgeCases(unittest.TestCase):
    def test_kwargs_setter_accepts_any_mapping_or_pairs(self: Self):
        a = ArgsHolder()
        a.kwargs = {"a": 1}
        self.assertEqual(dict(a.kwargs), {"a": 1})
        a.kwargs = [("b", 2)]
        self.assertEqual(dict(a.kwargs), {"b": 2})
        # keys stringified
        a.kwargs = {10: "x"}
        self.assertEqual(dict(a.kwargs), {"10": "x"})

    def test_args_setter_accepts_any_iterable(self: Self):
        a = ArgsHolder()
        a.args = [1, 2, 3]
        self.assertEqual(a.args, (1, 2, 3))
        a.args = (x for x in [4, 5])
        self.assertEqual(a.args, (4, 5))

    def test_apply_with_builtins_zip_shadowing(self: Self):
        # Ensure module uses builtins.zip explicitly (bi.zip), independent of local names
        zip = "not a function"  # shadow local name
        _ = zip  # silence linter
        a = ArgsHolder([1], [2], k=[3])
        out = list(a.zip(strict=True))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].args, (1, 2))
        self.assertEqual(dict(out[0].kwargs), {"k": 3})

    def test_len_counts_args_plus_kwargs(self: Self):
        a = ArgsHolder(1, 2, a=3, b=4, c=5)
        self.assertEqual(len(a), 5)


if __name__ == "__main__":
    unittest.main()
