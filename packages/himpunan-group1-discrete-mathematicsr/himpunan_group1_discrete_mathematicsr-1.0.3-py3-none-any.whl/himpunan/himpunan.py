from decimal import Decimal
from fractions import Fraction

class Himpunan:
    def __init__(self, *args):
        self.data = []
        for item in args:
            if isinstance(item, (list, set, tuple)):
                for i in item:
                    self._tambah(i)
            else:
                self._tambah(item)

    def _tambah(self, item):
        if isinstance(item, (int, float, Decimal, Fraction)):
            for existing in self.data:
                if isinstance(existing, (int, float, Decimal, Fraction)):
                    if float(existing) == float(item):
                        return
        if item not in self.data:
            self.data.append(item)

    def __repr__(self):
        return "{" + ", ".join(map(str, self.data)) + "}"

    def __iadd__(self, item):
        """Adds an element to a set ('+=' operator)"""
        self._tambah(item)
        return self

    def __isub__(self, item):
        """Removes an element from a set ('-=' operator)"""
        val = float(item) if isinstance(item, (int, float, Decimal, Fraction)) else item
        if val in self.data:
            self.data.remove(val)
        return self

    def __len__(self):
        """This function counts the number of elements within a set."""
        return len(self.data)

    def __contains__(self, item):
        """Checks if an item is in the set."""
        val = float(item) if isinstance(item, (int, float, Decimal, Fraction)) else item
        return val in self.data

    def __eq__(self, other):
        """Checks if a set is equal to another set."""
        return sorted(self.data) == sorted(other.data)

    def __le__(self, other):
        """Subset: True if every element of self is present in other."""
        return all(x in other.data for x in self.data)

    def __lt__(self, other):
        """Proper subset: True if it has elements all in other and NOT having the exact same elements as in the other set."""
        return self <= other and self != other

    def __ge__(self, other):
        """Superset: True if every element of 'other' is present in self."""
        return all(x in self.data for x in other.data)

    def __floordiv__(self, other):
        """Equivalent: True if both have the exact same elements regardless of order."""
        return set(self.data) == set(other.data)

    def __add__(self, other):
        """Union"""
        result = list(self.data)
        for x in other.data:
            if x not in result:
                result.append(x)
        return Himpunan(*result)

    def __truediv__(self, other):
        """Intersection"""
        result = [x for x in self.data if x in other.data]
        return Himpunan(*result)

    def __sub__(self, other):
        """Difference"""
        result = [x for x in self.data if x not in other.data]
        return Himpunan(*result)

    def __mul__(self, other):
        """Symetric Difference"""
        result = [x for x in self.data if x not in other.data] + \
                 [x for x in other.data if x not in self.data]
        return Himpunan(*result)

    def __pow__(self, other):
        """Cartesian Pro duct"""
        result = [(a, b) for a in self.data for b in other.data]
        return result
    
    def Komplemen(self, semesta):
        """Complement against the universal set"""
        result = [x for x in semesta.data if x not in self.data]
        return Himpunan(*result)
    
    def __abs__(self):
        """Number of power set"""
        return 2 ** len(self.data)

    def ListKuasa(self):
        """Shows all subsets of the set"""
        hasil = [[]]
        for elemen in self.data:
            hasil += [subset + [elemen] for subset in hasil]
        return [Himpunan(*subset) for subset in hasil]
