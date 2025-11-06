"""
Vim Hotkey Reference Guide - Quick reference for vim keybindings
"""

from textual.widgets import Static
from rc3.plugins.base import BasePlugin


class Plugin(BasePlugin):
    """Vim hotkey reference guide plugin"""
    
    name = "Vim Hotkeys"
    description = "Vim keybinding reference guide"
    
    def render(self):
        """Render the vim hotkey reference guide"""
        guide = """VIM HOTKEY REFERENCE GUIDE

═══════════════════════════════════════════════════════════════════
FREQUENTLY USED - COPY/PASTE MASTERY
═══════════════════════════════════════════════════════════════════

BASIC COPY/PASTE (Yank/Delete/Put)
  yy           Yank (copy) current line
  3yy          Yank 3 lines starting from cursor
  dd           Delete (cut) current line
  5dd          Delete (cut) 5 lines
  p            Paste after cursor/below line
  P            Paste before cursor/above line
  yyp          Duplicate current line (yank then paste)

VISUAL MODE COPY/PASTE
  v + motion   Select characters, then y to copy
  V + motion   Select lines, then y to copy
  Ctrl+v       Block select, then y to copy column
  Example:     vjjy (select 3 lines down and copy)
  Example:     viwp (select word and paste over it)

COPY WITH TEXT OBJECTS (y + text object)
  yiw          Yank inner word (cursor on word)
  yaw          Yank a word (includes whitespace)
  yi"          Yank inside double quotes
  ya"          Yank around quotes (includes quotes)
  yi'          Yank inside single quotes
  yi(          Yank inside parentheses
  ya(          Yank around parentheses (includes parens)
  yi{          Yank inside braces
  yib          Yank inner block (same as yi{)
  yit          Yank inside HTML/XML tag
  yip          Yank inner paragraph
  yap          Yank a paragraph (includes blank lines)

ADVANCED COPY OPERATIONS
  y$           Yank to end of line
  y0           Yank to start of line
  y^           Yank to first non-blank character
  yG           Yank from cursor to end of file
  ygg          Yank from cursor to start of file
  y'a          Yank from cursor to mark 'a'
  y/pattern    Yank until search pattern match
  V%y          Yank from cursor to matching bracket

SYSTEM CLIPBOARD (Windows/Linux/Mac)
  "+yy         Copy line to system clipboard
  "+y          Copy selection to system clipboard
  "+p          Paste from system clipboard after
  "+P          Paste from system clipboard before
  "*yy         Copy to selection clipboard (Linux)
  "*p          Paste from selection clipboard
  Example:     "+yG (copy to end of file to clipboard)

REGISTERS (Multiple Clipboards)
  "ayy         Yank line into register 'a'
  "ayw         Yank word into register 'a'
  "ap          Paste from register 'a'
  "Ayy         Append line to register 'a'
  "0p          Paste last yanked text (not deleted)
  "1p          Paste last deleted text
  :reg         View all register contents
  :reg a       View register 'a' contents

PRACTICAL EXAMPLES
  yyp          Duplicate this line
  ddp          Swap current line with line below
  yiwppp       Copy word and paste 3 times
  V%y          Copy entire function/block
  ci"Ctrl+r0   Change inside quotes, paste last yank
  "+yG         Copy from here to EOF to clipboard
  gg"+yG       Copy entire file to clipboard
  "ayy"byy"ap"bp   Swap two lines using registers

DELETE AS CUT (Deleted text goes to clipboard)
  dw           Delete (cut) word
  diw          Delete inner word
  di"          Delete inside quotes
  d$           Delete to end of line
  dG           Delete to end of file
  Then: p      Paste what was deleted

═══════════════════════════════════════════════════════════════════
BASIC ESSENTIALS
═══════════════════════════════════════════════════════════════════

MODE SWITCHING
  i            Insert mode (before cursor)
  a            Insert mode (after cursor)
  o            Insert mode (new line below)
  O            Insert mode (new line above)
  ESC          Return to Normal mode
  v            Visual mode (character selection)
  V            Visual mode (line selection)
  Ctrl+v       Visual block mode
  :            Command mode

NAVIGATION
  h j k l      Left, Down, Up, Right
  w            Next word start
  b            Previous word start
  e            Next word end
  0            Start of line
  ^            First non-blank character
  $            End of line
  gg           Top of file
  G            Bottom of file
  {number}G    Go to line number
  Ctrl+d       Page down
  Ctrl+u       Page up

SAVE & QUIT
  :w           Save file
  :q           Quit (fails if unsaved)
  :wq          Save and quit
  :q!          Quit without saving
  :x           Save and quit (only if changes)
  ZZ           Save and quit
  ZQ           Quit without saving

BASIC EDITING
  x            Delete character under cursor
  dd           Delete line
  yy           Copy (yank) line
  p            Paste after cursor/line
  P            Paste before cursor/line
  u            Undo
  Ctrl+r       Redo
  .            Repeat last command
  >>           Indent line
  <<           Unindent line

═══════════════════════════════════════════════════════════════════
INTERMEDIATE
═══════════════════════════════════════════════════════════════════

TEXT OBJECTS (combine with d, c, y, v)
  iw           Inner word
  aw           A word (includes surrounding whitespace)
  is           Inner sentence
  as           A sentence
  ip           Inner paragraph
  ap           A paragraph
  i" i' i`     Inside quotes
  a" a' a`     Around quotes (includes quotes)
  i( i[ i{     Inside brackets
  a( a[ a{     Around brackets (includes brackets)
  it           Inner tag (HTML/XML)
  at           Around tag

REGISTERS
  "ay          Yank into register a
  "ap          Paste from register a
  :reg         Show all registers
  "+y          Copy to system clipboard
  "+p          Paste from system clipboard

MARKS
  ma           Set mark 'a' at cursor
  'a           Jump to mark 'a'
  `a           Jump to mark 'a' exact position
  '.           Jump to last edit position
  ''           Jump back to previous position

SEARCH & REPLACE
  /pattern     Search forward
  ?pattern     Search backward
  n            Next match
  N            Previous match
  *            Search word under cursor (forward)
  #            Search word under cursor (backward)
  :s/old/new   Replace first on line
  :s/old/new/g Replace all on line
  :%s/old/new/g Replace in entire file
  :%s/old/new/gc Replace with confirmation

VISUAL MODE OPERATIONS
  v + motion   Select text
  V + motion   Select lines
  Ctrl+v       Block select
  >            Indent selection
  <            Unindent selection
  y            Yank selection
  d            Delete selection
  c            Change selection
  ~            Toggle case
  U            Uppercase
  u            Lowercase

ADVANCED MOVEMENTS
  f{char}      Find next {char} on line
  F{char}      Find previous {char} on line
  t{char}      Till next {char} on line
  T{char}      Till previous {char} on line
  ;            Repeat last f/F/t/T
  ,            Repeat last f/F/t/T reverse
  %            Jump to matching bracket

MULTIPLE FILES
  :e file      Edit file
  :bn          Next buffer
  :bp          Previous buffer
  :bd          Delete buffer (close file)
  :ls          List buffers

═══════════════════════════════════════════════════════════════════
"""
        
        return Static(guide, classes="info")
