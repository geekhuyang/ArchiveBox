__package__ = 'archivebox.extractors'

import os

from typing import Optional

from ..index.schema import Link, ArchiveResult, ArchiveOutput
from ..util import (
    enforce_types,
    TimedProgress,
    run,
    PIPE,
    is_static_file,
    ArchiveError,
    chrome_args,
    chmod_file,
)
from ..config import (
    TIMEOUT,
    SAVE_DOM,
    CHROME_VERSION,
)



@enforce_types
def should_save_dom(link: Link, out_dir: Optional[str]=None) -> bool:
    out_dir = out_dir or link.link_dir
    if is_static_file(link.url):
        return False
    
    if os.path.exists(os.path.join(out_dir, 'output.html')):
        return False

    return SAVE_DOM
    
@enforce_types
def save_dom(link: Link, out_dir: Optional[str]=None, timeout: int=TIMEOUT) -> ArchiveResult:
    """print HTML of site to file using chrome --dump-html"""

    out_dir = out_dir or link.link_dir
    output: ArchiveOutput = 'output.html'
    output_path = os.path.join(out_dir, str(output))
    cmd = [
        *chrome_args(TIMEOUT=timeout),
        '--dump-dom',
        link.url
    ]
    status = 'succeeded'
    timer = TimedProgress(timeout, prefix='      ')
    try:
        with open(output_path, 'w+') as f:
            result = run(cmd, stdout=f, stderr=PIPE, cwd=out_dir, timeout=timeout)

        if result.returncode:
            hints = result.stderr.decode()
            raise ArchiveError('Failed to save DOM', hints)

        chmod_file(output, cwd=out_dir)
    except Exception as err:
        status = 'failed'
        output = err
    finally:
        timer.end()

    return ArchiveResult(
        cmd=cmd,
        pwd=out_dir,
        cmd_version=CHROME_VERSION,
        output=output,
        status=status,
        **timer.stats,
    )