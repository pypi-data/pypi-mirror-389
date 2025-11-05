"""
Type definitions for IronFlock table query functionality.
Contains Pydantic models for runtime validation of query parameters.
"""

from typing import List, Union, Optional, Any
import warnings
from pydantic import BaseModel, Field, field_validator, ValidationInfo


class TableQueryCondition(BaseModel):
    """Individual condition for table queries"""
    field: str = Field(..., min_length=1, description="Field name to filter on")
    operator: str = Field(..., min_length=1, description="Comparison operator (=, !=, >, <, >=, <=, IN, NOT IN, LIKE, etc.)")
    value: Union[str, int, float, bool, List[Union[str, int, float]]] = Field(..., description="Value to compare against")
    
    @field_validator('operator')
    @classmethod
    def validate_operator(cls, v: str) -> str:
        """Validate that operator is from a known set"""
        valid_operators = ['=', '!=', '>', '<', '>=', '<=', 'IN', 'NOT IN', 'LIKE', 'NOT LIKE', 'IS NULL', 'IS NOT NULL']
        v_upper = v.upper()
        if v_upper not in valid_operators:
            # Allow the operator but warn about potentially unsafe operators
            warnings.warn(f"Operator '{v}' is not in standard list: {valid_operators}", UserWarning)
        return v
    
    @field_validator('value')
    @classmethod
    def validate_value_for_operator(cls, v: Union[str, int, float, bool, List[Union[str, int, float]]], info: ValidationInfo) -> Union[str, int, float, bool, List[Union[str, int, float]]]:
        """Validate that value type matches the operator"""
        if info.data and 'operator' in info.data:
            operator = info.data['operator'].upper()
            if operator in ('IN', 'NOT IN'):
                # IN operators should have list values
                if not isinstance(v, list):
                    raise ValueError(f"Operator '{operator}' requires a list of values")
                if len(v) == 0:
                    raise ValueError(f"Operator '{operator}' requires at least one value")
            elif isinstance(v, list):
                # Non-IN operators should not have list values
                raise ValueError(f"Operator '{operator}' does not support list values")
        return v


class ISOTimeRange(BaseModel):
    """ISO time range specification with validation"""
    start: str = Field(..., description="ISO datetime string for range start")
    end: str = Field(..., description="ISO datetime string for range end")
    
    @field_validator('start', 'end')
    @classmethod
    def validate_iso_datetime(cls, v: str) -> str:
        """Validate that the datetime strings are valid ISO format"""
        from datetime import datetime
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError(f"Invalid ISO datetime format: {v}")


class SQLFilterAnd(BaseModel):
    """SQL filter specification for AND conditions with validation"""
    column: str = Field(..., min_length=1, description="Database column name")
    operator: str = Field(..., description="SQL operator (=, >, <, LIKE, etc.)")
    value: Union[str, int, float, bool, List[Union[str, int, float]]] = Field(..., description="Filter value or list of values for IN operator")
    
    @field_validator('operator')
    @classmethod
    def validate_operator(cls, v: str) -> str:
        """Validate that operator is a known SQL operator"""
        valid_operators = {'=', '!=', '<>', '>', '<', '>=', '<=', 'LIKE', 'ILIKE', 'IN', 'NOT IN', 'IS', 'IS NOT'}
        if v.upper() not in valid_operators:
            # Allow the operator but warn about potentially unsafe operators
            warnings.warn(f"Operator '{v}' is not in standard list: {valid_operators}", UserWarning)
        return v
    
    @field_validator('value')
    @classmethod
    def validate_value_for_operator(cls, v: Union[str, int, float, bool, List[Union[str, int, float]]], info: ValidationInfo) -> Union[str, int, float, bool, List[Union[str, int, float]]]:
        """Validate that value type matches the operator"""
        if info.data and 'operator' in info.data:
            operator = info.data['operator'].upper()
            if operator in ('IN', 'NOT IN'):
                # IN operators should have list values
                if not isinstance(v, list):
                    raise ValueError(f"Operator '{operator}' requires a list of values")
                if len(v) == 0:
                    raise ValueError(f"Operator '{operator}' requires at least one value")
            elif isinstance(v, list):
                # Non-IN operators should not have list values
                raise ValueError(f"Operator '{operator}' does not support list values")
        return v


class TableQueryParams(BaseModel):
    """Parameters for table history queries with comprehensive validation
    
    Equivalent to TypeScript:
    {
      limit: number & tags.Type<"uint32"> & tags.Maximum<10000>;
      offset?: number & tags.Type<"uint32">;
      timeRange?: ISOTimeRange;
      filterAnd?: SQLFilterAnd[];
    }
    """
    limit: int = Field(..., gt=0, le=10000, description="Maximum number of rows (1-10000)")
    offset: Optional[int] = Field(None, ge=0, description="Offset for pagination (>=0)")
    timeRange: Optional[ISOTimeRange] = Field(None, description="Time range filter")
    filterAnd: Optional[List[SQLFilterAnd]] = Field(None, description="AND conditions for filtering")
    
    @field_validator('limit')
    @classmethod
    def validate_limit_uint32(cls, v: int) -> int:
        """Validate that limit fits in uint32 range"""
        if v > 4294967295:  # 2^32 - 1
            raise ValueError("limit exceeds uint32 maximum")
        return v
    
    @field_validator('offset')
    @classmethod
    def validate_offset_uint32(cls, v: Optional[int]) -> Optional[int]:
        """Validate that offset fits in uint32 range"""
        if v is not None and v > 4294967295:  # 2^32 - 1
            raise ValueError("offset exceeds uint32 maximum")
        return v


# Additional Pydantic models for other IronFlock functions

class PublishParams(BaseModel):
    """Parameters for publish operations"""
    topic: str = Field(..., min_length=1, description="Topic URI (e.g., 'com.myapp.mytopic1')")
    args: Optional[List[Any]] = Field(default_factory=list, description="Positional arguments")
    kwargs: Optional[dict] = Field(default_factory=dict, description="Keyword arguments")
    
    @field_validator('topic')
    @classmethod
    def validate_topic_format(cls, v: str) -> str:
        """Validate topic follows URI-like format"""
        if not v or not isinstance(v, str):
            raise ValueError("Topic must be a non-empty string")
        # Basic topic format validation (can be enhanced as needed)
        if len(v.strip()) != len(v):
            raise ValueError("Topic cannot have leading/trailing whitespace")
        return v


class CallParams(BaseModel):
    """Parameters for remote procedure calls"""
    device_key: str = Field(..., min_length=1, description="Target device key")
    topic: str = Field(..., min_length=1, description="Procedure topic URI")
    args: Optional[List[Any]] = Field(default_factory=list, description="Positional arguments")
    kwargs: Optional[dict] = Field(default_factory=dict, description="Keyword arguments")
    options: Optional[dict] = Field(None, description="Call options")
    
    @field_validator('device_key', 'topic')
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        """Validate that string fields are non-empty"""
        if not v or not isinstance(v, str):
            raise ValueError("Field must be a non-empty string")
        if len(v.strip()) != len(v):
            raise ValueError("Field cannot have leading/trailing whitespace")
        return v


class LocationParams(BaseModel):
    """Parameters for device location updates"""
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    
    @field_validator('longitude', 'latitude')
    @classmethod
    def validate_coordinates(cls, v: float) -> float:
        """Validate coordinate values are finite numbers"""
        if not isinstance(v, (int, float)):
            raise ValueError("Coordinates must be numeric")
        if not (-1000 <= v <= 1000):  # Reasonable bounds check
            raise ValueError("Coordinate value seems unrealistic")
        return float(v)


class TableParams(BaseModel):
    """Parameters for table operations"""
    tablename: str = Field(..., min_length=1, description="Table name")
    args: Optional[List[Any]] = Field(default_factory=list, description="Positional arguments")
    kwargs: Optional[dict] = Field(default_factory=dict, description="Keyword arguments")
    
    @field_validator('tablename')
    @classmethod
    def validate_tablename(cls, v: str) -> str:
        """Validate table name format"""
        if not v or not isinstance(v, str):
            raise ValueError("Table name must be a non-empty string")
        
        # Remove leading/trailing whitespace
        v = v.strip()
        if not v:
            raise ValueError("Table name cannot be empty or just whitespace")
            
        # Basic table name validation
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Table name should contain only alphanumeric characters, hyphens, and underscores")
            
        if len(v) > 100:  # Reasonable length limit
            raise ValueError("Table name too long (max 100 characters)")
            
        return v


class SubscriptionParams(BaseModel):
    """Parameters for subscription operations"""
    topic: str = Field(..., min_length=1, description="Topic URI to subscribe to")
    options: Optional[Union[dict, Any]] = Field(None, description="Subscription options (dict or autobahn options object)")
    
    @field_validator('topic')
    @classmethod
    def validate_topic_format(cls, v: str) -> str:
        """Validate topic follows URI-like format"""
        if not v or not isinstance(v, str):
            raise ValueError("Topic must be a non-empty string")
        if len(v.strip()) != len(v):
            raise ValueError("Topic cannot have leading/trailing whitespace")
        return v
    
    @field_validator('options')
    @classmethod
    def validate_options(cls, v: Optional[Union[dict, Any]]) -> Optional[Union[dict, Any]]:
        """Accept either dict or autobahn options objects"""
        if v is None:
            return v
        # Accept any object that autobahn might pass (SubscribeOptions, etc.)
        return v


class CrossbarCallParams(BaseModel):
    """Parameters for low-level Crossbar calls"""
    topic: str = Field(..., min_length=1, description="Topic URI")
    args: Optional[List[Any]] = Field(default_factory=list, description="Positional arguments")
    kwargs: Optional[dict] = Field(default_factory=dict, description="Keyword arguments")
    options: Optional[Union[dict, Any]] = Field(None, description="Call options (dict or autobahn options object)")
    
    @field_validator('options')
    @classmethod
    def validate_options(cls, v: Optional[Union[dict, Any]]) -> Optional[Union[dict, Any]]:
        """Accept either dict or autobahn options objects"""
        if v is None:
            return v
        # Accept any object that autobahn might pass (PublishOptions, CallOptions, etc.)
        return v
    
    @field_validator('topic')
    @classmethod
    def validate_topic_format(cls, v: str) -> str:
        """Validate topic follows URI-like format"""
        if not v or not isinstance(v, str):
            raise ValueError("Topic must be a non-empty string")
        if len(v.strip()) != len(v):
            raise ValueError("Topic cannot have leading/trailing whitespace")
        return v