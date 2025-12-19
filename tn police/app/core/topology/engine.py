"""
TOR Topology Engine - Core Component

This module is responsible for:
1. Fetching public TOR relay metadata from official sources
2. Parsing and normalizing relay descriptors
3. Building time-aware topology snapshots
4. Maintaining topology history

Data Sources:
- TOR Metrics (Onionoo) API: https://onionoo.torproject.org/
- TOR Collector: https://collector.torproject.org/

LEGAL NOTICE:
This module uses ONLY publicly available TOR relay metadata.
All data is published by the TOR Project for transparency and research.
"""
import httpx
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

from app.models.topology import TORRelay, TopologySnapshot, RelayFlags
from config import settings


logger = logging.getLogger(__name__)


class TORTopologyEngine:
    """
    Manages fetching, parsing, and storing TOR network topology data
    
    This engine provides the foundational network graph for all correlation analysis.
    It maintains time-aware snapshots to enable historical analysis.
    """
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.cache_dir = settings.RAW_DATA_DIR
        self.processed_dir = settings.PROCESSED_DATA_DIR
        
        logger.info("TOR Topology Engine initialized")
    
    async def fetch_relay_details(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch relay details from TOR Onionoo API
        
        Onionoo provides a JSON API with comprehensive relay metadata
        including flags, bandwidth, geographic info, and version data.
        
        Args:
            limit: Optional limit on number of relays to fetch (for testing)
        
        Returns:
            List of relay data dictionaries
        
        Raises:
            httpx.HTTPError: If API request fails
        """
        logger.info("Fetching relay details from Onionoo API...")
        
        try:
            # Onionoo details endpoint provides comprehensive relay information
            url = f"{settings.TOR_METRICS_API}details"
            
            params = {
                "running": "true",  # Only fetch currently running relays
                "fields": "nickname,fingerprint,or_addresses,dir_address,last_seen,first_seen,"
                         "flags,country,as_number,as_name,consensus_weight,"
                         "observed_bandwidth,advertised_bandwidth,platform,version,contact,"
                         "exit_policy_summary,last_changed_address_or_port"
            }
            
            if limit:
                params["limit"] = str(limit)
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            relays = data.get("relays", [])
            
            logger.info(f"Successfully fetched {len(relays)} relay records from Onionoo")
            
            # Cache raw response
            await self._cache_raw_response(data, "onionoo_details")
            
            return relays
        
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch relay details: {e}")
            raise
    
    async def _cache_raw_response(self, data: Dict[str, Any], source: str):
        """Cache raw API response for audit trail"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{source}_{timestamp}.json"
        filepath = self.cache_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.debug(f"Cached raw response to {filepath}")
    
    def _parse_relay(self, relay_data: Dict[str, Any], snapshot_time: datetime) -> Optional[TORRelay]:
        """
        Parse raw relay data from Onionoo into our TORRelay model
        
        Args:
            relay_data: Raw relay dictionary from Onionoo
            snapshot_time: Timestamp of this snapshot
        
        Returns:
            TORRelay object or None if parsing fails
        """
        try:
            # Extract primary identifiers
            fingerprint = relay_data.get("fingerprint", "")
            nickname = relay_data.get("nickname")
            
            # Extract network information
            # or_addresses is a list like ["1.2.3.4:9001", "[ipv6]:9001"]
            or_addresses = relay_data.get("or_addresses", [])
            if not or_addresses:
                logger.warning(f"Relay {fingerprint} has no OR addresses, skipping")
                return None
            
            # Parse first IPv4 address and port
            primary_address = or_addresses[0]
            if ":" in primary_address:
                # Handle both IPv4 and bracketed IPv6
                if primary_address.startswith("["):
                    # IPv6 format: [address]:port
                    address = primary_address.split("]")[0][1:]
                    or_port = int(primary_address.split(":")[-1])
                else:
                    # IPv4 format: address:port
                    address, port_str = primary_address.rsplit(":", 1)
                    or_port = int(port_str)
            else:
                logger.warning(f"Relay {fingerprint} has malformed address, skipping")
                return None
            
            # Parse directory port if available
            dir_address = relay_data.get("dir_address")
            dir_port = None
            if dir_address and ":" in dir_address:
                dir_port = int(dir_address.split(":")[-1])
            
            # Parse bandwidth metrics
            observed_bw = relay_data.get("observed_bandwidth", 0)
            advertised_bw = relay_data.get("advertised_bandwidth", 0)
            consensus_weight = relay_data.get("consensus_weight", 0)
            
            # Parse relay flags
            flags_raw = relay_data.get("flags", [])
            flags = []
            for flag in flags_raw:
                try:
                    flags.append(RelayFlags(flag))
                except ValueError:
                    # Unknown flag, skip it
                    logger.debug(f"Unknown flag '{flag}' for relay {fingerprint}")
            
            # Parse timestamps
            first_seen = self._parse_timestamp(relay_data.get("first_seen"))
            last_seen = self._parse_timestamp(relay_data.get("last_seen"))
            last_changed = self._parse_timestamp(relay_data.get("last_changed_address_or_port"))
            
            # Geographic and network info
            country_code = relay_data.get("country")
            as_number = relay_data.get("as_number")
            as_name = relay_data.get("as_name")
            
            # Version and platform
            platform = relay_data.get("platform")
            version = relay_data.get("version")
            
            # Contact and policies
            contact = relay_data.get("contact")
            exit_policy = relay_data.get("exit_policy_summary")
            
            # Create TORRelay object
            relay = TORRelay(
                fingerprint=fingerprint,
                nickname=nickname,
                address=address,
                or_port=or_port,
                dir_port=dir_port,
                observed_bandwidth=observed_bw,
                advertised_bandwidth=advertised_bw,
                consensus_weight=consensus_weight,
                flags=flags,
                country_code=country_code,
                as_number=as_number,
                as_name=as_name,
                first_seen=first_seen,
                last_seen=last_seen,
                last_changed_address_or_port=last_changed,
                platform=platform,
                version=version,
                contact=contact,
                exit_policy_summary=exit_policy,
                snapshot_timestamp=snapshot_time
            )
            
            return relay
        
        except Exception as e:
            logger.error(f"Failed to parse relay {relay_data.get('fingerprint', 'unknown')}: {e}")
            return None
    
    def _parse_timestamp(self, ts_str: Optional[str]) -> datetime:
        """Parse ISO timestamp string to datetime object"""
        if not ts_str:
            return datetime.utcnow()
        
        try:
            # Onionoo uses ISO 8601 format: "2025-12-20 12:00:00"
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except Exception as e:
            logger.warning(f"Failed to parse timestamp '{ts_str}': {e}")
            return datetime.utcnow()
    
    async def create_topology_snapshot(self, limit: Optional[int] = None) -> TopologySnapshot:
        """
        Create a complete topology snapshot of the TOR network
        
        This is the main entry point for getting current network state.
        
        Args:
            limit: Optional limit on relays (for testing with smaller datasets)
        
        Returns:
            TopologySnapshot containing all parsed relays
        """
        logger.info("Creating new topology snapshot...")
        snapshot_time = datetime.utcnow()
        
        # Fetch raw relay data
        raw_relays = await self.fetch_relay_details(limit=limit)
        
        # Parse into TORRelay objects
        relays = []
        for raw_relay in raw_relays:
            relay = self._parse_relay(raw_relay, snapshot_time)
            if relay:
                relays.append(relay)
        
        # Calculate statistics
        total_relays = len(relays)
        guard_relays = sum(1 for r in relays if r.is_guard)
        exit_relays = sum(1 for r in relays if r.is_exit)
        
        total_bandwidth = sum(r.observed_bandwidth for r in relays)
        avg_bandwidth = total_bandwidth / total_relays if total_relays > 0 else 0.0
        
        # Create snapshot ID
        snapshot_id = f"snapshot-{snapshot_time.strftime('%Y%m%d-%H%M%S')}"
        
        # Create snapshot object
        snapshot = TopologySnapshot(
            snapshot_id=snapshot_id,
            valid_after=snapshot_time,
            valid_until=snapshot_time + timedelta(hours=1),  # Assume 1-hour validity
            fresh_until=snapshot_time + timedelta(minutes=30),
            total_relays=total_relays,
            guard_relays=guard_relays,
            exit_relays=exit_relays,
            relays=relays,
            avg_bandwidth=avg_bandwidth,
            total_bandwidth=total_bandwidth,
            created_at=snapshot_time
        )
        
        logger.info(f"Created snapshot {snapshot_id}: {total_relays} relays "
                   f"({guard_relays} guards, {exit_relays} exits)")
        
        # Save snapshot to disk
        await self._save_snapshot(snapshot)
        
        return snapshot
    
    async def _save_snapshot(self, snapshot: TopologySnapshot):
        """Save topology snapshot to disk for persistence"""
        filename = f"{snapshot.snapshot_id}.json"
        filepath = self.processed_dir / filename
        
        # Convert to JSON-serializable dict
        snapshot_dict = snapshot.model_dump(mode='json')
        
        with open(filepath, 'w') as f:
            json.dump(snapshot_dict, f, indent=2, default=str)
        
        logger.info(f"Saved snapshot to {filepath}")
    
    async def load_snapshot(self, snapshot_id: str) -> Optional[TopologySnapshot]:
        """Load a previously saved topology snapshot"""
        filename = f"{snapshot_id}.json"
        filepath = self.processed_dir / filename
        
        if not filepath.exists():
            logger.warning(f"Snapshot {snapshot_id} not found")
            return None
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            snapshot = TopologySnapshot(**data)
            logger.info(f"Loaded snapshot {snapshot_id}")
            return snapshot
        
        except Exception as e:
            logger.error(f"Failed to load snapshot {snapshot_id}: {e}")
            return None
    
    def list_snapshots(self) -> List[str]:
        """List all available topology snapshots"""
        snapshots = []
        for filepath in self.processed_dir.glob("snapshot-*.json"):
            snapshot_id = filepath.stem
            snapshots.append(snapshot_id)
        
        return sorted(snapshots, reverse=True)  # Most recent first
    
    async def close(self):
        """Clean up resources"""
        await self.client.aclose()
        logger.info("TOR Topology Engine closed")
