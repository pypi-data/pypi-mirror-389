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
        val = float(item) if isinstance(item, (int, float, Decimal, Fraction)) else item
        if val not in self.data:
            self.data.append(val)

    def __repr__(self):
        return "{" + ", ".join(map(str, self.data)) + "}"

    def __iadd__(self, item):
        self._tambah(item)
        return self

    def __isub__(self, item):
        val = float(item) if isinstance(item, (int, float, Decimal, Fraction)) else item
        if val in self.data:
            self.data.remove(val)
        return self

    def __len__(self):
        return len(self.data)

    def __contains__(self, item):
        val = float(item) if isinstance(item, (int, float, Decimal, Fraction)) else item
        return val in self.data

    def __eq__(self, other):
        return sorted(self.data) == sorted(other.data)

    def __le__(self, other):
        return all(x in other.data for x in self.data)

    def __lt__(self, other):
        return self <= other and self != other

    def __ge__(self, other):
        return all(x in self.data for x in other.data)

    def __floordiv__(self, other):
        return set(self.data) == set(other.data)

    def __add__(self, other):
        result = list(self.data)
        for x in other.data:
            if x not in result:
                result.append(x)
        return Himpunan(*result)

    def __truediv__(self, other):
        result = [x for x in self.data if x in other.data]
        return Himpunan(*result)

    def __sub__(self, other):
        result = [x for x in self.data if x not in other.data]
        return Himpunan(*result)

    def __mul__(self, other):
        result = [x for x in self.data if x not in other.data] + \
                 [x for x in other.data if x not in self.data]
        return Himpunan(*result)

    def __pow__(self, other):
        result = [(a, b) for a in self.data for b in other.data]
        return result

    def ListKuasa(self):
        hasil = [[]]
        for elemen in self.data:
            hasil += [subset + [elemen] for subset in hasil]
        return [Himpunan(*subset) for subset in hasil]
