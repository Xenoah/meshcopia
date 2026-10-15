#!/usr/bin/env python3
"""Merge verified previous license/attribution into one short LICENSE.txt.

This module performs no network requests and changes no asset. The canonical
route policy is a supplied, externally verified publication prerequisite.
"""
from __future__ import annotations
import re
from urllib.parse import urlsplit
from minimal_packages import PackageError, require

LICENSE_URL = 'https://creativecommons.org/licenses/by/4.0/'
SITE = 'https://xenoah.github.io/meshcopia'


def baseline_notices(metadata, site=SITE):
    """Exact baseline generate.mjs/catalog.mjs templates, for uncached notices.

    These are reconstructed supplied notices, not claims that a ZIP was fetched.
    Callers must bind the reviewed generator/source commit outside the archive.
    """
    a = metadata
    license_text = (f"{a['titleEn']}\nCopyright (c) {a['created'][:4]} {a['author']}\n"
                    'Licensed under Creative Commons Attribution 4.0 International (CC BY 4.0).\n'
                    f'{LICENSE_URL}\n{LICENSE_URL}legalcode.en\n\n'
                    'You may share and adapt, including commercially. Give appropriate credit, link the license, and indicate changes. '
                    'No additional restrictions. No warranties. This notice is a summary; the linked legal code controls.\n')
    origin = '\nOriginal source: ' + a['provenance']['sourceUrl'] if a['provenance'].get('sourceUrl') else ''
    changes = a['provenance'].get('changes') or 'none. If modified, replace this line with a description of your changes.'
    attribution = (f"{a['titleEn']} by {a['author']} / Meshcopia\n{site}/assets/{a['id']}/\n"
                   f'CC BY 4.0 — {LICENSE_URL}{origin}\nChanges: {changes}\n')
    return license_text, attribution


def safe_public_url(value):
    require(isinstance(value, str) and not re.search(r'[\s\\\x00-\x1f\x7f]', value), 'Unsafe source URL')
    parsed = urlsplit(value)
    require(parsed.scheme == 'https' and parsed.hostname and not parsed.username and not parsed.password,
            'Source URL must use HTTPS without credentials')
    return value


def modification_text(text):
    # Three reviewed baseline notices append this forensic sentence. Its digest
    # remains in external provenance; the complete modification is unchanged.
    return re.sub(r' Baseline GLB SHA-256: [0-9a-f]{64}\.', '', text)


def make_notice(metadata, previous_license, previous_attribution, *, fbx_attribution=None, site=SITE):
    """Return UTF-8 notice text, preserving actual previous copyright/credit.

    No source hashes, validation claims or absent-document references are emitted.
    The previous metadata modification statement is retained if distinct from the
    supplied previous attribution statement. FBX adds its existing conversion note.
    """
    if isinstance(previous_license, bytes):
        previous_license = previous_license.decode('utf-8')
    if isinstance(previous_attribution, bytes):
        previous_attribution = previous_attribution.decode('utf-8')
    if isinstance(fbx_attribution, bytes):
        fbx_attribution = fbx_attribution.decode('utf-8')
    a = metadata
    require(a.get('license') == 'CC-BY-4.0' and a.get('author'), 'Explicit creator and CC-BY-4.0 metadata required')
    copyrights = [line for line in previous_license.splitlines() if line.startswith('Copyright ')]
    require(len(copyrights) == 1 and a['author'] in copyrights[0], 'One actual matching previous copyright notice is required')
    require(LICENSE_URL in previous_license and ('No warranties' in previous_license or 'without warranties' in previous_license),
            'Prior license does not match the reviewed license/disclaimer form')
    credit = previous_attribution.splitlines()[0]
    require(a['author'] in credit and ' / Meshcopia' in credit, 'Previous creator/designated attribution is missing')
    url = safe_public_url(f"{site}/assets/{a['id']}/")
    require(url in previous_attribution.splitlines(), 'Previous attribution must identify the exact canonical detail URL')
    urls = []
    for line in previous_attribution.splitlines():
        if line.startswith('Original source: '):
            urls.append(safe_public_url(line[len('Original source: '):]))
    if a.get('provenance', {}).get('sourceUrl'):
        urls.append(safe_public_url(a['provenance']['sourceUrl']))
    changes = []
    for line in previous_attribution.splitlines():
        if line.startswith('Changes: '):
            changes.append(line[len('Changes: '):])
    require(len(changes) == 1, 'Previous attribution must contain one modification indication')
    if a.get('provenance', {}).get('changes'):
        changes.append(a['provenance']['changes'])
    if fbx_attribution is not None:
        conversion = [line[len('Changes: '):] for line in fbx_attribution.splitlines() if line.startswith('Changes: ')]
        require(len(conversion) == 1 and 'FBX' in conversion[0], 'Previous FBX conversion notice is required')
        changes.extend(conversion)
    changes = [modification_text(text).replace('none. If modified, replace this line with a description of your changes.', 'none.') for text in changes]
    changes = list(dict.fromkeys(changes))
    lines = [credit, copyrights[0], f'CC BY 4.0: {LICENSE_URL}', f'Source: {url}']
    lines.extend('Original source: ' + value for value in dict.fromkeys(urls))
    lines.append('Provided as-is, without warranties (license Section 5).')
    lines.extend(('Changes: ' if index == 0 else 'Additional changes: ') + text for index, text in enumerate(changes))
    notice = '\n'.join(lines) + '\n'
    require(not any(token in notice for token in ('THIRD_PARTY_NOTICES.md', 'asset.json', 'CONVERSION_NOTES.md', 'SHA-256:', '/workspace/', '/tmp/')),
            'Notice contains a removed-document reference, hash, or local path')
    return notice
