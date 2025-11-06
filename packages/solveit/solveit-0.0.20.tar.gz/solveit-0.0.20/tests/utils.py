import uuid
from fastcore.utils import patch, str_enum
from playwright.sync_api import Page, expect
from enum import StrEnum

url = 'http://localhost:5001'
editor_container_id = 'full_editor'
dialog_container_id = 'dialog-container'

_keys = dict(
    down="ArrowDown", up="ArrowUp", left="ArrowLeft", right="ArrowRight", meta="ControlOrMeta",
    enter="Enter", escape="Escape", shift="Shift", slash="/", alt="Alt", ctrl="Control"
)
key = StrEnum('key', {k:v for k,v in _keys.items()})
ss = str_enum('ss', 'primary', 'unselected')

@patch
def sleep(self:Page, delay=200): return self.wait_for_timeout(delay)

@patch
def kbp(self:Page, k):
    self.keyboard.press(k)
    self.sleep()

@patch
def kbt(self:Page, t):
    self.keyboard.type(t)
    self.sleep()

@patch
def mk_dlg(self:Page, nm=None):
    self.goto(url)
    nm = nm or f"sm:{str(uuid.uuid4())[:8]}"
    self.get_by_role("textbox", name="Dialog Name").click()
    self.kbt(nm)
    self.get_by_role("button", name="Create", exact=True).click()
    self.wait_for_function("""() => (window.editor && window.editor.getModel().uri.path.endsWith('temp')) ? true : false""")
    return nm

@patch
def mk_msg(self:Page, content, typ='code'):
    t2k = {'code':'J', 'note':'K', 'prompt':'L'}
    self.kbt(content)
    if typ != 'code': self.kbp(f'{key.meta}+{key.shift}+{t2k[typ]}')
    self.kbp(f"{key.meta}+{key.enter}")

@patch
def edit_mode(self:Page):
    self.kbp(key.escape) # de-focus editor
    self.kbp(key.enter) # enter edit mode

@patch
def editor(self:Page): return self.get_by_role("textbox", name="Editor content")
