class Semver:
    """
    A class to represent a semantic version.
    """

    def __init__(self, version: str):
        self.major, self.minor, self.patch = (int(v) for v in version.split('.'))

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"

    def __eq__(self, other):
        if isinstance(other, Semver):
            return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)
        if isinstance(other, str):
            return str(self) == other
        return False

    def __lt__(self, other):
        if isinstance(other, Semver):
            return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
        if isinstance(other, str):
            return self < Semver(other)
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, Semver):
            return (self.major, self.minor, self.patch) <= (other.major, other.minor, other.patch)
        if isinstance(other, str):
            return self <= Semver(other)
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Semver):
            return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)
        if isinstance(other, str):
            return self > Semver(other)
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Semver):
            return (self.major, self.minor, self.patch) >= (other.major, other.minor, other.patch)
        if isinstance(other, str):
            return self >= Semver(other)
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, Semver):
            return (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch)
        if isinstance(other, str):
            return str(self) != other
        return NotImplemented