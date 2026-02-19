"""3D vector implementation."""

import math
from typing import Union, Tuple


class Vector3:
    """
    3D vector with mathematical operations.
    
    Represents a point or direction in 3D space.
    
    Example:
        >>> v1 = Vector3(1, 2, 3)
        >>> v2 = Vector3(4, 5, 6)
        >>> distance = v1.distance_to(v2)
        >>> v3 = v1 + v2
    """
    
    __slots__ = ('x', 'y', 'z')
    
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        """
        Initialize a 3D vector.
        
        Args:
            x: X coordinate (default: 0.0)
            y: Y coordinate (default: 0.0)
            z: Z coordinate (default: 0.0)
        """
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"Vector3({self.x}, {self.y}, {self.z})"
    
    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, Vector3):
            return NotImplemented
        return (
            abs(self.x - other.x) < 1e-6 and
            abs(self.y - other.y) < 1e-6 and
            abs(self.z - other.z) < 1e-6
        )
    
    def __add__(self, other: 'Vector3') -> 'Vector3':
        """Vector addition."""
        if not isinstance(other, Vector3):
            return NotImplemented
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other: 'Vector3') -> 'Vector3':
        """Vector subtraction."""
        if not isinstance(other, Vector3):
            return NotImplemented
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar: Union[int, float]) -> 'Vector3':
        """Scalar multiplication."""
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def __rmul__(self, scalar: Union[int, float]) -> 'Vector3':
        """Right scalar multiplication."""
        return self.__mul__(scalar)
    
    def __truediv__(self, scalar: Union[int, float]) -> 'Vector3':
        """Scalar division."""
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        if scalar == 0:
            raise ValueError("Cannot divide by zero")
        return Vector3(self.x / scalar, self.y / scalar, self.z / scalar)
    
    def __neg__(self) -> 'Vector3':
        """Negation."""
        return Vector3(-self.x, -self.y, -self.z)
    
    def dot(self, other: 'Vector3') -> float:
        """
        Compute dot product with another vector.
        
        Args:
            other: Another Vector3
        
        Returns:
            Dot product (scalar)
        """
        if not isinstance(other, Vector3):
            raise TypeError(f"Expected Vector3, got {type(other)}")
        return self.x * other.x + self.y * other.y + self.z * other.z
    
    def cross(self, other: 'Vector3') -> 'Vector3':
        """
        Compute cross product with another vector.
        
        Args:
            other: Another Vector3
        
        Returns:
            Cross product (Vector3)
        """
        if not isinstance(other, Vector3):
            raise TypeError(f"Expected Vector3, got {type(other)}")
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )
    
    def magnitude(self) -> float:
        """
        Compute the magnitude (length) of the vector.
        
        Returns:
            Magnitude as a float
        """
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)
    
    def length(self) -> float:
        """Alias for magnitude()."""
        return self.magnitude()
    
    def normalize(self) -> 'Vector3':
        """
        Return a normalized (unit) vector in the same direction.
        
        Returns:
            Normalized Vector3
        
        Raises:
            ValueError: If vector has zero magnitude
        """
        mag = self.magnitude()
        if mag == 0:
            raise ValueError("Cannot normalize zero vector")
        return self / mag
    
    def distance_to(self, other: 'Vector3') -> float:
        """
        Compute distance to another point.
        
        Args:
            other: Another Vector3
        
        Returns:
            Distance as a float
        """
        if not isinstance(other, Vector3):
            raise TypeError(f"Expected Vector3, got {type(other)}")
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)
    
    def to_tuple(self) -> Tuple[float, float, float]:
        """
        Convert to tuple.
        
        Returns:
            (x, y, z) tuple
        """
        return (self.x, self.y, self.z)
    
    @staticmethod
    def from_tuple(t: Tuple[float, float, float]) -> 'Vector3':
        """
        Create Vector3 from tuple.
        
        Args:
            t: (x, y, z) tuple
        
        Returns:
            Vector3 instance
        """
        if len(t) != 3:
            raise ValueError(f"Expected tuple of length 3, got {len(t)}")
        return Vector3(t[0], t[1], t[2])
