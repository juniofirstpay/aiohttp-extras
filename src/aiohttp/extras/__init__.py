import aiohttp
import urllib.parse
import functools
from typing import Dict, Callable, Awaitable, Any

class HTTPSessionConfig:
    name: str
    base_url: str
    dns_cache: bool = True
    conn_limit: int = 20


async def configure_session(
    base_url: str,
    dns_cache: bool = True,
    connection_limit: int = 20
):
    
    parsed_url = urllib.parse(base_url)
    conn = aiohttp.TCPConnector(
        ssl= True if parsed_url.scheme else False,
        use_dns_cache=dns_cache,
        limit=connection_limit
    )

    session = aiohttp.ClientSession(
        base_url=f"{parsed_url.scheme}://{parsed_url.netloc}", connector=conn
    )

    return session

AsyncCallable = Callable[...,Awaitable[Any]]

class HTTPSessions:

    def __init__(self):
        self.__session_mapping: Dict[str, aiohttp.ClientSession] = dict()
        self.__session_config_mapping: Dict[str, HTTPSessionConfig] = dict()

    def add(self, config: HTTPSessionConfig):
        self.__session_config_mapping[config.name] = config
    
    async def configure(self):
        for name, config in self.__session_config_mapping.items():
            client_session = await configure_session(config.base_url, config.dns_cache, config.conn_limit)
            self.__session_mapping[name] = client_session
    
    def require(self, name: str) -> Callable:
        def delayed_wrapper(async_callable: AsyncCallable) -> AsyncCallable:
            
            @functools.wraps(async_callable)
            async def wrapped_async_callable(*args, **kwargs):
                aiohttp_client_session = self.__session_mapping.get(name)

                if aiohttp_client_session is None:
                    raise KeyError("no client session configured")
                
                return await async_callable(aiohttp_client_session, *args, **kwargs)
            
            return wrapped_async_callable
        
        return delayed_wrapper
            

__all__ = ("HTTPSessionConfig", "HTTPSessions")