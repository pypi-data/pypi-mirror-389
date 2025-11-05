import asyncio
import time
import os
from typing import Optional, List, Dict, Any, Callable
from autobahn.asyncio.wamp import ApplicationSession
from autobahn.asyncio.component import Component
from autobahn.wamp import auth
from enum import Enum

# Import Pydantic types for validation
try:
    from .types import CrossbarCallParams, SubscriptionParams
except ImportError:
    from ironflock.types import CrossbarCallParams, SubscriptionParams

class Stage(Enum):
    """Stage enumeration for different deployment environments"""
    DEVELOPMENT = "DEV"
    PRODUCTION = "PROD"

def getSerialNumber(serial_number: str = None) -> str:
    """Get device serial number from parameter or environment variable"""
    if serial_number is None:
        s_num = os.environ.get("DEVICE_SERIAL_NUMBER")
        if s_num is None:
            raise Exception("ENV Variable 'DEVICE_SERIAL_NUMBER' is not set!")
    else:
        s_num = serial_number
    return s_num

STUDIO_DEV_WS_URI = "wss://cbw.ironflock.dev/ws-ua-usr"
STUDIO_WS_URI_OLD = "wss://cbw.record-evolution.com/ws-ua-usr"
STUDIO_WS_URI = "wss://cbw.ironflock.com/ws-ua-usr"
LOCALHOST_WS_URI = "ws://localhost:8080/ws-ua-usr"

socketURIMap = {
    "https://studio.ironflock.dev": STUDIO_DEV_WS_URI,
    "https://studio.record-evolution.com": STUDIO_WS_URI_OLD,
    "https://studio.ironflock.com": STUDIO_WS_URI,
    "http://localhost:8086": LOCALHOST_WS_URI,
    "http://host.docker.internal:8086": LOCALHOST_WS_URI
}

class CrossbarConnection:
    """
    Python version of the TypeScript CrossbarConnection class.
    Manages WAMP connections with automatic reconnection, subscription management, and session handling.
    """
    
    def __init__(self):
        self.session: Optional[ApplicationSession] = None
        self.component: Optional[Component] = None
        self.connection_options: Optional[Dict[str, Any]] = None
        self.subscriptions: List[Any] = []  # List of autobahn subscriptions
        self.registrations: List[Any] = []  # List of autobahn registrations
        self.connection_drop_wait_time: int = 6000  # milliseconds
        self.realm: Optional[str] = None
        self.serial_number: Optional[str] = None
        self._first_connection_future: Optional[asyncio.Future] = None
        self._is_connected = False
        self._session_wait_timeout = 6.0  # seconds
        
    @staticmethod
    def getWebSocketURI():
        reswarm_url = os.environ.get("RESWARM_URL")
        if not reswarm_url:
            return STUDIO_WS_URI
        return socketURIMap.get(reswarm_url)
        
    async def configure(
        self, 
        swarm_key: int, 
        app_key: int, 
        stage: Stage,
        cburl: Optional[str] = None,
        serial_number: Optional[str] = None
    ):
        """
        Configure the crossbar connection with realm and WAMPCRA authentication details.
        
        Args:
            swarm_key: The swarm key identifier
            app_key: The application key identifier  
            stage: The deployment stage (development, production)
            cburl: Optional crossbar URL (defaults to environment variable RESWARM_URL mapping)
            serial_number: Optional device serial number (defaults to DEVICE_SERIAL_NUMBER env var)
        """
        self.realm = f"realm-{swarm_key}-{app_key}-{stage.value.lower()}"
        self.serial_number = getSerialNumber(serial_number)
        
        # Get URL from environment if not provided
        if cburl is None:
            cburl = self.getWebSocketURI()
            
        self.connection_options = {
            'url': cburl,
            'realm': self.realm,
            'authmethods': ['wampcra'],
            'authid': self.serial_number,
            'max_retries': -1,  # infinite retries
            'max_retry_delay': 2,
            'initial_retry_delay': 1,
            'serializers': ['msgpack']
        }
        
        # Create the component with WAMPCRA authentication
        transports = [{
            'type': 'websocket',
            'url': cburl,
            'serializers': ['msgpack']
        }]
        
        # Custom session class for WAMPCRA authentication
        class AppSession(ApplicationSession):
            def onConnect(session_self):
                print('onConnect called')
                session_self.join(self.realm, ['wampcra'], self.serial_number)
                
            def onChallenge(session_self, challenge):
                print(f'challenge requested for {challenge.method}')
                if challenge.method == "wampcra":
                    signature = auth.compute_wcs(
                        self.serial_number, challenge.extra["challenge"]
                    )
                    return signature
                raise Exception(f"Invalid authmethod {challenge.method}")
        
        self.component = Component(
            transports=transports,
            realm=self.realm,
            session_factory=AppSession
        )
        
        # Set up event handlers
        self.component.on('join', self._on_open)
        self.component.on('leave', self._on_close)
        self.component.on('disconnect', self._on_disconnect)
        
        # Create future for first connection
        self._first_connection_future = asyncio.Future()
        
    async def _on_open(self, session: ApplicationSession, details):
        """Handle session open event"""
        self.session = session
        self._is_connected = True
        await self._resubscribe_all()
        print(f"Connection to IronFlock app realm '{session._realm}' established")
        
        if self._first_connection_future and not self._first_connection_future.done():
            self._first_connection_future.set_result(None)
            
    async def _on_close(self, session: ApplicationSession, details):
        """Handle session close event"""
        self.session = None
        self._is_connected = False
        print(f"Connection to IronFlock app realm {self.realm} closed: {details.reason}")
        
        if self._first_connection_future and not self._first_connection_future.done():
            print(f"⚠️  Initial connection attempt failed: {details.reason}")
            print("🔄 Will keep trying to reconnect...")
            # Resolve the future so start() doesn't crash, Autobahn will keep retrying
            self._first_connection_future.set_result(None)
            
    async def _on_disconnect(self, session: ApplicationSession, was_clean: bool):
        """Handle disconnect event"""
        self.session = None
        self._is_connected = False
        print(f"Disconnected from IronFlock app realm {self.realm}, clean: {was_clean}")

    async def _session_wait(self) -> None:
        """Wait for session to be available"""
        start_time = time.time()
        while not self.session or not self._is_connected:
            if time.time() - start_time > self._session_wait_timeout:
                raise TimeoutError('Timeout waiting for session')
            await asyncio.sleep(0.2)
            
    @property
    def is_open(self) -> bool:
        """Check if the connection is open"""
        return self._is_connected and self.session is not None
        
    async def start(self) -> None:
        """Start the connection"""
        if not self.component:
            raise ValueError("Must call configure() before start()")

        print(f'Starting connection for IronFlock app realm {self.realm}')

        # Start the component (non-blocking in autobahn asyncio)
        self.component.start()
        
        # Wait for first connection to be established
        if self._first_connection_future:
            await self._first_connection_future
            
    async def stop(self) -> None:
        """Stop the connection"""
        if self.component:
            # Check if component is properly initialized before stopping
            if hasattr(self.component, '_done_f') and self.component._done_f is not None:
                await self.component.stop()
        self._is_connected = False
        self.session = None
        
    async def call(
        self, 
        topic: str, 
        args: Optional[List[Any]] = None, 
        kwargs: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Call a remote procedure"""
        # Validate parameters using Pydantic
        try:
            params = CrossbarCallParams(
                topic=topic,
                args=args or [],
                kwargs=kwargs or {},
                options=options
            )
        except Exception as e:
            raise ValueError(f"Invalid call parameters: {e}")
        
        await self._session_wait()
        if not self.session:
            raise RuntimeError("No active session")
            
        result = await self.session.call(params.topic, *params.args, **params.kwargs, options=params.options)
        return result
        
    async def subscribe(
        self, 
        topic: str, 
        handler: Callable,
        options: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """Subscribe to a topic"""
        # Validate parameters using Pydantic
        try:
            params = SubscriptionParams(
                topic=topic,
                options=options
            )
        except Exception as e:
            raise ValueError(f"Invalid subscription parameters: {e}")
        
        await self._session_wait()
        if not self.session:
            raise RuntimeError("No active session")
            
        subscription = await self.session.subscribe(handler, params.topic, options=params.options)
        if subscription:
            self.subscriptions.append(subscription)
        return subscription
        
    async def publish(
        self, 
        topic: str, 
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """Publish to a topic"""
        # Validate parameters using Pydantic
        try:
            params = CrossbarCallParams(  # Using CrossbarCallParams as it has the same structure
                topic=topic,
                args=args or [],
                kwargs=kwargs or {},
                options=options
            )
        except Exception as e:
            raise ValueError(f"Invalid publish parameters: {e}")
        
        await self._session_wait()
        if not self.session:
            raise RuntimeError("No active session")
            
        result = await self.session.publish(params.topic, *params.args, options=params.options, **params.kwargs)
        return result
        
    async def unsubscribe(self, subscription: Any) -> None:
        """Unsubscribe from a subscription"""
        await self._session_wait()
        if not self.session:
            raise RuntimeError("No active session")
            
        if subscription in self.subscriptions:
            self.subscriptions.remove(subscription)
            await self.session.unsubscribe(subscription)
            
    async def unsubscribe_func(
        self, 
        topic: str, 
        handler: Optional[Callable] = None
    ) -> None:
        """Unsubscribe a specific function from a topic"""
        await self._session_wait()
        
        if handler is None:
            return await self.unsubscribe_topic(topic)
            
        # Find and remove subscriptions matching topic and handler
        to_remove = []
        for subscription in self.subscriptions:
            if hasattr(subscription, 'topic') and subscription.topic == topic:
                if hasattr(subscription, 'handler') and subscription.handler == handler:
                    to_remove.append(subscription)
                    
        for subscription in to_remove:
            try:
                await self.unsubscribe(subscription)
            except Exception as e:
                print(f"Failed to unsubscribe from {topic}: {e}")
                
    async def unsubscribe_topic(self, topic: str) -> bool:
        """Unsubscribe all handlers from a topic"""
        matching_subs = [
            sub for sub in self.subscriptions 
            if hasattr(sub, 'topic') and sub.topic == topic
        ]
        
        if not matching_subs:
            return True
            
        # Unsubscribe all matching subscriptions
        tasks = [self.unsubscribe(sub) for sub in matching_subs]
        await asyncio.gather(*tasks, return_exceptions=True)
        return True
        
    async def register(
        self, 
        topic: str, 
        endpoint: Callable,
        options: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """Register a procedure"""
        await self._session_wait()
        if not self.session:
            raise RuntimeError("No active session")
            
        registration = await self.session.register(endpoint, topic, options=options)
        if registration:
            self.registrations.append(registration)
        return registration
        
    async def unregister(self, registration: Any) -> None:
        """Unregister a procedure"""
        await self._session_wait()
        if not self.session:
            raise RuntimeError("No active session")
            
        if registration in self.registrations:
            self.registrations.remove(registration)
            await self.session.unregister(registration)
            
    async def _resubscribe_all(self) -> None:
        """Resubscribe to all topics after reconnection"""
        if not self.subscriptions:
            return
            
        print(f'Resubscribing to {len(self.subscriptions)} subscriptions')
        
        # Store current subscriptions and clear the list
        old_subscriptions = self.subscriptions.copy()
        self.subscriptions.clear()
        
        # Resubscribe to all topics
        tasks = []
        for old_sub in old_subscriptions:
            if hasattr(old_sub, 'topic') and hasattr(old_sub, 'handler'):
                task = self.subscribe(old_sub.topic, old_sub.handler)
                tasks.append(task)
                
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)