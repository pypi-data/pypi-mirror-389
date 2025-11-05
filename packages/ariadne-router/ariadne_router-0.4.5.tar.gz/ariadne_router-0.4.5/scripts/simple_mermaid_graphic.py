#!/usr/bin/env python3
"""
Create a simplified, clean decision tree graphic for social media.
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch


def create_simple_decision_tree():
    """Create a super clean, minimal decision tree."""

    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis("off")

    # Modern color palette
    colors = {
        "primary": "#2196F3",  # Blue
        "success": "#4CAF50",  # Green
        "warning": "#FF9800",  # Orange
        "secondary": "#9C27B0",  # Purple
        "neutral": "#607D8B",  # Blue grey
    }

    def create_circle(x, y, text, color, size=0.8):
        """Create a circular node."""
        circle = Circle((x, y), size / 2, facecolor=color, alpha=0.9, edgecolor="white", linewidth=3)
        ax.add_patch(circle)
        ax.text(x, y, text, ha="center", va="center", fontsize=10, fontweight="bold", color="white")

    def create_rect(x, y, width, height, text, color):
        """Create a rectangular node."""
        rect = FancyBboxPatch(
            (x - width / 2, y - height / 2),
            width,
            height,
            boxstyle="round,pad=0.1",
            facecolor=color,
            alpha=0.9,
            edgecolor="white",
            linewidth=2,
        )
        ax.add_patch(rect)
        lines = text.split("\n")
        for i, line in enumerate(lines):
            ax.text(
                x,
                y + (len(lines) - 1 - 2 * i) * 0.15,
                line,
                ha="center",
                va="center",
                fontsize=9,
                fontweight="bold",
                color="white",
            )

    def draw_arrow(x1, y1, x2, y2, label=""):
        """Draw arrow between nodes."""
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", lw=2.5, color="#424242", alpha=0.8)
        )
        if label:
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(
                mid_x,
                mid_y + 0.15,
                label,
                ha="center",
                va="center",
                fontsize=8,
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.9, edgecolor="#ccc"),
            )

    # Title
    ax.text(5, 7.3, "Ariadne: Smart Quantum Simulator Router", ha="center", va="center", fontsize=16, fontweight="bold")
    ax.text(
        5,
        6.9,
        "Automatic backend selection for optimal performance",
        ha="center",
        va="center",
        fontsize=11,
        color="#666",
        style="italic",
    )

    # Input
    create_circle(5, 6, "Quantum\nCircuit", colors["primary"])

    # Analysis step
    create_rect(5, 5, 2.5, 0.6, "Circuit Analysis\nClifford • Entanglement • Topology", colors["neutral"])
    draw_arrow(5, 5.6, 5, 5.3)

    # Decision nodes
    create_circle(2, 3.5, "Clifford\nOnly?", colors["warning"], 0.7)
    create_circle(5, 3.5, "Low\nEntangle?", colors["warning"], 0.7)
    create_circle(8, 3.5, "GPU\nAvailable?", colors["warning"], 0.7)

    # Decision arrows
    draw_arrow(4.2, 4.5, 2.7, 4)
    draw_arrow(5, 4.7, 5, 4)
    draw_arrow(5.8, 4.5, 7.3, 4)

    # Backend results
    create_rect(2, 2, 1.6, 0.8, "Stim\n100K+ shots/s", colors["success"])
    create_rect(5, 2, 1.6, 0.8, "MPS\n5K shots/s", colors["success"])
    create_rect(8, 2, 1.6, 0.8, "CUDA/Metal\n50x faster", colors["success"])

    # Result arrows
    draw_arrow(2, 3.1, 2, 2.4, "YES")
    draw_arrow(5, 3.1, 5, 2.4, "YES")
    draw_arrow(8, 3.1, 8, 2.4, "YES")

    # Fallback
    create_rect(5, 0.8, 2.2, 0.6, "Qiskit Aer (Fallback)\nGeneral Purpose", colors["secondary"])

    # Fallback arrows
    draw_arrow(2, 3.1, 4.2, 1.2, "NO")
    draw_arrow(5, 3.1, 5, 1.4, "NO")
    draw_arrow(8, 3.1, 5.8, 1.2, "NO")

    # Bottom highlight
    ax.text(
        5,
        0.2,
        "🎯 Result: Up to 100x performance improvement automatically!",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFF3E0", edgecolor=colors["warning"], linewidth=2),
    )

    plt.tight_layout()
    return fig


def create_before_after_graphic():
    """Create a simple before/after comparison."""

    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")

    # Title
    ax.text(
        6, 5.5, "Quantum Computing: Before vs After Ariadne", ha="center", va="center", fontsize=16, fontweight="bold"
    )

    # Before section
    ax.text(
        3, 4.8, "BEFORE: The Simulator Maze", ha="center", va="center", fontsize=14, fontweight="bold", color="#D32F2F"
    )

    before_box = FancyBboxPatch(
        (0.5, 2), 5, 2.5, boxstyle="round,pad=0.3", facecolor="#FFEBEE", edgecolor="#D32F2F", linewidth=2
    )
    ax.add_patch(before_box)

    before_text = """1. Write quantum circuit
2. Research which simulator to use
3. Try Stim... doesn't work for general circuits
4. Try Qiskit... slow for Clifford circuits
5. Try MPS... good for some, not others
6. Hours later... suboptimal results"""

    ax.text(3, 3.2, before_text, ha="center", va="center", fontsize=10, linespacing=1.5)

    # After section
    ax.text(
        9, 4.8, "AFTER: Intelligent Routing", ha="center", va="center", fontsize=14, fontweight="bold", color="#388E3C"
    )

    after_box = FancyBboxPatch(
        (6.5, 2), 5, 2.5, boxstyle="round,pad=0.3", facecolor="#E8F5E8", edgecolor="#388E3C", linewidth=2
    )
    ax.add_patch(after_box)

    after_text = """1. Write quantum circuit
2. from ariadne import simulate
3. result = simulate(circuit, shots=1000)
4. Ariadne automatically picks optimal backend
5. 10-100x performance improvement
6. Focus on algorithms, not infrastructure!"""

    ax.text(9, 3.2, after_text, ha="center", va="center", fontsize=10, linespacing=1.5)

    # Arrow between
    ax.annotate("", xy=(6.3, 3.2), xytext=(5.7, 3.2), arrowprops=dict(arrowstyle="->", lw=5, color="#FF9800"))
    ax.text(6, 3.6, "Ariadne", ha="center", va="center", fontsize=12, fontweight="bold", color="#FF9800")

    # Bottom call to action
    ax.text(
        6,
        1.2,
        "pip install ariadne-router",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#E3F2FD", edgecolor="#1976D2", linewidth=2),
    )
    ax.text(6, 0.6, "github.com/Hmbown/ariadne", ha="center", va="center", fontsize=11, color="#666")

    plt.tight_layout()
    return fig


def main():
    """Create simplified social graphics."""

    output_dir = Path("social_graphics")
    output_dir.mkdir(exist_ok=True)

    print("🎨 Creating simplified social media graphics...")

    # Simple decision tree
    print("  🌳 Creating clean decision tree...")
    fig1 = create_simple_decision_tree()
    fig1.savefig(output_dir / "ariadne_decision_tree_clean.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig1)

    # Before/after comparison
    print("  🔄 Creating before/after comparison...")
    fig2 = create_before_after_graphic()
    fig2.savefig(output_dir / "ariadne_before_after.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig2)

    print(f"\n✅ Additional graphics saved to {output_dir}/")
    print("   🌳 ariadne_decision_tree_clean.png - Clean decision flowchart")
    print("   🔄 ariadne_before_after.png - Before/after problem comparison")


if __name__ == "__main__":
    main()
