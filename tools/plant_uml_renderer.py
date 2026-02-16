"""
PlantUML Renderer Tool
Generates PNG diagrams from PlantUML code using local PlantUML jar
"""

import os
import subprocess
import shutil
import tempfile
from typing import Optional

from utils.constants import PLANTUML_JAR_PATH
from utils.file_utils import ensure_directory_exists, save_png_file, load_file


def render_plantuml_to_png(
    plantuml_code: str,
    output_path: str,
    temp_dir: Optional[str] = None
) -> Optional[str]:
    """
    Core renderer: PlantUML string → PNG
    """

    # Use system temp directory if not specified
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp(prefix="plantuml_")
    else:
        ensure_directory_exists(temp_dir)

    try:
        temp_puml_path = os.path.join(temp_dir, "diagram.puml")

        with open(temp_puml_path, "w", encoding="utf-8") as f:
            f.write(plantuml_code)

        # Build command with headless flags
        cmd = [
            "java",
            "-Djava.awt.headless=true",
            "-Dapple.awt.UIElement=true",
            "-jar",
            PLANTUML_JAR_PATH,
            "-tpng",
            "-nbthread", "1",
            temp_puml_path
        ]

        print(f"[PlantUMLRenderer] Running: {' '.join(cmd)}")

        # Run subprocess (same for all platforms)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print("[PlantUMLRenderer] ❌ Error:")
            print(result.stderr)
            return None

        generated_png = os.path.join(temp_dir, "diagram.png")

        if not os.path.exists(generated_png):
            print("[PlantUMLRenderer] ❌ PNG not generated")
            return None

        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        ensure_directory_exists(output_dir)

        # Copy to final location
        save_png_file(generated_png, output_path)

        print(f"[PlantUMLRenderer] ✅ PNG saved to: {output_path}")

        return output_path

    except subprocess.TimeoutExpired:
        print("[PlantUMLRenderer] ❌ Timeout (30s)")
        return None
    except Exception as e:
        print(f"[PlantUMLRenderer] ❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        # ALWAYS cleanup temp directory
        try:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"[PlantUMLRenderer] ✅ Cleaned up: {temp_dir}")
        except Exception as cleanup_error:
            print(f"[PlantUMLRenderer] ⚠️ Cleanup failed: {cleanup_error}")


class PlantUMLRenderer:
    """
    Wrapper class used by driver
    """

    def render_file(self, plantuml_file_path: str) -> Optional[str]:
        """
        Takes .puml file → generates PNG next to it

        Example:
        input:  data/.../diagram.puml
        output: data/.../diagram.png
        """

        if not os.path.exists(plantuml_file_path):
            print(f"[PlantUMLRenderer] ❌ File not found: {plantuml_file_path}")
            return None

        # Load code
        plantuml_code = load_file(plantuml_file_path)

        if not plantuml_code:
            print(f"[PlantUMLRenderer] ❌ Empty PlantUML file")
            return None

        # Replace .puml → .png
        output_path = plantuml_file_path.replace(".puml", ".png")

        return render_plantuml_to_png(
            plantuml_code=plantuml_code,
            output_path=output_path
        )