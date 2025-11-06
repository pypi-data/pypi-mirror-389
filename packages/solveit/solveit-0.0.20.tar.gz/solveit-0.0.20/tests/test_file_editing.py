"""
Solveit File Editing Tests
- python tests/test_file_editing.py
"""
import shutil, subprocess, time, uuid
from pathlib import Path
from fastcore.test import test_eq as teq
from fastcore.utils import patch
from git import Repo
from playwright.sync_api import sync_playwright, Page
from utils import key, url

tdir = Path("eddy")

def kill_app(): subprocess.run("pkill -9 -f 'localhost:5001'", shell=True)
def start_app(): subprocess.Popen("python solveit/main.py", shell=True)
def rm_test_dir(): shutil.rmtree(tdir.as_posix()) if tdir.is_dir() else None

def cleanup(): rm_test_dir(); kill_app();
def setup(): cleanup(); start_app(); time.sleep(1.)

def dname(): return str(uuid.uuid4())[:8]
def repo(fp:Path): return Repo(fp if fp.is_dir() else fp.parent)
def n_commits(fp:Path, delay=2.0): time.sleep(delay); return len(list(repo(fp).iter_commits()))
def n_tracked_files(fp:Path, delay=.2): time.sleep(delay); return len(repo(fp).git.ls_files().split("\n"))
def is_git_enabled(fp:Path): return (fp/".git").exists()

@patch
def open_file_editor(self: Page, fp):
    self.goto(f"{url}/file_editor_?fp={fp}")
    self.wait_for_function("() => window.file_editor")

def test_enable_git(pg:Page):
    # confirm git isn't enabled by default
    teq(tdir.exists(), True)
    teq(is_git_enabled(tdir), False)
    # navigate to the parent directory and enable git
    pg.goto(f"{url}?at={tdir.name}")
    pg.get_by_role("checkbox", name="Enable git?").check(); pg.sleep(2000) # git folder creation can be slow
    # confirm that a `.git` folder was created
    teq(is_git_enabled(tdir), True)
    # confirm we have 1 commit and 1 tracked file (.gitignore)
    teq(n_commits(tdir), 1); teq(n_tracked_files(tdir), 1)
    # disable git
    pg.on("dialog", lambda d: d.accept())  # this ensures the confirm dialog is accepted
    pg.get_by_role("checkbox", name="Enable git?").uncheck(); pg.sleep() # allow some time for folder deletion
    teq(is_git_enabled(tdir), False)

def test_dialog_edit_tracking(pg:Page):
    # make a dialog
    nm = dname()
    fp = tdir/f"{nm}.ipynb"
    # make a dialog and confirm git isn't enabled on the parent dir
    pg.mk_dlg(nm=f"{fp.parent}/{fp.stem}")
    teq(fp.exists(), True)
    teq(is_git_enabled(fp.parent), False)
    # make a message, save it
    pg.mk_msg("1"); pg.kbp("s")
    # confirm the save alert appeared but the changes were not tracked
    teq(pg.locator("p#save-alert").is_visible(), True); teq(is_git_enabled(fp.parent), False)
    # navigate to the parent directory and enable git
    pg.get_by_role("link", name="📚 solveit").click()
    pg.get_by_role("checkbox", name="Enable git?").check(); pg.sleep(2000) # git folder creation can be slow
    # navigate back to the dialog and wait for it to load
    pg.get_by_role("link", name=nm).click(); pg.wait_for_function("""() => window.editor""")
    # hit save and confirm that we now have 2 commits and 2 tracked files
    pg.kbp("s"); teq(n_commits(fp), 2); teq(n_tracked_files(fp), 2)

def test_file_edit_tracking(pg:Page):
    # make python file
    (tdir/"t1.py").touch()
    # open it in the file editor
    pg.open_file_editor(tdir.absolute()/'t1.py')
    # make some changes and save them
    pg.kbt("print('t1...')"); pg.kbp(f"{key.meta}+{key.shift}+s")
    # confirm changes are saved to disk but not tracked
    teq((tdir/"t1.py").read_text(), "print('t1...')"); teq(pg.locator("p#save-alert").is_visible(), True); teq(is_git_enabled(tdir), False)
    # enable tracking
    pg.goto(f"{url}?at={tdir.name}")
    pg.get_by_role("checkbox", name="Enable git?").check(); pg.sleep(2000) # git folder creation can be slow
    # open file editor make some changes and save them
    pg.open_file_editor(tdir.absolute() / 't1.py'); pg.kbt("# "); pg.kbp(f"{key.meta}+{key.shift}+s")
    # confirm they are saved
    teq((tdir/"t1.py").read_text(), "# print('t1...')"); teq(pg.locator("p#save-alert").is_visible(), True)
    # confirm they are tracked
    teq(is_git_enabled(tdir), True); teq(n_commits(tdir), 2); teq(n_tracked_files(tdir), 2)

tests = [
    test_enable_git,
    # TODO:
    #  `test_file_edit_tracking` is run before `test_dialog_edit_tracking` because the dialog created
    #  in `test_dialog_edit_tracking` is retained in memory and interferes with `test_file_edit_tracking`.
    #  In particular it inflates the count of `n_tracked_files`.
    test_file_edit_tracking,
    test_dialog_edit_tracking,
]

def run_tests():
    setup()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        pg = browser.new_page()
        pg.set_default_timeout(10_000)
        for t in tests: rm_test_dir(); tdir.mkdir(exist_ok=True); t(pg)
    print("Success.")
    cleanup()

run_tests()
