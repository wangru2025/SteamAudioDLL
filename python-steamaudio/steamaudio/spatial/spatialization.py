"""Spatialization parameters."""

from typing import Dict, Any
from .vector3 import Vector3


class SpatializationParams:
    """
    Spatialization parameters for 3D audio processing.
    
    Encapsulates all parameters needed for spatial audio rendering,
    including listener position/orientation and sound source position.
    
    Example:
        >>> params = SpatializationParams()
        >>> params.listener_pos = Vector3(0, 0, 0)
        >>> params.sound_pos = Vector3(5, 0, 0)
        >>> distance = params.distance
    """
    
    def __init__(self):
        """Initialize spatialization parameters with defaults."""
        # Listener position and orientation
        self.listener_pos = Vector3(0, 0, 0)
        self.listener_forward = Vector3(0, 0, 1)
        self.listener_up = Vector3(0, 1, 0)
        
        # Sound source position
        self.sound_pos = Vector3(0, 0, 0)
        
        # Distance attenuation parameters
        self.min_distance = 0.1
        self.max_distance = 1000.0
        self.rolloff = 1.0
        
        # Directional attenuation
        self.directional_attenuation = 1.0
    
    @property
    def distance(self) -> float:
        """
        Compute distance from listener to sound source.
        
        Returns:
            Distance in world units
        """
        return self.listener_pos.distance_to(self.sound_pos)
    
    @property
    def direction(self) -> Vector3:
        """
        Compute direction from listener to sound source.
        
        Returns:
            Normalized direction vector
        """
        direction = self.sound_pos - self.listener_pos
        mag = direction.magnitude()
        
        if mag < 0.001:
            # When listener and source are at same position,
            # use listener's forward direction
            return self.listener_forward
        
        return direction / mag
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert parameters to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'listener_pos': self.listener_pos.to_tuple(),
            'listener_forward': self.listener_forward.to_tuple(),
            'listener_up': self.listener_up.to_tuple(),
            'sound_pos': self.sound_pos.to_tuple(),
            'min_distance': self.min_distance,
            'max_distance': self.max_distance,
            'rolloff': self.rolloff,
            'directional_attenuation': self.directional_attenuation,
            'distance': self.distance,
            'direction': self.direction.to_tuple(),
        }
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"SpatializationParams("
            f"listener_pos={self.listener_pos}, "
            f"sound_pos={self.sound_pos}, "
            f"distance={self.distance:.2f})"
        )
