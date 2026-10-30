"""Package committed Lab 2 materials; verify before replacing the existing ZIP."""
from pathlib import Path
import hashlib
import os
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT.parent / 'Serbina_Sofiya_Lab2.zip'
PREFIX = 'Serbina_Sofiya_Lab2/'


def main():
    branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip()
    if branch != 'lab2-rest-queues':
        raise SystemExit('Refusing to package another branch')
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().strip('\0').split('\0')
    prohibited = {'.git', '.venv', '__pycache__', '.pytest_cache', '.DS_Store',
                  'data', 'k8s', 'app', '.idea', 'node_modules', '.aws'}
    for name in names:
        path = Path(name)
        assert not (set(path.parts) & prohibited), name
        assert path.suffix not in {'.docx', '.zip', '.pyc', '.pem', '.key'}, name
        assert not path.name.startswith('.env'), name
        assert not path.name.startswith('Lab3'), name
    required = {'spec.md','app.py','worker.py','queue_storage.py','requirements.txt',
                'requirements-dev.txt','README.md','report.pdf','tests/test_lab2.py',
                'evidence/pytest.txt','evidence/metrics.json'}
    required |= {f'screenshots/{name}' for name in (
        '01_rest_api_200_400_404.png','02_job_queued.png','03_api_logs.png',
        '04_job_completed.png','05_pytest_41_passed.png')}
    assert required <= set(names)
    fd, temporary = tempfile.mkstemp(prefix='.lab2-submission-',suffix='.zip',dir=DEST.parent)
    os.close(fd)
    try:
        with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED) as archive:
            for name in names:
                archive.write(ROOT/name,PREFIX+name)
        with zipfile.ZipFile(temporary) as archive:
            assert archive.testzip() is None
            assert len(archive.namelist()) == len(set(archive.namelist()))
            assert set(archive.namelist()) == {PREFIX+name for name in names}
            for name in names:
                assert archive.read(PREFIX+name) == (ROOT/name).read_bytes()
        os.replace(temporary,DEST)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(f'Verified {len(names)} files: {DEST}')
    print('SHA256:', hashlib.sha256(DEST.read_bytes()).hexdigest())


if __name__=='__main__':
    main()
