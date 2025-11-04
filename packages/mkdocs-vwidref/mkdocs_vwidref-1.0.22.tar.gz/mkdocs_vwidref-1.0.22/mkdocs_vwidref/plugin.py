# mkdocs_vwidref/plugin.py
from __future__ import annotations
import re
import logging
from typing import Dict, Optional, Any, Tuple
from urllib.parse import quote, urlsplit, urlunsplit
import posixpath

import yaml
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import Files, File
from mkdocs.structure.nav import Navigation

log = logging.getLogger("mkdocs.plugins.vwidref")

# Supported syntaxes (flags order flexible):
#   [[id:tm-gp]]
#   [[id:s:tm-gp]]
#   [[id:p:tm-gp]]
#   [[id:t:tm-gp]]
#   [[id:as:tm-gp]]
#   [[id:ap1:tm-gp]]
#   [[id:ap2:tm-gp]]
#   [[id:s:t:tm-gp]]
#   [[id:p:t:tm-gp]]
#   [[id:s:p:t:tm-gp]]
#   [[id:s:p:tm-gp]]
#   [[id:t:test-id#section-id]]          # NEW: explicit section fragment
# Optional custom label: [[id:s:t:tm-gp|Custom]]  (label only used when :t)
FLAG_TOKENS = ("ap2", "ap1", "as", "s", "p", "t", "idt", "c")
FLAG_PATTERN = "|".join(FLAG_TOKENS)
FLAG_SET = set(FLAG_TOKENS)

IDREF_PATTERN = re.compile(
    rf"""\[\[
        id:
        (?:(?P<flags>(?:(?:{FLAG_PATTERN}):)+))?  # zero or more known flags
        (?P<idfrag>[^|\]]+)                      # id or id#fragment (no '|' or ']]')
        (?:\|(?P<label>[^\]]+))?                 # optional |label (used only if :t)
    \]\]""",
    re.VERBOSE,
)

# Skip fenced code blocks when rewriting
FENCE_PATTERN = re.compile(r"(^|\n)(?P<fence>```|~~~)[^\n]*\n.*?(\n\2\s*$)", re.DOTALL)

def _read_front_matter(abs_path: str) -> Optional[dict]:
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            text = f.read()
        if not text.startswith("---\n"):
            return None
        end = text.find("\n---", 4)
        if end == -1:
            return None
        block = text[4:end]
        data = yaml.safe_load(block) or {}
        return data if isinstance(data, dict) else None
    except Exception as e:
        log.debug("[vwidref] front-matter read failed for %s: %s", abs_path, e)
        return None

def _format_page_url(url: str, use_directory_urls: bool) -> str:
    """
    Normalise MkDocs navigation URLs into either directory-style or .html links.
    The plugin forces root-relative links elsewhere, so return just the path here.
    """
    url = (url or "").strip()

    # Preserve root handling (empty string) for directory URLs to mirror MkDocs.
    if not url or url == "/":
        return "" if use_directory_urls else "index.html"

    if use_directory_urls:
        if url.endswith(".html"):
            url = url[:-5]
        if not url.endswith("/"):
            url += "/"
        return url

    # use_directory_urls is False -> prefer explicit .html files
    url = url.rstrip("/")
    if not url.endswith(".html"):
        url = f"{url}.html"
    return url

def _round_progress(value: Any) -> Optional[int]:
    try:
        raw = float(str(value).strip())
    except Exception:
        return None
    if raw < 0:
        return -1
    v = min(100.0, raw)
    choices = [0, 20, 40, 60, 80, 100]
    return min(choices, key=lambda c: abs(c - v))

# Progress bars WITHOUT angle brackets (angle brackets added only when multiple components shown)
PROGRESS_BARS = {
    -1:  ":board-progempty:",
    0:   ":board-progtodo:",
    20:  ":board-prog20:",
    40:  ":board-prog40:",
    60:  ":board-prog60:",
    80:  ":board-prog80:",
    100: ":board-progdone:",
}

STATUS_ICONS = {
    "todo": ":board-statustodo:",
    "inprogress": ":board-statusinprogress:",
    "done": ":board-statusdone:",
    "deprecated": ":board-statusdeprecated:",
}


def _progress_bar_from_round(value: Optional[str]) -> str:
    """
    Convert a rounded progress value (stored as string) into a shortcode.
    Returns empty string when no mapping is available.
    """
    if not value:
        return ""
    try:
        return PROGRESS_BARS.get(int(value), "")
    except (TypeError, ValueError):
        return ""

class IdRefPlugin(BasePlugin):
    """
    [[id:foo]] -> link to the page whose front-matter has id: foo
    [[id:foo#frag]] -> same page, but anchor to #frag (explicit section)

    Link text rules (title appears ONLY when :t is present):
      No flags        -> id string
      s               -> status only (no parentheses)
      p               -> progress only (no angle brackets)
      t               -> title only
      s:t             -> (status) Title
      p:t             -> <progress> Title
      s:p:t           -> (status) <progress> Title
      s:p             -> (status) <progress>        # no title without :t
    """

    config_scheme = (
        ("id_field",       config_options.Type(str, default="id")),
        ("title_field",    config_options.Type(str, default="title")),
        ("status_field",   config_options.Type(str, default="status")),
        ("progress_field", config_options.Type(str, default="progress")),
        ("auto_status_field", config_options.Type(str, default="auto_status")),
        ("auto_progress_1_field", config_options.Type(str, default="auto_progress_1")),
        ("auto_progress_2_field", config_options.Type(str, default="auto_progress_2")),
        ("append_hash",    config_options.Type(bool, default=True)),
        ("lowercase_ids",  config_options.Type(bool, default=False)),
        ("debug",          config_options.Type(bool, default=False)),
    )

    def __init__(self):
        super().__init__()
        self._id_index: Dict[str, Dict[str, str]] = {}
        self._current_page_url: str = ""

    def on_config(self, config: MkDocsConfig, **kwargs):
        self._current_page_url = ""
        return config

    # ---------- Index build ----------

    def on_files(self, files: Files, config: MkDocsConfig, **kwargs):
        id_key = self.config["id_field"]
        title_key = self.config["title_field"]
        status_key = self.config["status_field"]
        progress_key = self.config["progress_field"]
        auto_status_key = self.config["auto_status_field"]
        auto_prog1_key = self.config["auto_progress_1_field"]
        auto_prog2_key = self.config["auto_progress_2_field"]
        lower = self.config["lowercase_ids"]

        count = 0
        for f in files:
            if isinstance(f, File) and f.src_path.endswith((".md", ".markdown")):
                meta = _read_front_matter(f.abs_src_path)
                if not meta or id_key not in (meta or {}):
                    continue

                raw_id = str(meta.get(id_key) or "").strip()
                if not raw_id:
                    continue
                idx = raw_id.lower() if lower else raw_id

                title = str(meta.get(title_key) or "").strip()
                status = str(meta.get(status_key) or "").strip().lower() if status_key in meta else ""
                progress_val = meta.get(progress_key) if progress_key in meta else None
                progress_round = _round_progress(progress_val) if progress_val is not None else None
                auto_status = str(meta.get(auto_status_key) or "").strip().lower() if auto_status_key in meta else ""
                auto_prog1_val = meta.get(auto_prog1_key) if auto_prog1_key in meta else None
                auto_prog2_val = meta.get(auto_prog2_key) if auto_prog2_key in meta else None
                auto_prog1_round = _round_progress(auto_prog1_val) if auto_prog1_val is not None else None
                auto_prog2_round = _round_progress(auto_prog2_val) if auto_prog2_val is not None else None

                self._id_index[idx] = {
                    "src_path": f.src_path,
                    "url": "",  # filled in on_nav
                    "title": title,
                    "status": status,
                    "progress_round": str(progress_round) if progress_round is not None else "",
                    "auto_status": auto_status,
                    "auto_progress_round_1": str(auto_prog1_round) if auto_prog1_round is not None else "",
                    "auto_progress_round_2": str(auto_prog2_round) if auto_prog2_round is not None else "",
                    "id": raw_id,  # original case preserved
                }
                count += 1

        log.info("[vwidref] collected %d ids from front-matter", count)
        return files

    def on_nav(self, nav: Navigation, config: MkDocsConfig, files: Files, **kwargs):
        by_src = {p.file.src_path: p for p in nav.pages}
        updated = 0
        for idx, rec in self._id_index.items():
            p = by_src.get(rec["src_path"])
            if not p:
                continue
            url = _format_page_url(p.url or "", config.use_directory_urls)
            url = "/" + url.lstrip("/")   # root-relative
            rec["url"] = url
            if not rec["title"]:
                rec["title"] = getattr(p, "title", "") or idx
            updated += 1
        log.info("[vwidref] attached URLs for %d ids", updated)
        return nav

    # ---------- Helpers ----------

    def _resolve(self, token_id: str) -> Optional[Dict[str, str]]:
        key = token_id.lower() if self.config["lowercase_ids"] else token_id
        return self._id_index.get(key)

    def _parse_flags(self, flags_text: Optional[str]) -> Tuple[bool, bool, bool, bool, bool, bool, bool, bool]:
        if not flags_text:
            return (False, False, False, False, False, False, False, False)
        tokens = [t for t in flags_text.split(":") if t]
        has_known = any(t in FLAG_SET for t in tokens)
        want_s = "s" in tokens
        want_p = "p" in tokens
        want_t = "t" in tokens
        want_as = "as" in tokens
        want_ap1 = "ap1" in tokens
        want_ap2 = "ap2" in tokens
        want_id_title = "idt" in tokens
        return (has_known, want_s, want_p, want_t, want_as, want_ap1, want_ap2, want_id_title)

    def _split_id_and_fragment(self, idfrag: str) -> Tuple[str, Optional[str]]:
        # Accept 'base#fragment' (fragment may contain URL-safe chars; we'll encode)
        if "#" in idfrag:
            base, frag = idfrag.split("#", 1)
            base = base.strip()
            frag = frag.strip()
            return base, frag or None
        return idfrag.strip(), None

    # ---------- Rewriter ----------

    def _rewrite_block(self, text: str) -> str:
        def repl(m: re.Match) -> str:
            flags_text = m.group("flags")
            idfrag = m.group("idfrag")
            override_label = m.group("label")

            base_id, explicit_frag = self._split_id_and_fragment(idfrag)

            rec = self._resolve(base_id)
            if not rec or not rec.get("url"):
                log.warning("[vwidref] unresolved id '%s' in %r", base_id, m.group(0))
                return m.group(0)

            has_flags, want_s, want_p, want_t, want_as, want_ap1, want_ap2, want_id_title = self._parse_flags(flags_text)

            # Determine inclusion strictly by flags
            include_status = bool(want_s and STATUS_ICONS.get(rec.get("status", "").lower()))
            include_progress = bool(want_p and rec.get("progress_round"))
            include_title = bool(want_t or want_id_title)
            include_auto_status = bool(want_as and STATUS_ICONS.get(rec.get("auto_status", "").lower()))
            include_auto_progress_1 = bool(want_ap1 and rec.get("auto_progress_round_1"))
            include_auto_progress_2 = bool(want_ap2 and rec.get("auto_progress_round_2"))

            # Build title text (custom label used ONLY if include_title)
            title_text = ""
            if include_title:
                if want_id_title:
                    raw_id_text = (rec.get("id") or base_id).strip()
                    title_value = (rec.get("title") or "").strip()
                    if title_value:
                        title_text = f"{raw_id_text} {title_value}"
                    else:
                        title_text = raw_id_text or base_id
                else:
                    title_text = (override_label.strip() if override_label else (rec.get("title") or base_id)).strip()

            # Prepare components for formatting
            component_texts = []

            status_icon = STATUS_ICONS.get(rec.get("status", "").lower())
            auto_status_icon = STATUS_ICONS.get(rec.get("auto_status", "").lower())

            if include_status and status_icon:
                component_texts.append(("status", status_icon))
            if include_auto_status and auto_status_icon:
                component_texts.append(("status", auto_status_icon))

            if include_progress:
                bar = _progress_bar_from_round(rec.get("progress_round"))
                if bar:
                    component_texts.append(("progress", bar))

            if include_auto_progress_1:
                bar = _progress_bar_from_round(rec.get("auto_progress_round_1"))
                if bar:
                    component_texts.append(("progress", bar))

            if include_auto_progress_2:
                bar = _progress_bar_from_round(rec.get("auto_progress_round_2"))
                if bar:
                    component_texts.append(("progress", bar))

            if include_title and title_text:
                component_texts.append(("title", title_text))

            components_count = len(component_texts)

            # If no flags at all -> plain id
            if not has_flags:
                link_text = rec.get("id") or base_id
            else:
                parts = []
                for kind, value in component_texts:
                    if kind == "status":
                        parts.append(f"({value})" if components_count > 1 else value)
                    elif kind == "progress":
                        parts.append(f"<{value}>" if components_count > 1 else value)
                    else:
                        parts.append(value)
                if not parts:
                    parts = [rec.get("id") or base_id]
                link_text = " ".join(parts)

            url = rec["url"]
            if self.config["append_hash"]:
                if explicit_frag:
                    # Encode fragment but keep common anchor-safe characters
                    q = quote(explicit_frag, safe="-._~!$&\\'()*+,;=:@/")
                    url = f"{url}#{q}"
                else:
                    url = f"{url}#{quote(rec.get('id', base_id), safe='-._~')}"

            url = self._convert_html_to_md(url)
            current_url = getattr(self, "_current_page_url", "")
            url = self._make_relative(url, current_url)

            return f"[{link_text}]({url})"

        return IDREF_PATTERN.sub(repl, text)

    def on_page_markdown(self, markdown: str, page, config: MkDocsConfig, files: Files, **kwargs):
        if "[[id:" not in markdown:
            return markdown

        prev_page_url = self._current_page_url
        try:
            current_page_url = ""
            if page and getattr(page, "url", None) is not None:
                formatted = _format_page_url(page.url, config.use_directory_urls)
                formatted = "/" + formatted.lstrip("/") if formatted else "/"
                current_page_url = self._convert_html_to_md(formatted)
            self._current_page_url = current_page_url

            parts = []
            last = 0
            for m in FENCE_PATTERN.finditer(markdown):
                start, end = m.start(), m.end()
                parts.append(self._rewrite_block(markdown[last:start]))  # non-code
                parts.append(markdown[start:end])                        # keep code intact
                last = end
            parts.append(self._rewrite_block(markdown[last:]))

            new_md = "".join(parts)
            if self.config["debug"] and new_md != markdown:
                log.debug("[vwidref] rewrote links on page %s", getattr(page.file, "src_path", "?"))
            return new_md
        finally:
            self._current_page_url = prev_page_url

    def _make_relative(self, target_url: str, current_url: str) -> str:
        if not target_url or not current_url:
            return target_url

        target_parts = urlsplit(target_url)
        if target_parts.scheme or target_parts.netloc or target_url.startswith("//"):
            return target_url

        current_parts = urlsplit(current_url)

        relative_path = self._relative_path_between(current_parts.path, target_parts.path)

        return urlunsplit(("", "", relative_path, target_parts.query, target_parts.fragment))

    @staticmethod
    def _relative_path_between(current_path: str, target_path: str) -> str:
        cur = current_path.lstrip("/")
        tgt = target_path.lstrip("/")

        cur_is_dir = current_path.endswith("/") or current_path == ""
        tgt_is_dir = target_path.endswith("/") or target_path == ""

        base_dir = cur.rstrip("/") if cur_is_dir else posixpath.dirname(cur)
        base_dir = base_dir or "."

        target_rel = tgt.rstrip("/")
        target_rel = target_rel or "."

        rel = posixpath.relpath(target_rel, base_dir)

        if tgt_is_dir:
            if rel in (".", "./"):
                rel = "./"
            elif not rel.endswith("/"):
                rel = f"{rel}/"
        else:
            if rel == ".":
                rel = "./"

        return rel

    @staticmethod
    def _convert_html_to_md(url: str) -> str:
        if not url:
            return url
        parts = urlsplit(url)
        path = parts.path
        if path.endswith(".html"):
            path = f"{path[:-5]}.md"
        return urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))


# -*- coding: utf-8 -*-
"""
mkdocs-vwidref (add-on v1.0.22)

Adds optional inline HTML comments after [[id:...]] tokens with the front-matter title,
with a flag-controlled behavior:

- If the token contains ":c" before the final ID segment (e.g., [[id:t:c:72ca28_zh]]),
  the plugin will add/update the managed inline comment after the token.
- If the token does NOT contain ":c" (e.g., [[id:t:72ca28_zh]]),
  the plugin will NOT add a comment and will REMOVE any existing managed comment.

New mkdocs.yml setting:
  plugins:
    - vwidref:
        auto_add_id_comment: true   # default false

Other features:
- Handles namespaced tokens by taking the last colon-segment as the canonical ID.
- Preserves original line breaks (LF/CRLF).
- Managed comment prefix is shortened to "id-t:".
"""

# ---------------------------------------------------------------------------
# KEEP YOUR ORIGINAL IMPORTS / CODE / PLUGIN CLASS(ES) HERE
# ---------------------------------------------------------------------------
# Example placeholder (do not delete your real code):
# from mkdocs.plugins import BasePlugin
# class VWIDRefPlugin(BasePlugin):
#     config_scheme = ( ... )
#     def on_config(self, config): ...
#     def on_page_markdown(self, markdown, page, config, files): ...
#     def on_post_build(self, config): ...
#     def on_serve(self, server, config, builder): ...
#
# Leave everything above as-is.


# =============================================================================
# AUTO COMMENT ADD-ON (ADDITIVE, SAFE)
# =============================================================================
from typing import Dict, Optional, Tuple
import pathlib
import re
import yaml

try:
    from mkdocs.plugins import BasePlugin  # type: ignore
except Exception:
    BasePlugin = object  # static analysis fallback

_VW_AUTOCOMMENT_KEY = 'auto_add_id_comment'
_VW_ID_KEY          = 'id_key'
_VW_TITLE_KEY       = 'title_key'
_VW_DOCS_DIR_KEY    = 'docs_dir'

_FM_RE = re.compile(r"^---\n(.*?)\n---\n?", flags=re.S)

# [[id:...]] ; allow letters/digits/underscore/dash/colon
# tail allows spaces/tabs and an optional managed comment
_VW_TOKEN_RE = re.compile(
    r"(\[\[\s*id:([a-zA-Z0-9_:-]{1,})\s*\]\])"
    r"(?P<tail>[^\S\r\n]*(?:<!--\s*id-t:.*?-->)?)"
)

_FENCE_RE = re.compile(r"^\s*```")
_COMMENT_PREFIX = "id-t:"
_EOL_RE = re.compile(r"(?:\r\n|\r|\n)$")

def _compose_comment(text: str) -> str:
    safe = (text or "").replace("--", "—").strip()
    return f"<!-- {_COMMENT_PREFIX}{safe} -->"

def _canonicalize_id(raw: str) -> str:
    if not raw:
        return raw
    return raw.split(":")[-1].lower()

def _parse_token_id_and_flag(raw: str) -> Tuple[str, bool]:
    """
    Returns (canonical_id, has_c_flag)

    - canonical_id = last colon segment, lowercased
    - has_c_flag   = True if any colon segment BEFORE the last one equals "c"
                     e.g., "t:c:72ca28_zh"  -> (72ca28_zh, True)
                           "s:t:72ca28_zh" -> (72ca28_zh, False)
    """
    parts = (raw or "").split(":")
    if not parts:
        return "", False
    canon = parts[-1].lower()
    has_c = any(seg.lower() == "c" for seg in parts[:-1])
    return canon, has_c

def _build_id_title_map(docs_dir: pathlib.Path,
                        id_key: str = 'id',
                        title_key: str = 'title') -> Dict[str, Optional[str]]:
    id2title: Dict[str, Optional[str]] = {}
    for p in docs_dir.rglob("*.md"):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        m = _FM_RE.match(text)
        if not m:
            continue
        try:
            meta = yaml.safe_load(m.group(1)) or {}
        except Exception:
            meta = {}
        pid = meta.get(id_key)
        title = meta.get(title_key)
        if pid:
            canon = _canonicalize_id(str(pid))
            id2title[canon] = (None if not title else str(title).strip())
    return id2title

def _split_eol(s: str) -> Tuple[str, str]:
    m = _EOL_RE.search(s)
    if not m:
        return s, ""
    idx = m.start()
    return s[:idx], s[idx:]

def _remove_managed_comment(tail: str) -> str:
    """Remove our managed comment from tail, preserving any other content/whitespace."""
    if _COMMENT_PREFIX not in tail:
        return tail
    managed_re = re.compile(rf"\s*<!--\s*{re.escape(_COMMENT_PREFIX)}(.*?)-->\s*")
    # Replace with a single space only if there was space around; otherwise empty.
    new_tail = managed_re.sub(lambda m: " " if m.group(0).strip() != m.group(0) else "", tail)
    return new_tail

def _annotate_line_content(line_content: str, id2title: Dict[str, Optional[str]]) -> str:
    def repl(m):
        token = m.group(1)
        raw_id = (m.group(2) or "")
        tail = m.group("tail") or ""

        canon_id, has_c = _parse_token_id_and_flag(raw_id)
        title = id2title.get(canon_id)
        text_to_show = title if title else "NO title found in front-matter"
        new_comment = _compose_comment(text_to_show)

        if has_c:
            # COMMENT MODE: ensure our comment exists/updated
            if not tail.strip():
                return f"{token} {new_comment}"
            if _COMMENT_PREFIX in tail:
                managed_re = re.compile(rf"<!--\s*{re.escape(_COMMENT_PREFIX)}(.*?)-->")
                def upd(cm):
                    existing = (cm.group(1) or "").strip()
                    expected = text_to_show
                    return new_comment if existing != expected else cm.group(0)
                updated_tail = managed_re.sub(upd, tail)
                return f"{token}{updated_tail}"
            # Some other comment or spaces present -> append ours too
            return f"{token}{tail} {new_comment}"
        else:
            # SILENT MODE: do not add; remove our managed comment if present
            cleaned_tail = _remove_managed_comment(tail)
            return f"{token}{cleaned_tail}"

    return _VW_TOKEN_RE.sub(repl, line_content)

def _annotate_file(md_path: pathlib.Path, id2title: Dict[str, Optional[str]]) -> bool:
    try:
        original = md_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False

    lines = original.splitlines(keepends=True)
    out = []
    in_fence = False
    changed = False

    for ln in lines:
        content, eol = _split_eol(ln)

        if _FENCE_RE.match(content):
            in_fence = not in_fence
            out.append(content + eol)
            continue

        if in_fence:
            out.append(content + eol)
            continue

        new_content = _annotate_line_content(content, id2title)
        if new_content != content:
            changed = True
        out.append(new_content + eol)

    if changed:
        md_path.write_text("".join(out), encoding="utf-8")
    return changed

def _run_auto_add_id_comment(plugin_self, mkdocs_config):
    cfg = getattr(plugin_self, 'config', {}) or {}
    if not cfg.get(_VW_AUTOCOMMENT_KEY, False):
        return
    docs_dir = pathlib.Path(cfg.get(_VW_DOCS_DIR_KEY) or mkdocs_config['docs_dir'])
    id_key = cfg.get(_VW_ID_KEY, 'id')
    title_key = cfg.get(_VW_TITLE_KEY, 'title')
    id2title = _build_id_title_map(docs_dir, id_key=id_key, title_key=title_key)
    for p in docs_dir.rglob("*.md"):
        if _annotate_file(p, id2title):
            print(f"[vwidref] auto-added/updated id comments: {p}")

def _extend_config_scheme(original_scheme):
    try:
        from mkdocs.config import config_options
        new_scheme = list(original_scheme or ())
        present = {k for (k, *_rest) in new_scheme}
        if _VW_AUTOCOMMENT_KEY not in present:
            new_scheme.append((_VW_AUTOCOMMENT_KEY, config_options.Type(bool, default=False)))
        if _VW_ID_KEY not in present:
            new_scheme.append((_VW_ID_KEY,    config_options.Type(str,  default='id')))
        if _VW_TITLE_KEY not in present:
            new_scheme.append((_VW_TITLE_KEY, config_options.Type(str,  default='title')))
        if _VW_DOCS_DIR_KEY not in present:
            new_scheme.append((_VW_DOCS_DIR_KEY, config_options.Type(str, default=None)))
        return tuple(new_scheme)
    except Exception:
        return original_scheme

def _wrap_plugin_class(cls):
    class _VWAutoCommentWrapper(cls):  # type: ignore[misc]
        config_scheme = _extend_config_scheme(getattr(cls, 'config_scheme', ()))
        def on_config(self, config):
            if hasattr(super(), 'on_config'):
                ret = super().on_config(config)  # type: ignore[attr-defined]
            else:
                ret = config
            return ret
        def on_serve(self, server, config, builder):
            if hasattr(super(), 'on_serve'):
                server = super().on_serve(server, config, builder)  # type: ignore[attr-defined]
            _run_auto_add_id_comment(self, config)
            return server
        def on_post_build(self, config):
            if hasattr(super(), 'on_post_build'):
                super().on_post_build(config)  # type: ignore[attr-defined]
            _run_auto_add_id_comment(self, config)
    _VWAutoCommentWrapper.__name__ = cls.__name__
    return _VWAutoCommentWrapper

def _find_and_wrap_target_class():
    candidates = []
    for name, obj in globals().items():
        try:
            is_sub = isinstance(obj, type) and issubclass(obj, BasePlugin) and obj is not BasePlugin
        except Exception:
            is_sub = False
        if is_sub:
            candidates.append((name, obj))
    if not candidates:
        return
    chosen = None
    for name, obj in candidates:
        if 'vwidref' in name.lower():
            chosen = (name, obj)
            break
    if not chosen:
        chosen = candidates[0]
    name, cls = chosen
    wrapped = _wrap_plugin_class(cls)
    globals()[name] = wrapped

_find_and_wrap_target_class()
