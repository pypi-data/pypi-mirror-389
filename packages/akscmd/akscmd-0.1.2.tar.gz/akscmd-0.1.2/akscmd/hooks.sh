# akscmd shell hooks (bash + zsh). Enables typing <...> and pressing Enter once.

# --- Zsh ---
if [ -n "$ZSH_VERSION" ]; then
  function _akscmd_accept_line() {
    local buf="$BUFFER"
    if [[ "$buf" == \<* \> ]]; then
      local inner="${buf:1:${#buf}-2}"
      local cmd
      cmd="$(akscmd only-cmd "$inner" 2>/dev/null)"
      if [ -n "$cmd" ]; then
        BUFFER="$cmd"
        zle redisplay
        zle .accept-line
        return
      fi
    fi
    zle .accept-line
  }
  zle -N accept-line _akscmd_accept_line
fi

# --- Bash ---
if [ -n "$BASH_VERSION" ]; then
  __akscmd_accept_line() {
    local line="$READLINE_LINE"
    # Strict match: starts with '<' ends with '>'
    if [[ "$line" =~ ^\<.*\>$ ]]; then
      local inner="${line:1:${#line}-2}"
      local cmd
      cmd="$(akscmd only-cmd "$inner" 2>/dev/null)"
      if [ -n "$cmd" ]; then
        READLINE_LINE="$cmd"
        READLINE_POINT=${#READLINE_LINE}
      fi
    fi
  }
  # Intercept Enter. If this causes conflicts in your env, comment it and use Alt-a below.
  bind -x '"\r":"__akscmd_accept_line"'
  # Optional: Alt-a converts <...> to command without executing.
  __akscmd_convert_only() {
    local line="$READLINE_LINE"
    if [[ "$line" =~ ^\<.*\>$ ]]; then
      local inner="${line:1:${#line}-2}"
      local cmd
      cmd="$(akscmd only-cmd "$inner" 2>/dev/null)"
      if [ -n "$cmd" ]; then
        READLINE_LINE="$cmd"
        READLINE_POINT=${#READLINE_LINE}
      fi
    fi
  }
  bind -x '"\ea":"__akscmd_convert_only"'
fi
