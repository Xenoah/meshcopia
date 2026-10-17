// Post-deployment check against actual published catalog/modules and payloads.
// Before activation this intentionally fails; fixtures are not live proof.
process.argv.push('--live');
await import('../scripts/test-minimal-downloads-browser.mjs');
