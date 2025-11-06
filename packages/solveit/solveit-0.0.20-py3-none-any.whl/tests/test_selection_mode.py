import uuid
import pytest

from urllib.parse import quote, urlparse, parse_qs
from fastcore.test import test_eq as teq
from fastcore.utils import patch, first
from playwright.sync_api import Page, expect
from utils import key, ss, url

editor_container_id = 'full_editor'
dialog_container_id = 'dialog-container'


@patch
def msgs(self: Page): return self.locator(f"#{dialog_container_id} >> [data-sm]")


def msgcards(m): return m.locator('.hljs').all()


def msgtxt(m):
    "Get the input, output text of message `m`."
    typ = m.locator('form input[name="msg_type"]').get_attribute('value')
    if typ == 'code':
        return [c.text_content() for c in msgcards(m)]
    else:
        return [m.locator('form input[name="content"]').get_attribute('value'), None]


def msg_status(msg): return msg.get_attribute('data-sm')


def msg_statuses(msgs): return [msg_status(m) for m in msgs.all()]


def has_icon(msg, ico): return msg.locator(f'use[href="#{ico}"]').first.is_visible()


def is_collapsed(msg): return has_icon(msg, 'chevron-down') and not has_icon(msg, 'chevron-up')


def is_primary(msg): return msg_status(msg) == 'primary'


def is_being_edited(msg): return 'ring-green-400' in msg.get_attribute(
    'class') and not 'ring-blue-400' in msg.get_attribute('class')


def is_editor_focused(pg): return pg.evaluate(
    f"""() => document.querySelector('#{editor_container_id}').contains(document.activeElement)""")


@patch
def edit_msg(self: Page, content):
    self.editor().fill(content)  # replace existing text with new content
    self.sleep()  # we sleep because we haven't patched `.fill` to sleep automatically after use
    self.kbp(f"{key.meta}+{key.enter}")


@patch
def add_above(self: Page, msg): msg.locator("[icon='arrow-up-to-line']").click(); self.sleep()


@patch
def add_below(self: Page, msg): msg.locator("[icon='arrow-down-to-line']").click(); self.sleep()


@patch
def delete(self: Page, msg): msg.locator("[icon='trash']").click(); self.sleep()


@patch
def toggle_collapse(self: Page, msg): msg.locator("[hx-post='/toggle_header_collapse_']").click(); self.sleep()


@pytest.fixture(scope="session")
def pg(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture(scope="session", autouse=True)
def setup_teardown(pg):
    # setup (create dialog)
    pg.set_default_timeout(5000)
    dname = pg.mk_dlg()
    yield
    # teardown (delete dialog)
    pg.goto(url)
    pg.sleep()
    pg.on("dialog", lambda dialog: dialog.accept())
    pg.click(f'[hx-post="/rm_dialog_?name={quote(dname)}"]')


@pytest.fixture(autouse=True)
def _test_cleanup_(pg):
    yield
    while pg.msgs().count() != 0: pg.delete(pg.msgs().nth(0))


# TODO:
#  We run `test_expand_collapse_msg` and `test_open_msg_in_new_tab` first as they tend to fail when run further down.
#  This isn't ideal so perhaps we should create a new dialog for each test?
#  This will make the tests slower but the upside should be increased stability.

def test_expand_collapse_msg(pg: Page):
    msgs = pg.msgs()
    pg.mk_msg('1')
    msg = msgs.nth(0)
    inp = msg.locator('> div').first
    out = msg.locator('> div').last
    teq(is_collapsed(inp), False)
    teq(is_collapsed(out), False)
    pg.kbp('i')  # collapse input
    teq(is_collapsed(inp), True)
    teq(is_collapsed(out), False)
    pg.kbp('i')  # expand input
    teq(is_collapsed(inp), False)
    teq(is_collapsed(out), False)
    pg.kbp('o')  # collapse output
    teq(is_collapsed(inp), False)
    teq(is_collapsed(out), True)
    pg.kbp('o')  # expand output
    teq(is_collapsed(inp), False)
    teq(is_collapsed(out), False)


def test_open_msg_in_new_tab(pg: Page):
    pg.mk_msg('1')
    # open msg in new tab
    with pg.context.expect_page() as tab_info: pg.kbp('t')
    tab = tab_info.value
    teq('with_input=1' in tab.url, True)
    tab.close();
    pg.sleep()
    # open msg output in new tab
    with pg.context.expect_page() as tab_info: pg.kbp('y')
    tab = tab_info.value
    teq('with_input=&' in tab.url, True)
    tab.close();
    pg.sleep()


def test_initial_state(pg: Page):
    teq(is_editor_focused(pg), True)
    teq(pg.msgs().count(), 0)


def test_initial_state_after_reload(pg: Page):
    # create a msg and confirm msg is selected on reload
    teq(is_editor_focused(pg), True)
    teq(pg.msgs().count(), 0)

    pg.mk_msg("1+1")
    pg.reload()
    pg.wait_for_function("""() => window.editor""")
    msgs = pg.msgs()
    teq(msgs.count(), 1)
    teq(is_primary(msgs.nth(0)), True)
    teq(msgtxt(msgs.nth(0)), ["1+1", "2"])
    teq(is_editor_focused(pg), False)


def test_redirect_focus(pg: Page):
    # ensure selection mode works when navigating back -> forward to same dialog
    pg.mk_msg("1+1")
    msgs = pg.msgs()
    teq(msg_statuses(msgs), [ss.primary])
    dname = first(parse_qs(urlparse(pg.url).query)['name'])
    pg.get_by_role('link', name='📚 solveit').click()
    pg.get_by_role("link", name=dname).click()
    pg.wait_for_function("""() => window.editor""")
    teq(msg_statuses(msgs), [ss.primary])


def test_create_msg(pg: Page):
    pg.mk_msg("1+1")
    msgs = pg.msgs()
    teq(msgs.count(), 1)
    teq(is_primary(msgs.nth(0)), True)
    teq(msgtxt(msgs.nth(0)), ["1+1", "2"])
    teq(is_editor_focused(pg), False)


def test_edit_msg(pg: Page):
    pg.mk_msg("1+1")
    msgs = pg.msgs()
    pg.edit_mode()
    teq(is_editor_focused(pg), True)
    teq(is_being_edited(msgs.nth(0)), True)

    pg.edit_msg("0+0")
    teq(msgs.count(), 1)
    teq(is_primary(msgs.nth(0)), True)
    teq(is_being_edited(msgs.nth(0)), False)
    teq(msgtxt(msgs.nth(0)), ["0+0", "0"])
    teq(is_editor_focused(pg), False)


def test_toggle_selection_mode(pg: Page):
    pg.mk_msg("1+1")
    msgs = pg.msgs()
    teq(is_editor_focused(pg), False)
    teq(is_primary(msgs.nth(0)), True)
    teq(is_being_edited(msgs.nth(0)), False)

    pg.kbp(key.enter)  # enter edit mode
    teq(is_editor_focused(pg), True)
    teq(is_primary(msgs.nth(0)), True)
    teq(is_being_edited(msgs.nth(0)), True)

    pg.kbp(key.escape)  # exit edit mode
    teq(is_editor_focused(pg), False)
    teq(is_primary(msgs.nth(0)), True)
    teq(is_being_edited(msgs.nth(0)), False)


def test_add_msg_above(pg: Page):
    # add msg using button click
    pg.mk_msg("1")
    msgs = pg.msgs()
    pg.add_above(msgs.nth(0))
    teq(is_editor_focused(pg), True)
    teq(is_being_edited(msgs.nth(0)), True)
    teq(is_primary(msgs.nth(0)), True)

    pg.mk_msg("0")
    teq(msgs.count(), 2)
    teq(is_editor_focused(pg), False)
    teq(is_being_edited(msgs.nth(0)), False)
    teq(is_primary(msgs.nth(0)), True)
    teq(msgtxt(msgs.nth(0)), ["0", "0"])

    # navigate to the 2nd message and add a message above using a keypress
    pg.kbp(key.down);
    pg.kbp('a')
    pg.mk_msg("0.5")
    teq(msgs.count(), 3)
    teq(is_editor_focused(pg), False)
    teq(is_being_edited(msgs.nth(1)), False)
    teq(is_primary(msgs.nth(1)), True)
    teq(msgtxt(msgs.nth(1)), ["0.5", "0.5"])

    teq(msg_statuses(msgs), [ss.unselected, ss.primary, ss.unselected])
    teq([first(msgtxt(m)) for m in msgs.all()], ["0", "0.5", "1"])


def test_add_msg_below(pg: Page):
    # add msg using button click
    pg.mk_msg("0")
    msgs = pg.msgs()
    pg.add_below(msgs.nth(0))
    teq(is_editor_focused(pg), True)
    teq(is_being_edited(msgs.nth(1)), True)
    teq(is_primary(msgs.nth(1)), True)

    pg.mk_msg("1")
    teq(msgs.count(), 2)
    teq(is_editor_focused(pg), False)
    teq(is_being_edited(msgs.nth(1)), False)
    teq(is_primary(msgs.nth(1)), True)
    teq(msgtxt(msgs.nth(1)), ["1", "1"])

    # navigate to the 2nd message and add a message below using a keypress
    pg.kbp(key.up);
    pg.kbp('b')
    pg.mk_msg("0.5")
    teq(msgs.count(), 3)
    teq(is_editor_focused(pg), False)
    teq(is_being_edited(msgs.nth(1)), False)
    teq(is_primary(msgs.nth(1)), True)
    teq(msgtxt(msgs.nth(1)), ["0.5", "0.5"])

    teq(msg_statuses(msgs), [ss.unselected, ss.primary, ss.unselected])
    teq([first(msgtxt(m)) for m in msgs.all()], ["0", "0.5", "1"])


def test_msg_navigation(pg: Page):
    # create 3 msgs and navigate between them
    msgs = pg.msgs()
    pg.mk_msg("1")
    pg.add_below(msgs.nth(0));
    pg.mk_msg("2")
    pg.add_below(msgs.nth(1));
    pg.mk_msg("3")
    teq(msgs.count(), 3)
    # navigate to the top message
    pg.kbp(key.up);
    pg.kbp(key.up)
    teq(is_primary(msgs.nth(0)), True)
    teq(is_primary(msgs.nth(1)), False)
    teq(is_primary(msgs.nth(2)), False)
    # navigate to the bottom message
    pg.kbp(key.down);
    pg.kbp(key.down)
    teq(is_primary(msgs.nth(0)), False)
    teq(is_primary(msgs.nth(1)), False)
    teq(is_primary(msgs.nth(2)), True)


def test_append_msg(pg: Page):
    msgs = pg.msgs()
    pg.mk_msg("1");
    pg.add_below(msgs.nth(0));
    pg.mk_msg("2")
    teq(msgs.count(), 2)
    pg.kbp(key.up)  # navigate to the top message
    teq(is_primary(msgs.nth(0)), True)
    teq(is_primary(msgs.nth(1)), False)
    teq(is_editor_focused(pg), False)
    pg.kbp(key.slash)  # focus the editor and de-select the top message
    teq(is_primary(msgs.nth(0)), False)
    teq(is_primary(msgs.nth(1)), False)
    teq(is_editor_focused(pg), True)
    pg.mk_msg("3")
    teq(msgs.count(), 3)
    teq(msgtxt(msgs.nth(2)), ["3", "3"])
    teq(is_editor_focused(pg), False)
    teq(is_primary(msgs.nth(2)), True)


def test_delete_msg(pg: Page):
    msgs = pg.msgs()
    pg.mk_msg("1")
    pg.add_below(msgs.nth(0));
    pg.mk_msg("2")
    pg.add_below(msgs.nth(1));
    pg.mk_msg("3")
    teq(msgs.count(), 3)
    # select the middle msg
    pg.kbp(key.up)
    teq(is_primary(msgs.nth(1)), True)
    # delete it (check the bottom message is then selected)
    pg.delete(msgs.nth(1))
    teq(msgs.count(), 2)
    teq(msgtxt(msgs.nth(1)), ["3", "3"])
    teq(is_primary(msgs.nth(1)), True)
    # delete the bottom message (check the top message is then selected)
    pg.delete(msgs.nth(1))
    teq(msgs.count(), 1)
    teq(msgtxt(msgs.nth(0)), ["1", "1"])
    teq(is_primary(msgs.nth(0)), True)
    # delete the final message (check editor is focused)
    pg.delete(msgs.nth(0))
    teq(msgs.count(), 0)
    teq(is_editor_focused(pg), True)

    # keyboard test: shift,d deletes the message
    pg.mk_msg("4")
    teq(msgs.count(), 1)
    pg.kbp("D")
    teq(msgs.count(), 0)


def test_delete_collapsed_section(pg: Page):
    msgs = pg.msgs()
    # create header with some notes
    pg.mk_msg('# 1', typ='note');
    pg.kbp('b');
    pg.mk_msg('1');
    pg.kbp('b');
    pg.mk_msg('2')
    teq(msgs.count(), 3)
    pg.toggle_collapse(msgs.nth(0))
    teq(msgs.count(), 1)
    # delete header
    pg.delete(msgs.nth(0))
    teq(msgs.count(), 0)
    # reload page and confirm no messages remain
    pg.reload()
    teq(msgs.count(), 0)


def test_run_options_in_editor(pg: Page):
    # regular enter (should create a message and select it on submission)
    pg.editor().fill("1+1")
    pg.kbp(f"{key.meta}+{key.enter}")
    msgs = pg.msgs()
    teq(msgs.count(), 1)
    teq(msgtxt(msgs.nth(0)), ["1+1", "2"])
    teq(is_editor_focused(pg), False)
    teq(is_primary(msgs.nth(0)), True)
    # alt enter (should create 2 messages. 1st message is 2+2, 2nd message is empty. editor should be focused)
    pg.add_below(msgs.nth(0))
    pg.editor().fill("2+2")
    pg.kbp(f"{key.alt}+{key.enter}")
    teq(msgs.count(), 3)
    teq(msgtxt(msgs.nth(1)), ["2+2", "4"])
    teq(msg_statuses(msgs), [ss.unselected, ss.unselected, ss.primary])
    teq(is_being_edited(msgs.nth(2)), True)
    teq(is_editor_focused(pg), True)
    # let's populate the message and do a regular submit
    pg.editor().fill("3+3")
    pg.kbp(f"{key.meta}+{key.enter}")
    teq(msgs.count(), 3)
    teq(msg_statuses(msgs), [ss.unselected, ss.unselected, ss.primary])
    teq([first(msgtxt(m)) for m in msgs.all()], ["1+1", "2+2", "3+3"])
    # shift enter (want to check that the next message is selected after submission)
    pg.kbp(key.up);
    pg.kbp(key.up);
    pg.kbp(key.up)
    teq(msg_statuses(msgs), [ss.primary, ss.unselected, ss.unselected])
    pg.kbp(key.enter)
    pg.editor().fill("1")
    pg.kbp(f"{key.shift}+{key.enter}")
    teq(msgs.count(), 3)
    teq(msg_statuses(msgs), [ss.unselected, ss.primary, ss.unselected])
    teq([first(msgtxt(m)) for m in msgs.all()], ["1", "2+2", "3+3"])


def test_run_options_in_msg(pg: Page):
    # create a msg but don't run it
    pg.editor().fill("1+1")
    pg.kbp(key.escape)
    msgs = pg.msgs()
    teq(msgs.count(), 1)
    teq(msgtxt(msgs.nth(0)), ["1+1"])
    # run msg using meta, enter
    pg.kbp(f"{key.meta}+{key.enter}")
    teq(msgs.count(), 1)
    teq(msgtxt(msgs.nth(0)), ["1+1", "2"])
    # run msg again but use alt, enter
    pg.kbp(f"{key.alt}+{key.enter}")
    teq(msgs.count(), 2)
    teq(msgtxt(msgs.nth(1)), [""])
    teq(msg_statuses(msgs), [ss.unselected, ss.primary])
    teq(is_being_edited(msgs.nth(1)), True)
    teq(is_editor_focused(pg), True)
    # populate the new empty msg
    pg.editor().fill("2+2");
    pg.kbp(f"{key.meta}+{key.enter}")
    teq(msgs.count(), 2)
    teq(msg_statuses(msgs), [ss.unselected, ss.primary])
    teq([first(msgtxt(m)) for m in msgs.all()], ["1+1", "2+2"])
    # navigate to the top msg and then run shift, enter
    pg.kbp(key.up)
    teq(msg_statuses(msgs), [ss.primary, ss.unselected])  # 1st msg should be selected
    pg.kbp(f"{key.shift}+{key.enter}")
    teq(msgs.count(), 2)
    teq(msg_statuses(msgs), [ss.unselected, ss.primary])  # 2nd msg should be selected
    teq([first(msgtxt(m)) for m in msgs.all()], ["1+1", "2+2"])


def test_copy_paste_msgs(pg: Page):
    msgs = pg.msgs()
    # create a msg and copy it
    pg.mk_msg("1")
    pg.kbp("c")
    # change the content from 1 => 0
    pg.kbp(key.up)
    pg.kbp(key.enter);
    pg.edit_msg("0")
    # paste the message and confirm that a new message is created with the original content
    pg.kbp("v")
    teq(msgs.count(), 2)
    teq([first(msgtxt(m)) for m in msgs.all()], ["0", "1"])
    teq(msg_statuses(msgs), [ss.unselected, ss.primary])


def test_cut_paste_msgs(pg: Page):
    msgs = pg.msgs()
    # create 2 msgs
    pg.mk_msg("0");
    pg.kbp('b');
    pg.mk_msg("1")
    teq(msgs.count(), 2)
    teq([first(msgtxt(m)) for m in msgs.all()], ["0", "1"])
    teq(msg_statuses(msgs), [ss.unselected, ss.primary])
    # cut the top 1
    pg.kbp(key.up);
    pg.kbp("x")
    teq(msgs.count(), 1)
    teq([first(msgtxt(m)) for m in msgs.all()], ["1"])
    teq(msg_statuses(msgs), [ss.primary])
    # paste the message
    pg.kbp("v")
    teq(msgs.count(), 2)
    teq([first(msgtxt(m)) for m in msgs.all()], ["1", "0"])
    teq(msg_statuses(msgs), [ss.unselected, ss.primary])


def test_copy_paste_collapsed_section(pg: Page):
    msgs = pg.msgs()
    # create header with 2 notes
    pg.mk_msg('# 1', typ='note');
    pg.kbp('b');
    pg.mk_msg('1');
    pg.kbp('b');
    pg.mk_msg('2')
    teq(msgs.count(), 3)
    pg.toggle_collapse(msgs.nth(0))
    teq(msgs.count(), 1)
    # copy/paste the header
    pg.kbp('c');
    pg.kbp('v')
    teq(msgs.count(), 2)
    pg.toggle_collapse(msgs.nth(0))
    pg.toggle_collapse(msgs.nth(3))
    teq(msgs.count(), 6)
    teq([first(msgtxt(m)) for m in msgs.all()], ["# 1", "1", "2", "# 1", "1", "2"])
    teq(msg_statuses(msgs), [ss.unselected, ss.unselected, ss.unselected, ss.primary, ss.unselected, ss.unselected])


def test_cut_paste_collapsed_section(pg: Page):
    msgs = pg.msgs()
    # create header with 2 notes
    pg.mk_msg('# 1', typ='note');
    pg.kbp('b');
    pg.mk_msg('1.1');
    pg.kbp('b');
    pg.mk_msg('1.2')
    teq(msgs.count(), 3)
    pg.toggle_collapse(msgs.nth(0))
    teq(msgs.count(), 1)
    # create another header with 2 notes
    pg.kbp('b');
    pg.mk_msg('# 2', typ='note');
    pg.kbp('b');
    pg.mk_msg('2.1');
    pg.kbp('b');
    pg.mk_msg('2.2')
    teq(msgs.count(), 4)
    pg.toggle_collapse(msgs.nth(1))
    teq(msgs.count(), 2)
    teq([first(msgtxt(m)) for m in msgs.all()], ["# 1", "# 2"])
    # cut the top header
    pg.kbp(key.up);
    pg.kbp('x')
    teq(msgs.count(), 1)
    # paste it and check that the header ordering has now flipped
    pg.kbp('v')
    teq(msgs.count(), 2)
    teq([first(msgtxt(m)) for m in msgs.all()], ["# 2", "# 1"])
    # expand both headers and confirm all messages are in the correct place
    pg.toggle_collapse(msgs.nth(0))
    pg.toggle_collapse(msgs.nth(3))
    teq(msgs.count(), 6)
    teq([first(msgtxt(m)) for m in msgs.all()], ["# 2", "2.1", "2.2", "# 1", "1.1", "1.2"])
    teq(msg_statuses(msgs), [ss.unselected, ss.unselected, ss.unselected, ss.primary, ss.unselected, ss.unselected])


def test_collapse_sections(pg: Page):
    msgs = pg.msgs()
    pg.mk_msg('# 1', typ='note')
    pg.kbp('b');
    pg.mk_msg('## 1.1', typ='note')
    pg.kbp('b');
    pg.mk_msg('1.2', typ='note')
    teq(msgs.count(), 3)
    teq(msg_statuses(msgs), [ss.unselected, ss.unselected, ss.primary])
    # hitting left selects the nearest header
    pg.kbp(key.left)
    teq(msgs.count(), 3)
    teq(msg_statuses(msgs), [ss.unselected, ss.primary, ss.unselected])
    # hitting left again collapses the smaller section
    pg.kbp(key.left)
    teq(msgs.count(), 2)
    teq(msg_statuses(msgs), [ss.unselected, ss.primary])
    # hitting left again selects the parent section
    pg.kbp(key.left)
    teq(msgs.count(), 2)
    teq(msg_statuses(msgs), [ss.primary, ss.unselected])
    # hitting left again collapses the parent section
    pg.kbp(key.left)
    teq(msgs.count(), 1)
    teq(msg_statuses(msgs), [ss.primary])
    # add a header above
    pg.kbp('a');
    pg.mk_msg('# 0', typ='note');
    pg.kbp(key.down)
    teq(msgs.count(), 2)
    teq(msg_statuses(msgs), [ss.unselected, ss.primary])
    teq([first(msgtxt(m)) for m in msgs.all()], ["# 0", "# 1"])
    # hitting left does nothing because the primary message has no parent
    pg.kbp(key.down);
    pg.kbp(key.left)
    teq(msgs.count(), 2)
    teq(msg_statuses(msgs), [ss.unselected, ss.primary])
    # now, let's expand the parent section and confirm that the nested section is still hidden
    pg.kbp(key.right)
    teq(msgs.count(), 3)
    teq(msg_statuses(msgs), [ss.unselected, ss.primary, ss.unselected])
    teq([first(msgtxt(m)) for m in msgs.all()], ["# 0", "# 1", "## 1.1"])
    # now, let's expand the child section
    pg.kbp(key.down);
    pg.kbp(key.right)
    teq(msgs.count(), 4)
    teq(msg_statuses(msgs), [ss.unselected, ss.unselected, ss.primary, ss.unselected])
    teq([first(msgtxt(m)) for m in msgs.all()], ["# 0", "# 1", "## 1.1", "1.2"])


# TODO: need to figure out how to create a prompt msg without calling the llm (maybe use dialoghelper??)
# def test_extract_fenced_code_blocks(pg: Page):
#     pass

def test_hide_msg_from_ai(pg: Page):
    msgs = pg.msgs()
    pg.mk_msg('1')
    msg = msgs.nth(0)
    teq(has_icon(msg, 'eye'), True)
    teq(has_icon(msg, 'eye-off'), False)
    pg.kbp('h')
    teq(has_icon(msg, 'eye'), False)
    teq(has_icon(msg, 'eye-off'), True)


def test_export_msg(pg: Page):
    msgs = pg.msgs()
    pg.mk_msg('1')
    msg = msgs.nth(0)
    teq(has_icon(msg, 'bookmark-x'), True)
    teq(has_icon(msg, 'bookmark-check'), False)
    pg.kbp('e')
    teq(has_icon(msg, 'bookmark-x'), False)
    teq(has_icon(msg, 'bookmark-check'), True)


def test_pin_message(pg: Page):
    msgs = pg.msgs()
    pg.mk_msg('1')
    msg = msgs.nth(0)
    teq(has_icon(msg, 'pin-off'), True)
    teq(has_icon(msg, 'pin'), False)
    pg.kbp('p')
    teq(has_icon(msg, 'pin-off'), False)
    teq(has_icon(msg, 'pin'), True)


def test_run_above(pg: Page):
    # create 3 messages, select the last one, confirm `run_above_` is called.
    msgs = pg.msgs()
    pg.mk_msg("1")
    pg.add_below(msgs.nth(0));
    pg.mk_msg("2")
    pg.add_below(msgs.nth(1));
    pg.mk_msg("3")
    with pg.expect_request("**/run_above_"): pg.kbp("A")
    teq(msg_statuses(msgs), [ss.unselected, ss.unselected, ss.primary])


def test_run_below(pg: Page):
    # create 3 messages, select the first one, confirm `run_below_` is called.
    msgs = pg.msgs()
    pg.mk_msg("1")
    pg.add_below(msgs.nth(0));
    pg.mk_msg("2")
    pg.add_below(msgs.nth(1));
    pg.mk_msg("3")
    pg.kbp(key.up);
    pg.kbp(key.up)
    with pg.expect_request("**/run_below_"): pg.kbp("B")
    teq(msg_statuses(msgs), [ss.primary, ss.unselected, ss.unselected])


# -------------------
# MONACO EDITOR TESTS
# -------------------

# TODO:
# In-Editor keybind tests:
# Submit Message - ⌘ + Enter, Shift + Enter AND Alt + Enter
# Cancel Message - Escape
# Copy Last Message - Ctrl + ⇧ + ▲
# Split Message - ⌘ + ⇧ + Minus
# Code Message - ⌘ + ⇧ + j
# Note Message - ⌘ + ⇧ + k
# Prompt Message - ⌘ + ⇧ + l
# Raw Message - ⌘ + ⇧ + ;
# Toggle Expanded View - ⌘ + ⇧ + x
# Trigger Inline Completion - ⌥ + .
# Trigger Super Completion - ⌘ + ⇧ + .
# Accept Inline Completion - ▶ (Tab if enter_comp=True)
# Accept Shell Completion - Tab (Enter if enter_comp=True)

# Key things to test:
# - Edit mode correctly setup and executed both when clicking message header & via keyboard (Enter on selected msg)

def _msg_type(pg: Page):
    return pg.evaluate("() => document.querySelector('#msg_type')?.value")


def _sel_msg_type(pg: Page):
    return pg.evaluate("() => $pm[0].querySelector('[name=msg_type]')?.value")


def test_me_submit_meta(pg: Page):
    "Submit Message - meta + Enter should create a message from editor contents."
    pg.mk_msg("1+1")
    msgs = pg.msgs()
    teq(msgs.count(), 1)
    teq(msgtxt(msgs.nth(0))[0], "1+1")


def test_me_cancel_message(pg: Page):
    "Cancel Message - Escape should exit edit mode and persist edited input while keeping prior output (no re-run)."
    pg.mk_msg("2+2")  # creates message with input '2+2' and output '4'
    msgs = pg.msgs()
    teq(msgtxt(msgs.nth(0)), ["2+2", "4"])
    pg.edit_mode()
    teq(is_being_edited(msgs.nth(0)), True)
    pg.editor().fill('0/0')
    pg.kbp("Escape")
    teq(is_being_edited(msgs.nth(0)), False)
    # Input should now show new code, output should remain the old result '4'
    teq(msgtxt(msgs.nth(0)), ["0/0", "4"])


# TODO:
# Figure out what to do with this keybind (doesn't work well in selection mode)

# def test_me_copy_last_message(pg: Page):
#     """Copy Last Message - Ctrl + Shift + ArrowUp should load last message into editor when focused."""
#     pg.mk_msg("10")
#     pg.kbp('b'); pg.mk_msg("20")  # add below to create second message
#     msgs = pg.msgs()
#     teq(msgs.count(), 2)
#     # Focus editor for a new (unsent) message (slash key behavior tested in selection suite)
#     pg.kbp("/")
#     teq(is_editor_focused(pg), True)
#     # Press Control+Shift+ArrowUp (platform agnostic variant) to copy last message
#     pg.kbp("Control+Shift+ArrowUp")
#     # Fallback for macOS if underlying mapping expects Meta (harmless if already copied)
#     if _editor_value(pg) != "20":
#         pg.kbp("Meta+Shift+ArrowUp")
#     teq(_editor_value(pg), "20")
#     # No new message should have been created
#     teq(msgs.count(), 2)

def test_me_split_message(pg: Page):
    "Split Message with Ctrl + Shift + '-'"
    pg.mk_msg("1\n2")
    msgs = pg.msgs()
    teq(msgs.count(), 1)
    pg.edit_mode()
    pg.kbp("ArrowUp")  # Move cursor one line up, so message splits non-trivially
    with pg.expect_request("**/split_msg_"): pg.kbp("Control+Shift+-")
    teq(msgs.count(), 2)
    teq(msgtxt(msgs.nth(0)), ["1", "2"])
    teq(msgtxt(msgs.nth(1)), ["2"])


def test_me_change_message_type(pg: Page):
    "Message type switching with meta+shift+(J|K|L|;)."
    pg.mk_msg("# My New Message")

    # Test when editor focused
    pg.edit_mode()
    teq(is_editor_focused(pg), True)
    pg.kbp(f"{key.meta}+Shift+K")
    teq(_msg_type(pg), 'note')
    pg.kbp(f"{key.meta}+Shift+L")
    teq(_msg_type(pg), 'prompt')
    pg.kbp(f"{key.meta}+Shift+Semicolon")
    teq(_msg_type(pg), 'raw')
    pg.kbp(f"{key.meta}+Shift+J")
    teq(_msg_type(pg), 'code')

    # Test when editor not focused
    pg.kbp("Escape")
    teq(is_editor_focused(pg), False)
    pg.kbp(f"{key.meta}+Shift+K")
    teq(_sel_msg_type(pg), 'note')
    pg.kbp(f"{key.meta}+Shift+L")
    teq(_sel_msg_type(pg), 'prompt')
    pg.kbp(f"{key.meta}+Shift+J")
    teq(_sel_msg_type(pg), 'code')
    pg.kbp(f"{key.meta}+Shift+Semicolon")
    teq(_sel_msg_type(pg), 'raw')


def test_me_toggle_expanded_view(pg: Page):
    "Toggle Expanded View - meta+shift+X should change editor container height"
    h_before = pg.evaluate(
        "() => document.querySelector('.monaco-editor-container')?.getBoundingClientRect().height || 0")
    pg.kbp(f"{key.meta}+Shift+X")
    expect(pg.locator("#myeditor")).not_to_have_css("height", f"{h_before}px")

    # Test toggle back
    pg.kbp(f"{key.meta}+Shift+X")
    expect(pg.locator("#myeditor")).to_have_css("height", f"{h_before}px")


def test_me_ghost_text(pg: Page):
    "Trigger Inline Completion - Alt + Period should set inlineSuggestionVisible (if any completion available)."
    pg.editor().fill("from datetime import ")
    pg.kbp(f"{key.alt}+.")  # trigger ghost text (even in learning mode)
    pg.wait_for_function("() => window.editor?._contextKeyService.getContextKeyValue('inlineSuggestionVisible')",
                         timeout=8000)
    pg.kbp(key.right)
    # Assert that editor value has changed (ghost text accepted)
    expect(pg.editor()).not_to_have_value("from datetime import ")
    pg.kbp(key.escape)


def test_me_super_completion(pg: Page):
    "Trigger Super Completion - Meta + Shift + Period; ensure editor leaves readOnly state after cycle."
    pg.editor().fill("# simple fib function demo:\n\n")
    pg.kbp(f"{key.meta}+Shift+.")
    pg.wait_for_function("() => !window.editor?.getOption(window.monaco.editor.EditorOption.readOnly)", timeout=8000)

    # Assert editor value has changed (super completion triggered)
    expect(pg.editor()).not_to_have_value("# simple fib function demo:\n\n")
    is_read_only = pg.evaluate("() => window.editor?.getOption(window.monaco.editor.EditorOption.readOnly)")
    teq(is_read_only, False)
    pg.kbp(key.escape)


def test_me_shell_completion(pg: Page):
    "Open suggestion widget & accept first suggestion (Tab by default)"
    pg.editor().fill("import os\n\nos")
    pg.kbp('.')
    expect(pg.editor()).to_be_focused()
    pg.wait_for_function("`() => window.editor?._contextKeyService.getContextKeyValue('suggestWidgetVisible')`",
                         timeout=8000)
    # Press Tab (default accept if enter_comp=False)
    pg.kbp("Tab")
    # After acceptance suggest widget should be hidden & editor value changed
    hidden = pg.evaluate("() => window.editor?._contextKeyService.getContextKeyValue('suggestWidgetVisible')")
    teq(hidden, False)
    expect(pg.editor()).not_to_have_value("import os\n\nos.")
    pg.kbp(key.escape)

# Super Edit Test

# VIM Mode Test (with setting on/off)