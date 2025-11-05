import os
import asyncio
from typing import Optional, Any, Union

from ironflock.CrossbarConnection import CrossbarConnection, Stage, getSerialNumber
from ironflock.types import TableQueryParams, PublishParams, CallParams, LocationParams, TableParams, SubscriptionParams
from autobahn.wamp.types import PublishOptions, RegisterOptions, SubscribeOptions, CallOptions
import warnings


class IronFlock:
    """Convenience class for easy-to-use message publishing in the IronFlock platform.

    Example:

        async def main():
            while True:
                publication = await ironflock.publish("test.publish.pw", 1, "two", 3, foo="bar")
                print(publication)
                await asyncio.sleep(3)


        if __name__ == "__main__":
            ironflock = IronFlock(mainFunc=main)
            await ironflock.run()
    """

    def __init__(self, serial_number: str = None, mainFunc=None) -> None:
        """Creates IronFlock Instance

        Args:
            serial_number (str, optional): serial_number of device.
            Defaults to None, in which case the environment variable DEVICE_SERIAL_NUMBER is used.
            mainFunc (callable, optional): Main function to run after connection is established.
        """
        self._serial_number = getSerialNumber(serial_number)
        self._device_name = os.environ.get("DEVICE_NAME")
        self._device_key = os.environ.get("DEVICE_KEY")
        self._app_name = os.environ.get("APP_NAME")
        self._swarm_key = int(os.environ.get("SWARM_KEY"))
        self._app_key = int(os.environ.get("APP_KEY"))
        self._env = os.environ.get("ENV")
        self._connection = CrossbarConnection()
        self.mainFunc = mainFunc
        self._main_task = None
        self._is_configured = False
        # Validate required environment variables
        missing_vars = []
        if not self._device_key:
            missing_vars.append("DEVICE_KEY")
        if not self._app_name:
            missing_vars.append("APP_NAME")
        if not self._serial_number:
            missing_vars.append("DEVICE_SERIAL_NUMBER")
        if not self._swarm_key:
            missing_vars.append("SWARM_KEY")
        if not self._app_key:
            missing_vars.append("APP_KEY")

        if missing_vars:
            warning_msg = f"Warning: The following environment variables must be present: {', '.join(missing_vars)}"
            warnings.warn(warning_msg, UserWarning, stacklevel=2)

    @property
    def connection(self) -> CrossbarConnection:
        """The CrossbarConnection instance

        Returns:
            CrossbarConnection
        """
        return self._connection

    @property
    def is_connected(self) -> bool:
        """Check if the connection is established

        Returns:
            bool: True if connected, False otherwise
        """
        return self._connection.is_open

    async def _configure_connection(self):
        """Configure the CrossbarConnection with environment variables"""
        if self._is_configured:
            return
            
        env_value = os.environ.get("ENV", "DEV").upper()
        
        # Map environment string to Stage enum
        stage_map = {
            "DEV": Stage.DEVELOPMENT,
            "PROD": Stage.PRODUCTION
        }
        stage = stage_map.get(env_value, Stage.DEVELOPMENT)
        
        await self._connection.configure(
            swarm_key=int(self._swarm_key),
            app_key=int(self._app_key),
            stage=stage,
            serial_number=self._serial_number
        )
        self._is_configured = True
        
    def getRemoteAccessUrlForPort(self, port: int) -> Optional[str]:
        """Get the remote access URL for a given port from the CrossbarConnection

        Args:
            port (int): The port number to get the URL for
        Returns:
            Optional[str]: The remote access URL or None if not available
        """
        return f"https://{self._device_key}-{self._app_name.lower()}-{port}.app.ironflock.com" if self._device_key and self._app_name else None

    async def publish(self, topic: str, *args, **kwargs) -> Optional[Any]:
        """Publishes to the IronFlock Platform Message Router

        Args:
            topic (str): The URI of the topic to publish to, e.g. "com.myapp.mytopic1"
            *args: Positional arguments to publish
            **kwargs: Keyword arguments to publish

        Returns:
            Optional[Any]: Object representing a publication
            (feedback from publishing an event when doing an acknowledged publish)
        """
        # Validate parameters using Pydantic
        try:
            params = PublishParams(
                topic=topic,
                args=list(args),
                kwargs=kwargs
            )
        except Exception as e:
            raise ValueError(f"Invalid publish parameters: {e}")
        
        if not self.is_connected:
            print("cannot publish, not connected")
            return None

        # Add device metadata to kwargs
        device_metadata = {
            "DEVICE_SERIAL_NUMBER": self._serial_number,
            "DEVICE_KEY": self._device_key,
            "DEVICE_NAME": self._device_name,
        }
        
        # Merge device metadata with user kwargs
        combined_kwargs = {**device_metadata, **params.kwargs}
        
        # Use acknowledged publish with proper PublishOptions
        options = PublishOptions(acknowledge=True)
        
        try:
            pub = await self._connection.publish(
                params.topic, 
                args=params.args, 
                kwargs=combined_kwargs,
                options=options
            )
            return pub
        except Exception as e:
            print(f"Publish failed: {e}")
            return None
            
    async def set_device_location(self, long: float, lat: float):
        """Update the location of the device registered in the platform
        
        This will update the device's location in the master data of the platform.
        The maps in the device or group overviews will reflect the new device location in realtime.
        The location history will not be stored in the platform. 
        If you need location history, then create a dedicated table for it.
        
        Args:
            long (float): Longitude coordinate
            lat (float): Latitude coordinate
        """
        # Validate parameters using Pydantic
        try:
            params = LocationParams(longitude=long, latitude=lat)
        except Exception as e:
            raise ValueError(f"Invalid location parameters: {e}")
        
        if not self.is_connected:
            print("cannot set location, not connected")
            return None

        payload = {
            "long": params.longitude,
            "lat": params.latitude
        }
        
        extra = {
            "DEVICE_SERIAL_NUMBER": self._serial_number,
            "DEVICE_KEY": self._device_key,
            "DEVICE_NAME": self._device_name
        }
        
        try:
            res = await self._connection.call(
                'ironflock.location_service.update', 
                args=[payload], 
                kwargs=extra
            )
            return res
        except Exception as e:
            print(f"Set location failed: {e}")
            return None
    
    async def register_function(self, topic: str, endpoint, options: Optional[dict] = None) -> Optional[Any]:
        """Registers a function with the IronFlock Platform Message Router

        Args:
            topic (str): The URI of the topic to register, e.g. "com.myapp.myprocedure1"
            endpoint: The function to register
            options (dict, optional): Registration options

        Returns:
            Optional[Any]: Object representing a registration
        """
        if not self.is_connected:
            print("cannot register, not connected")
            return None

        # Convert options dict to RegisterOptions if provided
        register_options = RegisterOptions(**options) if options else None
        
        full_topic = f"{self._swarm_key}.{self._device_key}.{self._app_key}.{self._env}.{topic}"

        try:
            reg = await self._connection.register(full_topic, endpoint, options=register_options)
            print(f"Function registered for IronFlock topic '{topic}'. (Full WAMP topic: '{full_topic}')")
            return reg
        except Exception as e:
            print(f"Register failed: {e}")
            return None

    async def register(self, topic: str, endpoint, options: Optional[dict] = None) -> Optional[Any]:
        """Alias for register_function() for backward compatibility"""
        return await self.register_function(topic, endpoint, options)

    async def subscribe(self, topic: str, handler, options: Optional[dict] = None) -> Optional[Any]:
        """Subscribes to a topic on the IronFlock Platform Message Router

        Args:
            topic (str): The URI of the topic to subscribe to, e.g. "com.myapp.mytopic1"
            handler: The function to call when a message is received
            options (dict, optional): Subscription options

        Returns:
            Optional[Any]: Object representing a subscription
        """
        if not self.is_connected:
            print("cannot subscribe, not connected")
            return None

        # Convert options dict to SubscribeOptions if provided
        subscribe_options = SubscribeOptions(**options) if options else None

        try:
            sub = await self._connection.subscribe(topic, handler, options=subscribe_options)
            return sub
        except Exception as e:
            print(f"Subscribe failed: {e}")
            return None

    async def call(self, device_key: str, topic: str, args: list = None, kwargs: dict = None, options: Optional[dict] = None):
        """Calls a remote procedure registered by another IronFlock device

        Args:
            device_key (str): The device key of the target device
            topic (str): The URI of the topic to call, e.g. "com.myapp.myprocedure1"
            args (list, optional): Positional arguments for the call. Defaults to None.
            kwargs (dict, optional): Keyword arguments for the call. Defaults to None.
            options (dict, optional): Call options. Defaults to None.

        Returns:
            Any: The result of the remote procedure call
        """
        # Validate parameters using Pydantic
        try:
            params = CallParams(
                device_key=device_key,
                topic=topic,
                args=args or [],
                kwargs=kwargs or {},
                options=options
            )
        except Exception as e:
            raise ValueError(f"Invalid call parameters: {e}")
        
        if not self.is_connected:
            print("cannot call, not connected")
            return None

        # Convert options dict to CallOptions if provided
        call_options = CallOptions(**params.options) if params.options else None

        call_topic = f"{params.device_key}.{params.topic}"

        try:
            result = await self._connection.call(call_topic, args=params.args, kwargs=params.kwargs, options=call_options)
            return result
        except Exception as e:
            print(f"Call failed: {e}")
            return None

    async def publish_to_table(
        self, tablename: str, *args, **kwargs
    ) -> Optional[Any]:
        """Publishes Data to a Table in the IronFlock Platform. This is a convenience function.
        
        You can achieve the same results by simply publishing a payload to the topic
        [SWARM_KEY].[APP_KEY].[your_table_name]
        
        The SWARM_KEY and APP_KEY are provided as environment variables to the device container.
        The also provided ENV variable holds either PROD or DEV to decide which topic to use, above.
        This function automatically detects the environment and publishes to the correct table.
        
        Args:
            tablename (str): The table name of the table to publish to, e.g. "sensordata"
            *args: Positional arguments to publish
            **kwargs: Keyword arguments to publish

        Returns:
            Optional[Any]: Object representing a publication
            (feedback from publishing an event when doing an acknowledged publish)
        """
        # Validate parameters using Pydantic
        try:
            params = TableParams(
                tablename=tablename,
                args=list(args),
                kwargs=kwargs
            )
        except Exception as e:
            raise ValueError(f"Invalid table parameters: {e}")

        if not self._swarm_key:
            raise Exception("SWARM_KEY not set in environment variables!")

        if not self._app_key:
            raise Exception("APP_KEY not set in environment variables!")

        topic = f"{self._swarm_key}.{self._app_key}.{params.tablename}"

        pub = await self.publish(topic, *params.args, **params.kwargs)
        return pub

    async def subscribe_to_table(
        self, tablename: str, handler, options: Optional[dict] = None
    ) -> Optional[Any]:
        """Subscribes to a Table in the IronFlock Platform. This is a convenience function.
        
        You can achieve the same results by simply subscribing to the topic
        [SWARM_KEY].[APP_KEY].[your_table_name]
        
        The SWARM_KEY and APP_KEY are provided as environment variables to the device container.
        The also provided ENV variable holds either PROD or DEV to decide which topic to use, above.
        This function automatically detects the environment and subscribes to the correct table.
        
        Args:
            tablename (str): The table name of the table to subscribe to, e.g. "sensordata"
            handler: The function to call when a message is received
            options (dict, optional): Subscription options

        Returns:
            Optional[Any]: Object representing a subscription
        """
        # Validate parameters using Pydantic  
        try:
            params = SubscriptionParams(
                topic=tablename,  # We validate the tablename as a topic
                options=options
            )
        except Exception as e:
            raise ValueError(f"Invalid subscription parameters: {e}")

        if not self._swarm_key:
            raise Exception("SWARM_KEY not set in environment variables!")

        if not self._app_key:
            raise Exception("APP_KEY not set in environment variables!")

        topic = f"{self._swarm_key}.{self._app_key}.{params.topic}"

        sub = await self.subscribe(topic, handler, params.options)
        return sub

    async def getHistory(self, tablename: str, queryParams: Union[TableQueryParams, dict] = {"limit": 10}) -> Optional[Any]:
        """Get historical data from a table using the history service
        
        Calls the "history.table" topic with the specified table name and query parameters.
        
        Args:
            tablename (str): The name of the table to query
            queryParams (TableQueryParams | dict): Query parameters including:
                - limit (int): Maximum number of rows (required, 1-10000)
                - offset (int, optional): Offset for pagination (>=0)
                - timeRange (ISOTimeRange, optional): Time range filter with start/end ISO dates
                - filterAnd (List[SQLFilterAnd], optional): AND conditions for filtering
        
        Returns:
            Optional[Any]: The query result data or None if the call fails
            
        Raises:
            ValueError: If validation fails for any parameter
            pydantic.ValidationError: If Pydantic validation fails
        """
        if not tablename:
            raise ValueError("Tablename must not be None or empty string!")
        
        # Validate and convert parameters using Pydantic BEFORE checking connection
        try:
            if isinstance(queryParams, dict):
                # Convert dict to Pydantic model (this triggers validation)
                validated_params = TableQueryParams(**queryParams)
            else:
                # Already a Pydantic model, but validate again to be safe
                validated_params = queryParams
                
        except Exception as e:
            raise ValueError(f"Invalid query parameters: {e}")
            
        if not self.is_connected:
            print("cannot get history, not connected")
            return None
            
        # Prepare the call arguments
        queryParams = validated_params.model_dump()
        
        topic = f"history.transformed.app.{self._app_key}.{tablename}"
        try:
            result = await self._connection.call(
                topic,
                args=[queryParams]
            )
            return result
        except Exception as e:
            # Check for specific WAMP errors indicating procedure not available
            error_str = str(e)
            if (hasattr(e, 'error') and 
                ('no_such_procedure' in str(e.error) or 'runtime_error' in str(e.error))) or \
               'no callee registered for procedure' in error_str:
                print(f"Get history failed: History service procedure '{topic}' not registered in Crossbar")
                print(f"  Error type: {getattr(e, 'error', 'Unknown')}")
                print(f"  Error details: {e}")
                print(f"  This indicates the history service is not available or not properly configured")
                return None
            else:
                print(f"Get history failed: {e}")
                return None

    async def start(self):
        """Start the connection and run the main function if provided"""
        await self._configure_connection()
        await self._connection.start()
        
        if self.mainFunc:
            self._main_task = asyncio.create_task(self.mainFunc())
        
    async def stop(self):
        """Stop the connection and cancel the main task if running"""
        if self._main_task and not self._main_task.done():
            self._main_task.cancel()
            try:
                await self._main_task
            except asyncio.CancelledError:
                pass
            self._main_task = None
            
        if self._connection:
            await self._connection.stop()

    def run(self):
        """Synchronous wrapper to run the IronFlock instance (original API)"""
        asyncio.run(self.run_async())

    async def run_async(self):
        """Start the connection and keep it running"""
        await self.start()
        
        try:
            # Keep running until manually stopped
            if self._main_task:
                await self._main_task
            else:
                # If no main function, just wait indefinitely
                while self.is_connected:
                    await asyncio.sleep(1)
        except asyncio.CancelledError:
            # Task was cancelled (likely from stop() being called)
            pass
        except KeyboardInterrupt:
            print("Shutting down...")
        except Exception as e:
            print(f"Exception in run(): {e}")
            raise
        finally:
            await self.stop()

    def run_sync(self):
        """Alias for run() method for clarity"""
        return self.run()
