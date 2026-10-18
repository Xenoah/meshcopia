"""Run the unchanged strict prep; retry only transient HTTP transport failures.

No patched reader, credentials, response cache, offline receipt or relaxed gate.
Every retry repeats the complete anonymous verifier and all byte/hash checks.
"""
from pathlib import Path
import argparse,importlib.util,sys,time,urllib.error,urllib.parse

def run(prepare,repo,delay=time.sleep):
    for attempt in range(1,4):
        try:return prepare(repo)
        except urllib.error.HTTPError as error:
            parsed=urllib.parse.urlsplit(error.url)
            path=parsed.path if parsed.hostname in {'api.github.com','github.com','raw.githubusercontent.com'} else '/redirected-public-payload'
            print(f'COHORT_HTTP_FAILURE attempt={attempt} status={error.code} host={parsed.hostname} path={path}',flush=True)
            transient=error.code in {429,500,502,503,504} or (error.code==403 and error.headers.get('X-RateLimit-Remaining')=='0')
            if not transient or attempt==3:raise
            delay(15*attempt)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repo',required=True,type=Path);args=parser.parse_args();repo=args.repo.resolve()
    spec=importlib.util.spec_from_file_location('unchanged_cohort_preparation',repo/'scripts/prepare-cohort-activation.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    try:run(module.prepare,repo)
    except Exception as error:
        print('STRICT_COHORT_PREP_STOP: '+(str(error)[:300] if isinstance(error,ValueError) else type(error).__name__),file=sys.stderr)
        raise SystemExit(1) from None
