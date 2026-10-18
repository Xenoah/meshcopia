"""Encode honest thumbnails from the actual single-sided WebGL canvas renders."""
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
for identity in ['garden-arch','wayfinding-sign','household-two-door-refrigerator']:
    image=Image.open(ROOT/f'test-results/asset-revisions/renders/{identity}-fixed-glb-outside-thumbnail.png').convert('RGB')
    image.resize((720,720),Image.Resampling.LANCZOS).save(ROOT/f'asset-revisions/repair-appliances-v1/{identity}/preview.webp',quality=90,method=6)
