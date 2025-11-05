from py4j.java_gateway import JavaObject
from ..ndtkit_socket_connection import gateway


class NIEnumSpecialValue:
    """Helper class for handling NDTKit's special values in data.

    This class provides access to and validation of special numerical values
    that represent specific states in NDTKit's data processing. These include:

    Special Values:
        - NOE (No Echo): Indicates no ultrasonic echo was detected
        - NOS (No Synchro): Indicates a synchronization failure
        - MASK: Masked or suppressed data point (equivalent to 'sup')
        - NAN (Not a Number): Indicates no acquisition was made at this point
        - ERROR: Indicates an error value

    The class caches the list of special values from the Java API for efficient
    repeated access and provides methods to check if a value is a special value.
    """

    # Cache for the list of special values
    all_special_values = None

    def __init__(self, java_object: JavaObject):
        """Initialize with a Java special value enum object.

        Args:
            java_object (JavaObject): The underlying Java NIEnumSpecialValue object
        """
        self._java_object = java_object

    @staticmethod
    def get_all_values() -> list[int]:
        """Get a list of all defined special values.

        This method caches the values from the Java API on first call for efficiency.
        Subsequent calls return the cached values.

        Returns:
            list[int]: List of integer codes representing special values (NOE, NOS, etc.)
        """
        if NIEnumSpecialValue.all_special_values is None:
            special_values_java = gateway.jvm.agi.ndtkit.api.model.NIEnumSpecialValue.getAllValues()
            NIEnumSpecialValue.all_special_values = [int(special_value) for special_value in special_values_java] if special_values_java else []
        return NIEnumSpecialValue.all_special_values

    @staticmethod
    def is_special_value(value: float) -> bool:
        """Test if a value matches any of the defined special values.

        A small tolerance (1E-6) is used for floating point comparisons to account
        for potential numerical precision differences.

        Args:
            value (float): The value to test

        Returns:
            bool: True if the value matches a special value within tolerance,
                False otherwise
        """
        for special_value in NIEnumSpecialValue.get_all_values():
            if abs(special_value - value) < 1E-6:
                return True
        return False
