import asyncio
from typing import Dict, Union
from loguru import logger
from ..client.game_client import GameClient






class GrandTournament(GameClient):
    """Grand Tournament operations handler."""
    
    
    
    
    
    async def get_tournament_missons(self, sync: bool = True) -> Union[Dict, bool]:
        """
        Get mission list for the Grand Tournament
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """ 
        
        
        try:
            if sync:
                return await self.send_rpc("aqs", {})
            
            else:
                await self.send_json_message("aqs", {})
                return True
        
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for GT missions response")
            return False
        except ConnectionError as e:
            logger.error(f"Connection error while getting GT missions: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while getting GT missions: {e}")
            return False
        
        
    async def get_tournament_contributors(self, sync: bool = True) -> Union[Dict, bool]:
        """
        Get contributors list for the Grand Tournament
        
        Args:
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """ 
        
        
        try:
            if sync:
                return await self.send_rpc("aqpc", {})
            
            else:
                await self.send_json_message("aqpc", {})
                return True
        
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for GT cotributors response")
            return False
        except ConnectionError as e:
            logger.error(f"Connection error while getting GT contributors: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while getting GT contributors: {e}")
            return False
        
        
    async def change_mission(
        self,
        mission_number: int,
        mission_id: int,
        sync: bool = True
    ) -> Union[Dict, bool]:
        """
        Missions management for the Grand Tournament
        
        Args:
            mission_number: Mission number from the list.
            mission_id: Mission Id
            sync: Whether to wait for server response
            
        Returns:
            Server response dictionary if sync=True and successful,
            True if async and successful, False on error
        """       
        
        try:
            if sync:
                data = {"S":mission_number,"QID":mission_id}
                return await self.send_rpc("raq", data)
            
            else:
                await self.send_json_message("raq", data)
                return True
              
        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for changing missions response")
            return False
        except ConnectionError as e:
            logger.error(f"Connection error while waiting for changing missions: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while waiting for changing missions: {e}")
            return False