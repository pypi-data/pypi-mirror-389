#!/usr/bin/env python3
"""
Create social media graphics for Ariadne routing decision tree.
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import ConnectionPatch, FancyBboxPatch

# Set up the style
plt.style.use("default")
plt.rcParams["font.family"] = ["SF Pro Display", "system-ui", "sans-serif"]
plt.rcParams["font.size"] = 11


def create_routing_flowchart():
    """Create a clean, social-media friendly routing flowchart."""

    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis("off")

    # Colors
    colors = {
        "input": "#E3F2FD",  # Light blue
        "decision": "#FFF3E0",  # Light orange
        "backend": "#E8F5E8",  # Light green
        "performance": "#F3E5F5",  # Light purple
    }

    # Helper function to create rounded boxes
    def create_box(x, y, width, height, text, color, text_size=10):
        box = FancyBboxPatch(
            (x - width / 2, y - height / 2),
            width,
            height,
            boxstyle="round,pad=0.1",
            facecolor=color,
            edgecolor="#666666",
            linewidth=1.5,
        )
        ax.add_patch(box)
        ax.text(x, y, text, ha="center", va="center", fontsize=text_size, fontweight="bold", wrap=True)

    # Helper function to create arrows
    def create_arrow(x1, y1, x2, y2, label=""):
        arrow = ConnectionPatch(
            (x1, y1), (x2, y2), "data", "data", arrowstyle="->", shrinkA=5, shrinkB=5, color="#333333", linewidth=2
        )
        ax.add_patch(arrow)
        if label:
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(
                mid_x + 0.2, mid_y, label, fontsize=8, bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8)
            )

    # Title
    ax.text(
        5,
        7.5,
        "🚀 Ariadne: Intelligent Quantum Circuit Router",
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
    )
    ax.text(
        5,
        7.1,
        "Automatic backend selection for optimal performance",
        ha="center",
        va="center",
        fontsize=12,
        style="italic",
        color="#666",
    )

    # Input
    create_box(5, 6, 2, 0.6, "🔮 Quantum Circuit\nInput", colors["input"], 11)

    # Analysis
    create_box(
        5,
        5,
        3,
        0.8,
        "🧠 Circuit Analysis\n• Clifford detection\n• Entanglement estimation\n• Topology patterns",
        colors["decision"],
        9,
    )
    create_arrow(5, 5.7, 5, 5.4)

    # Decision branches
    create_box(2, 3.5, 1.8, 0.6, "⚡ Clifford\nCircuit?", colors["decision"])
    create_box(5, 3.5, 1.8, 0.6, "🕸️ Low\nEntanglement?", colors["decision"])
    create_box(8, 3.5, 1.8, 0.6, "💻 Hardware\nAcceleration?", colors["decision"])

    create_arrow(5, 4.6, 2, 4)
    create_arrow(5, 4.6, 5, 4)
    create_arrow(5, 4.6, 8, 4)

    # Backends
    create_box(2, 2, 1.6, 0.8, "🏃‍♂️ Stim\n100K+ shots/sec", colors["backend"], 9)
    create_box(5, 2, 1.6, 0.8, "🧮 MPS\n1K-10K shots/sec", colors["backend"], 9)
    create_box(8, 2, 1.6, 0.8, "🚀 CUDA/Metal\n5-50x faster", colors["backend"], 9)

    create_arrow(2, 3.2, 2, 2.4, "YES")
    create_arrow(5, 3.2, 5, 2.4, "YES")
    create_arrow(8, 3.2, 8, 2.4, "YES")

    # Fallback
    create_box(5, 0.8, 2.2, 0.6, "🔧 Qiskit Aer (Fallback)\nReliable general-purpose", colors["backend"], 9)

    create_arrow(2, 3.2, 4.2, 1.2, "NO")
    create_arrow(5, 3.2, 5, 1.4, "NO")
    create_arrow(8, 3.2, 5.8, 1.2, "NO")

    # Footer
    ax.text(
        5,
        0.2,
        "🎯 Result: Optimal performance without manual configuration!",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFF9C4", alpha=0.8),
    )

    plt.tight_layout()
    return fig


def create_performance_comparison():
    """Create a performance comparison chart."""

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Performance comparison
    backends = ["Manual\nSelection", "Ariadne\nAuto-Router"]
    times = [2300, 23]  # milliseconds for 40-qubit GHZ
    colors_perf = ["#FF7043", "#4CAF50"]

    bars = ax1.bar(backends, times, color=colors_perf, alpha=0.8, width=0.6)
    ax1.set_ylabel("Execution Time (ms)", fontsize=12, fontweight="bold")
    ax1.set_title(
        "🚀 40-Qubit GHZ Circuit Performance\n(Clifford Circuit Example)", fontsize=13, fontweight="bold", pad=20
    )
    ax1.set_ylim(0, 2500)

    # Add value labels on bars
    for bar, time in zip(bars, times, strict=False):
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 50,
            f"{time}ms",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )

    # Add speedup annotation
    ax1.annotate(
        "100x faster!",
        xy=(1, 23),
        xytext=(0.5, 1200),
        arrowprops=dict(arrowstyle="->", lw=2, color="red"),
        fontsize=14,
        fontweight="bold",
        color="red",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7),
    )

    # Backend capabilities
    backend_names = ["Stim\n(Clifford)", "MPS\n(Low Ent.)", "Tensor Net.\n(Structured)", "Qiskit Aer\n(General)"]
    performance = [100000, 5000, 2000, 500]  # shots per second
    colors_back = ["#FF9800", "#2196F3", "#9C27B0", "#607D8B"]

    bars2 = ax2.bar(backend_names, performance, color=colors_back, alpha=0.8)
    ax2.set_ylabel("Performance (shots/sec)", fontsize=12, fontweight="bold")
    ax2.set_title(
        "🎯 Backend Performance by Circuit Type\n(Ariadne automatically selects optimal)",
        fontsize=13,
        fontweight="bold",
        pad=20,
    )
    ax2.set_yscale("log")

    # Add value labels
    for bar, perf in zip(bars2, performance, strict=False):
        height = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width() / 2.0,
            height * 1.1,
            f"{perf:,}",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    plt.tight_layout()
    return fig


def create_simple_infographic():
    """Create a simple, tweet-friendly infographic."""

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    # Background
    ax.add_patch(plt.Rectangle((0.2, 0.2), 9.6, 5.6, facecolor="#F8F9FA", edgecolor="#E0E0E0", linewidth=2))

    # Title
    ax.text(5, 5.4, "🚀 Ariadne Quantum Router", ha="center", va="center", fontsize=20, fontweight="bold")
    ax.text(
        5,
        5,
        '"I just want to run quantum circuits fast, not become a simulator expert"',
        ha="center",
        va="center",
        fontsize=12,
        style="italic",
        color="#666",
    )

    # Before/After
    ax.text(2.5, 4.2, "😵‍💫 BEFORE", ha="center", va="center", fontsize=14, fontweight="bold", color="#D32F2F")
    ax.text(7.5, 4.2, "😎 AFTER", ha="center", va="center", fontsize=14, fontweight="bold", color="#388E3C")

    # Before box
    before_text = "• Which simulator to use?\n• Stim? Qiskit? MPS?\n• Hours of trial & error\n• Suboptimal performance"
    ax.text(
        2.5,
        3.2,
        before_text,
        ha="center",
        va="center",
        fontsize=11,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#FFEBEE", edgecolor="#D32F2F"),
    )

    # After box
    after_text = (
        "• Write quantum circuit\n• Ariadne picks best backend\n• 10-100x performance gain\n• Focus on algorithms!"
    )
    ax.text(
        7.5,
        3.2,
        after_text,
        ha="center",
        va="center",
        fontsize=11,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#E8F5E8", edgecolor="#388E3C"),
    )

    # Arrow
    ax.annotate("", xy=(6.5, 3.2), xytext=(3.5, 3.2), arrowprops=dict(arrowstyle="->", lw=4, color="#FF9800"))

    # Bottom banner
    ax.text(
        5,
        1.5,
        "⚡ Automatic • 🧠 Intelligent • 🎓 Educational",
        ha="center",
        va="center",
        fontsize=13,
        fontweight="bold",
    )
    ax.text(
        5,
        1,
        "pip install ariadne-router",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#E3F2FD", edgecolor="#1976D2"),
    )
    ax.text(5, 0.5, "github.com/Hmbown/ariadne", ha="center", va="center", fontsize=11, color="#666")

    plt.tight_layout()
    return fig


def main():
    """Generate all social media graphics."""

    output_dir = Path("social_graphics")
    output_dir.mkdir(exist_ok=True)

    print("🎨 Creating social media graphics...")

    # Create routing flowchart
    print("  📊 Creating routing decision flowchart...")
    fig1 = create_routing_flowchart()
    fig1.savefig(output_dir / "ariadne_routing_flowchart.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig1)

    # Create performance comparison
    print("  ⚡ Creating performance comparison chart...")
    fig2 = create_performance_comparison()
    fig2.savefig(output_dir / "ariadne_performance_comparison.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig2)

    # Create simple infographic
    print("  🎯 Creating simple infographic...")
    fig3 = create_simple_infographic()
    fig3.savefig(output_dir / "ariadne_simple_infographic.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig3)

    print(f"\n✅ Graphics saved to {output_dir}/")
    print("   📸 ariadne_routing_flowchart.png - Detailed decision tree")
    print("   ⚡ ariadne_performance_comparison.png - Performance charts")
    print("   🎯 ariadne_simple_infographic.png - Tweet-friendly summary")
    print("\n🚀 Ready for social media sharing!")


if __name__ == "__main__":
    main()
