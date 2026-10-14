/** Recorded project origin or reuse; independent of authorship and license. */
export interface AssetUsage {
  relationship: 'original' | 'reuse';
  project: string;
  sourceUrl?: string;
  /** Immutable source commit/version when known, not an invented deployment ref. */
  sourceRef?: string;
  /** Repository-relative paths, never machine-local paths. */
  sourcePaths?: string[];
  /** Exact object names or other identifiers in the source, not executable code. */
  selectors?: string[];
  context?: string;
}
