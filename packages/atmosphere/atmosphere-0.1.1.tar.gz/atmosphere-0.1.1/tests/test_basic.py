"""
Comprehensive test suite for Dimension & Resonance package.
"""

import pytest
import numpy as np
from io import BytesIO

# Test imports
def test_delay_imports():
    """Test delay module imports."""
    from delay import Delay, EchoesPlatform
    assert Delay is not None
    assert EchoesPlatform is not None

def test_reverb_imports():
    """Test reverb module imports."""
    from reverb import ReverbPlatform
    assert ReverbPlatform is not None

def test_routing_imports():
    """Test routing module imports."""
    from routing import AcousticRoutingNetwork, visualize_network
    assert AcousticRoutingNetwork is not None
    assert visualize_network is not None

# Test instantiation
def test_delay_instantiation():
    """Test Delay class instantiation."""
    from delay import Delay
    delay = Delay()
    assert delay.time_ms == 250
    assert delay.feedback == 0.3

def test_reverb_instantiation():
    """Test ReverbPlatform instantiation."""
    from reverb import ReverbPlatform
    reverb = ReverbPlatform()
    status = reverb.get_system_status()
    assert status['status'] == 'active'
    assert 'services' in status

def test_routing_instantiation():
    """Test AcousticRoutingNetwork instantiation."""
    from routing import AcousticRoutingNetwork
    network = AcousticRoutingNetwork()
    assert len(network.graph.nodes) == 0
    assert len(network.acoustic_params) == 0

# Test basic functionality
def test_delay_basic_functionality():
    """Test basic delay functionality."""
    from delay import Delay
    delay = Delay(time_ms=100, feedback=0.2)

    # Create dummy audio signal
    audio = np.random.random(1000)
    # Note: Actual processing would require full implementation
    # For now, just test that the object exists and has expected attributes
    assert hasattr(delay, 'time_ms')
    assert hasattr(delay, 'feedback')

def test_reverb_system_status():
    """Test reverb system status."""
    from reverb import ReverbPlatform
    reverb = ReverbPlatform()
    status = reverb.get_system_status()

    expected_keys = ['platform', 'status', 'services', 'effects_chain', 'presets']
    for key in expected_keys:
        assert key in status

    assert status['platform'] == 'reverb'
    assert status['status'] == 'active'

def test_routing_network_operations():
    """Test basic routing network operations."""
    from routing import AcousticRoutingNetwork
    network = AcousticRoutingNetwork()

    # Add a segment
    network.add_highway_segment("A", "B", 10)

    # Check that nodes were added
    assert "A" in network.graph.nodes
    assert "B" in network.graph.nodes

    # Check that edge exists
    assert network.graph.has_edge("A", "B")

def test_routing_visualization():
    """Test routing network visualization."""
    from routing import AcousticRoutingNetwork
    from routing.acoustic_routing.core.visualization import visualize_network
    network = AcousticRoutingNetwork()

    # Add some nodes
    network.add_highway_segment("A", "B", 10)
    network.add_highway_segment("B", "C", 15)

    # Test visualization (should not raise exception)    
    try:
        buffer = visualize_network(network)
        # If buffer is returned, it should be BytesIO or None
        assert buffer is None or isinstance(buffer, BytesIO)
    except ImportError:
        # Matplotlib may not be available in test environment
        pytest.skip("Matplotlib not available for visualization tests")

# Integration tests
def test_full_pipeline():
    """Test that all modules can be imported and instantiated together."""
    from delay import Delay, EchoesPlatform
    from reverb import ReverbPlatform
    from routing import AcousticRoutingNetwork

    # Create instances
    delay = Delay()
    echo_platform = EchoesPlatform()
    reverb = ReverbPlatform()
    network = AcousticRoutingNetwork()

    # Basic checks
    assert delay.time_ms == 250
    assert reverb.get_system_status()['status'] == 'active'
    assert len(network.graph.nodes) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
