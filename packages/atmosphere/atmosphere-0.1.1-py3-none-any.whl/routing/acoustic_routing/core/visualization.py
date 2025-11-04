"""
Visualization utilities for acoustic routing networks.

This module provides functions for visualizing network topologies
and acoustic propagation patterns.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Optional
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from io import BytesIO

def visualize_network(network, save_path: Optional[str] = None) -> Optional[BytesIO]:
    """
    Visualize the acoustic routing network with 3D depth and dimension.
    """

    # Create figure with enhanced 3D-like depth effects
    fig, ax = plt.subplots(figsize=(14, 10), facecolor='#0a0a0a')

    # Create gradient background for depth illusion
    gradient = np.linspace(0, 1, 100).reshape(1, -1)
    gradient = np.vstack((gradient, gradient))
    ax.imshow(gradient, extent=[-150, 150, -100, 100], aspect='auto',
             cmap='Blues', alpha=0.1, zorder=-1)

    # Add multiple depth layers with subtle grids
    for depth_level in [0.8, 0.6, 0.4]:
        ax.grid(True, which='both', color='#404040', linestyle='-',
               linewidth=0.3, alpha=depth_level * 0.2, zorder=depth_level)

    # Calculate 3D-like positioning based on acoustic parameters
    pos = network.node_positions.copy()

    # Add depth dimension based on connectivity and acoustic properties
    node_depths = {}
    node_sizes = {}
    node_alphas = {}

    for node in network.graph.nodes():
        # Calculate node's "depth" based on its connections and acoustic properties
        connected_params = []
        for neighbor in network.graph.neighbors(node):
            edge_key = (node, neighbor) if (node, neighbor) in network.acoustic_params else (neighbor, node)
            if edge_key in network.acoustic_params:
                connected_params.append(network.acoustic_params[edge_key])

        if connected_params:
            # Average acoustic properties determine depth
            avg_density = np.mean([p.reverb_density for p in connected_params])
            avg_delay = np.mean([p.delay_time for p in connected_params])
            avg_feedback = np.mean([p.feedback for p in connected_params])

            # Depth calculation: higher density = closer to viewer (larger, more opaque)
            depth_factor = (avg_density * 0.6 + (1 - avg_delay/10000) * 0.3 + avg_feedback * 0.1)
            node_depths[node] = max(0.3, min(1.0, depth_factor))
        else:
            node_depths[node] = 0.5

        # Size and alpha based on depth (perspective effect)
        base_size = 500
        depth_size = base_size * (0.8 + node_depths[node] * 0.4)  # Closer = larger
        node_sizes[node] = depth_size

        depth_alpha = 0.7 + node_depths[node] * 0.3  # Closer = more opaque
        node_alphas[node] = depth_alpha

    # Create dynamic edge colors based on acoustic parameters
    edge_colors = []
    edge_widths = []
    edge_alphas = []

    # Get acoustic parameter ranges for normalization
    delays = [params.delay_time for params in network.acoustic_params.values()]
    feedbacks = [params.feedback for params in network.acoustic_params.values()]
    # decays = [params.decay for params in network.acoustic_params.values()]  # Not used
    densities = [params.reverb_density for params in network.acoustic_params.values()]

    delay_min, delay_max = min(delays), max(delays) if delays else (0, 1)
    feedback_min, feedback_max = min(feedbacks), max(feedbacks) if feedbacks else (0, 1)
    density_min, density_max = min(densities), max(densities) if densities else (0, 1)

    # Create color mapping based on combined acoustic properties
    for (u, v) in network.graph.edges():
        if (u, v) in network.acoustic_params:
            params = network.acoustic_params[(u, v)]

            # Normalize parameters to 0-1 range
            delay_norm = (params.delay_time - delay_min) / (delay_max - delay_min) if delay_max > delay_min else 0.5
            feedback_norm = (params.feedback - feedback_min) / (feedback_max - feedback_min) if feedback_max > feedback_min else 0.5
            density_norm = (params.reverb_density - density_min) / (density_max - density_min) if density_max > density_min else 0.5

            # Create gradient color based on input/output principle
            if density_norm > 0.6:  # High connectivity (input-like)
                # Cool colors for input flows
                r = int(100 + (delay_norm * 100))  # Red increases with delay
                g = int(150 + (feedback_norm * 100))  # Green increases with feedback
                b = int(200 + (density_norm * 55))  # Blue high for connectivity
            else:  # Low connectivity (output-like)
                # Warm colors for output flows
                r = int(200 + (delay_norm * 55))  # Red high for delay
                g = int(100 + (feedback_norm * 100))  # Green varies with feedback
                b = int(100 + (density_norm * 100))  # Blue low for sparse connections

            # Ensure RGB values are within 0-255
            r, g, b = max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))

            # Create hex color
            color = f'#{r:02x}{g:02x}{b:02x}'
            edge_colors.append(color)

            # Dynamic width based on feedback (more feedback = thicker lines)
            width = 1.5 + (params.feedback * 3)
            edge_widths.append(width)

            # Alpha based on decay (less decay = more opaque)
            alpha = 0.6 + (params.decay * 0.4)
            edge_alphas.append(alpha)
        else:
            # Default fallback
            edge_colors.append('#cccccc')
            edge_widths.append(2)
            edge_alphas.append(0.8)

    # Draw nodes with depth-based sizing and shadow effects
    # First draw shadows for depth illusion
    for node in network.graph.nodes():
        x, y = pos[node]
        shadow_offset = (1 - node_depths.get(node, 0.5)) * 3  # Further back = larger shadow
        shadow_alpha = node_alphas.get(node, 0.8) * 0.3

        # Draw shadow circle
        shadow_circle = plt.Circle((x + shadow_offset, y - shadow_offset),
                                 node_sizes.get(node, 500) * 0.08,
                                 color='#000000', alpha=shadow_alpha, zorder=1)
        ax.add_patch(shadow_circle)

    # Draw main nodes with depth-based properties
    node_colors = []
    node_sizes_list = []
    node_alphas_list = []

    for node in network.graph.nodes():
        node_colors.append('#4a90e2')
        node_sizes_list.append(node_sizes.get(node, 500))
        node_alphas_list.append(node_alphas.get(node, 0.8))

    # Draw nodes with depth-based properties
    import networkx as nx
    nx.draw_networkx_nodes(network.graph, pos, node_color=node_colors,
                          node_size=node_sizes_list, alpha=node_alphas_list,
                          ax=ax)

    # Draw edges with individual colors and properties
    for i, (u, v) in enumerate(network.graph.edges()):
        color = edge_colors[i] if i < len(edge_colors) else '#cccccc'
        width = edge_widths[i] if i < len(edge_widths) else 2
        alpha = edge_alphas[i] if i < len(edge_alphas) else 0.8

        nx.draw_networkx_edges(network.graph, pos, edgelist=[(u, v)],
                             edge_color=color, width=width, alpha=alpha,
                             arrows=True, arrowsize=20, ax=ax)

    # Draw node labels with depth-based properties
    label_colors = []
    label_sizes = []
    for node in network.graph.nodes():
        depth = node_depths.get(node, 0.5)
        # Labels for closer nodes are more visible
        label_colors.append(('white', depth * 0.8 + 0.2))
        label_sizes.append(8 + depth * 4)  # Closer = larger labels

    # Draw labels individually with depth properties
    for i, node in enumerate(network.graph.nodes()):
        color, alpha = label_colors[i]
        fontsize = label_sizes[i]
        plt.annotate(node, pos[node], xytext=(0, 0), textcoords='offset points',
                    ha='center', va='center', fontsize=fontsize,
                    color=color, alpha=alpha, fontweight='bold', zorder=3)

    # Enhanced title with depth context
    ax.set_title('Dimension & Resonance Acoustic Network\n(Component Interconnectivity with 3D Depth)',
                fontsize=16, fontweight='bold', color='white',
                pad=20, bbox=dict(boxstyle="round,pad=0.7",
                                facecolor='#2a2a2a',
                                edgecolor='#404040',
                                alpha=0.9))

    # Set axis limits to show full depth range
    all_x = [pos[node][0] for node in pos]
    all_y = [pos[node][1] for node in pos]
    margin = 20
    ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
    ax.set_ylim(min(all_y) - margin, max(all_y) + margin)

    # Remove axis ticks for cleaner look
    ax.set_xticks([])
    ax.set_yticks([])

    # Add depth legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#4a90e2',
                  markersize=15, alpha=0.9, label='High Connectivity (Close)'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#4a90e2',
                  markersize=10, alpha=0.6, label='Medium Connectivity'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#4a90e2',
                  markersize=8, alpha=0.4, label='Low Connectivity (Far)')
    ]
    ax.legend(handles=legend_elements, loc='upper right',
             facecolor='#2a2a2a', edgecolor='#404040',
             labelcolor='white', fontsize=8)

    # Add subtle border with depth effect
    for spine in ax.spines.values():
        spine.set_edgecolor('#404040')
        spine.set_linewidth(2)
        spine.set_alpha(0.5)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight',
                   facecolor=fig.get_facecolor(), edgecolor='none')
        return None
    else:
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight',
                   facecolor=fig.get_facecolor(), edgecolor='none')
        buffer.seek(0)
        plt.close(fig)
        return buffer
