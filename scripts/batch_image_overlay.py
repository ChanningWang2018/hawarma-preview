#!/usr/bin/env python3
"""
Script for batch editing images by overlaying specific regions.
Takes a base image and overlays a specific region from another image
onto a specific region of the base image.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image


def parse_region(region_str: str) -> Tuple[int, int, int, int]:
    """
    Parse region string in format 'x,y,width,height' to tuple.

    Args:
        region_str: String in format 'x,y,width,height'

    Returns:
        Tuple of (x, y, width, height)

    Raises:
        ValueError: If format is invalid
    """
    try:
        parts = [int(x.strip()) for x in region_str.split(",")]
        if len(parts) != 4:
            raise ValueError("Region must have exactly 4 values")
        if parts[2] <= 0 or parts[3] <= 0:
            raise ValueError("Width and height must be positive")
        return tuple(parts)
    except ValueError as e:
        raise ValueError(
            f"Invalid region format '{region_str}'. Expected 'x,y,width,height': {e}"
        )


def overlay_image_region(
    base_path: str,
    source_path: str,
    base_region: Tuple[int, int, int, int],
    source_region: Tuple[int, int, int, int],
    output_path: str,
    resize_source: bool = True,
) -> bool:
    """
    Overlay a region from source image onto base image.

    Args:
        base_path: Path to base image
        source_path: Path to source image
        base_region: (x, y, width, height) region on base image
        source_region: (x, y, width, height) region on source image
        output_path: Path to save result
        resize_source: Whether to resize source region to match base region

    Returns:
        True if successful, False otherwise
    """
    try:
        # Open images
        with Image.open(base_path) as base_img, Image.open(source_path) as source_img:
            # Ensure images are in RGBA mode for proper alpha handling
            base_img = base_img.convert("RGBA")
            source_img = source_img.convert("RGBA")

            # Extract regions
            base_x, base_y, base_w, base_h = base_region
            src_x, src_y, src_w, src_h = source_region

            # Validate regions are within image bounds
            if (
                base_x < 0
                or base_y < 0
                or base_x + base_w > base_img.width
                or base_y + base_h > base_img.height
            ):
                print(
                    f"Error: Base region {base_region} is outside base image bounds ({base_img.width}x{base_img.height})"
                )
                return False

            if (
                src_x < 0
                or src_y < 0
                or src_x + src_w > source_img.width
                or src_y + src_h > source_img.height
            ):
                print(
                    f"Error: Source region {source_region} is outside source image bounds ({source_img.width}x{source_img.height})"
                )
                return False

            # Crop source region
            source_crop = source_img.crop((src_x, src_y, src_x + src_w, src_y + src_h))

            # Resize source crop to match base region if needed
            if resize_source and (src_w != base_w or src_h != base_h):
                source_crop = source_crop.resize(
                    (base_w, base_h), Image.Resampling.LANCZOS
                )

            # Create a copy of the base image
            result_img = base_img.copy()

            # Paste the source crop onto the base image
            result_img.paste(source_crop, (base_x, base_y), source_crop)

            # Convert back to RGB if saving as JPEG
            if output_path.lower().endswith(".jpg") or output_path.lower().endswith(
                ".jpeg"
            ):
                result_img = result_img.convert("RGB")

            # Ensure output directory exists
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save result
            result_img.save(output_path)
            print(f"Successfully created: {output_path}")
            return True

    except Exception as e:
        print(f"Error processing {base_path} + {source_path}: {e}")
        return False


def load_batch_config(config_path: str) -> Optional[List[Dict]]:
    """
    Load batch configuration from JSON file.

    Args:
        config_path: Path to JSON configuration file

    Returns:
        List of batch operations or None if error
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        if not isinstance(config, list):
            print("Error: Configuration must be a list of operations")
            return None

        return config
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {config_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}")
        return None
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return None


def process_batch_operations(
    operations: List[Dict], output_dir: str = "output"
) -> Dict[str, int]:
    """
    Process a batch of overlay operations.

    Args:
        operations: List of operation dictionaries
        output_dir: Base output directory

    Returns:
        Dictionary with success/failure counts
    """
    stats = {"success": 0, "failed": 0}

    for i, operation in enumerate(operations):
        print(f"\nProcessing operation {i + 1}/{len(operations)}")

        try:
            # Validate required fields
            required_fields = [
                "base_image",
                "source_image",
                "base_region",
                "source_region",
            ]
            for field in required_fields:
                if field not in operation:
                    print(
                        f"Error: Missing required field '{field}' in operation {i + 1}"
                    )
                    stats["failed"] += 1
                    continue

            # Parse regions
            base_region = parse_region(operation["base_region"])
            source_region = parse_region(operation["source_region"])

            # Determine output path
            output_filename = operation.get("output_filename")
            if not output_filename:
                base_name = Path(operation["base_image"]).stem
                source_name = Path(operation["source_image"]).stem
                output_filename = f"{base_name}_overlay_{source_name}.png"

            output_path = Path(output_dir) / output_filename

            # Process overlay
            resize_source = operation.get("resize_source", True)
            success = overlay_image_region(
                operation["base_image"],
                operation["source_image"],
                base_region,
                source_region,
                str(output_path),
                resize_source,
            )

            if success:
                stats["success"] += 1
            else:
                stats["failed"] += 1

        except Exception as e:
            print(f"Error processing operation {i + 1}: {e}")
            stats["failed"] += 1

    return stats


def create_sample_config():
    """
    Create a sample configuration file for batch operations.
    """
    sample_config = [
        {
            "base_image": "images/base1.png",
            "source_image": "images/overlay1.png",
            "base_region": "50,50,100,100",
            "source_region": "0,0,200,200",
            "output_filename": "output1.png",
            "resize_source": True,
        },
        {
            "base_image": "images/base2.png",
            "source_image": "images/overlay2.png",
            "base_region": "100,100,150,150",
            "source_region": "25,25,150,150",
            "output_filename": "output2.png",
            "resize_source": False,
        },
    ]

    config_path = "batch_overlay_config.json"
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(sample_config, f, indent=2, ensure_ascii=False)
        print(f"Created sample configuration file: {config_path}")
        print("\nEdit this file to define your batch operations, then run:")
        print(f"python scripts/batch_image_overlay.py --config {config_path}")
    except Exception as e:
        print(f"Error creating sample config: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Batch overlay image regions from source images onto base images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single operation
  python scripts/batch_image_overlay.py \\
    --base images/base.png \\
    --source images/overlay.png \\
    --base-region "50,50,100,100" \\
    --source-region "0,0,100,100" \\
    --output result.png
  
  python scripts/batch_image_overlay.py \\
    --base "tmp/2025-10-09 (3).png" \\
    --source "tmp/2025-10-09 (5).png" \\
    --base-region "600,330,65,65" \\
    --source-region "600,330,65,65" \\
    --output overlayed.png

  # Batch operations from config file
  python scripts/batch_image_overlay.py --config batch_config.json

  # Create sample configuration file
  python scripts/batch_image_overlay.py --create-sample-config

Region format: "x,y,width,height"
        """,
    )

    parser.add_argument(
        "--config", help="Path to JSON configuration file for batch operations"
    )
    parser.add_argument("--base", help="Base image path (for single operation)")
    parser.add_argument("--source", help="Source image path (for single operation)")
    parser.add_argument("--base-region", help='Base image region: "x,y,width,height"')
    parser.add_argument(
        "--source-region", help='Source image region: "x,y,width,height"'
    )
    parser.add_argument(
        "--output",
        default="output.png",
        help="Output image path (for single operation)",
    )
    parser.add_argument(
        "--output-dir", default="output", help="Output directory for batch operations"
    )
    parser.add_argument(
        "--no-resize",
        action="store_true",
        help="Do not resize source region to match base region",
    )
    parser.add_argument(
        "--create-sample-config",
        action="store_true",
        help="Create sample configuration file",
    )

    args = parser.parse_args()

    if args.create_sample_config:
        create_sample_config()
        return

    # Batch mode with config file
    if args.config:
        operations = load_batch_config(args.config)
        if operations is None:
            return

        print(f"Loaded {len(operations)} operations from {args.config}")
        stats = process_batch_operations(operations, args.output_dir)

        print("\nBatch processing complete!")
        print(f"Successful: {stats['success']}")
        print(f"Failed: {stats['failed']}")
        print(f"Total: {len(operations)}")

    # Single operation mode
    elif args.base and args.source and args.base_region and args.source_region:
        try:
            base_region = parse_region(args.base_region)
            source_region = parse_region(args.source_region)

            success = overlay_image_region(
                args.base,
                args.source,
                base_region,
                source_region,
                args.output,
                not args.no_resize,
            )

            if success:
                print(
                    f"Operation completed successfully! Output saved to: {args.output}"
                )
            else:
                print("Operation failed!")

        except Exception as e:
            print(f"Error: {e}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
