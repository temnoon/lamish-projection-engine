#!/usr/bin/env python3
"""Interactive maieutic dialogue for narrative exploration."""
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from lamish_projection_engine.core.maieutic import run_maieutic_dialogue

if __name__ == "__main__":
    try:
        run_maieutic_dialogue()
    except KeyboardInterrupt:
        print("\n\nDialogue interrupted.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()