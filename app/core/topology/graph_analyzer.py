"""
Graph analysis utilities for TOR topology

Provides graph-based analysis of TOR network structure:
- Path feasibility checking
- Guard-to-exit path analysis
- Relay family and subnet constraints
"""
import networkx as nx
import logging
from typing import List, Set, Tuple, Optional
from ipaddress import ip_address, ip_network

from app.models.topology import TORRelay, TopologySnapshot, TORCircuit


logger = logging.getLogger(__name__)


class TORGraphAnalyzer:
    """
    Analyzes TOR network topology as a graph
    
    Implements TOR path selection constraints:
    - No relays in the same /16 subnet
    - No relays in the same family
    - Proper flag requirements (Guard -> Middle -> Exit)
    """
    
    def __init__(self, snapshot: TopologySnapshot):
        self.snapshot = snapshot
        self.graph = nx.DiGraph()
        self._build_graph()
        
        logger.info(f"Graph analyzer initialized with {len(self.snapshot.relays)} relays")
    
    def _build_graph(self):
        """Build NetworkX graph from topology snapshot"""
        # Add all relays as nodes
        for relay in self.snapshot.relays:
            self.graph.add_node(
                relay.fingerprint,
                relay=relay,
                is_guard=relay.is_guard,
                is_exit=relay.is_exit,
                address=relay.address,
                bandwidth=relay.observed_bandwidth
            )
        
        logger.info(f"Built graph with {self.graph.number_of_nodes()} nodes")
    
    def _same_subnet(self, ip1: str, ip2: str) -> bool:
        """Check if two IPs are in the same /16 subnet (TOR constraint)"""
        try:
            addr1 = ip_address(ip1)
            addr2 = ip_address(ip2)
            
            # TOR uses /16 for IPv4, /32 for IPv6
            if addr1.version == 4 and addr2.version == 4:
                net1 = ip_network(f"{ip1}/16", strict=False)
                return addr2 in net1
            
            # For IPv6 or mixed, consider them different subnets
            return False
        
        except Exception as e:
            logger.warning(f"Failed to check subnet for {ip1}, {ip2}: {e}")
            return False
    
    def is_valid_circuit(self, guard_fp: str, middle_fp: str, exit_fp: str) -> Tuple[bool, List[str]]:
        """
        Check if a 3-hop circuit satisfies TOR path selection constraints
        
        Args:
            guard_fp: Guard relay fingerprint
            middle_fp: Middle relay fingerprint
            exit_fp: Exit relay fingerprint
        
        Returns:
            Tuple of (is_valid, list_of_constraint_violations)
        """
        violations = []
        
        # Get relay objects
        guard = self._get_relay(guard_fp)
        middle = self._get_relay(middle_fp)
        exit_relay = self._get_relay(exit_fp)
        
        if not all([guard, middle, exit_relay]):
            violations.append("One or more relays not found in topology")
            return False, violations
        
        # Constraint 1: Guard must have Guard flag
        if not guard.is_guard:
            violations.append("First relay is not a guard")
        
        # Constraint 2: Exit must have Exit flag
        if not exit_relay.is_exit:
            violations.append("Last relay is not an exit")
        
        # Constraint 3: No same /16 subnet
        if self._same_subnet(guard.address, middle.address):
            violations.append("Guard and middle in same /16 subnet")
        
        if self._same_subnet(middle.address, exit_relay.address):
            violations.append("Middle and exit in same /16 subnet")
        
        if self._same_subnet(guard.address, exit_relay.address):
            violations.append("Guard and exit in same /16 subnet")
        
        # Constraint 4: All must be Running and Valid
        for relay, name in [(guard, "guard"), (middle, "middle"), (exit_relay, "exit")]:
            if not any(f.value == "Running" for f in relay.flags):
                violations.append(f"{name} relay is not Running")
            if not any(f.value == "Valid" for f in relay.flags):
                violations.append(f"{name} relay is not Valid")
        
        is_valid = len(violations) == 0
        return is_valid, violations
    
    def _get_relay(self, fingerprint: str) -> Optional[TORRelay]:
        """Get relay by fingerprint"""
        for relay in self.snapshot.relays:
            if relay.fingerprint == fingerprint:
                return relay
        return None
    
    def get_possible_guards(self) -> List[TORRelay]:
        """Get all relays that can serve as guards"""
        guards = [r for r in self.snapshot.relays if r.is_guard]
        # Sort by consensus weight (higher weight = more likely to be selected)
        guards.sort(key=lambda r: r.consensus_weight, reverse=True)
        return guards
    
    def get_possible_exits(self) -> List[TORRelay]:
        """Get all relays that can serve as exits"""
        exits = [r for r in self.snapshot.relays if r.is_exit]
        exits.sort(key=lambda r: r.consensus_weight, reverse=True)
        return exits
    
    def get_compatible_guards_for_exit(self, exit_fp: str) -> List[TORRelay]:
        """
        Get all guards that could theoretically be used with a given exit
        (considering subnet constraints)
        """
        exit_relay = self._get_relay(exit_fp)
        if not exit_relay:
            return []
        
        compatible_guards = []
        for guard in self.get_possible_guards():
            # Check subnet constraint
            if not self._same_subnet(guard.address, exit_relay.address):
                compatible_guards.append(guard)
        
        return compatible_guards
    
    def estimate_guard_selection_probability(self, guard_fp: str) -> float:
        """
        Estimate the probability a given guard would be selected
        
        TOR uses weighted random selection based on consensus weight
        This gives a rough probability estimate
        """
        guard = self._get_relay(guard_fp)
        if not guard or not guard.is_guard:
            return 0.0
        
        all_guards = self.get_possible_guards()
        total_weight = sum(g.consensus_weight for g in all_guards)
        
        if total_weight == 0:
            return 0.0
        
        probability = (guard.consensus_weight / total_weight) * 100
        return probability
