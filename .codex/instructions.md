Prefer local workspace inspection over any remote repository fallback.

For non-trivial tasks, start by producing a short implementation plan and wait
for confirmation before making edits. Do not begin code changes immediately
unless the user explicitly asks for direct implementation.

Do not browse or rely on the remote GitHub tree for planning, review, or
implementation when the local workspace is available.

If local shell access fails, first try the simplest non-login, non-interactive
local read path. Only if local access is still unavailable, state that clearly
and describe the limitation before using any remote source.

For PR review or implementation work, do not base conclusions only on the remote
repository if local branch state may differ.
